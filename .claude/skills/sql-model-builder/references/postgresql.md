# PostgreSQL-Specific Patterns

SQLAlchemy 2.x patterns and features specific to PostgreSQL databases.

## Connection URLs

```python
# Sync driver (psycopg2)
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/dbname"

# Async driver (asyncpg) - Recommended for async applications
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"

# With connection parameters
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/dbname?sslmode=require&connect_timeout=10"
```

## PostgreSQL-Specific Column Types

```python
from sqlalchemy import ARRAY, JSON
from sqlalchemy.dialects.postgresql import (
    UUID, JSONB, INET, CIDR, MACADDR, INTERVAL,
    ENUM, TSVECTOR, HSTORE
)
from sqlalchemy.orm import Mapped, mapped_column
from typing import List, Dict, Any
import uuid

class Product(Base):
    __tablename__ = "products"

    # UUID primary key (common in PostgreSQL)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # JSONB for structured data (preferred over JSON for performance)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON)  # Use JSONB instead

    # Array types
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))
    prices: Mapped[List[float]] = mapped_column(ARRAY(Float))

    # Network types
    ip_address: Mapped[str] = mapped_column(INET)
    network: Mapped[str] = mapped_column(CIDR)
    mac_address: Mapped[str] = mapped_column(MACADDR)

    # Full-text search
    search_vector: Mapped[str] = mapped_column(TSVECTOR)
```

## JSONB Operations

```python
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

# Query JSONB fields
stmt = select(Product).where(
    Product.metadata["status"].astext == "active"
)

# JSONB contains operator
stmt = select(Product).where(
    Product.metadata.contains({"category": "electronics"})
)

# JSONB path query
stmt = select(Product).where(
    Product.metadata["price"].astext.cast(Float) > 100.0
)

# Update JSONB field
stmt = (
    update(Product)
    .where(Product.id == product_id)
    .values(metadata=Product.metadata.concat({"updated": True}))
)
```

## Arrays

```python
from sqlalchemy import select, func

# Query array contains
stmt = select(Product).where(
    Product.tags.contains(["featured"])
)

# Array overlap
stmt = select(Product).where(
    Product.tags.overlap(["sale", "new"])
)

# Array length
stmt = select(Product).where(
    func.array_length(Product.tags, 1) > 3
)

# ANY operator
stmt = select(Product).where(
    "featured" == func.any_(Product.tags)
)
```

## Full-Text Search

```python
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TSVECTOR

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', title || ' ' || content)")
    )

# Search query
stmt = select(Article).where(
    Article.search_vector.match("python sqlalchemy", postgresql_regconfig="english")
)

# Ranked search results
stmt = (
    select(
        Article,
        func.ts_rank(Article.search_vector, func.to_tsquery("python & sqlalchemy"))
        .label("rank")
    )
    .where(Article.search_vector.match("python sqlalchemy"))
    .order_by("rank DESC")
)
```

## INSERT ... ON CONFLICT (Upsert)

```python
from sqlalchemy.dialects.postgresql import insert

# Insert with ON CONFLICT DO NOTHING
stmt = insert(User).values(
    username="john",
    email="john@example.com"
).on_conflict_do_nothing(
    index_elements=["username"]
)

# Insert with ON CONFLICT DO UPDATE
stmt = insert(User).values(
    username="john",
    email="john@example.com",
    login_count=1
).on_conflict_do_update(
    index_elements=["username"],
    set_={
        "email": "john@example.com",
        "login_count": User.login_count + 1,
        "updated_at": func.now()
    }
)

session.execute(stmt)
```

## PostgreSQL Indexes

```python
from sqlalchemy import Index, text

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    username: Mapped[str]
    data: Mapped[Dict] = mapped_column(JSONB)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))

    # B-tree index (default)
    __table_args__ = (
        Index("ix_users_email", "email"),

        # Unique partial index
        Index(
            "ix_users_active_username",
            "username",
            unique=True,
            postgresql_where=text("deleted_at IS NULL")
        ),

        # GIN index for JSONB
        Index("ix_users_data_gin", "data", postgresql_using="gin"),

        # GIN index for arrays
        Index("ix_users_tags_gin", "tags", postgresql_using="gin"),

        # GiST index for full-text search
        Index("ix_users_search", "search_vector", postgresql_using="gist"),

        # Composite index
        Index("ix_users_email_username", "email", "username"),

        # Expression index
        Index(
            "ix_users_lower_email",
            text("lower(email)"),
            postgresql_ops={"lower(email)": "text_pattern_ops"}
        ),
    )
```

## Async Connection Best Practices

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

# For web apps with connection pooling
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# For serverless/Lambda (disable pooling)
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    poolclass=NullPool,
    connect_args={
        "server_settings": {
            "application_name": "my_app",
            "jit": "off",  # Disable JIT for short connections
        },
        "command_timeout": 60,
        "timeout": 10,
    }
)
```

## Common PostgreSQL Extensions

```python
# Enable extensions in migration
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")  # Trigram similarity
    op.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")  # UUID functions
    op.execute("CREATE EXTENSION IF NOT EXISTS hstore")  # Key-value store
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")  # GIS data

# Use trigram similarity for fuzzy search
stmt = select(User).where(
    func.similarity(User.username, "jon") > 0.3
).order_by(
    func.similarity(User.username, "jon").desc()
)
```

## Performance Tips

1. **Use JSONB over JSON** for better indexing and query performance
2. **Add GIN indexes** on JSONB columns that are frequently queried
3. **Use partial indexes** to reduce index size for filtered queries
4. **Enable connection pooling** with appropriate pool size
5. **Use prepared statements** (SQLAlchemy does this automatically)
6. **Batch INSERT operations** using bulk_insert_mappings()
7. **Use EXPLAIN ANALYZE** to optimize queries (see performance.md)
