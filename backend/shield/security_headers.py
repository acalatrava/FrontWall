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


class CspState:
    """Shared mutable state for the CSP header, readable by the middleware."""

    def __init__(self, csp: str | None = None):
        self.csp = csp
        self.learn_mode = False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects hardened security headers into every response.

    When learn_mode is active on the shared CspState, the CSP is sent as
    Content-Security-Policy-Report-Only with a report-uri so the browser
    reports blocked domains instead of blocking them.
    """

    def __init__(self, app, csp_state: CspState | None = None, custom_headers: dict[str, str] | None = None):
        super().__init__(app)
        self.base_headers = {**DEFAULT_HEADERS}
        self.csp_state = csp_state or CspState()
        if custom_headers:
            self.base_headers.update(custom_headers)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        for key, value in self.base_headers.items():
            response.headers[key] = value

        csp = self.csp_state.csp
        if csp:
            if self.csp_state.learn_mode:
                response.headers["Content-Security-Policy-Report-Only"] = csp + "; report-uri /__csp_report"
                if "Content-Security-Policy" in response.headers:
                    del response.headers["Content-Security-Policy"]
            else:
                response.headers["Content-Security-Policy"] = csp
                if "Content-Security-Policy-Report-Only" in response.headers:
                    del response.headers["Content-Security-Policy-Report-Only"]

        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        path = request.url.path
        is_ok = 200 <= response.status_code < 400
        if is_ok:
            if any(path.endswith(ext) for ext in IMMUTABLE_EXTENSIONS):
                for k, v in IMMUTABLE_CACHE_HEADERS.items():
                    response.headers[k] = v
            else:
                for k, v in STATIC_CACHE_HEADERS.items():
                    response.headers[k] = v
        else:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        return response
