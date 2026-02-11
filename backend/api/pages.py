import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.page import Page
from models.site import Site
from schemas.page import PageResponse, PageCreate
from crawler.url_rewriter import URLRewriter
from crawler.asset_processor import extract_asset_urls, download_asset
from crawler.form_detector import detect_forms
from crawler.engine import CrawlerEngine
from database import async_session

logger = logging.getLogger("frontwall.api.pages")

router = APIRouter(prefix="/api/pages", tags=["pages"])


@router.get("/{site_id}", response_model=list[PageResponse])
async def list_pages(site_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Page).where(Page.site_id == site_id).order_by(Page.path)
    )
    return result.scalars().all()


@router.get("/{site_id}/stats")
async def page_stats(site_id: str, db: AsyncSession = Depends(get_db)):
    total = await db.execute(
        select(func.count(Page.id)).where(Page.site_id == site_id)
    )
    total_size = await db.execute(
        select(func.sum(Page.size_bytes)).where(Page.site_id == site_id)
    )
    with_forms = await db.execute(
        select(func.count(Page.id)).where(
            Page.site_id == site_id, Page.detected_forms.isnot(None)
        )
    )
    return {
        "total_pages": total.scalar() or 0,
        "total_size_bytes": total_size.scalar() or 0,
        "pages_with_forms": with_forms.scalar() or 0,
    }


