import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PostRule(Base):
    __tablename__ = "post_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url_pattern: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    forward_to: Mapped[str] = mapped_column(String(2048), nullable=False)
    success_redirect: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    success_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    rate_limit_requests: Mapped[int] = mapped_column(Integer, default=10)
    rate_limit_window: Mapped[int] = mapped_column(Integer, default=60)

    honeypot_field: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enable_csrf: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_actions: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    site: Mapped["Site"] = relationship("Site", back_populates="post_rules")  # type: ignore[name-defined] # noqa: F821
    fields: Mapped[list["RuleField"]] = relationship("RuleField", back_populates="rule", cascade="all, delete-orphan")


class RuleField(Base):
    __tablename__ = "rule_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("post_rules.id", ondelete="CASCADE"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), default="text")
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    max_length: Mapped[int] = mapped_column(Integer, default=1000)
    validation_regex: Mapped[str | None] = mapped_column(String(500), nullable=True)

    rule: Mapped["PostRule"] = relationship("PostRule", back_populates="fields")
