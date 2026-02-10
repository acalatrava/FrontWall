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
    }
