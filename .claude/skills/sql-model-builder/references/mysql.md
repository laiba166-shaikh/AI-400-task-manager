# MySQL-Specific Patterns

SQLAlchemy 2.x patterns and features specific to MySQL/MariaDB databases.

## Connection URLs

```python
# Sync driver (mysqlclient - recommended)
SQLALCHEMY_DATABASE_URL = "mysql://user:password@localhost:3306/dbname"
SQLALCHEMY_DATABASE_URL = "mysql+mysqldb://user:password@localhost:3306/dbname"

# PyMySQL (pure Python)
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/dbname"

# Async driver (aiomysql)
SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://user:password@localhost:3306/dbname"

# With connection parameters
SQLALCHEMY_DATABASE_URL = "mysql://user:password@localhost:3306/dbname?charset=utf8mb4&ssl_ca=/path/to/ca.pem"
```

## MySQL-Specific Column Types

```python
from sqlalchemy import String, Text, Integer
from sqlalchemy.dialects.mysql import (
    TINYINT, SMALLINT, MEDIUMINT, BIGINT,
    FLOAT, DOUBLE, DECIMAL,
    VARCHAR, CHAR, TINYTEXT, TEXT, MEDIUMTEXT, LONGTEXT,
    TINYBLOB, BLOB, MEDIUMBLOB, LONGBLOB,
    DATETIME, TIMESTAMP, TIME, YEAR,
    JSON, SET, ENUM
)
from sqlalchemy.orm import Mapped, mapped_column
from typing import List, Dict, Any
from datetime import datetime

class Product(Base):
    __tablename__ = "products"

    # Integer types with specific sizes
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    quantity: Mapped[int] = mapped_column(SMALLINT)
    views: Mapped[int] = mapped_column(MEDIUMINT, default=0)
    is_active: Mapped[int] = mapped_column(TINYINT(1), default=1)  # Boolean as TINYINT

    # String types with specific sizes
    sku: Mapped[str] = mapped_column(VARCHAR(50), unique=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    description: Mapped[str] = mapped_column(TEXT)
    details: Mapped[str] = mapped_column(MEDIUMTEXT)

    # JSON type (MySQL 5.7+)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON)

    # ENUM type
    status: Mapped[str] = mapped_column(
        ENUM("draft", "published", "archived"),
        default="draft"
    )

    # SET type (multi-select)
    tags: Mapped[str] = mapped_column(
        SET("featured", "sale", "new", "trending")
    )

    # Timestamp with auto-update
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
```

## Character Set and Collation

```python
from sqlalchemy import Table, Column, Integer, String, MetaData

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(100, collation="utf8mb4_unicode_ci")
    )
    email: Mapped[str] = mapped_column(
        String(255, collation="utf8mb4_unicode_ci")
    )

    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }
```

## MySQL JSON Operations

```python
from sqlalchemy import select, func, cast, String
from sqlalchemy.dialects.mysql import JSON

# Extract JSON field
stmt = select(Product).where(
    cast(Product.metadata["status"], String) == "active"
)

# JSON_EXTRACT function
stmt = select(Product).where(
    func.json_extract(Product.metadata, "$.price") > 100
)

# JSON_CONTAINS (MySQL 5.7+)
stmt = select(Product).where(
    func.json_contains(
        Product.metadata,
        cast('{"featured": true}', JSON)
    )
)

# JSON_SEARCH
stmt = select(Product).where(
    func.json_search(Product.metadata, "one", "electronics", None, "$.category").isnot(None)
)
```

## INSERT ... ON DUPLICATE KEY UPDATE

```python
from sqlalchemy.dialects.mysql import insert

# Upsert using ON DUPLICATE KEY UPDATE
stmt = insert(User).values(
    username="john",
    email="john@example.com",
    login_count=1
)

# Update on duplicate key
stmt = stmt.on_duplicate_key_update(
    email=stmt.inserted.email,
    login_count=User.login_count + 1,
    updated_at=func.now()
)

session.execute(stmt)

# Multiple rows upsert
data = [
    {"username": "john", "email": "john@example.com", "login_count": 1},
    {"username": "jane", "email": "jane@example.com", "login_count": 1},
]

stmt = insert(User).values(data)
stmt = stmt.on_duplicate_key_update(
    email=stmt.inserted.email,
    login_count=User.login_count + 1
)

session.execute(stmt)
```

