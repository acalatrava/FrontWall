import asyncio
import json
import logging
from urllib.parse import urlparse

logger = logging.getLogger("frontwall.shield.csp_learner")

_MAX_ORIGINS = 200


class CspLearner:
    """Captures CSP violation reports from the browser and learns which
    external origins a site actually needs."""

    def __init__(self, site_id: str):
        self.site_id = site_id
        self.enabled = False
        self.learned_origins: set[str] = set()
        self._dirty = False
        self._flush_task: asyncio.Task | None = None

    def start(self):
        self._flush_task = asyncio.create_task(self._flush_loop())

    def stop(self):
        if self._flush_task:
            self._flush_task.cancel()

    def load_persisted(self, origins_csv: str | None):
        """Load previously learned origins from the database."""
        if not origins_csv:
            return
        for o in origins_csv.split(","):
            o = o.strip()
            if o:
                self.learned_origins.add(o)

    def process_report(self, report_body: dict) -> str | None:
        """Process a CSP violation report and extract the blocked origin.
        Returns the newly learned origin or None if already known / invalid."""
        csp_report = report_body.get("csp-report", report_body)

        blocked_uri = csp_report.get("blocked-uri", "")
        if not blocked_uri:
            return None

        if blocked_uri in ("inline", "eval", "self", "data", "blob"):
            return None

        try:
            parsed = urlparse(blocked_uri)
            if not parsed.scheme or not parsed.netloc:
                return None
            origin = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return None

        if origin in self.learned_origins:
            return None

        if len(self.learned_origins) >= _MAX_ORIGINS:
            logger.warning("CSP learner for site %s hit max origins limit (%d)", self.site_id, _MAX_ORIGINS)
            return None

        self.learned_origins.add(origin)
        self._dirty = True
        logger.info("CSP learner discovered new origin for site %s: %s", self.site_id, origin)
        return origin

    def get_origins_csv(self) -> str:
        return ", ".join(sorted(self.learned_origins))

    async def _flush_loop(self):
        """Periodically persist learned origins to the database."""
        while True:
            try:
                await asyncio.sleep(10)
                if not self._dirty:
                    continue
                self._dirty = False
                await self._persist()
            except asyncio.CancelledError:
                if self._dirty:
                    await self._persist()
                break
            except Exception:
                logger.exception("CSP learner flush error for site %s", self.site_id)

    async def _persist(self):
        try:
            from database import async_session
            from models.site import Site

            csv = self.get_origins_csv()
            async with async_session() as db:
                site = await db.get(Site, self.site_id)
                if site:
                    site.learned_csp_origins = csv
                    await db.commit()
                    logger.info("Persisted %d learned CSP origins for site %s", len(self.learned_origins), self.site_id)
        except Exception:
            logger.exception("Failed to persist CSP origins for site %s", self.site_id)
