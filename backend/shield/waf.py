import logging
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shield.rate_limiter import RateLimiter
from shield.geo_resolver import get_country_code
from utils import get_client_ip

logger = logging.getLogger("frontwall.shield.waf")

_BOT_WORDS = [
    "sqlmap", "nikto", "nessus", "masscan", "dirbuster",
    "gobuster", "nmap", "havij", "w3af", "acunetix",
]
MALICIOUS_BOT_RE = re.compile("|".join(_BOT_WORDS), re.IGNORECASE)

_SUSPICIOUS_PATH_WORDS = [
    r"\.\./", r"\.\.\\", r"%2e%2e", r"%252e",
    r"/etc/passwd", r"/proc/self",
    r"wp-admin", r"wp-login\.php", r"xmlrpc\.php", r"wp-config",
    r"\.git/", r"\.env", r"phpmyadmin",
]
SUSPICIOUS_PATH_RE = re.compile("|".join(_SUSPICIOUS_PATH_WORDS), re.IGNORECASE)

BLOCKED_RESPONSE = Response(content="Forbidden", status_code=403, media_type="text/plain")
GEO_BLOCKED_RESPONSE = Response(content="Access Denied", status_code=403, media_type="text/plain")
RATE_LIMITED_RESPONSE = Response(content="Too Many Requests", status_code=429, media_type="text/plain")
PAYLOAD_TOO_LARGE = Response(content="Payload Too Large", status_code=413, media_type="text/plain")
GENERIC_400 = Response(content="Bad Request", status_code=400, media_type="text/plain")

STATIC_ASSET_EXTENSIONS = frozenset({
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".map",
    ".pdf", ".mp4", ".webm", ".mp3", ".ogg",
})


def _build_combined_re(base: re.Pattern, custom: list[str]) -> re.Pattern:
    """Merge custom blocked patterns into the base regex as a single compiled alternation."""
    if not custom:
        return base
    escaped = [re.escape(p) for p in custom]
    combined = base.pattern + "|" + "|".join(escaped)
    return re.compile(combined, re.IGNORECASE)


class WAFMiddleware(BaseHTTPMiddleware):
    """Web Application Firewall middleware for the shield server."""

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter | None = None,
        max_body_size: int = 1_048_576,
        request_size_limit_enabled: bool = True,
        ip_whitelist: set[str] | None = None,
        ip_blacklist: set[str] | None = None,
        post_handler=None,
        block_bots: bool = True,
        block_suspicious_paths: bool = True,
        blocked_countries: set[str] | None = None,
        custom_blocked_patterns: list[str] | None = None,
        site_id: str = "",
        event_collector=None,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.max_body_size = max_body_size
        self.request_size_limit_enabled = request_size_limit_enabled
        self.ip_whitelist = ip_whitelist or set()
        self.ip_blacklist = frozenset(ip_blacklist) if ip_blacklist else frozenset()
        self.post_handler = post_handler
        self.block_bots = block_bots
        self.block_suspicious_paths = block_suspicious_paths
        self.blocked_countries = frozenset(blocked_countries) if blocked_countries else frozenset()
        self.site_id = site_id
        self.collector = event_collector

        self._suspicious_re = _build_combined_re(SUSPICIOUS_PATH_RE, custom_blocked_patterns or [])

        self._has_ip_checks = bool(self.ip_blacklist) or bool(self.ip_whitelist)
        self._has_geo_checks = bool(self.blocked_countries)

    def _emit(self, event_type, severity, client_ip, path, method, user_agent, details=None, country=None):
        if self.collector:
            self.collector.emit(
                event_type=event_type,
                severity=severity,
                client_ip=client_ip,
                path=path,
                method=method,
                user_agent=user_agent,
                site_id=self.site_id,
                details=details,
                blocked=True,
                country=country,
            )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        dot_idx = path.rfind(".")
        is_static = dot_idx != -1 and path[dot_idx:].lower() in STATIC_ASSET_EXTENSIONS

        if is_static and method == "GET" and not self._has_ip_checks and not self._has_geo_checks:
            return await call_next(request)

        client_ip = get_client_ip(request)

        if self.ip_blacklist and client_ip in self.ip_blacklist:
            user_agent = request.headers.get("user-agent", "")
            self._emit("ip_blacklisted", "critical", client_ip, path, method, user_agent)
            return BLOCKED_RESPONSE

        if self._has_geo_checks:
            country = get_country_code(request, client_ip)
            if country and country in self.blocked_countries:
                user_agent = request.headers.get("user-agent", "")
                self._emit(
                    "country_blocked", "high", client_ip, path, method, user_agent,
                    {"country": country}, country=country,
                )
                return GEO_BLOCKED_RESPONSE

        if is_static:
            return await call_next(request)

        user_agent = request.headers.get("user-agent", "")

        if self.block_bots and MALICIOUS_BOT_RE.search(user_agent):
            self._emit("bot_blocked", "high", client_ip, path, method, user_agent, {"user_agent": user_agent})
            return BLOCKED_RESPONSE

        if self.rate_limiter:
            if not await self.rate_limiter.check_global(client_ip):
                self._emit("rate_limited", "medium", client_ip, path, method, user_agent)
                return RATE_LIMITED_RESPONSE

        if self.block_suspicious_paths and self._suspicious_re.search(path):
            post_allowed = (
                method == "POST"
                and self.post_handler
                and (
                    self.post_handler.find_matching_rule(path)
                    or self.post_handler.learn_mode
                )
            )
            if not post_allowed:
                self._emit("suspicious_path", "high", client_ip, path, method, user_agent, {"path": path})
                return BLOCKED_RESPONSE

        query = request.url.query
        if query and self.block_suspicious_paths and self._suspicious_re.search(query):
            self._emit("suspicious_query", "high", client_ip, path, method, user_agent, {"query": query})
            return BLOCKED_RESPONSE

        if self.request_size_limit_enabled:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > self.max_body_size:
                        self._emit("payload_too_large", "medium", client_ip, path, method, user_agent, {"size": content_length})
                        return PAYLOAD_TOO_LARGE
                except (ValueError, OverflowError):
                    return GENERIC_400

        return await call_next(request)
