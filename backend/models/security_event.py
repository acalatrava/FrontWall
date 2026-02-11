import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    client_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), default="")
    method: Mapped[str] = mapped_column(String(10), default="GET")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[str] = mapped_column(Text, default="{}")
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    blocked: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_security_events_site_ts", "site_id", "timestamp"),
    )
