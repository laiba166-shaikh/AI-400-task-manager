# Performance Optimization

Performance patterns and optimization strategies for SQLAlchemy 2.x applications.

## Query Optimization

### N+1 Query Problem

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload, subqueryload

# ❌ BAD: N+1 queries (1 query for users + N queries for posts)
users = await session.execute(select(User))
for user in users.scalars():
    print(user.posts)  # Lazy load - separate query for each user!

# ✅ GOOD: Eager loading with selectinload (2 queries total)
stmt = select(User).options(selectinload(User.posts))
users = await session.execute(stmt)
for user in users.scalars():
    print(user.posts)  # Already loaded

# ✅ GOOD: Eager loading with joinedload (1 query with LEFT OUTER JOIN)
stmt = select(User).options(joinedload(User.posts))
users = await session.execute(stmt)

# For deeply nested relationships
stmt = select(User).options(
    selectinload(User.posts).selectinload(Post.comments)
)

# Choose the right loading strategy:
# - joinedload: Use for one-to-one or small one-to-many (single query with JOIN)
# - selectinload: Use for one-to-many or many-to-many (2 queries, IN clause)
# - subqueryload: Alternative to selectinload (2 queries, subquery)
```

### Selecting Only Required Columns

```python
from sqlalchemy import select

# ❌ BAD: Loading full objects when only few fields needed
users = await session.execute(select(User))

# ✅ GOOD: Select only required columns
stmt = select(User.id, User.username, User.email)
result = await session.execute(stmt)
for row in result:
    print(row.id, row.username, row.email)

# Load as model instances with only specific columns
stmt = select(User).with_only_columns(User.id, User.username)
```

### Query Result Caching

```python
from sqlalchemy import select
from sqlalchemy.orm import Query
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache with TTL
cache = {}
CACHE_TTL = timedelta(minutes=5)

async def get_user_cached(session: AsyncSession, user_id: int):
    cache_key = f"user:{user_id}"

    # Check cache
    if cache_key in cache:
        data, timestamp = cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return data

    # Fetch from database
    user = await session.get(User, user_id)

    # Store in cache
    cache[cache_key] = (user, datetime.now())

    return user

# Using Redis for distributed caching
import redis.asyncio as redis
import pickle

redis_client = redis.Redis(host="localhost", port=6379, db=0)

async def get_user_redis_cached(session: AsyncSession, user_id: int):
    cache_key = f"user:{user_id}"

    # Check Redis cache
    cached = await redis_client.get(cache_key)
    if cached:
        return pickle.loads(cached)

    # Fetch from database
    user = await session.get(User, user_id)

    # Store in Redis with TTL
    await redis_client.setex(
        cache_key,
        300,  # 5 minutes
        pickle.dumps(user)
    )

    return user
```

## Bulk Operations

### Bulk Insert

```python
from sqlalchemy import insert

# ❌ BAD: Individual inserts
for data in user_data_list:
    user = User(**data)
    session.add(user)
await session.commit()  # Slow!

# ✅ GOOD: Bulk insert with Core
stmt = insert(User).values(user_data_list)
await session.execute(stmt)
await session.commit()

# ✅ GOOD: Bulk insert with ORM (if you need objects back)
session.add_all([User(**data) for data in user_data_list])
await session.commit()

# ✅ BEST: Bulk insert with returning
stmt = insert(User).values(user_data_list).returning(User)
result = await session.execute(stmt)
users = result.scalars().all()
```

### Bulk Update

```python
from sqlalchemy import update

# ❌ BAD: Individual updates
for user_id in user_ids:
    user = await session.get(User, user_id)
    user.is_active = True
await session.commit()

# ✅ GOOD: Single bulk update
stmt = update(User).where(User.id.in_(user_ids)).values(is_active=True)
await session.execute(stmt)
await session.commit()

# Bulk update with dict of values
data = [
    {"id": 1, "username": "user1"},
    {"id": 2, "username": "user2"},
]

from sqlalchemy.dialects.postgresql import insert
stmt = insert(User).values(data)
stmt = stmt.on_conflict_do_update(
    index_elements=["id"],
    set_={"username": stmt.excluded.username}
)
await session.execute(stmt)
```

### Bulk Delete

```python
from sqlalchemy import delete

# ❌ BAD: Individual deletes
for user_id in user_ids:
    user = await session.get(User, user_id)
    await session.delete(user)
await session.commit()

# ✅ GOOD: Bulk delete
stmt = delete(User).where(User.id.in_(user_ids))
await session.execute(stmt)
await session.commit()
```

## Pagination

```python
from sqlalchemy import select, func

