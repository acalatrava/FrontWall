import logging
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shield.rate_limiter import RateLimiter

logger = logging.getLogger("webshield.shield.waf")

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
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_body_size = max_body_size
        self.ip_whitelist = ip_whitelist or set()
        self.ip_blacklist = ip_blacklist or set()
        self.post_handler = post_handler

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)

        if client_ip in self.ip_blacklist:
            logger.warning("Blocked blacklisted IP: %s", client_ip)
            return BLOCKED_RESPONSE

        if self.ip_whitelist and client_ip not in self.ip_whitelist:
            pass

        user_agent = request.headers.get("user-agent", "")
        if self._is_malicious_bot(user_agent):
            logger.warning("Blocked malicious bot: %s (IP: %s)", user_agent, client_ip)
            return BLOCKED_RESPONSE

        path = request.url.path

        is_static = any(path.lower().endswith(ext) for ext in STATIC_ASSET_EXTENSIONS)
        if not is_static:
            if not await self.rate_limiter.check_global(client_ip):
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                return RATE_LIMITED_RESPONSE
        if self._is_suspicious_path(path):
            post_allowed = (
                request.method == "POST"
                and self.post_handler
                and (
                    self.post_handler.find_matching_rule(path)
                    or self.post_handler.learn_mode
                )
            )
            if not post_allowed:
                logger.warning("Blocked suspicious path: %s (IP: %s)", path, client_ip)
                return BLOCKED_RESPONSE

        query = str(request.url.query)
        if query and self._is_suspicious_path(query):
            logger.warning("Blocked suspicious query: %s (IP: %s)", query, client_ip)
            return BLOCKED_RESPONSE

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    logger.warning("Blocked oversized request: %s bytes (IP: %s)", content_length, client_ip)
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
