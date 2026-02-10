from datetime import datetime
from pydantic import BaseModel


class PageCreate(BaseModel):
    url: str
    site_id: str


class PageResponse(BaseModel):
    id: str
    site_id: str
    url: str
    path: str
    content_type: str
    status_code: int
    cache_path: str
    size_bytes: int
    etag: str | None
    last_modified: str | None
    detected_forms: str | None
    is_manual: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