@router.post("/add", response_model=PageResponse, status_code=201)
async def add_manual_page(data: PageCreate, db: AsyncSession = Depends(get_db)):
    """Manually add a URL to the cache — performs a full crawl of the page and its assets."""
    site = await db.get(Site, data.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    rewriter = URLRewriter(site.target_url)
    if not rewriter.is_same_origin(data.url):
        raise HTTPException(status_code=400, detail="URL must belong to the target site")

    cache_dir = Path(settings.cache_dir) / data.site_id
    cache_dir.mkdir(parents=True, exist_ok=True)

    auth = None
    if site.auth_user and site.auth_password:
        auth = httpx.BasicAuth(site.auth_user, site.auth_password)

    headers = {
        "User-Agent": "FrontWall Crawler/1.0 (+https://github.com/acalatrava/frontwall)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if site.internal_url:
        override_host = site.override_host or urlparse(site.target_url).netloc
        headers["Host"] = override_host

    def _to_fetch_url(url: str) -> str:
        if not site.internal_url:
            return url
        parsed = urlparse(url)
        int_parsed = urlparse(site.internal_url)
        return f"{int_parsed.scheme}://{int_parsed.netloc}{parsed.path}" + (
            f"?{parsed.query}" if parsed.query else ""
        )

    fetch_url = _to_fetch_url(data.url)

    try:
        async with httpx.AsyncClient(
            headers=headers, auth=auth, follow_redirects=True, http2=True,
        ) as client:
            resp = await client.get(fetch_url, timeout=30)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Target returned {resp.status_code}")

            content_type = resp.headers.get("content-type", "")

            if "text/html" not in content_type:
                cache_path = rewriter.url_to_cache_path(data.url)
                full_path = cache_dir / cache_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_bytes(resp.content)

                clean_path = rewriter.url_to_cache_path_no_query(data.url)
                if clean_path != cache_path:
                    clean_full = cache_dir / clean_path
                    if not clean_full.exists():
                        clean_full.parent.mkdir(parents=True, exist_ok=True)
                        clean_full.write_bytes(resp.content)

                page = Page(
                    site_id=data.site_id,
                    url=data.url,
                    path=rewriter.to_relative_path(data.url),
                    content_type=content_type.split(";")[0].strip(),
                    status_code=resp.status_code,
                    cache_path=cache_path,
                    size_bytes=len(resp.content),
                    is_manual=True,
                )
                db.add(page)
                await db.commit()
                await db.refresh(page)
                logger.info("Manual add asset %s: %d bytes cached", data.url, len(resp.content))
                return page

            html = resp.text
            rewritten = rewriter.rewrite_html(html)
            cache_path = rewriter.url_to_cache_path(data.url)
            full_path = cache_dir / cache_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(rewritten, encoding="utf-8")

            clean_path = rewriter.url_to_cache_path_no_query(data.url)
            if clean_path != cache_path:
                clean_full = cache_dir / clean_path
                if not clean_full.exists():
                    clean_full.parent.mkdir(parents=True, exist_ok=True)
                    clean_full.write_text(rewritten, encoding="utf-8")

            asset_urls = extract_asset_urls(html, data.url)
            translator = _to_fetch_url if site.internal_url else None
            assets_downloaded = 0
            for asset_url in asset_urls:
                if rewriter.is_same_origin(asset_url):
                    size = await download_asset(client, asset_url, cache_dir, rewriter, translator)
                    if size > 0:
                        assets_downloaded += 1

            forms_json = detect_forms(html, data.url)

            page = Page(
                site_id=data.site_id,
                url=data.url,
                path=rewriter.to_relative_path(data.url),
                content_type=content_type.split(";")[0].strip(),
                status_code=resp.status_code,
                cache_path=cache_path,
                size_bytes=len(rewritten.encode("utf-8")),
                is_manual=True,
                detected_forms=forms_json,
            )
            db.add(page)
            await db.commit()
            await db.refresh(page)

            logger.info("Manual add %s: page cached + %d assets downloaded", data.url, assets_downloaded)

            if data.spider:
                _launch_spider(data.site_id, data.url, site, cache_dir)

            return page

    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {exc}")


def _launch_spider(site_id: str, start_url: str, site, cache_dir: Path) -> None:
    """Launch a background spider starting from the given URL."""
    auth = None
    if site.auth_user and site.auth_password:
        auth = (site.auth_user, site.auth_password)

    engine = CrawlerEngine(
        site_id=site_id,
        target_url=site.target_url,
        cache_dir=cache_dir,
        max_concurrency=site.crawl_concurrency,
        delay=site.crawl_delay,
        max_pages=site.crawl_max_pages,
        respect_robots=site.respect_robots_txt,
        auth=auth,
        internal_url=site.internal_url,
        override_host=site.override_host,
    )
    engine.visited.add(start_url)

    async def _run():
        headers = {
            "User-Agent": "FrontWall Crawler/1.0 (+https://github.com/frontwall)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        if site.internal_url:
            headers["Host"] = site.override_host or urlparse(site.target_url).netloc

        http_auth = httpx.BasicAuth(auth[0], auth[1]) if auth else None

        try:
            async with httpx.AsyncClient(
                headers=headers, auth=http_auth, follow_redirects=True, http2=True,
            ) as client:
                spider_fetch_url = engine._to_fetch_url(start_url) if site.internal_url else start_url
                resp = await client.get(spider_fetch_url, follow_redirects=True, timeout=30)
                if resp.status_code != 200 or "text/html" not in resp.headers.get("content-type", ""):
                    return

                from bs4 import BeautifulSoup
                from urllib.parse import urljoin, urlparse
                soup = BeautifulSoup(resp.text, "lxml")
                rewriter = URLRewriter(site.target_url)

                for tag in soup.find_all("a", href=True):
                    href = tag.get("href")
                    if not href or not isinstance(href, str):
                        continue
                    if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                        continue
                    absolute = urljoin(start_url, href)
                    parsed = urlparse(absolute)
                    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        normalized += f"?{parsed.query}"
                    if rewriter.is_same_origin(normalized) and normalized not in engine.visited:
                        engine.queue.append(normalized)
                        engine.pages_found += 1

                if not engine.queue:
                    return

                logger.info("Spider from %s: discovered %d links", start_url, len(engine.queue))

                while engine.queue and not engine._stop_event.is_set():
                    if engine.pages_crawled >= engine.max_pages:
                        break
                    batch_size = min(engine.max_concurrency, len(engine.queue))
                    batch = [engine.queue.popleft() for _ in range(batch_size)]
                    tasks = [engine._crawl_page(client, url) for url in batch]
                    await asyncio.gather(*tasks)

            logger.info(
                "Spider from %s completed: %d pages, %d assets",
                start_url, engine.pages_crawled, engine.assets_downloaded,
            )
        except Exception as exc:
            logger.error("Spider from %s failed: %s", start_url, exc)

    asyncio.create_task(_run())


@router.delete("/{page_id}", status_code=204)
async def delete_page(page_id: str, db: AsyncSession = Depends(get_db)):
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    cache_file = Path(settings.cache_dir) / page.site_id / page.cache_path
    if cache_file.exists():
        cache_file.unlink()

    await db.delete(page)
    await db.commit()
