"""Global pytest fixtures providing database sessions, test clients, and test users."""

import uuid
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.base import Base

TEST_USER_A_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_B_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture(scope="session")
def user_a_token() -> str:
    return create_access_token(user_id=TEST_USER_A_ID, email="usera@example.com")


@pytest.fixture(scope="session")
def user_b_token() -> str:
    return create_access_token(user_id=TEST_USER_B_ID, email="userb@example.com")


@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated in-memory SQLite database session for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient bound to the FastAPI application with test database."""
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