async def get_users_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20
):
    # Get total count
    count_stmt = select(func.count()).select_from(User)
    total = await session.scalar(count_stmt)

    # Get paginated results
    offset = (page - 1) * page_size
    stmt = select(User).offset(offset).limit(page_size).order_by(User.id)
    result = await session.execute(stmt)
    users = result.scalars().all()

    return {
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

# Cursor-based pagination (better for large datasets)
async def get_users_cursor(
    session: AsyncSession,
    cursor: int | None = None,
    limit: int = 20
):
    stmt = select(User).limit(limit).order_by(User.id)

    if cursor:
        stmt = stmt.where(User.id > cursor)

    result = await session.execute(stmt)
    users = result.scalars().all()

    next_cursor = users[-1].id if users else None

    return {
        "items": users,
        "next_cursor": next_cursor
    }
```

## Indexing Strategies

```python
from sqlalchemy import Index, text

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[datetime]
    is_active: Mapped[bool]

    __table_args__ = (
        # Single column index for equality lookups
        Index("ix_users_email", "email"),

        # Unique index for constraints
        Index("ix_users_username", "username", unique=True),

        # Composite index for multi-column queries
        Index("ix_users_active_created", "is_active", "created_at"),

        # Partial/filtered index (PostgreSQL)
        Index(
            "ix_users_active_email",
            "email",
            postgresql_where=text("is_active = true")
        ),

        # Expression index (PostgreSQL)
        Index("ix_users_lower_email", text("lower(email)")),

        # Covering index (PostgreSQL) - includes extra columns
        Index(
            "ix_users_username_covering",
            "username",
            postgresql_include=["email", "created_at"]
        ),
    )
```

## Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

# Default pooling (QueuePool) for web apps
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Additional connections when pool is full
    pool_timeout=30,       # Wait time for available connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Verify connection before using
)

# NullPool for serverless (Lambda, Cloud Functions)
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    poolclass=NullPool,
)

# Custom pool configuration
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo_pool=True,  # Log pool checkouts/checkins (debug only)
)
```

## Query Analysis

### EXPLAIN Queries

```python
from sqlalchemy import select, text

# Get query execution plan
stmt = select(User).where(User.email == "user@example.com")

# PostgreSQL
explain_stmt = text(f"EXPLAIN ANALYZE {str(stmt.compile())}")
result = await session.execute(explain_stmt)
print(result.fetchall())

# Helper function
async def explain_query(session: AsyncSession, stmt):
    compiled = stmt.compile(compile_kwargs={"literal_binds": True})
    explain_stmt = text(f"EXPLAIN ANALYZE {str(compiled)}")
    result = await session.execute(explain_stmt)
    for row in result:
        print(row[0])
```

### Slow Query Logging

```python
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.INFO)

# Log slow queries
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)

    # Log queries taking more than 1 second
    if total > 1.0:
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

## Async Best Practices

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager

# Use async context managers
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

# Properly close sessions
async with async_sessionmaker() as session:
    user = await session.get(User, 1)
    # Session automatically closes

# Batch operations in transactions
async with session.begin():
    session.add_all([User(username=f"user{i}") for i in range(1000)])
    # Automatically commits on success, rollback on error

# Stream large result sets
stmt = select(User)
async_result = await session.stream(stmt)
async for user in async_result.scalars():
    process(user)  # Process one at a time
```

## Write-Only Relationships (Async)

```python
from sqlalchemy.orm import WriteOnlyMapped, relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Use WriteOnlyMapped for large collections
    posts: WriteOnlyMapped["Post"] = relationship()

# Access write-only relationships
user = await session.get(User, 1)

# Add to collection
new_post = Post(title="New Post")
await user.posts.add(new_post)

# Query collection
posts = await session.scalars(user.posts.select().limit(10))

# Count without loading
count = await session.scalar(
    select(func.count()).select_from(user.posts.select().subquery())
)
```

## Performance Monitoring

```python
from prometheus_client import Counter, Histogram
import time

# Metrics
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["query_type"]
)

db_query_total = Counter(
    "db_query_total",
    "Total database queries",
    ["query_type", "status"]
)

# Track query performance
async def get_user_with_metrics(session: AsyncSession, user_id: int):
    start_time = time.time()

    try:
        user = await session.get(User, user_id)
        db_query_total.labels(query_type="get_user", status="success").inc()
        return user
    except Exception as e:
        db_query_total.labels(query_type="get_user", status="error").inc()
        raise
    finally:
        duration = time.time() - start_time
        db_query_duration.labels(query_type="get_user").observe(duration)
```

## Performance Checklist

- [ ] Use eager loading to avoid N+1 queries
- [ ] Select only required columns
- [ ] Use bulk operations for batch inserts/updates/deletes
- [ ] Implement proper pagination (cursor-based for large datasets)
- [ ] Add indexes on frequently queried columns
- [ ] Configure connection pooling appropriately
- [ ] Use query result caching where appropriate
- [ ] Monitor and log slow queries
- [ ] Use EXPLAIN ANALYZE to optimize queries
- [ ] Use WriteOnlyMapped for large collections in async
- [ ] Stream large result sets instead of loading all at once
- [ ] Batch operations within transactions
- [ ] Use compiled queries for frequently executed statements
- [ ] Implement query timeouts for long-running queries
- [ ] Monitor database connection pool usage
