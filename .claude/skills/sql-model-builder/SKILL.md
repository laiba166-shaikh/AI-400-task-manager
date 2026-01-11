---
name: sql-model-builder
description: >
  Build production-ready SQL data models and data-access layers with SQLAlchemy ORM 2.x and Pydantic v2.
  Use this skill when the user needs to: (1) Create database models with SQLAlchemy declarative syntax,
  (2) Set up Pydantic schemas for validation and serialization, (3) Implement database session management
  (sync or async), (4) Create CRUD operations and repository patterns, (5) Configure Alembic migrations,
  (6) Optimize database queries and indexing, (7) Implement security best practices for data access,
  (8) Build FastAPI integrations with dependency injection, (9) Set up multi-database support
  (PostgreSQL, MySQL, SQLite), or (10) Design scalable, production-ready data-access layers.
  This skill provides official documentation-based patterns, reusable script templates, and
  comprehensive guidance for database design, performance optimization, and security.
---

# SQL Model Builder

Build production-ready SQL data models and data-access layers using SQLAlchemy ORM 2.x and Pydantic v2.

## Quick Start

### 1. Choose Database Backend

Ask the user which database they're using, then load the appropriate reference:

- **PostgreSQL**: Read `references/postgresql.md`
- **MySQL**: Read `references/mysql.md`
- **SQLite**: Read `references/sqlite.md`

### 2. Use Script Templates

All script templates in `scripts/` are production-ready and follow SQLAlchemy 2.x best practices:

**Base Models** (`scripts/base_models.py`):
- `Base` - Synchronous base class
- `AsyncBase` - Async base class with `AsyncAttrs`
- `TimestampMixin` - Auto-managed created_at/updated_at
- `SoftDeleteMixin` - Soft delete with deleted_at

**Session Management** (`scripts/session_factory.py`):
- `SyncSessionFactory` - Sync session management
- `AsyncSessionFactory` - Async session management
- `get_db()` - FastAPI dependency for sync sessions
- `get_async_db()` - FastAPI dependency for async sessions

**CRUD Repository** (`scripts/crud_repository.py`):
- `SyncRepository[ModelType]` - Generic sync CRUD operations
- `AsyncRepository[ModelType]` - Generic async CRUD operations

### 3. Implementation Workflow

When building a data model:

1. **Start with base model**
   - Copy relevant base class from `scripts/base_models.py`
   - Use `Mapped[]` type annotations (required in SQLAlchemy 2.x)
   - Add mixins as needed (TimestampMixin, SoftDeleteMixin)

2. **Create Pydantic schemas**
   - Separate schemas for Create, Update, and Response
   - Use `ConfigDict(from_attributes=True)` for ORM compatibility
   - Exclude sensitive fields (password_hash, etc.)

3. **Set up session management**
   - Copy session factory from `scripts/session_factory.py`
   - Configure connection pooling for production
   - Use FastAPI dependencies for injection

4. **Implement business logic**
   - Use repository pattern from `scripts/crud_repository.py`
   - Add custom methods as needed
   - Keep database logic separate from business logic

5. **Configure migrations**
   - Copy `assets/alembic.ini` and `assets/env.py`
   - Run `alembic init alembic` if starting fresh
   - Follow `references/alembic_guide.md` for migration workflows

## Production Readiness

Before deploying to production, consult these references:

### Security (`references/security.md`)
Read this when implementing:
- User authentication and authorization
- Password storage
- SQL injection prevention
- Data exposure controls
- Row-level security (PostgreSQL RLS)
- Audit logging

### Performance (`references/performance.md`)
Read this when:
- Queries are slow or timing out
- Database is under high load
- Implementing pagination
- Working with large datasets
- Optimizing N+1 queries

### Migrations (`references/alembic_guide.md`)
Read this when:
- Setting up database migrations
- Creating auto-generated migrations
- Writing data migrations
- Handling zero-downtime deployments
- Troubleshooting migration issues

## Database-Specific Patterns

Load the appropriate reference based on the target database:

### PostgreSQL (`references/postgresql.md`)
Use for:
- UUID primary keys
- JSONB operations
- Array columns
- Full-text search with TSVECTOR
- INSERT ... ON CONFLICT (upsert)
- GIN/GiST indexes
- PostgreSQL extensions

### MySQL (`references/mysql.md`)
Use for:
- Character sets (utf8mb4)
- JSON operations
- INSERT ... ON DUPLICATE KEY UPDATE
- FULLTEXT search
- Storage engines (InnoDB vs MyISAM)
- Prefix indexes

### SQLite (`references/sqlite.md`)
Use for:
- Development and testing setups
- In-memory databases
- FTS5 full-text search
- Batch operations
- PRAGMA configuration
- WAL mode for concurrency

## FastAPI Integration Pattern

For FastAPI applications, follow this pattern:

