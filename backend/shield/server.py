import logging
import mimetypes
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response

from config import settings
from crawler.url_rewriter import URLRewriter
from shield.security_headers import SecurityHeadersMiddleware, CspState

logger = logging.getLogger("frontwall.shield.server")

BLOCKED_EXTENSIONS = {
    ".php", ".asp", ".aspx", ".jsp", ".cgi", ".pl", ".py", ".rb",
    ".sh", ".bash", ".env", ".ini", ".conf", ".yml", ".yaml",
    ".sql", ".bak", ".swp", ".log", ".htaccess", ".htpasswd",
    ".git", ".svn",
}

GENERIC_404 = Response(content="Not Found", status_code=404, media_type="text/plain")
GENERIC_403 = Response(content="Forbidden", status_code=403, media_type="text/plain")
GENERIC_400 = Response(content="Bad Request", status_code=400, media_type="text/plain")

BYPASS_HOP_HEADERS = {
    "transfer-encoding", "connection", "keep-alive", "te",
    "trailer", "upgrade", "proxy-authorization", "proxy-authenticate",
}


class BypassState:
    def __init__(self, target_url: str, internal_url: str | None = None, override_host: str | None = None):
        self.enabled = False
        self.target_url = target_url
        self.internal_url = internal_url
        self.override_host = override_host


async def _bypass_proxy_request(bp: BypassState, request: Request, path: str) -> Response:
    """Reverse-proxy a request to the origin WordPress server."""
    base_url = bp.internal_url or bp.target_url
    parsed = urlparse(base_url)
    target = f"{parsed.scheme}://{parsed.netloc}/{path}"
    if request.url.query:
        target += f"?{request.url.query}"

    fwd_headers = {}
    for k, v in request.headers.items():
        if k.lower() not in BYPASS_HOP_HEADERS and k.lower() != "host":
            fwd_headers[k] = v

    fwd_headers["host"] = bp.override_host or parsed.netloc
    if bp.internal_url:
        target_parsed = urlparse(bp.target_url)
        fwd_headers["x-forwarded-proto"] = target_parsed.scheme
        fwd_headers["x-forwarded-host"] = bp.override_host or target_parsed.netloc

    body = await request.body()

    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=30.0) as client:
        resp = await client.request(
            method=request.method,
            url=target,
            headers=fwd_headers,
            content=body if body else None,
        )

    resp_headers = {}
    for k, v in resp.headers.multi_items():
        if k.lower() not in BYPASS_HOP_HEADERS and k.lower() != "content-encoding":
            resp_headers[k] = v
    resp_headers["x-frontwall-bypass"] = "true"

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp_headers,
        media_type=resp.headers.get("content-type"),
    )


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


def _resolve_cache_file(cache_root: Path, path: str, query: str = "") -> Path:
    """Resolve a request path to a cached file, with query string fallback."""

    def _try_path(p: str) -> Path | None:
        if not p or p.endswith("/"):
            candidate = cache_root / p / "index.html"
        else:
            candidate = cache_root / p
            if candidate.is_dir():
                candidate = candidate / "index.html"
            elif not candidate.exists():
                alt = cache_root / p / "index.html"
                if alt.exists():
                    candidate = alt
        if candidate.exists() and candidate.is_file():
            return candidate
        return None

    if query:
        safe_query = quote(query, safe="")
        base = path.strip("/") or "index.html"
        if "." in base.split("/")[-1]:
            name_parts = base.rsplit(".", 1)
            query_path = f"{name_parts[0]}_{safe_query}.{name_parts[1]}"
        else:
            query_path = f"{base}/index.html".replace("/index.html", f"_{safe_query}/index.html")

        result = _try_path(query_path)
        if result:
            return result

    result = _try_path(path)
    if result:
        return result

    return cache_root / path / "index.html" if not path or path.endswith("/") else cache_root / path


def create_shield_app(
    site_id: str | None = None,
    csp: str | None = None,
    asset_learner=None,
    security_headers: bool = True,
    csp_learner=None,
    csp_state: CspState | None = None,
    bypass_state: "BypassState | None" = None,
) -> FastAPI:
    """Create a hardened FastAPI app that serves cached static files."""

    shield = FastAPI(
        title="FrontWall",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    if security_headers:
        state = csp_state or CspState(csp=csp)
        shield.add_middleware(SecurityHeadersMiddleware, csp_state=state)

    @shield.post("/__csp_report")
    async def csp_report(request: Request):
        if not csp_learner or not csp_learner.enabled:
            return Response(status_code=204)
        try:
            body = await request.json()
            csp_learner.process_report(body)
        except Exception:
            pass
        return Response(status_code=204)

    @shield.api_route("/{path:path}", methods=["GET", "HEAD"])
    async def serve_static(request: Request, path: str = ""):
        if bypass_state and bypass_state.enabled:
            return await _bypass_proxy_request(bypass_state, request, path)

        if request.method not in ("GET", "HEAD"):
            return GENERIC_400

        if not _is_path_safe(path):
            logger.warning("Path traversal attempt blocked: %s (IP: %s)", path,
                           request.client.host if request.client else "unknown")
            return GENERIC_403

        ext = Path(path).suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            logger.warning("Blocked extension access: %s (IP: %s)", path,
                           request.client.host if request.client else "unknown")
            return GENERIC_403

        if site_id:
            cache_root = Path(settings.cache_dir) / site_id
        else:
            cache_root = Path(settings.cache_dir)

        query = request.url.query
        file_path = _resolve_cache_file(cache_root, path, query)

        try:
            resolved = file_path.resolve()
            cache_resolved = cache_root.resolve()
            if not str(resolved).startswith(str(cache_resolved)):
                logger.warning("Path escape attempt blocked: %s -> %s", path, resolved)
                return GENERIC_403
        except (OSError, ValueError):
            return GENERIC_403

        if not file_path.exists() or not file_path.is_file():
            if asset_learner and asset_learner.enabled:
                learned_path = await asset_learner.try_fetch_and_cache(path, query)
                if learned_path and learned_path.exists():
                    ct, _ = mimetypes.guess_type(str(learned_path))
                    return FileResponse(
                        path=str(learned_path),
                        media_type=ct or "application/octet-stream",
                        headers={"X-Served-By": "FrontWall", "X-Learned": "true"},
                    )
            return GENERIC_404

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            headers={"X-Served-By": "FrontWall"},
        )

    return shield
