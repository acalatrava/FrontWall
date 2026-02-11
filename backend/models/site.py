import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    crawl_concurrency: Mapped[int] = mapped_column(Integer, default=5)
    crawl_delay: Mapped[float] = mapped_column(Float, default=0.5)
    crawl_max_pages: Mapped[int] = mapped_column(Integer, default=10000)
    respect_robots_txt: Mapped[bool] = mapped_column(Boolean, default=True)

    auth_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    internal_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    override_host: Mapped[str | None] = mapped_column(String(255), nullable=True)

    shield_active: Mapped[bool] = mapped_column(Boolean, default=False)
    shield_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    waf_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_requests: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_window: Mapped[int] = mapped_column(Integer, default=60)
    security_headers_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    block_bots: Mapped[bool] = mapped_column(Boolean, default=True)
    block_suspicious_paths: Mapped[bool] = mapped_column(Boolean, default=True)
    max_body_size: Mapped[int] = mapped_column(Integer, default=1_048_576)
    ip_whitelist: Mapped[str] = mapped_column(Text, default="")
    ip_blacklist: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    pages: Mapped[list["Page"]] = relationship("Page", back_populates="site", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    post_rules: Mapped[list["PostRule"]] = relationship("PostRule", back_populates="site", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    crawl_jobs: Mapped[list["CrawlJob"]] = relationship("CrawlJob", back_populates="site", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
