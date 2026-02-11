from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

DEFAULT_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Cross-Origin-Opener-Policy": "same-origin",
}

STATIC_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=3600, must-revalidate",
}

IMMUTABLE_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
}

IMMUTABLE_EXTENSIONS = {
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects hardened security headers into every response."""

    def __init__(self, app, csp: str | None = None, custom_headers: dict[str, str] | None = None):
        super().__init__(app)
        self.headers = {**DEFAULT_HEADERS}
        if csp:
            self.headers["Content-Security-Policy"] = csp
        if custom_headers:
            self.headers.update(custom_headers)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        for key, value in self.headers.items():
            response.headers[key] = value

        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        path = request.url.path
        if any(path.endswith(ext) for ext in IMMUTABLE_EXTENSIONS):
            for k, v in IMMUTABLE_CACHE_HEADERS.items():
                response.headers[k] = v
        else:
            for k, v in STATIC_CACHE_HEADERS.items():
                response.headers[k] = v

        return response
