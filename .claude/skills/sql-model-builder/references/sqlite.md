# SQLite-Specific Patterns

SQLAlchemy 2.x patterns and features specific to SQLite databases.

## Connection URLs

```python
# Sync connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"  # Relative path
SQLALCHEMY_DATABASE_URL = "sqlite:////absolute/path/to/app.db"  # Absolute path
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"  # In-memory database

# Async connection (aiosqlite)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./app.db"
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

## SQLite Configuration

```python
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

# Enable foreign key support (disabled by default in SQLite)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")  # Performance optimization
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
    cursor.close()

# Create engine with pragmas
engine = create_engine(
    "sqlite:///./app.db",
    echo=False,
    connect_args={
        "check_same_thread": False,  # Allow multi-threaded access (be careful!)
        "timeout": 30,  # Connection timeout in seconds
    }
)
```

## Async SQLite Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import event
from sqlalchemy.pool import NullPool

# Async engine with pragmas
engine = create_async_engine(
    "sqlite+aiosqlite:///./app.db",
    echo=False,
    poolclass=NullPool,  # Recommended for SQLite async
)

# Enable foreign keys and optimizations for async
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

@event.listens_for(AsyncEngine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
```

## Column Type Mapping

SQLite has limited native types; SQLAlchemy maps Python types appropriately:

```python
from sqlalchemy import String, Integer, Float, Boolean, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from typing import Optional
import uuid

class Example(Base):
    __tablename__ = "examples"

    # Integer types (stored as INTEGER)
    id: Mapped[int] = mapped_column(primary_key=True)
    count: Mapped[int]

    # Float types (stored as REAL)
    price: Mapped[float]

    # String types (stored as TEXT)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)

    # Boolean (stored as INTEGER 0/1)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Datetime (stored as TEXT ISO 8601 or INTEGER UNIX timestamp)
    created_at: Mapped[datetime]
    updated_at: Mapped[Optional[datetime]]

    # Date and Time
    birth_date: Mapped[date]
    wake_time: Mapped[time]

    # Binary data (stored as BLOB)
    file_data: Mapped[bytes] = mapped_column(LargeBinary)

    # UUID (stored as TEXT or BLOB)
    uuid: Mapped[uuid.UUID] = mapped_column(String(36))
```

## JSON Support (SQLite 3.38+)

```python
from sqlalchemy import JSON, select, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Dict, Any

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON)

# Query JSON fields
stmt = select(Product).where(
    Product.metadata["status"].astext == "active"
)

# JSON functions (SQLite 3.38+)
stmt = select(Product).where(
    func.json_extract(Product.metadata, "$.price").cast(Float) > 100
)

# JSON_EACH for array iteration
stmt = select(
    func.json_each(Product.metadata["tags"])
)
```

## Full-Text Search (FTS5)

```python
from sqlalchemy import Table, Column, Integer, Text, MetaData, event, text

# FTS5 virtual table
fts_table = Table(
    "articles_fts",
    Base.metadata,
    Column("title", Text),
    Column("content", Text),
    prefixes=[text("CREATE VIRTUAL TABLE")],
    postgresql_ignore_search_path=True,
    info={"fts5": True}
)

# Create FTS5 table using raw SQL
@event.listens_for(Base.metadata, "after_create")
def create_fts_table(target, connection, **kw):
    connection.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts
        USING fts5(title, content, content=articles, content_rowid=id)
    """))

    # Triggers to keep FTS in sync
    connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
            INSERT INTO articles_fts(rowid, title, content)
            VALUES (new.id, new.title, new.content);
        END
    """))

    connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
            UPDATE articles_fts
            SET title=new.title, content=new.content
            WHERE rowid=old.id;
        END
    """))

    connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
            DELETE FROM articles_fts WHERE rowid=old.id;
        END
    """))

# Search query
stmt = text("""
    SELECT a.* FROM articles a
    JOIN articles_fts fts ON a.id = fts.rowid
    WHERE articles_fts MATCH :query
    ORDER BY rank
""").bindparams(query="python sqlalchemy")
```

