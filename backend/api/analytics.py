from fastapi import APIRouter, Query

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
