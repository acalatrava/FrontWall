import csv
import io
import json
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from database import async_session
from models.security_event import SecurityEvent
from services.security_collector import collector

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/global/summary")
async def global_summary(hours: int = Query(24, ge=1, le=720)):
    return await collector.get_global_summary(hours)


@router.get("/{site_id}/summary")
async def summary(site_id: str, hours: int = Query(24, ge=1, le=720)):
    return await collector.get_summary(site_id, hours)


@router.get("/{site_id}/timeline")
async def timeline(
    site_id: str,
    hours: int = Query(24, ge=1, le=720),
    bucket: str = Query("hour", pattern="^(hour|day|minute)$"),
):
    return await collector.get_timeline(site_id, hours, bucket)


@router.get("/{site_id}/top-attackers")
async def top_attackers(
    site_id: str,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(10, ge=1, le=50),
):
    return await collector.get_top_attackers(site_id, hours, limit)


@router.get("/{site_id}/event-types")
async def event_types(site_id: str, hours: int = Query(24, ge=1, le=720)):
    return await collector.get_event_type_breakdown(site_id, hours)


@router.get("/{site_id}/severity")
async def severity(site_id: str, hours: int = Query(24, ge=1, le=720)):
    return await collector.get_severity_breakdown(site_id, hours)


@router.get("/{site_id}/recent")
async def recent(site_id: str, limit: int = Query(50, ge=1, le=200)):
    return collector.get_recent(site_id, limit)


_EXPORT_COLUMNS = [
    "timestamp", "event_type", "severity", "client_ip",
    "method", "path", "user_agent", "details", "country", "blocked",
]


@router.get("/{site_id}/export")
async def export_events(
    site_id: str,
    hours: int = Query(24, ge=1, le=720),
    fmt: str = Query("csv", pattern="^(csv|json)$"),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with async_session() as session:
        stmt = (
            select(SecurityEvent)
            .where(SecurityEvent.site_id == site_id)
            .where(SecurityEvent.timestamp >= cutoff)
            .order_by(SecurityEvent.timestamp.desc())
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

    rows = []
    for ev in events:
        rows.append({
            "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
            "event_type": ev.event_type,
            "severity": ev.severity,
            "client_ip": ev.client_ip,
            "method": ev.method,
            "path": ev.path,
            "user_agent": ev.user_agent,
            "details": ev.details,
            "country": ev.country or "",
            "blocked": str(ev.blocked),
        })

    filename = f"security_events_{site_id[:8]}_{hours}h"

    if fmt == "json":
        content = json.dumps(rows, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
        )

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_EXPORT_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
