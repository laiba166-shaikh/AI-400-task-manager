# SQLModel Implementation Plan - Task Manager API

## Overview
Using **SQLModel** (combines Pydantic + SQLAlchemy) for unified model definitions that work for both database ORM and API validation.

---

## Key Differences from SQLAlchemy + Pydantic Approach

### Before (Separate):
```python
# models.py - SQLAlchemy ORM
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()

# schemas.py - Pydantic validation
class TaskCreate(BaseModel):
    title: str

class TaskResponse(BaseModel):
    id: int
    title: str
```

### After (Unified with SQLModel):
```python
# models.py - ONE file, ONE class hierarchy
from sqlmodel import SQLModel, Field

class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=200, index=True)
    description: str | None = None
    completed: bool = False

class Task(TaskBase, table=True):
    """Database model"""
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None

class TaskCreate(TaskBase):
    """For POST requests"""
    pass  # Inherits title, description, completed

class TaskRead(TaskBase):
    """For responses"""
    id: int
    created_at: datetime
    updated_at: datetime | None

class TaskUpdate(SQLModel):
    """For PATCH requests - all optional"""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None
```

---

## Review of Current Files

### ✅ Correctly Implemented:
1. **pyproject.toml** - Dependencies updated to SQLModel ✓
2. **Directory structure** - Correct ✓
3. **pytest.ini** - Correct ✓
4. **.env.example** - Correct ✓

### ❌ Needs Rewrite:
1. **app/database.py** - Mixing SQLModel and SQLAlchemy imports incorrectly
   - Issue: Using `sqlmodel.create_engine` (unused) and `sqlalchemy.ext.asyncio.create_async_engine`
   - Issue: Importing `AsyncEngine` from wrong location
   - Fix: Use SQLAlchemy's async engine directly (SQLModel doesn't have full async engine support yet)

2. **app/models.py** - Still using old SQLAlchemy `Mapped[]` syntax
   - Issue: Using `Mapped`, `mapped_column`, `AsyncBase`
   - Issue: Not using SQLModel's `Field()` for dual purpose
   - Fix: Rewrite with SQLModel base class and Field()

---

## Corrected Architecture

### 1. Dependencies (pyproject.toml)

```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlmodel>=0.0.14",        # Combines Pydantic + SQLAlchemy
    "asyncpg>=0.29.0",         # Async PostgreSQL driver
    "python-dotenv>=1.0.0",
]
```

**Note:** `psycopg2-binary` is for sync connections. We use `asyncpg` for async.

### 2. Database Layer (app/database.py)

```python
"""Database configuration with SQLModel + Async support."""
import os
from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from fastapi import Depends
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    def __init__(self):
        url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
        if not url:
            raise ValueError("DATABASE_URL or DB_URL required")

        # Auto-convert to async driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.url: str = url
        self.echo = os.getenv("SQL_ECHO", "False").lower() == "true"


# Global engine
_engine: AsyncEngine | None = None


def init_db() -> AsyncEngine:
    """Initialize async database engine."""
    global _engine
    config = DatabaseConfig()

    _engine = create_async_engine(
        config.url,
        echo=config.echo,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

    return _engine


def get_engine() -> AsyncEngine:
    """Get database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes.

    Usage:
        @app.get("/tasks")
        async def get_tasks(session: AsyncSession = Depends(get_session)):
            ...
    """
    if _engine is None:
        raise RuntimeError("Database not initialized.")

    async with AsyncSession(_engine, expire_on_commit=False) as session:
        yield session


# Type alias for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

### 3. Models (app/models.py) - Unified ORM + Schemas

```python
"""SQLModel models - serve as both ORM models and Pydantic schemas."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class TaskBase(SQLModel):
    """Base task fields shared across variants."""
    title: str = Field(min_length=1, max_length=200, index=True)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)


class Task(TaskBase, table=True):
    """
    Database table model.

    table=True makes this a database table.
    Inherits title, description, completed from TaskBase.
    """
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class TaskCreate(TaskBase):
    """
    Schema for creating tasks (POST /tasks/).

    Inherits: title, description, completed
    No id or timestamps (auto-generated)
    """
    pass


class TaskRead(TaskBase):
    """
    Schema for reading tasks (responses).

    Includes all fields including id and timestamps.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime]