## Auto-Increment with AUTOINCREMENT

```python
from sqlalchemy import Integer

class User(Base):
    __tablename__ = "users"

    # SQLite AUTOINCREMENT (prevents rowid reuse)
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        sqlite_autoincrement=True
    )
    username: Mapped[str]
```

## UPSERT (INSERT OR REPLACE)

```python
from sqlalchemy.dialects.sqlite import insert

# Insert or replace
stmt = insert(User).values(
    id=1,
    username="john",
    email="john@example.com"
).prefix_with("OR REPLACE")

session.execute(stmt)

# Insert or ignore
stmt = insert(User).values(
    username="john",
    email="john@example.com"
).prefix_with("OR IGNORE")

session.execute(stmt)

# ON CONFLICT (SQLite 3.24+)
stmt = insert(User).values(
    username="john",
    email="john@example.com"
)

stmt = stmt.on_conflict_do_update(
    index_elements=["username"],
    set_={"email": "john@example.com"}
)

session.execute(stmt)
```

## Indexes

```python
from sqlalchemy import Index

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[datetime]

    __table_args__ = (
        # Standard index
        Index("ix_users_email", "email"),

        # Unique index
        Index("ix_users_username", "username", unique=True),

        # Composite index
        Index("ix_users_email_username", "email", "username"),

        # Partial index (SQLite 3.8+)
        Index(
            "ix_users_active_username",
            "username",
            unique=True,
            sqlite_where=text("deleted_at IS NULL")
        ),

        # Expression index (SQLite 3.9+)
        Index("ix_users_lower_email", text("lower(email)")),
    )
```

## Concurrency and WAL Mode

```python
from sqlalchemy import event, text

# Enable WAL mode for better concurrency
@event.listens_for(Engine, "connect")
def enable_wal_mode(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
    cursor.close()

# WAL mode benefits:
# - Multiple readers can access the database simultaneously
# - Writers don't block readers
# - Better performance for write-heavy workloads
```

## Limitations and Workarounds

### 1. No ALTER TABLE for Column Modifications

```python
# In Alembic migrations, use batch mode
def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("email", new_column_name="email_address")
        batch_op.add_column(Column("phone", String(20)))
```

### 2. Limited Date/Time Functions

```python
from sqlalchemy import func, text

# Current timestamp
created_at: Mapped[datetime] = mapped_column(
    server_default=func.current_timestamp()
)

# Use strftime for date operations
stmt = select(User).where(
    text("strftime('%Y', created_at) = '2024'")
)
```

### 3. No Native Boolean Type

```python
# SQLAlchemy automatically maps bool to INTEGER
is_active: Mapped[bool] = mapped_column(default=True)

# Stored as 0 (False) or 1 (True)
```

## Testing with In-Memory Database

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create in-memory database for testing
def get_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=True
    )

    # Enable foreign keys
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    return TestingSessionLocal()

# Use in tests
def test_create_user():
    db = get_test_db()
    user = User(username="test", email="test@example.com")
    db.add(user)
    db.commit()
    assert user.id is not None
```

## Performance Tips

1. **Enable WAL mode** for better concurrency and performance
2. **Increase cache_size** for better read performance (default is ~2MB)
3. **Use synchronous=NORMAL** for better write performance (less durable)
4. **Batch INSERT operations** to reduce transaction overhead
5. **Create indexes** on frequently queried columns
6. **Use temp_store=MEMORY** for faster temporary tables
7. **Avoid check_same_thread=False** in production (use NullPool for async)
8. **Run VACUUM** periodically to reclaim space and optimize
9. **Use ANALYZE** to update query planner statistics
10. **Consider limitations** - SQLite is not suitable for high-concurrency writes

## When to Use SQLite

**Good for:**
- Development and testing
- Small to medium applications (< 1TB data)
- Read-heavy workloads
- Embedded applications
- Single-server deployments
- File-based storage needs

**Not recommended for:**
- High-concurrency write workloads
- Network-accessed databases
- Very large datasets (> 1TB)
- Applications requiring fine-grained access control
- Distributed systems
