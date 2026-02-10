import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.crawl_job import CrawlJob
from schemas.crawl_job import CrawlJobResponse
from services import crawl_service

logger = logging.getLogger("webshield.api.crawler")

router = APIRouter(prefix="/api/crawler", tags=["crawler"])
ws_router = APIRouter(prefix="/api/crawler", tags=["crawler-ws"])

_ws_connections: dict[str, list[WebSocket]] = {}


@router.get("/jobs/{site_id}", response_model=list[CrawlJobResponse])
async def list_jobs(site_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrawlJob).where(CrawlJob.site_id == site_id).order_by(CrawlJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/jobs/{site_id}/latest", response_model=CrawlJobResponse | None)
async def latest_job(site_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrawlJob)
        .where(CrawlJob.site_id == site_id)
        .order_by(CrawlJob.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.post("/start/{site_id}", response_model=CrawlJobResponse, status_code=202)
async def start_crawl(site_id: str, db: AsyncSession = Depends(get_db)):
    async def progress_callback(data: dict):
        ws_list = _ws_connections.get(site_id, [])
        for ws in ws_list:
            try:
                await ws.send_json(data)
            except Exception:
                pass

    try:
        job = await crawl_service.start_crawl(site_id, db, progress_callback)
        return job
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/stop/{site_id}")
async def stop_crawl(site_id: str):
    stopped = crawl_service.stop_crawl(site_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="No active crawl for this site")
    return {"status": "stopping"}


@router.get("/status/{site_id}")
async def crawl_status(site_id: str):
    return {"is_crawling": crawl_service.is_crawling(site_id)}


@ws_router.websocket("/ws/{site_id}")
async def crawl_websocket(websocket: WebSocket, site_id: str):
    await websocket.accept()
    if site_id not in _ws_connections:
        _ws_connections[site_id] = []
    _ws_connections[site_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections[site_id].remove(websocket)
        if not _ws_connections[site_id]:
            del _ws_connections[site_id]
