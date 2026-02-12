import ipaddress
import socket
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, HttpUrl, field_validator

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
]


def _check_ssrf(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")

    try:
        resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            for net in BLOCKED_IP_NETWORKS:
                if ip in net:
                    raise ValueError(f"URL resolves to a blocked address ({ip})")
    except socket.gaierror:
        pass

    return url


class SiteCreate(BaseModel):
    name: str
    target_url: str
    crawl_concurrency: int = 5
    crawl_delay: float = 0.5
    crawl_max_pages: int = 10000
    respect_robots_txt: bool = True
    auth_user: str | None = None
    auth_password: str | None = None
    internal_url: str | None = None
    override_host: str | None = None
    shield_port: int | None = None
    waf_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    security_headers_enabled: bool = True
    block_bots: bool = True
    block_suspicious_paths: bool = True
    max_body_size: int = 1_048_576
    request_size_limit_enabled: bool = True
    sanitization_enabled: bool = True
    custom_blocked_patterns: str = ""
    ip_whitelist: str = ""
    ip_blacklist: str = ""
    blocked_countries: str = ""

    @field_validator("blocked_countries")
    @classmethod
    def validate_blocked_countries(cls, v: str) -> str:
        if not v or not v.strip():
            return ""
        import re as _re
        codes = [c.strip().upper() for c in v.split(",") if c.strip()]
        for code in codes:
            if not _re.fullmatch(r"[A-Z]{2}", code):
                raise ValueError(f"Invalid country code: {code}")
        return ",".join(sorted(set(codes)))

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 255:
            raise ValueError("Name must be between 1 and 255 characters")
        return v

    @field_validator("crawl_concurrency")
    @classmethod
    def validate_concurrency(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("Concurrency must be between 1 and 20")
        return v

    @field_validator("crawl_delay")
    @classmethod
    def validate_delay(cls, v: float) -> float:
        if v < 0.1 or v > 60:
            raise ValueError("Delay must be between 0.1 and 60 seconds")
        return v

    @field_validator("crawl_max_pages")
    @classmethod
    def validate_max_pages(cls, v: int) -> int:
        if v < 1 or v > 100000:
            raise ValueError("Max pages must be between 1 and 100,000")
        return v

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        HttpUrl(v)
        _check_ssrf(v)
        return v.rstrip("/")

    @field_validator("internal_url")
    @classmethod
    def validate_internal_url(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            HttpUrl(v)
            return v.rstrip("/")
        return None

    @field_validator("override_host")
    @classmethod
    def validate_override_host(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            import re as _re
            v = v.strip()
            if len(v) > 255 or not _re.fullmatch(r"[a-zA-Z0-9._:-]+", v):
                raise ValueError("Invalid hostname: only letters, digits, dots, colons, and hyphens allowed")
            if "\n" in v or "\r" in v:
                raise ValueError("Hostname must not contain newline characters")
            return v
        return None

    @field_validator("shield_port")
    @classmethod
    def validate_shield_port(cls, v: int | None) -> int | None:
        if v is not None:
            from config import settings
            if v < 1024 or v > 65535:
                raise ValueError("Shield port must be between 1024 and 65535")
            if v == settings.admin_port:
                raise ValueError("Shield port must not be the same as the admin port")
        return v

    @field_validator("rate_limit_requests")
    @classmethod
    def validate_rate_limit_requests(cls, v: int) -> int:
        if v < 1 or v > 10000:
            raise ValueError("Rate limit requests must be between 1 and 10,000")
        return v

    @field_validator("rate_limit_window")
    @classmethod
    def validate_rate_limit_window(cls, v: int) -> int:
        if v < 1 or v > 3600:
            raise ValueError("Rate limit window must be between 1 and 3600 seconds")
        return v

    @field_validator("max_body_size")
    @classmethod
    def validate_max_body_size(cls, v: int) -> int:
        if v < 1024 or v > 104_857_600:
            raise ValueError("Max body size must be between 1KB and 100MB")
        return v


class SiteUpdate(BaseModel):
    name: str | None = None
    target_url: str | None = None
    is_active: bool | None = None
    crawl_concurrency: int | None = None
    crawl_delay: float | None = None
    crawl_max_pages: int | None = None
    respect_robots_txt: bool | None = None
    auth_user: str | None = None
    auth_password: str | None = None
    internal_url: str | None = None
    override_host: str | None = None
    shield_port: int | None = None
    waf_enabled: bool | None = None
    rate_limit_enabled: bool | None = None
    rate_limit_requests: int | None = None
    rate_limit_window: int | None = None
    security_headers_enabled: bool | None = None
    block_bots: bool | None = None
    block_suspicious_paths: bool | None = None
    max_body_size: int | None = None
    request_size_limit_enabled: bool | None = None
    sanitization_enabled: bool | None = None
    custom_blocked_patterns: str | None = None
    ip_whitelist: str | None = None
    ip_blacklist: str | None = None
    blocked_countries: str | None = None

    @field_validator("blocked_countries")
    @classmethod
    def validate_blocked_countries(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return v
        import re as _re
        codes = [c.strip().upper() for c in v.split(",") if c.strip()]
        for code in codes:
            if not _re.fullmatch(r"[A-Z]{2}", code):
                raise ValueError(f"Invalid country code: {code}")
        return ",".join(sorted(set(codes)))

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is not None:
            HttpUrl(v)
            _check_ssrf(v)
            return v.rstrip("/")
        return v

    @field_validator("internal_url")
    @classmethod
    def validate_internal_url(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            HttpUrl(v)
            return v.rstrip("/")
        return None

    @field_validator("override_host")
    @classmethod
    def validate_override_host(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            import re as _re
            v = v.strip()
            if len(v) > 255 or not _re.fullmatch(r"[a-zA-Z0-9._:-]+", v):
                raise ValueError("Invalid hostname")
            return v
        return None

    @field_validator("shield_port")
    @classmethod
    def validate_shield_port(cls, v: int | None) -> int | None:
        if v is not None:
            from config import settings
            if v < 1024 or v > 65535:
                raise ValueError("Shield port must be between 1024 and 65535")
            if v == settings.admin_port:
                raise ValueError("Shield port must not be the same as the admin port")
        return v


class SiteResponse(BaseModel):
    id: str
    name: str
    target_url: str
    is_active: bool
    crawl_concurrency: int
    crawl_delay: float
    crawl_max_pages: int
    respect_robots_txt: bool
    auth_user: str | None
    internal_url: str | None
    override_host: str | None
    shield_active: bool
    shield_port: int | None
    waf_enabled: bool
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window: int
    security_headers_enabled: bool
    block_bots: bool
    block_suspicious_paths: bool
    max_body_size: int
    request_size_limit_enabled: bool
    sanitization_enabled: bool
    custom_blocked_patterns: str
    ip_whitelist: str
    ip_blacklist: str
    blocked_countries: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
