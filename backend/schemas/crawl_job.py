from datetime import datetime
from pydantic import BaseModel


class CrawlJobResponse(BaseModel):
    id: str
    site_id: str
    status: str
    pages_found: int
    pages_crawled: int
    assets_downloaded: int
    errors: int
    error_log: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