1. **Initialize database on startup**:
   ```python
   from session_factory import init_async_db, DatabaseConfig

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       config = DatabaseConfig(url=os.getenv("DATABASE_URL"))
       init_async_db(config)
       yield
       # Cleanup on shutdown

   app = FastAPI(lifespan=lifespan)
   ```

2. **Use dependency injection**:
   ```python
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from session_factory import get_async_db

   @app.get("/users/{user_id}")
   async def get_user(
       user_id: int,
       db: AsyncSession = Depends(get_async_db)
   ):
       # Use db session here
   ```

3. **Implement service layer with repositories**:
   ```python
   from crud_repository import AsyncRepository

   class UserService:
       def __init__(self, session: AsyncSession):
           self.repo = AsyncRepository(User, session)

       async def get_user(self, user_id: int):
           return await self.repo.get(user_id)
   ```

## Common Patterns

### Creating Models

Use SQLAlchemy 2.x declarative syntax with `Mapped[]` annotations:

```python
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str]
    full_name: Mapped[Optional[str]]  # Nullable field
    is_active: Mapped[bool] = mapped_column(default=True)
```

### Relationships

```python
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from typing import List

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    posts: Mapped[List["Post"]] = relationship(back_populates="user")

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
```

### Pydantic Schemas

Separate schemas for different operations:

```python
from pydantic import BaseModel, ConfigDict, EmailStr

# For creating new records
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# For updating existing records
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

# For API responses
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    # Never include password_hash!
```

## Key Principles

1. **Use Official Documentation Patterns**
   - All patterns follow SQLAlchemy 2.x and Pydantic v2 official docs
   - Avoid deprecated 1.x patterns (Query API, declarative_base from sqlalchemy.ext.declarative)

2. **Separate Concerns**
   - Models: Database schema (SQLAlchemy)
   - Schemas: Data validation and serialization (Pydantic)
   - Repositories: Data access patterns
   - Services: Business logic

3. **Security First**
   - Never expose password hashes
   - Use bound parameters (automatic with ORM)
   - Validate all user input
   - Implement proper access controls

4. **Performance Matters**
   - Use eager loading for relationships
   - Add indexes on frequently queried columns
   - Implement pagination for large datasets
   - Monitor and optimize slow queries

5. **Migration Discipline**
   - Review auto-generated migrations
   - Test migrations before production
   - Plan zero-downtime migrations
   - Keep schema and data migrations separate

## When to Read References

The skill includes detailed reference files. Read them selectively:

- **Starting a new project?** Read the database-specific reference (postgresql.md, mysql.md, or sqlite.md)
- **Implementing auth?** Read security.md
- **Queries too slow?** Read performance.md
- **Setting up migrations?** Read alembic_guide.md
- **Need a specific pattern?** Search the relevant reference file

## Script Usage

Scripts are templates to copy and customize:

1. **Read the script** to understand the pattern
2. **Copy relevant parts** to your codebase
3. **Customize** for your specific needs
4. **Test thoroughly** before deploying

Do not import scripts directly - they're templates, not a library.

## Troubleshooting

### Type Errors with Mapped[]

If you see type errors with `Mapped[]`, ensure you're using SQLAlchemy 2.0+:
```bash
pip install "sqlalchemy>=2.0"
```

### Async Relationship Loading

For async models, use `selectinload()` or `joinedload()` for eager loading:
```python
stmt = select(User).options(selectinload(User.posts))
result = await session.execute(stmt)
```

Or use `AsyncAttrs` and `awaitable_attrs`:
```python
user = await session.get(User, 1)
posts = await user.awaitable_attrs.posts
```

### Migration Not Detected

Ensure all models are imported in `env.py`:
```python
# env.py
from app.models import User, Post, Comment  # Import all models
```

## Example: Complete User Management

Combining all patterns for a complete example:

```python
# models.py
from base_models import TimestampMixin, Base
from sqlalchemy.orm import Mapped, mapped_column

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)

# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    is_active: bool

# services.py
from crud_repository import AsyncRepository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = AsyncRepository(User, session)

    async def create_user(self, data: UserCreate) -> User:
        hashed_password = pwd_context.hash(data.password)
        return await self.repo.create({
            "username": data.username,
            "email": data.email,
            "password_hash": hashed_password
        })

    async def get_user(self, user_id: int) -> User | None:
        return await self.repo.get(user_id)

# routes.py
from fastapi import APIRouter, Depends, HTTPException
from session_factory import get_async_db

router = APIRouter(prefix="/users")

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    service = UserService(db)
    return await service.create_user(user_data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

This example demonstrates:
- SQLAlchemy 2.x models with type annotations
- Pydantic schemas for validation
- Repository pattern for data access
- Service layer for business logic
- FastAPI integration with dependency injection
- Password hashing for security
- Proper separation of concerns
