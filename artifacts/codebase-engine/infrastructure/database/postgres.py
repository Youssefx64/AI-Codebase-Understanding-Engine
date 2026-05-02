"""PostgreSQL database engine and session factory (SQLAlchemy async)."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_async_url(raw_url: str) -> tuple[str, dict]:
    """
    Convert a standard postgres:// URL to asyncpg driver format.
    Strips query params that asyncpg doesn't support (e.g. sslmode)
    and returns them as engine connect_args instead.
    """
    import urllib.parse

    # Replace scheme
    if raw_url.startswith("postgresql://"):
        url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgres://"):
        url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        url = raw_url

    # Parse and strip unsupported query params
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

    connect_args: dict = {}
    ssl_mode = params.pop("sslmode", [None])[0]
    if ssl_mode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = "require"
    elif ssl_mode == "prefer":
        connect_args["ssl"] = "prefer"

    # Rebuild URL without stripped params
    new_query = urllib.parse.urlencode(
        {k: v[0] for k, v in params.items()}, doseq=False
    )
    clean_url = urllib.parse.urlunparse(parsed._replace(query=new_query))
    return clean_url, connect_args


def create_engine():
    """Create the async SQLAlchemy engine."""
    settings = get_settings()
    db_url = settings.database_url or "sqlite+aiosqlite:///./data/codebase_engine.db"

    # SQLite fallback for development without PostgreSQL
    if "sqlite" in db_url:
        engine = create_async_engine(
            db_url,
            echo=settings.debug,
        )
    else:
        clean_url, connect_args = _build_async_url(db_url)
        engine = create_async_engine(
            clean_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.debug,
            connect_args=connect_args,
        )

    logger.info("Database engine created", url=db_url.split("@")[-1])
    return engine


# Module-level singletons
engine = create_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (idempotent)."""
    # Import ORM models so they register with Base.metadata
    import infrastructure.database.orm_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables initialised")


async def health_check() -> bool:
    """Return True if the database is reachable."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed", error=str(exc))
        return False
