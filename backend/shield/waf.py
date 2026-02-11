import logging
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shield.rate_limiter import RateLimiter

logger = logging.getLogger("frontwall.shield.waf")

MALICIOUS_BOT_PATTERNS = [
    re.compile(r"sqlmap", re.IGNORECASE),
    re.compile(r"nikto", re.IGNORECASE),
    re.compile(r"nessus", re.IGNORECASE),
    re.compile(r"masscan", re.IGNORECASE),
    re.compile(r"dirbuster", re.IGNORECASE),
    re.compile(r"gobuster", re.IGNORECASE),
    re.compile(r"nmap", re.IGNORECASE),
    re.compile(r"havij", re.IGNORECASE),
    re.compile(r"w3af", re.IGNORECASE),
    re.compile(r"acunetix", re.IGNORECASE),
]

SUSPICIOUS_PATH_PATTERNS = [
    re.compile(r"\.\./"),
    re.compile(r"\.\.\\"),
    re.compile(r"%2e%2e", re.IGNORECASE),
    re.compile(r"%252e", re.IGNORECASE),
    re.compile(r"/etc/passwd"),
    re.compile(r"/proc/self"),
    re.compile(r"wp-admin", re.IGNORECASE),
    re.compile(r"wp-login\.php", re.IGNORECASE),
    re.compile(r"xmlrpc\.php", re.IGNORECASE),
    re.compile(r"wp-config", re.IGNORECASE),
    re.compile(r"\.git/", re.IGNORECASE),
    re.compile(r"\.env", re.IGNORECASE),
    re.compile(r"phpmyadmin", re.IGNORECASE),
]

BLOCKED_RESPONSE = Response(content="Forbidden", status_code=403, media_type="text/plain")
RATE_LIMITED_RESPONSE = Response(content="Too Many Requests", status_code=429, media_type="text/plain")
PAYLOAD_TOO_LARGE = Response(content="Payload Too Large", status_code=413, media_type="text/plain")
GENERIC_400 = Response(content="Bad Request", status_code=400, media_type="text/plain")

STATIC_ASSET_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".map",
    ".pdf", ".mp4", ".webm", ".mp3", ".ogg",
}


class WAFMiddleware(BaseHTTPMiddleware):
    """Web Application Firewall middleware for the shield server."""

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter | None = None,
        max_body_size: int = 1_048_576,
        ip_whitelist: set[str] | None = None,
        ip_blacklist: set[str] | None = None,
        post_handler=None,
        block_bots: bool = True,
        block_suspicious_paths: bool = True,
        site_id: str = "",
        event_collector=None,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_body_size = max_body_size
        self.ip_whitelist = ip_whitelist or set()
        self.ip_blacklist = ip_blacklist or set()
        self.post_handler = post_handler
        self.block_bots = block_bots
        self.block_suspicious_paths = block_suspicious_paths
        self.site_id = site_id
        self.collector = event_collector

    def _emit(self, event_type, severity, client_ip, path, method, user_agent, details=None):
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
            )

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        path = request.url.path
        method = request.method

        if client_ip in self.ip_blacklist:
            logger.warning("Blocked blacklisted IP: %s", client_ip)
            self._emit("ip_blacklisted", "critical", client_ip, path, method, user_agent)
            return BLOCKED_RESPONSE

        if self.ip_whitelist and client_ip not in self.ip_whitelist:
            pass

        if self.block_bots and self._is_malicious_bot(user_agent):
            logger.warning("Blocked malicious bot: %s (IP: %s)", user_agent, client_ip)
            self._emit("bot_blocked", "high", client_ip, path, method, user_agent, {"user_agent": user_agent})
            return BLOCKED_RESPONSE

        is_static = any(path.lower().endswith(ext) for ext in STATIC_ASSET_EXTENSIONS)
        if not is_static and self.rate_limiter:
            if not await self.rate_limiter.check_global(client_ip):
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                self._emit("rate_limited", "medium", client_ip, path, method, user_agent)
                return RATE_LIMITED_RESPONSE

        if self.block_suspicious_paths and self._is_suspicious_path(path):
            post_allowed = (
                method == "POST"
                and self.post_handler
                and (
                    self.post_handler.find_matching_rule(path)
                    or self.post_handler.learn_mode
                )
            )
            if not post_allowed:
                logger.warning("Blocked suspicious path: %s (IP: %s)", path, client_ip)
                self._emit("suspicious_path", "high", client_ip, path, method, user_agent, {"path": path})
                return BLOCKED_RESPONSE

        query = str(request.url.query)
        if self.block_suspicious_paths and query and self._is_suspicious_path(query):
            logger.warning("Blocked suspicious query: %s (IP: %s)", query, client_ip)
            self._emit("suspicious_query", "high", client_ip, path, method, user_agent, {"query": query})
            return BLOCKED_RESPONSE

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    logger.warning("Blocked oversized request: %s bytes (IP: %s)", content_length, client_ip)
                    self._emit("payload_too_large", "medium", client_ip, path, method, user_agent, {"size": content_length})
                    return PAYLOAD_TOO_LARGE
            except (ValueError, OverflowError):
                return GENERIC_400

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",")]
            return parts[-1] if len(parts) > 1 else parts[0]
        return request.client.host if request.client else "0.0.0.0"

    def _is_malicious_bot(self, user_agent: str) -> bool:
        for pattern in MALICIOUS_BOT_PATTERNS:
            if pattern.search(user_agent):
                return True
        return False

    def _is_suspicious_path(self, path: str) -> bool:
        for pattern in SUSPICIOUS_PATH_PATTERNS:
            if pattern.search(path):
                return True
        return False
