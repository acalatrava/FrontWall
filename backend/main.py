import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete

from config import settings
from database import init_db, async_session
from services.shield_service import auto_deploy_if_needed
from services.security_collector import collector as security_collector
from api.auth import router as auth_router, require_admin_for_writes
from api.sites import router as sites_router
from api.pages import router as pages_router
from api.rules import router as rules_router
from api.crawler import router as crawler_router, ws_router as crawler_ws_router
from api.shield import router as shield_router
from api.analytics import router as analytics_router
from models.refresh_token import RefreshToken

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("frontwall")

_cleanup_task: asyncio.Task | None = None


async def _cleanup_expired_tokens():
    while True:
        try:
            await asyncio.sleep(3600)
            async with async_session() as db:
                now = datetime.now(timezone.utc)
                result = await db.execute(
                    delete(RefreshToken).where(
                        (RefreshToken.expires_at < now) | (RefreshToken.revoked == True)  # noqa: E712
                    )
                )
                await db.commit()
                if result.rowcount:
                    logger.info("Cleaned up %d expired/revoked refresh tokens", result.rowcount)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Token cleanup error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cleanup_task
    settings.setup_dirs()
    await init_db()
    await auto_deploy_if_needed()
    _cleanup_task = asyncio.create_task(_cleanup_expired_tokens())
    security_collector.start()
    logger.info("FrontWall started — admin on port %s", settings.admin_port)
    yield
    security_collector.stop()
    if _cleanup_task:
        _cleanup_task.cancel()
    logger.info("FrontWall shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_cors_origins = [
    f"http://localhost:{settings.admin_port}",
    f"http://127.0.0.1:{settings.admin_port}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Requested-With"],
)


app.include_router(auth_router)
app.include_router(crawler_ws_router)
app.include_router(sites_router, dependencies=[Depends(require_admin_for_writes)])
app.include_router(pages_router, dependencies=[Depends(require_admin_for_writes)])
app.include_router(rules_router, dependencies=[Depends(require_admin_for_writes)])
app.include_router(crawler_router, dependencies=[Depends(require_admin_for_writes)])
app.include_router(shield_router, dependencies=[Depends(require_admin_for_writes)])
app.include_router(analytics_router, dependencies=[Depends(require_admin_for_writes)])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


_static_dir: Path | None = None
for _candidate in [
    Path(__file__).parent / "static",
    Path(__file__).parent.parent / "frontend" / "dist",
]:
    if _candidate.exists():
        _static_dir = _candidate
        break

if _static_dir:
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="static-assets")

    _index_html = _static_dir / "index.html"

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str = ""):
        file_path = _static_dir / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_index_html))
