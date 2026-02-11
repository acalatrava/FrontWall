import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, LargeBinary, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Passkey(Base):
    __tablename__ = "passkeys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(BigInteger, default=0)
    name: Mapped[str] = mapped_column(String(255), default="Passkey")
    transports: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
