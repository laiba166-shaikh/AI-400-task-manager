"""Pytest fixtures for testing with SQLModel."""
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel
from httpx import AsyncClient, ASGITransport

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.database import get_session
from app.models import Task

# Test database URL - use the same Neon DB but with transaction rollback for isolation
# Or set TEST_DATABASE_URL environment variable for a separate test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("DB_URL")

if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL, DATABASE_URL, or DB_URL environment variable required for tests")

# Auto-convert to async driver if needed
if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Convert sslmode to ssl for asyncpg compatibility
if "sslmode=" in TEST_DATABASE_URL:
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("sslmode=", "ssl=")

# Remove channel_binding parameter (not supported by asyncpg)
if "channel_binding=" in TEST_DATABASE_URL:
    import re
    TEST_DATABASE_URL = re.sub(r'[&?]channel_binding=[^&]*', '', TEST_DATABASE_URL)


# Test engine - function scoped to avoid event loop issues
@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test database engine.

    Scope: function - new engine for each test to avoid event loop issues
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for debugging
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides test database session with transaction rollback.

    Each test function gets a clean database state:
    1. Creates all tables
    2. Yields session within a transaction
    3. Rolls back transaction (discards all changes)
    4. Drops all tables

    This ensures test isolation - tests don't affect each other.

    Scope: function - new session for each test
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session and start transaction
    async with AsyncSession(test_engine, expire_on_commit=False) as test_session:
        yield test_session
        # Rollback transaction (happens automatically on context exit)
        await test_session.rollback()

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides async HTTP test client with database dependency override.

    The client uses the test database session instead of the real one,
    ensuring all API calls in tests use the test database.

    Usage in tests:
        async def test_create_task(client):
            response = await client.post("/tasks/", json={"title": "Test"})
            assert response.status_code == 201
    """
    # Override the get_session dependency to use test session
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up: clear dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_task(session: AsyncSession) -> Task:
    """
    Factory fixture for creating a sample test task.

    Creates a task in the database and returns it.
    Useful for tests that need an existing task.

    Usage:
        async def test_get_task(client, sample_task):
            response = await client.get(f"/tasks/{sample_task.id}")
            assert response.status_code == 200
            assert response.json()["title"] == sample_task.title
    """
    task = Task(
        title="Test Task",
        description="Test Description",
        completed=False
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


@pytest_asyncio.fixture
async def multiple_tasks(session: AsyncSession) -> list[Task]:
    """
    Factory fixture for creating multiple test tasks.

    Creates 5 tasks with different states for testing list/filter operations.

    Usage:
        async def test_list_tasks(client, multiple_tasks):
            response = await client.get("/tasks/")
            assert len(response.json()) == 5
    """
    tasks = [
        Task(title="Task 1", description="First task", completed=False),
        Task(title="Task 2", description="Second task", completed=True),
        Task(title="Task 3", description=None, completed=False),
        Task(title="Task 4", description="Fourth task", completed=True),
        Task(title="Task 5", description="Fifth task", completed=False),
    ]

    for task in tasks:
        session.add(task)

    await session.flush()

    for task in tasks:
        await session.refresh(task)

    return tasks


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
