import logging
from fastapi import APIRouter, HTTPException

from services import shield_service

logger = logging.getLogger("frontwall.api.shield")

router = APIRouter(prefix="/api/shield", tags=["shield"])


@router.post("/deploy/{site_id}")
async def deploy(site_id: str):
    try:
        port = await shield_service.deploy_shield(site_id)
        return {
            "status": "deployed",
            "site_id": site_id,
            "port": port,
            "message": f"Shield active on port {port}",
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to deploy shield for site %s: %s", site_id, exc)
        raise HTTPException(status_code=500, detail="Failed to deploy shield")


@router.post("/undeploy/{site_id}")
async def undeploy(site_id: str):
    result = await shield_service.undeploy_shield(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="No active shield for this site")
    return {"status": "undeployed", "site_id": site_id}


@router.get("/status")
async def status_all():
    shields = shield_service.get_all_shields_status()
    return {"shields": shields}


@router.get("/status/{site_id}")
async def status_site(site_id: str):
    return {
        "site_id": site_id,
        "active": shield_service.is_shield_active(site_id),
        "learn_mode": shield_service.is_learn_mode(site_id),
    }


@router.post("/learn-mode/{site_id}")
async def toggle_learn_mode(site_id: str, enabled: bool = True):
    if not shield_service.is_shield_active(site_id):
        raise HTTPException(status_code=400, detail="Shield is not active for this site")
    shield_service.set_learn_mode(site_id, enabled)
    return {"site_id": site_id, "learn_mode": enabled}


@router.get("/learned-posts/{site_id}")
async def learned_posts(site_id: str):
    return shield_service.get_learned_posts(site_id)


@router.get("/learned-assets/{site_id}")
async def learned_assets(site_id: str):
    return shield_service.get_learned_assets(site_id)
