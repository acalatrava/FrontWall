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

IMMUTABLE_EXTENSIONS = frozenset({
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico",
})

HEADERS_TO_STRIP = ("Server", "X-Powered-By")


class CspState:
    """Shared mutable state for the CSP header, readable by the middleware."""

    __slots__ = ("csp", "learn_mode")

    def __init__(self, csp: str | None = None):
        self.csp = csp
        self.learn_mode = False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects hardened security headers into every response.

    Pre-computes header tuples at init time so the per-request overhead
    is just a loop over a fixed-size list instead of dict lookups.
    """

    def __init__(self, app, csp_state: CspState | None = None, custom_headers: dict[str, str] | None = None):
        super().__init__(app)
        merged = {**DEFAULT_HEADERS}
        if custom_headers:
            merged.update(custom_headers)
        self._header_pairs = tuple(merged.items())
        self.csp_state = csp_state or CspState()

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        rh = response.headers
        for key, value in self._header_pairs:
            rh[key] = value

        csp = self.csp_state.csp
        if csp:
            if self.csp_state.learn_mode:
                rh["Content-Security-Policy-Report-Only"] = csp + "; report-uri /__csp_report"
                rh.pop("Content-Security-Policy", None)
            else:
                rh["Content-Security-Policy"] = csp
                rh.pop("Content-Security-Policy-Report-Only", None)

        for h in HEADERS_TO_STRIP:
            rh.pop(h, None)

        return response
