"""Database session, engine configuration, and dependency providers."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import logger
from app.models.base import Base


def create_engine_and_session() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Builds configured SQLAlchemy async engine and session factory."""
    connect_args = {}
    engine_kwargs = {"echo": settings.DEBUG, "future": True}

    if settings.is_sqlite:
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_pre_ping"] = True

    engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return engine, session_factory


engine, async_session_factory = create_engine_and_session()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session within a transaction."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(target_engine: AsyncEngine = engine) -> None:
    """Creates database tables and vector extension if supported."""
    async with target_engine.begin() as conn:
        # If Postgres, enable vector extension
        if not settings.is_sqlite:
            try:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as exc:
                logger.warning(f"Could not enable pgvector extension automatically: {exc}")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
