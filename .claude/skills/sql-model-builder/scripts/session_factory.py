"""
SQLAlchemy 2.x Session Management Templates

Provides session factory patterns for both sync and async database operations,
including FastAPI dependency injection patterns.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import Session, sessionmaker


# ============================================================================
# CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """
    Database configuration holder.

    Usage:
        config = DatabaseConfig(
            url="postgresql://user:pass@localhost/dbname",
            echo=True
        )
    """
    def __init__(
        self,
        url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600,
    ):
        self.url = url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_pre_ping = pool_pre_ping
        self.pool_recycle = pool_recycle


# ============================================================================
# SYNCHRONOUS SESSION FACTORY
# ============================================================================

class SyncSessionFactory:
    """
    Synchronous session factory with connection pooling.

    Usage:
        factory = SyncSessionFactory(config)

        # Context manager
        with factory.session() as session:
            user = session.get(User, 1)

        # Manual management
        session = factory.get_session()
        try:
            user = session.get(User, 1)
            session.commit()
        finally:
            session.close()
    """

    def __init__(self, config: DatabaseConfig):
        self.engine = create_engine(
            config.url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_pre_ping=config.pool_pre_ping,
            pool_recycle=config.pool_recycle,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def get_session(self) -> Session:
        """Get a new session instance"""
        return self.SessionLocal()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager for session lifecycle"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# ============================================================================
# ASYNCHRONOUS SESSION FACTORY
# ============================================================================

class AsyncSessionFactory:
    """
    Asynchronous session factory with connection pooling.

    Usage:
        factory = AsyncSessionFactory(config)

        # Context manager
        async with factory.session() as session:
            user = await session.get(User, 1)

        # Manual management
        session = factory.get_session()
        try:
            async with session.begin():
                user = await session.get(User, 1)
        finally:
            await session.close()
    """

    def __init__(self, config: DatabaseConfig):
        # Convert sync URL to async (e.g., postgresql -> postgresql+asyncpg)
        async_url = self._convert_to_async_url(config.url)

        self.engine = create_async_engine(
            async_url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_pre_ping=config.pool_pre_ping,
            pool_recycle=config.pool_recycle,
        )
        self.async_session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @staticmethod
    def _convert_to_async_url(url: str) -> str:
        """Convert sync database URL to async driver"""
        replacements = {
            "postgresql://": "postgresql+asyncpg://",
            "mysql://": "mysql+aiomysql://",
            "sqlite:///": "sqlite+aiosqlite:///",
        }
        for sync_prefix, async_prefix in replacements.items():
            if url.startswith(sync_prefix):
                return url.replace(sync_prefix, async_prefix, 1)
        return url

    def get_session(self) -> AsyncSession:
        """Get a new async session instance"""
        return self.async_session_maker()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for async session lifecycle"""
        session = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# FASTAPI DEPENDENCY INJECTION
# ============================================================================

# Global session factories (initialize in app startup)
_sync_factory: SyncSessionFactory | None = None
_async_factory: AsyncSessionFactory | None = None


def init_sync_db(config: DatabaseConfig) -> None:
    """Initialize sync database factory (call in FastAPI startup)"""
    global _sync_factory
    _sync_factory = SyncSessionFactory(config)


def init_async_db(config: DatabaseConfig) -> None:
    """Initialize async database factory (call in FastAPI startup)"""
    global _async_factory
    _async_factory = AsyncSessionFactory(config)


# Sync dependency
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for sync database sessions.

    Usage:
        @app.get("/users/{user_id}")
        def get_user(user_id: int, db: Session = Depends(get_db)):
            return db.get(User, user_id)
    """
    if _sync_factory is None:
        raise RuntimeError("Database not initialized. Call init_sync_db() first.")

    with _sync_factory.session() as session:
        yield session


# Async dependency
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions.

    Usage:
        @app.get("/users/{user_id}")
        async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
            return await db.get(User, user_id)
    """
    if _async_factory is None:
        raise RuntimeError("Database not initialized. Call init_async_db() first.")

    async with _async_factory.session() as session:
        yield session


# ============================================================================
# EXAMPLE FASTAPI INTEGRATION
# ============================================================================

"""
# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config = DatabaseConfig(
        url=os.getenv("DATABASE_URL"),
        echo=True
    )
    init_async_db(config)
    yield
    # Shutdown
    if _async_factory:
        await _async_factory.engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
"""
