import logging
from fastapi import APIRouter, HTTPException

from config import settings
from services import shield_service

logger = logging.getLogger("webshield.api.shield")

router = APIRouter(prefix="/api/shield", tags=["shield"])


@router.post("/deploy/{site_id}")
async def deploy(site_id: str):
    try:
        await shield_service.deploy_shield(site_id)
        return {
            "status": "deployed",
            "port": settings.shield_port,
            "message": f"Shield active on port {settings.shield_port}",
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to deploy shield: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to deploy shield")


@router.post("/undeploy")
async def undeploy():
    result = await shield_service.undeploy_shield()
    if not result:
        raise HTTPException(status_code=404, detail="No active shield")
    return {"status": "undeployed"}


@router.get("/status")
async def status():
    return {
        "active": shield_service.is_shield_active(),
        "port": settings.shield_port,
        "learn_mode": shield_service.is_learn_mode(),
    }


@router.post("/learn-mode")
async def toggle_learn_mode(enabled: bool = True):
    if not shield_service.is_shield_active():
        raise HTTPException(status_code=400, detail="Shield is not active")
    shield_service.set_learn_mode(enabled)
    return {"learn_mode": enabled}


@router.get("/learned-posts")
async def learned_posts():
    return shield_service.get_learned_posts()
