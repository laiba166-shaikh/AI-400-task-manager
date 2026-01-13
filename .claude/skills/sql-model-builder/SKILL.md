---
name: sql-model-builder
description: >
  Build production-ready SQL data models using SQLModel (combines SQLAlchemy ORM + Pydantic validation in one).
  Use this skill when the user needs to: (1) Create unified database models that work for both ORM and API validation,
  (2) Implement database session management (sync or async), (3) Create CRUD operations and repository patterns,
  (4) Build FastAPI integrations with automatic validation, (5) Set up multi-database support
  (PostgreSQL, MySQL, SQLite), (6) Optimize database queries and indexing, (7) Configure Alembic migrations,
  (8) Implement security best practices for data access, or (9) Design scalable, production-ready data-access layers.
  SQLModel eliminates code duplication by using a single model class hierarchy for both database tables and Pydantic schemas,
  providing type safety, automatic validation, and seamless FastAPI integration.
---

# SQL Model Builder

Build production-ready SQL data models using **SQLModel** - a library that combines SQLAlchemy ORM and Pydantic validation in one unified approach.

## Why SQLModel?

SQLModel provides a single source of truth for your data models:
- **One model definition** instead of separate ORM + Pydantic schemas
- **Automatic validation** - Pydantic validation works on database models
- **Type safety** - Full IDE autocomplete and type checking
- **Less boilerplate** - No need for `model_config = {"from_attributes": True}`
- **FastAPI optimized** - Created by the same author for seamless integration

## Quick Start

### 1. Choose Database Backend

Ask the user which database they're using, then load the appropriate reference for driver setup:

- **PostgreSQL**: Read `references/postgresql.md` for asyncpg configuration
- **MySQL**: Read `references/mysql.md` for aiomysql configuration
- **SQLite**: Read `references/sqlite.md` for aiosqlite configuration

### 2. Model Pattern - Single Source of Truth

**Traditional Approach (Separate ORM + Pydantic):**
```python
# models.py - SQLAlchemy ORM
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column()

# schemas.py - Pydantic validation
class UserCreate(BaseModel):
    email: str

class UserRead(BaseModel):
    id: int
    email: str
    model_config = {"from_attributes": True}
```

**SQLModel Approach (Unified):**
```python
# models.py - SQLModel does both!
from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    email: str = Field(index=True)

class User(UserBase, table=True):
    """Database table"""
    id: int | None = Field(default=None, primary_key=True)

class UserCreate(UserBase):
    """For API POST requests"""
    pass

class UserRead(UserBase):
    """For API responses"""
    id: int
```

### 3. Use Script Templates

All script templates in `scripts/` are production-ready:

**Models** (`scripts/base_models.py`):
- `TaskBase` - Shared fields across variants
- `Task` (table=True) - Database table model
- `TaskCreate` - POST request schema
- `TaskRead` - GET response schema
- `TaskUpdate` - PATCH request schema (all optional)

**Session Management** (`scripts/session_factory.py`):
- `DatabaseConfig` - Environment-based configuration
- Async engine setup with connection pooling
- `get_session()` - FastAPI dependency for async sessions
- Auto-conversion of PostgreSQL URLs to async drivers

**CRUD Repository** (`scripts/crud_repository.py`):
- `TaskRepository` - Generic async CRUD operations
- Uses `select()` from sqlmodel (not sqlalchemy.select)
- All operations are async for performance

### 4. Implementation Workflow

When building a data model:

1. **Define base model with shared fields**
   ```python
   class TaskBase(SQLModel):
       title: str = Field(min_length=1, max_length=200, index=True)
       completed: bool = Field(default=False)
   ```

2. **Create table model (table=True)**
   ```python
   class Task(TaskBase, table=True):
       __tablename__ = "tasks"
       id: int | None = Field(default=None, primary_key=True)
       created_at: datetime = Field(default_factory=datetime.utcnow)
   ```

3. **Create request/response schemas**
   ```python
   class TaskCreate(TaskBase):
       """Inherits title, completed from TaskBase"""
       pass

   class TaskRead(TaskBase):
       """Includes all fields for responses"""
       id: int
       created_at: datetime

   class TaskUpdate(SQLModel):
       """All fields optional for PATCH"""
       title: str | None = None
       completed: bool | None = None
   ```

4. **Set up async session management**
   - Copy session factory from `scripts/session_factory.py`
   - Configure connection pooling for production
   - Use FastAPI dependencies for injection

5. **Implement repository pattern**
   - Use repository from `scripts/crud_repository.py`
   - Add custom methods as needed
   - Keep database logic separate from business logic

6. **Configure migrations**
   - Copy `assets/alembic.ini` and `assets/env.py`
   - Use `SQLModel.metadata` instead of `Base.metadata`
   - Follow `references/alembic_guide.md` for migration workflows

## Key Differences from SQLAlchemy

### Field Definitions

**SQLAlchemy:**
```python
email: Mapped[str] = mapped_column(index=True)
```

**SQLModel:**
```python
email: str = Field(index=True)
```

### Relationships

**SQLAlchemy:**
```python
posts: Mapped[List["Post"]] = relationship(back_populates="author")
```

**SQLModel:**
```python
posts: List["Post"] = Relationship(back_populates="author")
```

### Queries

**SQLAlchemy:**
```python
from sqlalchemy import select
stmt = select(User).where(User.email == "test@example.com")
```

**SQLModel:**
```python
from sqlmodel import select
stmt = select(User).where(User.email == "test@example.com")
```

### Table Creation

**SQLAlchemy:**
```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

**SQLModel:**
```python
async with engine.begin() as conn:
    await conn.run_sync(SQLModel.metadata.create_all)
```

## Production Readiness

Before deploying to production, consult these references:

### Security (`references/security.md`)
Read when implementing:
- User authentication and authorization
- Password storage
- SQL injection prevention
- Data exposure controls

### Performance (`references/performance.md`)
Read when:
- Queries are slow or timing out
- Database is under high load
- Implementing pagination
- Optimizing N+1 queries

### Migrations (`references/alembic_guide.md`)
Read when:
- Setting up database migrations
- Creating migration scripts
- Handling schema changes
- Running migrations in production

## Dependencies

```toml
[project]
dependencies = [
    "sqlmodel>=0.0.14",
    "asyncpg>=0.29.0",      # For PostgreSQL
    "python-dotenv>=1.0.0",
]
```

For MySQL, replace `asyncpg` with `aiomysql>=0.2.0`.
For SQLite, add `aiosqlite>=0.19.0`.

## Common Patterns

### Timestamps
```python
class TaskBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

### Soft Deletes
```python
class TaskBase(SQLModel):
    deleted_at: datetime | None = Field(default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
```

### Validation
```python
class TaskCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    email: str = Field(regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    priority: int = Field(ge=1, le=5)
```

### FastAPI Integration
```python
from fastapi import FastAPI, Depends
from sqlmodel import Session

@app.post("/tasks/", response_model=TaskRead)
async def create_task(task: TaskCreate, session: SessionDep):
    repo = TaskRepository(session)
    db_task = await repo.create(task.model_dump())
    await session.commit()
    return db_task
```

## References

- **Database-specific patterns**: See `references/postgresql.md`, `references/mysql.md`, or `references/sqlite.md`
- **Security best practices**: See `references/security.md`
- **Performance optimization**: See `references/performance.md`
- **Migration workflows**: See `references/alembic_guide.md`