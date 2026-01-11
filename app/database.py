"""Database configuration and session management with SQLModel + Async support."""
import os
from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from fastapi import Depends
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration loaded from environment."""

    def __init__(self):
        # Try DATABASE_URL first, fallback to DB_URL
        url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
        if not url:
            raise ValueError("DATABASE_URL or DB_URL environment variable is required")

        # Auto-convert sync URL to async for PostgreSQL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Convert sslmode to ssl for asyncpg compatibility
        # Neon uses sslmode=require but asyncpg uses ssl=require
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")

        # Remove channel_binding parameter (not supported by asyncpg)
        if "channel_binding=" in url:
            import re
            url = re.sub(r'[&?]channel_binding=[^&]*', '', url)

        self.url: str = url
        self.echo = os.getenv("SQL_ECHO", "False").lower() == "true"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))


# Global engine instance
_engine: AsyncEngine | None = None


def init_db() -> AsyncEngine:
    """
    Initialize async database engine.

    Returns:
        AsyncEngine instance
    """
    global _engine
    config = DatabaseConfig()

    _engine = create_async_engine(
        config.url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )

    return _engine


def get_engine() -> AsyncEngine:
    """
    Get the database engine.

    Returns:
        AsyncEngine instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database sessions.

    Usage:
        @app.get("/tasks")
        async def get_tasks(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Task))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSession(_engine, expire_on_commit=False) as session:
        yield session


# Type alias for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_session)]
