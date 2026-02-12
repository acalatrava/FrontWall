import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response

from config import settings
from shield.security_headers import SecurityHeadersMiddleware, CspState
from shield.cache_index import CacheIndex, CachedEntry
from shield.hot_cache import HotResponseCache

logger = logging.getLogger("frontwall.shield.server")

BLOCKED_EXTENSIONS = frozenset({
    ".php", ".asp", ".aspx", ".jsp", ".cgi", ".pl", ".py", ".rb",
    ".sh", ".bash", ".env", ".ini", ".conf", ".yml", ".yaml",
    ".sql", ".bak", ".swp", ".log", ".htaccess", ".htpasswd",
    ".git", ".svn",
})

_RESP_404 = Response(content="Not Found", status_code=404, media_type="text/plain")
_RESP_403 = Response(content="Forbidden", status_code=403, media_type="text/plain")
_RESP_400 = Response(content="Bad Request", status_code=400, media_type="text/plain")

BYPASS_HOP_HEADERS = frozenset({
    "transfer-encoding", "connection", "keep-alive", "te",
    "trailer", "upgrade", "proxy-authorization", "proxy-authenticate",
})


class BypassState:
    __slots__ = ("enabled", "target_url", "internal_url", "override_host")

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
        kl = k.lower()
        if kl not in BYPASS_HOP_HEADERS and kl != "host":
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
        kl = k.lower()
        if kl not in BYPASS_HOP_HEADERS and kl not in ("content-encoding", "content-length"):
            resp_headers[k] = v
    resp_headers["x-frontwall-bypass"] = "true"

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp_headers,
        media_type=resp.headers.get("content-type"),
    )


def _is_path_safe(path: str) -> bool:
    """Fast path-safety check: prevent directory traversal and null byte attacks."""
    if not path:
        return True
    if "\x00" in path or "\\" in path:
        return False
    if ".." in path:
        return False
    if "/." in path:
        return False
    return True


def create_shield_app(
    site_id: str | None = None,
    csp: str | None = None,
    asset_learner=None,
    security_headers: bool = True,
    csp_learner=None,
    csp_state: CspState | None = None,
    bypass_state: "BypassState | None" = None,
) -> FastAPI:
    """Create a hardened FastAPI app that serves cached static files.

    Performance optimizations:
    - Pre-computed cache index eliminates all filesystem stat calls
    - In-memory file cache serves small files without touching disk
    - Hot response cache returns pre-built Response objects for frequent paths
    - Security header values pre-computed as frozen dict
    """

    shield = FastAPI(
        title="FrontWall",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    if site_id:
        cache_root = Path(settings.cache_dir) / site_id
    else:
        cache_root = Path(settings.cache_dir)

    cache_index = CacheIndex()
    cache_index.build(cache_root)

    hot_cache = HotResponseCache()

    STATIC_HEADERS = {"X-Served-By": "FrontWall"}
    IMMUTABLE_CACHE = "public, max-age=31536000, immutable"
    REVALIDATE_CACHE = "public, max-age=3600, must-revalidate"

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

    @shield.get("/__cache_stats")
    async def cache_stats():
        return {
            "index": cache_index.stats,
            "hot_cache": hot_cache.stats,
        }

    @shield.api_route("/{path:path}", methods=["GET", "HEAD"])
    async def serve_static(request: Request, path: str = ""):
        if bypass_state and bypass_state.enabled:
            return await _bypass_proxy_request(bypass_state, request, path)

        if request.method not in ("GET", "HEAD"):
            return _RESP_400

        if not _is_path_safe(path):
            return _RESP_403

        dot_idx = path.rfind(".")
        if dot_idx != -1 and path[dot_idx:].lower() in BLOCKED_EXTENSIONS:
            return _RESP_403

        query = request.url.query or ""

        cache_key = f"{path}?{query}" if query else path
        cached_resp = hot_cache.get(cache_key)
        if cached_resp is not None:
            return cached_resp

        entry = cache_index.lookup(path, query)

        if entry is None:
            if asset_learner and asset_learner.enabled:
                learned_path = await asset_learner.try_fetch_and_cache(path, query)
                if learned_path and learned_path.exists():
                    new_entry = cache_index.add_learned_file(cache_root, str(learned_path.relative_to(cache_root)))
                    if new_entry:
                        entry = new_entry
                    else:
                        return FileResponse(
                            path=str(learned_path),
                            media_type="application/octet-stream",
                            headers={**STATIC_HEADERS, "X-Learned": "true"},
                        )
            if entry is None:
                return _RESP_404

        cc = IMMUTABLE_CACHE if entry.is_immutable else REVALIDATE_CACHE

        if entry.body is not None:
            resp = Response(
                content=entry.body,
                status_code=200,
                media_type=entry.content_type,
                headers={
                    **STATIC_HEADERS,
                    "Content-Length": str(entry.content_length),
                    "Cache-Control": cc,
                },
            )
            hot_cache.put(cache_key, resp, entry.content_length)
            return resp

        resp = FileResponse(
            path=entry.disk_path,
            media_type=entry.content_type,
            headers={
                **STATIC_HEADERS,
                "Cache-Control": cc,
            },
        )
        return resp

    return shield
