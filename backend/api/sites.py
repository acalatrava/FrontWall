from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.site import Site
from schemas.site import SiteCreate, SiteUpdate, SiteResponse

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("/", response_model=list[SiteResponse])
async def list_sites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    return result.scalars().all()


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str, db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post("/", response_model=SiteResponse, status_code=201)
async def create_site(data: SiteCreate, db: AsyncSession = Depends(get_db)):
    site = Site(**data.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(site_id: str, data: SiteUpdate, db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(site, key, value)
    await db.commit()
    await db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=204)
async def delete_site(site_id: str, db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await db.delete(site)
    await db.commit()
