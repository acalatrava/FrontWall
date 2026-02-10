import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db
from api.auth import router as auth_router, get_current_user
from api.sites import router as sites_router
from api.pages import router as pages_router
from api.rules import router as rules_router
from api.crawler import router as crawler_router, ws_router as crawler_ws_router
from api.shield import router as shield_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("webshield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.setup_dirs()
    await init_db()
    logger.info("Web Shield started — admin on port %s", settings.admin_port)
    yield
    logger.info("Web Shield shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(crawler_ws_router)
app.include_router(sites_router, dependencies=[Depends(get_current_user)])
app.include_router(pages_router, dependencies=[Depends(get_current_user)])
app.include_router(rules_router, dependencies=[Depends(get_current_user)])
app.include_router(crawler_router, dependencies=[Depends(get_current_user)])
app.include_router(shield_router, dependencies=[Depends(get_current_user)])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.app_version}


_static_candidates = [
    Path(__file__).parent / "static",
    Path(__file__).parent.parent / "frontend" / "dist",
]
for _candidate in _static_candidates:
    if _candidate.exists():
        app.mount("/", StaticFiles(directory=str(_candidate), html=True), name="frontend")
        break
