import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    import models.refresh_token  # noqa: F401
    import models.security_event  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_add_missing_columns)


def _add_missing_columns(conn) -> None:
    """Add columns that may be missing from existing tables after schema updates."""
    inspector = sa.inspect(conn)
    _ensure_column(conn, inspector, "sites", "internal_url", "VARCHAR(2048)")
    _ensure_column(conn, inspector, "sites", "override_host", "VARCHAR(255)")
    _ensure_column(conn, inspector, "sites", "shield_port", "INTEGER")
    _ensure_column(conn, inspector, "sites", "waf_enabled", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, inspector, "sites", "rate_limit_enabled", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, inspector, "sites", "rate_limit_requests", "INTEGER DEFAULT 60")
    _ensure_column(conn, inspector, "sites", "rate_limit_window", "INTEGER DEFAULT 60")
    _ensure_column(conn, inspector, "sites", "security_headers_enabled", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, inspector, "sites", "block_bots", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, inspector, "sites", "block_suspicious_paths", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, inspector, "sites", "max_body_size", "INTEGER DEFAULT 1048576")
    _ensure_column(conn, inspector, "sites", "ip_whitelist", "TEXT DEFAULT ''")
    _ensure_column(conn, inspector, "sites", "ip_blacklist", "TEXT DEFAULT ''")


def _ensure_column(conn, inspector, table: str, column: str, col_type: str) -> None:
    existing = [c["name"] for c in inspector.get_columns(table)]
    if column not in existing:
        conn.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with async_session() as session:
        yield session
