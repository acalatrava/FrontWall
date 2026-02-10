import logging
import mimetypes
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response

from config import settings
from shield.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger("webshield.shield.server")

BLOCKED_EXTENSIONS = {
    ".php", ".asp", ".aspx", ".jsp", ".cgi", ".pl", ".py", ".rb",
    ".sh", ".bash", ".env", ".ini", ".conf", ".yml", ".yaml",
    ".sql", ".bak", ".swp", ".log", ".htaccess", ".htpasswd",
    ".git", ".svn",
}

GENERIC_404 = Response(content="Not Found", status_code=404, media_type="text/plain")
GENERIC_403 = Response(content="Forbidden", status_code=403, media_type="text/plain")
GENERIC_400 = Response(content="Bad Request", status_code=400, media_type="text/plain")


def _is_path_safe(path: str) -> bool:
    """Prevent directory traversal and null byte attacks."""
    if not path:
        return True
    if "\x00" in path:
        return False
    parts = path.replace("\\", "/").split("/")
    for segment in parts:
        if not segment:
            continue
        if segment == "..":
            return False
        if segment.startswith("."):
            return False
    return True


def create_shield_app(site_id: str | None = None) -> FastAPI:
    """Create a hardened FastAPI app that serves cached static files."""

    shield = FastAPI(
        title="Web Shield",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    shield.add_middleware(SecurityHeadersMiddleware)

    @shield.api_route("/{path:path}", methods=["GET", "HEAD"])
    async def serve_static(request: Request, path: str = ""):
        if request.method not in ("GET", "HEAD"):
            return GENERIC_400

        if not _is_path_safe(path):
            logger.warning("Path traversal attempt blocked: %s (IP: %s)", path, request.client.host if request.client else "unknown")
            return GENERIC_403

        ext = Path(path).suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            logger.warning("Blocked extension access: %s (IP: %s)", path, request.client.host if request.client else "unknown")
            return GENERIC_403

        if site_id:
            cache_root = Path(settings.cache_dir) / site_id
        else:
            cache_root = Path(settings.cache_dir)

        if not path or path.endswith("/"):
            file_path = cache_root / path / "index.html"
        else:
            file_path = cache_root / path
            if file_path.is_dir():
                file_path = file_path / "index.html"
            elif not file_path.exists():
                file_path_with_html = cache_root / path / "index.html"
                if file_path_with_html.exists():
                    file_path = file_path_with_html

        try:
            resolved = file_path.resolve()
            cache_resolved = cache_root.resolve()
            if not str(resolved).startswith(str(cache_resolved)):
                logger.warning("Path escape attempt blocked: %s -> %s", path, resolved)
                return GENERIC_403
        except (OSError, ValueError):
            return GENERIC_403

        if not file_path.exists() or not file_path.is_file():
            return GENERIC_404

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            headers={"X-Served-By": "WebShield"},
        )

    return shield
