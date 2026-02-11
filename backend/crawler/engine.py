import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models.page import Page
from models.crawl_job import CrawlJob
from crawler.url_rewriter import URLRewriter
from crawler.sitemap_parser import discover_urls_from_sitemaps
from crawler.form_detector import detect_forms
from crawler.asset_processor import extract_asset_urls, download_asset

logger = logging.getLogger("frontwall.crawler.engine")


class CrawlerEngine:
    """Async BFS crawler that mirrors a website into static files."""

    def __init__(
        self,
        site_id: str,
        target_url: str,
        cache_dir: Path,
        max_concurrency: int = 5,
        delay: float = 0.5,
        max_pages: int = 10000,
        respect_robots: bool = True,
        auth: tuple[str, str] | None = None,
        progress_callback: Callable[[dict[str, Any]], Any] | None = None,
        internal_url: str | None = None,
        override_host: str | None = None,
    ):
        self.site_id = site_id
        self.target_url = target_url.rstrip("/")
        self.cache_dir = cache_dir
        self.max_concurrency = max_concurrency
        self.delay = delay
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self.auth = auth
        self.progress_callback = progress_callback

        self.internal_url = internal_url.rstrip("/") if internal_url else None
        self.override_host = override_host or urlparse(self.target_url).netloc

        self.rewriter = URLRewriter(self.target_url)
        self.visited: set[str] = set()
        self.queue: deque[str] = deque()
        self.disallowed_paths: list[str] = []
        self.semaphore = asyncio.Semaphore(max_concurrency)

        self.pages_found = 0
        self.pages_crawled = 0
        self.assets_downloaded = 0
        self.errors = 0
        self.error_log: list[str] = []
        self._stop_event = asyncio.Event()
        self._downloaded_assets: set[str] = set()

    def _to_fetch_url(self, url: str) -> str:
        """Convert a public-facing URL to the actual fetch URL (internal if configured)."""
        if not self.internal_url:
            return url
        parsed = urlparse(url)
        internal_parsed = urlparse(self.internal_url)
        return f"{internal_parsed.scheme}://{internal_parsed.netloc}{parsed.path}" + (
            f"?{parsed.query}" if parsed.query else ""
        )

    def stop(self) -> None:
        self._stop_event.set()

    async def _emit_progress(self) -> None:
        if self.progress_callback:
            data = {
                "site_id": self.site_id,
                "pages_found": self.pages_found,
                "pages_crawled": self.pages_crawled,
                "assets_downloaded": self.assets_downloaded,
                "errors": self.errors,
                "queue_size": len(self.queue),
            }
            result = self.progress_callback(data)
            if asyncio.iscoroutine(result):
                await result

    @staticmethod
    def _is_directory_listing(html: str) -> bool:
        lower = html[:4096].lower()
        if "<title>index of " in lower or "<title>index of/" in lower:
            return True
        if ">[to parent directory]<" in lower:
            return True
        if '<pre><img alt="[' in lower and 'parent directory' in lower:
            return True
        return False

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        for disallowed in self.disallowed_paths:
            if parsed.path.startswith(disallowed):
                return False
        return True

    def _should_crawl(self, url: str) -> bool:
        if not self.rewriter.is_same_origin(url):
            return False
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        if clean_url in self.visited:
            return False
        if not self._is_allowed(url):
            return False
        skip_extensions = {".zip", ".tar", ".gz", ".exe", ".dmg", ".iso"}
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False
        return True

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean += f"?{parsed.query}"
        return clean

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            if not isinstance(tag, Tag):
                continue
            href = tag.get("href")
            if not href or not isinstance(href, str):
                continue
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(base_url, href)
            normalized = self._normalize_url(absolute)
            if self._should_crawl(normalized):
                links.append(normalized)
        return links

    async def _crawl_page(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> None:
        if self._stop_event.is_set():
            return

        async with self.semaphore:
            if url in self.visited:
                return
            self.visited.add(url)

            try:
                fetch_url = self._to_fetch_url(url)
                resp = await client.get(fetch_url, follow_redirects=True, timeout=30)
                content_type = resp.headers.get("content-type", "")

                if "text/html" not in content_type:
                    return

                html = resp.text

                if self._is_directory_listing(html):
                    logger.debug("Skipping directory listing: %s", url)
                    return

                cache_path = self.rewriter.url_to_cache_path(url)
                full_path = self.cache_dir / cache_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                rewritten_html = self.rewriter.rewrite_html(html)
                full_path.write_text(rewritten_html, encoding="utf-8")

                clean_path = self.rewriter.url_to_cache_path_no_query(url)
                if clean_path != cache_path:
                    clean_full = self.cache_dir / clean_path
                    if not clean_full.exists():
                        clean_full.parent.mkdir(parents=True, exist_ok=True)
                        clean_full.write_text(rewritten_html, encoding="utf-8")

                forms_json = detect_forms(html, url)

                async with async_session() as db:
                    page = Page(
                        site_id=self.site_id,
                        url=url,
                        path=self.rewriter.to_relative_path(url),
                        content_type=content_type.split(";")[0].strip(),
                        status_code=resp.status_code,
                        cache_path=cache_path,
                        size_bytes=len(rewritten_html.encode("utf-8")),
                        etag=resp.headers.get("etag"),
                        last_modified=resp.headers.get("last-modified"),
                        detected_forms=forms_json,
                    )
                    db.add(page)
                    try:
                        await db.commit()
                    except Exception:
                        await db.rollback()
                        logger.warning("Duplicate page skipped: %s", url)

                self.pages_crawled += 1
                await self._emit_progress()

                asset_urls = extract_asset_urls(html, url)
                translator = self._to_fetch_url if self.internal_url else None
                for asset_url in asset_urls:
                    if asset_url not in self._downloaded_assets and self.rewriter.is_same_origin(asset_url):
                        self._downloaded_assets.add(asset_url)
                        size = await download_asset(client, asset_url, self.cache_dir, self.rewriter, translator)
                        if size > 0:
                            self.assets_downloaded += 1

                new_links = self._extract_links(html, url)
                for link in new_links:
                    if link not in self.visited and link not in set(self.queue):
                        self.queue.append(link)
                        self.pages_found += 1

                if self.delay > 0:
                    await asyncio.sleep(self.delay)

            except Exception as exc:
                self.errors += 1
                msg = f"Error crawling {url}: {exc}"
                self.error_log.append(msg)
                logger.warning(msg)

    async def run(self, job_id: str) -> None:
        """Execute the crawl. Updates the CrawlJob record with progress."""
        async with async_session() as db:
            job = await db.get(CrawlJob, job_id)
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        headers = {
            "User-Agent": "FrontWall Crawler/1.0 (+https://github.com/frontwall)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if self.internal_url:
            headers["Host"] = self.override_host

        auth = None
        if self.auth:
            auth = httpx.BasicAuth(self.auth[0], self.auth[1])

        base_url = self.internal_url or self.target_url

        async with httpx.AsyncClient(
            headers=headers,
            auth=auth,
            follow_redirects=True,
            http2=True,
        ) as client:
            sitemap_urls, self.disallowed_paths = await discover_urls_from_sitemaps(
                client, base_url, self.respect_robots
            )

            self.queue.append(self.target_url)
            for url in sitemap_urls:
                normalized = self._normalize_url(url)
                if self._should_crawl(normalized):
                    self.queue.append(normalized)

            self.pages_found = len(self.queue)
            await self._emit_progress()

            while self.queue and not self._stop_event.is_set():
                if self.pages_crawled >= self.max_pages:
                    logger.info("Reached max pages limit (%d)", self.max_pages)
                    break

                batch_size = min(self.max_concurrency, len(self.queue))
                batch = [self.queue.popleft() for _ in range(batch_size)]

                tasks = [self._crawl_page(client, url) for url in batch]
                await asyncio.gather(*tasks)

        async with async_session() as db:
            job = await db.get(CrawlJob, job_id)
            job.status = "completed" if not self._stop_event.is_set() else "stopped"
            job.pages_found = self.pages_found
            job.pages_crawled = self.pages_crawled
            job.assets_downloaded = self.assets_downloaded
            job.errors = self.errors
            job.error_log = "\n".join(self.error_log) if self.error_log else None
            job.finished_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(
            "Crawl %s: %d pages, %d assets, %d errors",
            job.status, self.pages_crawled, self.assets_downloaded, self.errors,
        )
