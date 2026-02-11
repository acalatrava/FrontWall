from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator


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

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        HttpUrl(v)
        return v.rstrip("/")

    @field_validator("internal_url")
    @classmethod
    def validate_internal_url(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            HttpUrl(v)
            return v.rstrip("/")
        return None


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

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is not None:
            HttpUrl(v)
            return v.rstrip("/")
        return v

    @field_validator("internal_url")
    @classmethod
    def validate_internal_url(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            HttpUrl(v)
            return v.rstrip("/")
        return None


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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
