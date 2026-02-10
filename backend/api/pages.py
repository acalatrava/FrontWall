import logging
from pathlib import Path

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

logger = logging.getLogger("webshield.api.pages")

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
    """Manually add a URL to the cache (fetch it from WordPress)."""
    site = await db.get(Site, data.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    rewriter = URLRewriter(site.target_url)
    if not rewriter.is_same_origin(data.url):
        raise HTTPException(status_code=400, detail="URL must belong to the target site")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(data.url)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Target returned {resp.status_code}")

            html = resp.text
            rewritten = rewriter.rewrite_html(html)
            cache_path = rewriter.url_to_cache_path(data.url)
            cache_dir = Path(settings.cache_dir) / data.site_id
            full_path = cache_dir / cache_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(rewritten, encoding="utf-8")

            page = Page(
                site_id=data.site_id,
                url=data.url,
                path=rewriter.to_relative_path(data.url),
                content_type="text/html",
                status_code=resp.status_code,
                cache_path=cache_path,
                size_bytes=len(rewritten.encode("utf-8")),
                is_manual=True,
            )
            db.add(page)
            await db.commit()
            await db.refresh(page)
            return page

    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {exc}")


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
