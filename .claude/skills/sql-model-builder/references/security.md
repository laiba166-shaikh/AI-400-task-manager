# Security Best Practices

Security patterns and practices for SQLAlchemy 2.x applications.

## SQL Injection Prevention

SQLAlchemy's ORM provides automatic protection against SQL injection when used correctly.

### Safe Patterns (Protected)

```python
from sqlalchemy import select, text

# ✅ SAFE: ORM queries with bound parameters
stmt = select(User).where(User.username == username)

# ✅ SAFE: Text with bound parameters
stmt = text("SELECT * FROM users WHERE username = :username")
result = session.execute(stmt, {"username": username})

# ✅ SAFE: Filter by keyword arguments
users = session.query(User).filter_by(username=username).all()

# ✅ SAFE: Using bindparam
from sqlalchemy import bindparam
stmt = text("SELECT * FROM users WHERE id = :user_id").bindparams(
    bindparam("user_id", type_=Integer)
)
```

### Unsafe Patterns (Vulnerable)

```python
# ❌ DANGEROUS: String formatting
stmt = text(f"SELECT * FROM users WHERE username = '{username}'")

# ❌ DANGEROUS: String concatenation
query = "SELECT * FROM users WHERE id = " + user_id

# ❌ DANGEROUS: % operator
stmt = text("SELECT * FROM users WHERE id = %s" % user_id)

# ❌ DANGEROUS: format() method
stmt = text("SELECT * FROM users WHERE id = {}".format(user_id))
```

## Credential Management

### Environment Variables

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Load settings
settings = Settings()

# Build connection URL
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# Never log passwords
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Don't echo SQL with credentials
    hide_parameters=True,  # Hide bound parameters in logs
)
```

### Secret Management (Production)

```python
# AWS Secrets Manager
import boto3
import json

def get_db_credentials():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret_value = client.get_secret_value(SecretId="prod/database/credentials")
    return json.loads(secret_value["SecretString"])

# HashiCorp Vault
import hvac

def get_db_credentials():
    client = hvac.Client(url="https://vault.example.com")
    secret = client.secrets.kv.v2.read_secret_version(
        path="database/credentials"
    )
    return secret["data"]["data"]
```

## Row-Level Security with PostgreSQL RLS

```python
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    tenant_id: Mapped[int]  # Multi-tenancy

# Enable RLS in migration
def upgrade():
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")

    # Policy: Users can only see their own tenant's data
    op.execute("""
        CREATE POLICY tenant_isolation ON users
        USING (tenant_id = current_setting('app.current_tenant')::int)
    """)

# Set tenant context for session
async def set_tenant_context(session: AsyncSession, tenant_id: int):
    await session.execute(
        text("SET app.current_tenant = :tenant_id"),
        {"tenant_id": tenant_id}
    )

# Use in FastAPI dependency
async def get_tenant_db(
    tenant_id: int = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    await set_tenant_context(db, tenant_id)
    return db
```

## Data Exposure Prevention

### Pydantic Schema Separation

```python
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

# Database model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    password_hash: Mapped[str]  # Never expose!
    is_admin: Mapped[bool]
    created_at: Mapped[datetime]

# Public response schema (safe to expose)
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime

# Private/admin schema (restricted)
class UserPrivate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    is_admin: bool
    created_at: datetime
    # Note: password_hash is NEVER included

# Create schema (for input)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # Plain password (will be hashed)

# Usage in FastAPI
@app.get("/users/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    user = await db.get(User, user_id)
    return user  # Pydantic automatically filters fields
```

### Exclude Sensitive Fields

```python
from pydantic import BaseModel, Field

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    # Exclude sensitive fields
    password_hash: str = Field(exclude=True)
    ssn: Optional[str] = Field(default=None, exclude=True)
```

## Password Hashing

```python
from passlib.context import CryptContext

# Use bcrypt or argon2
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=4,
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Usage
async def create_user(db: AsyncSession, user_data: UserCreate):
    hashed_password = hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(user)
    await db.commit()
    return user
```

## Connection Security

### SSL/TLS Connections

```python
# PostgreSQL with SSL
DATABASE_URL = "postgresql+asyncpg://user:pass@host/db?ssl=require"

# MySQL with SSL
DATABASE_URL = "mysql+aiomysql://user:pass@host/db?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/cert.pem&ssl_key=/path/to/key.pem"

# PostgreSQL with custom SSL context
import ssl

ssl_context = ssl.create_default_context(
    cafile="/path/to/ca.pem"
)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_REQUIRED

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    connect_args={
        "ssl": ssl_context,
    }
)
```

## Audit Logging

```python
from sqlalchemy import event
from datetime import datetime
import logging

audit_logger = logging.getLogger("audit")

# Audit mixin
class AuditMixin:
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())

# Separate audit log table
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str]
    record_id: Mapped[int]
    action: Mapped[str]  # INSERT, UPDATE, DELETE
    user_id: Mapped[Optional[int]]
    changes: Mapped[Dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

# Event listeners for automatic auditing
@event.listens_for(Session, "before_flush")
def receive_before_flush(session, flush_context, instances):
    for obj in session.new:
        audit_logger.info(f"INSERT: {obj.__class__.__name__} {obj.id}")

    for obj in session.dirty:
        audit_logger.info(f"UPDATE: {obj.__class__.__name__} {obj.id}")

    for obj in session.deleted:
        audit_logger.info(f"DELETE: {obj.__class__.__name__} {obj.id}")
```

## Rate Limiting Database Access

```python
from fastapi import HTTPException, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/users/{user_id}")
@limiter.limit("100/minute")  # Rate limit
async def get_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

## Input Validation

```python
from pydantic import BaseModel, validator, Field, EmailStr

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v

    @validator("username")
    def username_not_reserved(cls, v):
        reserved = ["admin", "root", "system"]
        if v.lower() in reserved:
            raise ValueError("Username is reserved")
        return v
```

## Defense Against Mass Assignment

```python
from pydantic import BaseModel

# User model with admin flag
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)  # Sensitive!

# Create schema - EXCLUDES is_admin
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    # is_admin is NOT here - users can't set it on creation

# Update schema - EXCLUDES is_admin
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    # is_admin is NOT here - users can't modify it

# Admin-only update schema
class UserAdminUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None  # Only admins can update this

# Safe update - only updates allowed fields
async def update_user(
    db: AsyncSession,
    user_id: int,
    user_update: UserUpdate
):
    user = await db.get(User, user_id)
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    return user
```

## Security Checklist

- [ ] Use bound parameters, never string concatenation
- [ ] Store database credentials in environment variables or secret managers
- [ ] Hash passwords with bcrypt or argon2
- [ ] Use SSL/TLS for database connections
- [ ] Separate public and private Pydantic schemas
- [ ] Never expose password hashes or sensitive data
- [ ] Implement rate limiting on endpoints
- [ ] Validate and sanitize all user input
- [ ] Use row-level security for multi-tenancy
- [ ] Implement audit logging for sensitive operations
- [ ] Prevent mass assignment vulnerabilities
- [ ] Set `echo=False` and `hide_parameters=True` in production
- [ ] Use principle of least privilege for database users
- [ ] Regularly update dependencies for security patches