class TaskUpdate(SQLModel):
    """
    Schema for updating tasks (PATCH /tasks/{id}).

    All fields optional for partial updates.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    completed: Optional[bool] = None
```

### 4. CRUD Operations (app/crud.py)

```python
"""CRUD operations using SQLModel."""
from typing import List, Optional, Dict, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Task


class TaskRepository:
    """Repository for Task CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_data: Dict[str, Any]) -> Task:
        """Create a new task."""
        task = Task(**task_data)
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return await self.session.get(Task, task_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks with pagination."""
        statement = select(Task).offset(skip).limit(limit).order_by(Task.id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(self, task_id: int, data: Dict[str, Any]) -> Optional[Task]:
        """Update task by ID."""
        task = await self.get(task_id)
        if not task:
            return None

        for key, value in data.items():
            setattr(task, key, value)

        # Update timestamp
        task.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: int) -> bool:
        """Delete task by ID."""
        task = await self.get(task_id)
        if not task:
            return False

        await self.session.delete(task)
        await self.session.flush()
        return True
```

### 5. API Router (app/routers/tasks.py)

```python
"""Task API endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.database import SessionDep
from app.models import TaskCreate, TaskRead, TaskUpdate
from app.crud import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, session: SessionDep):
    """Create a new task."""
    repo = TaskRepository(session)
    db_task = await repo.create(task.model_dump())
    await session.commit()
    return db_task


@router.get("/", response_model=List[TaskRead])
async def list_tasks(session: SessionDep, skip: int = 0, limit: int = 100):
    """List all tasks."""
    repo = TaskRepository(session)
    tasks = await repo.get_all(skip=skip, limit=limit)
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, session: SessionDep):
    """Get a specific task."""
    repo = TaskRepository(session)
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task_update: TaskUpdate, session: SessionDep):
    """Update a task (partial update)."""
    repo = TaskRepository(session)

    # Get only fields that were actually set
    update_data = task_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    task = await repo.update(task_id, update_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    await session.commit()
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: SessionDep):
    """Delete a task."""
    repo = TaskRepository(session)
    deleted = await repo.delete(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    await session.commit()
    return None
```

### 6. Main Application (main.py)

```python
"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel
from app.database import init_db, get_engine
from app.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup: Initialize database and create tables
    engine = init_db()

    async with engine.begin() as conn:
        # Create all tables from SQLModel metadata
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Shutdown: Dispose engine
    await engine.dispose()


app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="Simple CRUD API for managing tasks with SQLModel",
    lifespan=lifespan,
)

# Include routers
app.include_router(tasks.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Task Manager API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

### 7. Test Infrastructure (tests/conftest.py)

```python
"""Pytest fixtures for testing."""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel
from httpx import AsyncClient
from app.main import app
from app.database import get_session
from app.models import Task

# Test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test_db")


# Test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides test database session with transaction rollback.
    Each test gets a clean database.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session with transaction
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides async test client with database override."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_task(session: AsyncSession) -> Task:
    """Factory fixture for creating test tasks."""
    task = Task(
        title="Test Task",
        description="Test Description",
        completed=False
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task
```

---

## Updated Implementation Steps (TDD)

### Phase 1: Setup ✅
- [x] Update pyproject.toml with SQLModel
- [x] Install dependencies
- [x] Create directory structure

### Phase 2: Database & Models
1. **Rewrite app/database.py** with corrected async support
2. **Rewrite app/models.py** with SQLModel (Base, Table, Create, Read, Update)
3. **Write model tests** (tests/unit/test_models.py)
4. **Run tests** - Should pass

### Phase 3: CRUD
1. **Write CRUD tests first** (tests/unit/test_crud.py)
2. **Run tests** - Should fail
3. **Implement app/crud.py** with TaskRepository
4. **Run tests** - Should pass

### Phase 4: API
1. **Write API tests first** (tests/api/test_tasks.py)
2. **Run tests** - Should fail
3. **Implement app/routers/tasks.py**
4. **Run tests** - Should pass

### Phase 5: Main App
1. **Create main.py** with SQLModel metadata
2. **Create tests/conftest.py** with fixtures
3. **Run full test suite**

### Phase 6: Manual Testing
1. Start server: `uvicorn main:app --reload`
2. Test endpoints with curl
3. Verify database tables created
4. Test full CRUD cycle

---

## Key SQLModel Benefits

1. **Single Source of Truth**: One model class hierarchy instead of duplicate ORM + Pydantic
2. **Type Safety**: Full editor autocomplete and type checking
3. **Less Boilerplate**: No need for `model_config = {"from_attributes": True}`
4. **Automatic Validation**: Pydantic validation works automatically on database models
5. **Easier Refactoring**: Change field once, updates everywhere

---

## Summary of Changes Needed

| File | Status | Action Required |
|------|--------|-----------------|
| pyproject.toml | ✅ Done | None |
| app/database.py | ❌ Wrong | Complete rewrite for async |
| app/models.py | ❌ Wrong | Rewrite with SQLModel classes |
| app/crud.py | ⚠️ Not created | Create with select() from sqlmodel |
| app/routers/tasks.py | ⚠️ Not created | Create using SQLModel schemas |
| main.py | ⚠️ Not created | Create with SQLModel.metadata |
| tests/conftest.py | ⚠️ Not created | Create with SQLModel fixtures |

---

**Next Step**: Start with rewriting app/database.py and app/models.py with the correct SQLModel patterns above.