## MySQL Indexes

```python
from sqlalchemy import Index, text

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    email: Mapped[str] = mapped_column(VARCHAR(255))
    username: Mapped[str] = mapped_column(VARCHAR(100))
    full_name: Mapped[str] = mapped_column(VARCHAR(255))
    bio: Mapped[str] = mapped_column(TEXT)

    __table_args__ = (
        # Standard B-tree index
        Index("ix_users_email", "email"),

        # Unique index
        Index("ix_users_username", "username", unique=True),

        # Composite index
        Index("ix_users_email_username", "email", "username"),

        # Prefix index (for TEXT/BLOB columns)
        Index("ix_users_full_name", text("full_name(50)")),

        # FULLTEXT index (for full-text search)
        Index("ix_users_bio_fulltext", "bio", mysql_prefix="FULLTEXT"),

        # Index with specific length
        Index("ix_users_email_prefix", text("email(20)")),

        # Table options
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
            "mysql_row_format": "DYNAMIC",
        }
    )
```

## Full-Text Search (MySQL)

```python
from sqlalchemy import func, text

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(VARCHAR(255))
    content: Mapped[str] = mapped_column(TEXT)

    __table_args__ = (
        # FULLTEXT index on multiple columns
        Index("ix_articles_search", "title", "content", mysql_prefix="FULLTEXT"),
    )

# Boolean mode search (supports +, -, *)
stmt = select(Article).where(
    text("MATCH(title, content) AGAINST(:search IN BOOLEAN MODE)")
).params(search="+python +sqlalchemy")

# Natural language search
stmt = select(Article).where(
    text("MATCH(title, content) AGAINST(:search)")
).params(search="python sqlalchemy")

# Search with relevance score
stmt = select(
    Article,
    text("MATCH(title, content) AGAINST(:search) AS score")
).where(
    text("MATCH(title, content) AGAINST(:search)")
).params(
    search="python sqlalchemy"
).order_by(text("score DESC"))
```

## Auto-Increment Configuration

```python
from sqlalchemy import event

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    username: Mapped[str]

    __table_args__ = {
        "mysql_auto_increment": 1000,  # Start auto-increment from 1000
    }

# Reset auto-increment after table creation
@event.listens_for(User.__table__, "after_create")
def set_auto_increment(target, connection, **kw):
    connection.execute(text("ALTER TABLE users AUTO_INCREMENT = 1000"))
```

## Async Connection Best Practices

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# For web apps with connection pooling
engine = create_async_engine(
    "mysql+aiomysql://user:pass@localhost/db?charset=utf8mb4",
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
    }
)

# For serverless (disable pooling)
engine = create_async_engine(
    "mysql+aiomysql://user:pass@localhost/db",
    poolclass=NullPool,
    connect_args={
        "charset": "utf8mb4",
        "connect_timeout": 10,
    }
)
```

## Storage Engines

```python
# InnoDB (default, supports transactions, foreign keys)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]

    __table_args__ = {"mysql_engine": "InnoDB"}

# MyISAM (faster reads, no foreign keys, full-text before MySQL 5.6)
class Log(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str]

    __table_args__ = {"mysql_engine": "MyISAM"}
```

## Performance Tips

1. **Always use utf8mb4** charset for full Unicode support
2. **Use InnoDB engine** for ACID compliance and foreign keys
3. **Add indexes on foreign keys** (MySQL doesn't auto-create them)
4. **Use prefix indexes** for long VARCHAR/TEXT columns
5. **Enable connection pooling** with pool_pre_ping=True
6. **Use BIGINT for auto-increment PKs** to avoid overflow
7. **Optimize FULLTEXT indexes** with ft_min_word_len and ft_max_word_len
8. **Use TIMESTAMP over DATETIME** for automatic timezone conversion
9. **Batch INSERT operations** for better performance
10. **Monitor slow query log** to identify optimization opportunities
