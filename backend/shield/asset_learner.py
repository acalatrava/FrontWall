import asyncio
import logging
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, quote

import httpx

from config import settings
from crawler.url_rewriter import URLRewriter

logger = logging.getLogger("webshield.shield.asset_learner")


class AssetLearner:
    """Fetches missing assets from the origin server when learn mode is active."""

    def __init__(
        self,
        site_id: str,
        target_url: str,
        cache_dir: Path,
        internal_url: str | None = None,
        override_host: str | None = None,
    ):
        self.site_id = site_id
        self.target_url = target_url.rstrip("/")
        self.cache_dir = cache_dir
        self.internal_url = internal_url.rstrip("/") if internal_url else None
        self.override_host = override_host or urlparse(target_url).netloc
        self.enabled = False
        self.learned_assets: list[dict] = []
        self.rewriter = URLRewriter(target_url)
        self._pending: set[str] = set()

    def _build_fetch_url(self, path: str) -> str:
        base = self.internal_url if self.internal_url else self.target_url
        return base + "/" + path.lstrip("/")

    async def try_fetch_and_cache(self, path: str, query: str = "") -> Path | None:
        """Try to fetch a missing resource from the origin and cache it.
        Returns the cached file path on success, None on failure.
        """
        if not self.enabled:
            return None

        if path in self._pending:
            return None
        self._pending.add(path)

        fetch_url = self._build_fetch_url(path)
        if query:
            fetch_url += f"?{query}"

        headers = {
            "User-Agent": "WebShield AssetLearner/1.0",
            "Accept": "*/*",
        }
        if self.internal_url:
            headers["Host"] = self.override_host

        try:
            async with httpx.AsyncClient(
                headers=headers, follow_redirects=True, timeout=15,
            ) as client:
                resp = await client.get(fetch_url)

            if resp.status_code != 200:
                self._pending.discard(path)
                return None

            content_type = resp.headers.get("content-type", "")
            content = resp.content

            if "text/css" in content_type:
                text = content.decode("utf-8", errors="replace")
                text = self.rewriter.rewrite_css(text)
                content = text.encode("utf-8")
            elif "text/html" in content_type:
                text = content.decode("utf-8", errors="replace")
                text = self.rewriter.rewrite_html(text)
                content = text.encode("utf-8")

            public_url = self.target_url + "/" + path.lstrip("/")
            cache_path = self.rewriter.url_to_cache_path(public_url)
            full_path = self.cache_dir / cache_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(content)

            clean_path = self.rewriter.url_to_cache_path_no_query(public_url)
            if clean_path != cache_path:
                clean_full = self.cache_dir / clean_path
                if not clean_full.exists():
                    clean_full.parent.mkdir(parents=True, exist_ok=True)
                    clean_full.write_bytes(content)

            already_known = any(a["path"] == path for a in self.learned_assets)
            if not already_known:
                self.learned_assets.append({
                    "path": "/" + path.lstrip("/"),
                    "content_type": content_type.split(";")[0].strip(),
                    "size": len(content),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            logger.info(
                "Learned asset: /%s (%s, %d bytes)",
                path, content_type.split(";")[0].strip(), len(content),
            )

            self._pending.discard(path)
            return full_path

        except Exception as exc:
            logger.debug("Failed to learn asset /%s: %s", path, exc)
            self._pending.discard(path)
            return None
