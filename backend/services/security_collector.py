import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, delete, text

from database import async_session
from models.security_event import SecurityEvent

logger = logging.getLogger("frontwall.services.security_collector")

_FLUSH_INTERVAL = 2
_CLEANUP_INTERVAL = 3600
_RETENTION_DAYS = 30
_RING_MAX = 1000


class SecurityEventCollector:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._rings: dict[str, deque] = {}
        self._global_ring: deque = deque(maxlen=_RING_MAX)
        self._flush_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None

    def start(self):
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    def stop(self):
        if self._flush_task:
            self._flush_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

    def emit(
        self,
        event_type: str,
        severity: str,
        client_ip: str,
        path: str = "",
        method: str = "GET",
        user_agent: str = "",
        site_id: str | None = None,
        details: dict | None = None,
        blocked: bool = True,
    ):
        now = datetime.now(timezone.utc)
        event = {
            "site_id": site_id,
            "timestamp": now.isoformat(),
            "event_type": event_type,
            "severity": severity,
            "client_ip": client_ip,
            "path": path,
            "method": method,
            "user_agent": user_agent[:500],
            "details": json.dumps(details or {}),
            "blocked": blocked,
        }

        self._global_ring.append(event)
        if site_id:
            if site_id not in self._rings:
                self._rings[site_id] = deque(maxlen=_RING_MAX)
            self._rings[site_id].append(event)

        self._queue.put_nowait(event)

    def get_recent(self, site_id: str | None = None, limit: int = 50) -> list[dict]:
        if site_id:
            ring = self._rings.get(site_id, deque())
        else:
            ring = self._global_ring
        items = list(ring)
        items.reverse()
        return items[:limit]

    async def get_summary(self, site_id: str, hours: int = 24) -> dict:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        yesterday_start = since - timedelta(hours=hours)
        async with async_session() as db:
            total_q = await db.execute(
                select(func.count(SecurityEvent.id)).where(
                    SecurityEvent.site_id == site_id,
                    SecurityEvent.timestamp >= since,
                )
            )
            total_today = total_q.scalar() or 0

            total_prev_q = await db.execute(
                select(func.count(SecurityEvent.id)).where(
                    SecurityEvent.site_id == site_id,
                    SecurityEvent.timestamp >= yesterday_start,
                    SecurityEvent.timestamp < since,
                )
            )
            total_prev = total_prev_q.scalar() or 0

            ips_q = await db.execute(
                select(func.count(func.distinct(SecurityEvent.client_ip))).where(
                    SecurityEvent.site_id == site_id,
                    SecurityEvent.timestamp >= since,
                )
            )
            unique_ips = ips_q.scalar() or 0

            top_type_q = await db.execute(
                select(SecurityEvent.event_type, func.count(SecurityEvent.id).label("cnt"))
                .where(SecurityEvent.site_id == site_id, SecurityEvent.timestamp >= since)
                .group_by(SecurityEvent.event_type)
                .order_by(text("cnt DESC"))
                .limit(1)
            )
            top_row = top_type_q.first()
            top_type = top_row[0] if top_row else None

            sev_q = await db.execute(
                select(SecurityEvent.severity, func.count(SecurityEvent.id).label("cnt"))
                .where(SecurityEvent.site_id == site_id, SecurityEvent.timestamp >= since)
                .group_by(SecurityEvent.severity)
                .order_by(text("cnt DESC"))
                .limit(1)
            )
            sev_row = sev_q.first()

            threat_level = "none"
            if total_today > 0 and sev_row:
                threat_level = sev_row[0]

        return {
            "total_events": total_today,
            "total_prev_period": total_prev,
            "unique_ips": unique_ips,
            "top_event_type": top_type,
            "threat_level": threat_level,
        }

    async def get_timeline(self, site_id: str, hours: int = 24, bucket: str = "hour") -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with async_session() as db:
            if bucket == "day":
                fmt = "%Y-%m-%d"
            elif bucket == "minute":
                fmt = "%Y-%m-%d %H:%M"
            else:
                fmt = "%Y-%m-%d %H:00"

            q = await db.execute(
                select(
                    func.strftime(fmt, SecurityEvent.timestamp).label("bucket"),
                    SecurityEvent.severity,
                    func.count(SecurityEvent.id).label("cnt"),
                )
                .where(SecurityEvent.site_id == site_id, SecurityEvent.timestamp >= since)
                .group_by("bucket", SecurityEvent.severity)
                .order_by(text("bucket ASC"))
            )
            rows = q.all()

        buckets: dict[str, dict] = {}
        for b, sev, cnt in rows:
            if b not in buckets:
                buckets[b] = {"bucket": b, "critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
            buckets[b][sev] = cnt
            buckets[b]["total"] += cnt

        return list(buckets.values())

    async def get_top_attackers(self, site_id: str, hours: int = 24, limit: int = 10) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with async_session() as db:
            q = await db.execute(
                select(
                    SecurityEvent.client_ip,
                    func.count(SecurityEvent.id).label("cnt"),
                    func.max(SecurityEvent.timestamp).label("last_seen"),
                )
                .where(SecurityEvent.site_id == site_id, SecurityEvent.timestamp >= since)
                .group_by(SecurityEvent.client_ip)
                .order_by(text("cnt DESC"))
                .limit(limit)
            )
            rows = q.all()

            result = []
            for ip, cnt, last_seen in rows:
                type_q = await db.execute(
                    select(SecurityEvent.event_type, func.count(SecurityEvent.id).label("c"))
                    .where(
                        SecurityEvent.site_id == site_id,
                        SecurityEvent.client_ip == ip,
                        SecurityEvent.timestamp >= since,
                    )
                    .group_by(SecurityEvent.event_type)
                    .order_by(text("c DESC"))
                    .limit(1)
                )
                type_row = type_q.first()
                sev_q = await db.execute(
                    select(SecurityEvent.severity)
                    .where(
                        SecurityEvent.site_id == site_id,
                        SecurityEvent.client_ip == ip,
                        SecurityEvent.timestamp >= since,
                    )
                    .order_by(
                        text("CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END")
                    )
                    .limit(1)
                )
                sev_row = sev_q.first()

                result.append({
                    "ip": ip,
                    "count": cnt,
                    "last_seen": last_seen.isoformat() if last_seen else None,
                    "top_event_type": type_row[0] if type_row else None,
                    "severity": sev_row[0] if sev_row else "low",
                })
        return result

    async def get_event_type_breakdown(self, site_id: str, hours: int = 24) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with async_session() as db:
            q = await db.execute(
                select(SecurityEvent.event_type, func.count(SecurityEvent.id).label("cnt"))
                .where(SecurityEvent.site_id == site_id, SecurityEvent.timestamp >= since)
                .group_by(SecurityEvent.event_type)
                .order_by(text("cnt DESC"))
            )
            return [{"event_type": t, "count": c} for t, c in q.all()]

    async def get_severity_breakdown(self, site_id: str, hours: int = 24) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with async_session() as db:
            q = await db.execute(
                select(SecurityEvent.severity, func.count(SecurityEvent.id).label("cnt"))
                .where(SecurityEvent.site_id == site_id, SecurityEvent.timestamp >= since)
                .group_by(SecurityEvent.severity)
            )
            return [{"severity": s, "count": c} for s, c in q.all()]

    async def get_global_summary(self, hours: int = 24) -> dict:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with async_session() as db:
            total_q = await db.execute(
                select(func.count(SecurityEvent.id)).where(SecurityEvent.timestamp >= since)
            )
            total = total_q.scalar() or 0

            ips_q = await db.execute(
                select(func.count(func.distinct(SecurityEvent.client_ip))).where(
                    SecurityEvent.timestamp >= since
                )
            )
            unique_ips = ips_q.scalar() or 0

            top_type_q = await db.execute(
                select(SecurityEvent.event_type, func.count(SecurityEvent.id).label("cnt"))
                .where(SecurityEvent.timestamp >= since)
                .group_by(SecurityEvent.event_type)
                .order_by(text("cnt DESC"))
                .limit(1)
            )
            top_row = top_type_q.first()

            sites_q = await db.execute(
                select(func.count(func.distinct(SecurityEvent.site_id))).where(
                    SecurityEvent.timestamp >= since
                )
            )
            affected_sites = sites_q.scalar() or 0

        return {
            "total_events": total,
            "unique_ips": unique_ips,
            "top_event_type": top_row[0] if top_row else None,
            "affected_sites": affected_sites,
        }

    async def _flush_loop(self):
        while True:
            try:
                await asyncio.sleep(_FLUSH_INTERVAL)
                batch = []
                while not self._queue.empty() and len(batch) < 200:
                    try:
                        batch.append(self._queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                if not batch:
                    continue

                async with async_session() as db:
                    for evt in batch:
                        row = SecurityEvent(
                            site_id=evt["site_id"],
                            timestamp=datetime.fromisoformat(evt["timestamp"]),
                            event_type=evt["event_type"],
                            severity=evt["severity"],
                            client_ip=evt["client_ip"],
                            path=evt["path"],
                            method=evt["method"],
                            user_agent=evt["user_agent"],
                            details=evt["details"],
                            blocked=evt["blocked"],
                        )
                        db.add(row)
                    await db.commit()
                    logger.debug("Flushed %d security events to DB", len(batch))
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Security event flush error")

    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(_CLEANUP_INTERVAL)
                cutoff = datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)
                async with async_session() as db:
                    result = await db.execute(
                        delete(SecurityEvent).where(SecurityEvent.timestamp < cutoff)
                    )
                    await db.commit()
                    if result.rowcount:
                        logger.info("Purged %d old security events", result.rowcount)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Security event cleanup error")


collector = SecurityEventCollector()
