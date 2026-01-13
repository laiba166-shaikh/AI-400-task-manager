"""
SQLModel Session Management Templates

Provides session factory patterns for async database operations with SQLModel,
including FastAPI dependency injection patterns.

SQLModel uses SQLAlchemy 2.x under the hood, so these patterns work for both
ORM operations and Pydantic validation.
"""

import os
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
)
from fastapi import Depends
from dotenv import load_dotenv


# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig:
    """
    Database configuration loaded from environment variables.

    Reads from DATABASE_URL or DB_URL environment variable and automatically:
    - Converts sync URLs to async (postgresql:// → postgresql+asyncpg://)
    - Converts sslmode to ssl for asyncpg compatibility
    - Removes unsupported parameters (channel_binding)

    Environment Variables:
        DATABASE_URL or DB_URL: Database connection string (required)
        SQL_ECHO: Enable SQL logging (default: False)
        DB_POOL_SIZE: Connection pool size (default: 5)
        DB_MAX_OVERFLOW: Max overflow connections (default: 10)

    Usage:
        config = DatabaseConfig()
        # Automatically loads from environment
    """
    def __init__(self):
        # Try DATABASE_URL first, fallback to DB_URL
        url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
        if not url:
            raise ValueError("DATABASE_URL or DB_URL environment variable is required")

        # Auto-convert sync URL to async for PostgreSQL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Convert sslmode to ssl for asyncpg compatibility
        # Some providers (like Neon) use sslmode=require but asyncpg uses ssl=require
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")

        # Remove channel_binding parameter (not supported by asyncpg)
        if "channel_binding=" in url:
            url = re.sub(r'[&?]channel_binding=[^&]*', '', url)

        self.url: str = url
        self.echo = os.getenv("SQL_ECHO", "False").lower() == "true"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_pre_ping = True
        self.pool_recycle = 3600  # Recycle connections after 1 hour


# ============================================================================
# ASYNC ENGINE INITIALIZATION
# ============================================================================

# Global engine instance
_engine: AsyncEngine | None = None


def init_db() -> AsyncEngine:
    """
    Initialize async database engine.

    Loads configuration from environment and creates a global engine instance
    with connection pooling.

    Returns:
        AsyncEngine instance

    Usage:
        # In FastAPI lifespan
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup: Initialize database
            engine = init_db()
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            yield
            # Shutdown: Dispose engine
            await engine.dispose()
    """
    global _engine
    config = DatabaseConfig()

    _engine = create_async_engine(
        config.url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=config.pool_pre_ping,
        pool_recycle=config.pool_recycle,
    )

    return _engine


def get_engine() -> AsyncEngine:
    """
    Get the database engine.

    Returns:
        AsyncEngine instance

    Raises:
        RuntimeError: If database not initialized

    Usage:
        engine = get_engine()
        async with engine.begin() as conn:
            # Use connection
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


# ============================================================================
# FASTAPI DEPENDENCY INJECTION
# ============================================================================

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database sessions.

    Automatically handles session lifecycle - creates session, yields it,
    then closes after request completes.

    Usage:
        from sqlalchemy.ext.asyncio import AsyncSession
        from fastapi import Depends

        @app.get("/tasks")
        async def get_tasks(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Task))
            return result.scalars().all()

    Or use the SessionDep type alias:
        @app.get("/tasks")
        async def get_tasks(session: SessionDep):
            result = await session.execute(select(Task))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session

    Raises:
        RuntimeError: If database not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSession(_engine, expire_on_commit=False) as session:
        yield session


# Type alias for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ============================================================================
# EXAMPLE FASTAPI INTEGRATION
# ============================================================================

"""
Complete example of SQLModel + FastAPI integration:

# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel
from app.database import init_db, SessionDep
from app.models import Task
from app.crud import TaskRepository

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database and create tables
    engine = init_db()

    async with engine.begin() as conn:
        # Create all tables defined in SQLModel metadata
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Shutdown: Dispose engine and close connections
    await engine.dispose()


app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/tasks/", response_model=TaskRead)
async def create_task(task: TaskCreate, session: SessionDep):
    repo = TaskRepository(session)
    db_task = await repo.create(task.model_dump())
    await session.commit()  # Commit in endpoint, not repository
    return db_task


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, session: SessionDep):
    repo = TaskRepository(session)
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# .env file
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
# Or for Neon DB:
# DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# The DatabaseConfig class will automatically:
# 1. Convert postgresql:// to postgresql+asyncpg://
# 2. Convert sslmode=require to ssl=require (for asyncpg compatibility)
# 3. Remove channel_binding parameter if present
"""