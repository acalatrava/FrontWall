import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import async_session
from models.site import Site
from models.page import Page
from models.crawl_job import CrawlJob
from crawler.engine import CrawlerEngine

logger = logging.getLogger("webshield.services.crawl")

_active_crawlers: dict[str, CrawlerEngine] = {}


async def start_crawl(
    site_id: str,
    db: AsyncSession,
    progress_callback: Callable[[dict[str, Any]], Any] | None = None,
) -> CrawlJob:
    """Start a new crawl job for the given site."""
    if site_id in _active_crawlers:
        raise RuntimeError(f"A crawl is already running for site {site_id}")

    site = await db.get(Site, site_id)
    if not site:
        raise ValueError(f"Site {site_id} not found")

    running = await db.execute(
        select(CrawlJob).where(CrawlJob.site_id == site_id, CrawlJob.status == "running")
    )
    if running.scalar_one_or_none():
        raise RuntimeError(f"A crawl is already running for site {site_id}")

    cache_dir = Path(settings.cache_dir) / site_id
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    existing_pages = await db.execute(select(Page).where(Page.site_id == site_id))
    for page in existing_pages.scalars():
        await db.delete(page)
    await db.commit()

    job = CrawlJob(site_id=site_id, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)

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
        progress_callback=progress_callback,
    )
    _active_crawlers[site_id] = engine

    async def _run_crawl():
        try:
            await engine.run(job.id)
        except Exception as exc:
            logger.error("Crawl failed for site %s: %s", site_id, exc)
            async with async_session() as session:
                crawl_job = await session.get(CrawlJob, job.id)
                if crawl_job:
                    crawl_job.status = "failed"
                    crawl_job.error_log = str(exc)
                    await session.commit()
        finally:
            _active_crawlers.pop(site_id, None)

    asyncio.create_task(_run_crawl())
    return job


def stop_crawl(site_id: str) -> bool:
    engine = _active_crawlers.get(site_id)
    if engine:
        engine.stop()
        return True
    return False


def is_crawling(site_id: str) -> bool:
    return site_id in _active_crawlers
