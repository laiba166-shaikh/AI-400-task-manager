# Database Integration with FastAPI

## Overview

FastAPI works with any database library. This guide covers SQLAlchemy and SQLModel (recommended by FastAPI creator).

## SQLModel (Recommended)

SQLModel combines SQLAlchemy and Pydantic, providing type safety and validation.

### Installation

```bash
pip install sqlmodel
```

### Basic Setup

```python
from sqlmodel import SQLModel, create_engine, Session

# Database URL
DATABASE_URL = "postgresql://user:password@localhost/dbname"
# For SQLite: "sqlite:///./database.db"

# Create engine
connect_args = {"check_same_thread": False}  # Only for SQLite
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=True)

# Create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Startup event
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

### Model Patterns with Multiple Models

```python
from sqlmodel import SQLModel, Field
from datetime import datetime

# Base model with shared fields
class UserBase(SQLModel):
    username: str = Field(index=True, min_length=3, max_length=50)
    email: str = Field(index=True)
    full_name: str | None = None

# Database table model
class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request model for creation
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# Request model for updates (all optional)
class UserUpdate(SQLModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: str | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8)

# Response model (safe for API)
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
```

### Session Dependency Injection

```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

def get_session():
    """Provides database session per request"""
    with Session(engine) as session:
        yield session

# Type alias for convenience
SessionDep = Annotated[Session, Depends(get_session)]

# Usage in endpoints
@app.get("/users/")
def list_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return users
```

### CRUD Operations

#### Create

```python
from fastapi import HTTPException, status

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: SessionDep):
    # Check if user exists
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create user
    db_user = User.model_validate(
        user,
        update={"hashed_password": hash_password(user.password)}
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

#### Read One

```python
@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
```

#### Read Many (with pagination)

```python
from sqlmodel import select

@app.get("/users/", response_model=list[UserResponse])
def list_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
):
    users = session.exec(
        select(User).offset(skip).limit(limit)
    ).all()
    return users
```

#### Update

```python
@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, session: SessionDep):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update only provided fields
    user_data = user.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = hash_password(user_data.pop("password"))

    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

#### Delete

```python
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    session.delete(user)
    session.commit()
    return None
```

### Relationships

```python
from sqlmodel import Relationship

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str

    # Relationship
    heroes: list["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = None

    # Foreign key
    team_id: int | None = Field(default=None, foreign_key="team.id")

    # Relationship
    team: Team | None = Relationship(back_populates="heroes")

# Response models with relationships
class TeamResponse(SQLModel):
    id: int
    name: str
    headquarters: str

class HeroResponse(SQLModel):
    id: int
    name: str
    age: int | None
    team: TeamResponse | None

# Query with relationships
@app.get("/heroes/{hero_id}", response_model=HeroResponse)
def read_hero_with_team(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

## SQLAlchemy (Traditional Approach)

### Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    init_db()
```

### Models

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Pydantic Schemas (Separate from SQLAlchemy)

```python
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
```

### Session Dependency

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDep = Annotated[Session, Depends(get_db)]
```

### CRUD with SQLAlchemy

```python
from sqlalchemy.orm import Session

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: DBDep):
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: DBDep):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Async Database Support

### AsyncSession with SQLModel

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

async_engine = create_async_engine(DATABASE_URL, echo=True)

async def get_async_session() -> AsyncSession:
    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# Async CRUD
@app.get("/users/{user_id}")
async def read_user(user_id: int, session: AsyncSessionDep):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Database Configuration

### Environment-Based Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    database_echo: bool = False

    class Config:
        env_file = ".env"

settings = Settings()

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo
)
```

### Multiple Databases

```python
# Primary database
primary_engine = create_engine(PRIMARY_DB_URL)

# Analytics database (read-only)
analytics_engine = create_engine(ANALYTICS_DB_URL)

def get_primary_session():
    with Session(primary_engine) as session:
        yield session

def get_analytics_session():
    with Session(analytics_engine) as session:
        yield session

@app.get("/users/")
def list_users(session: Annotated[Session, Depends(get_primary_session)]):
    return session.exec(select(User)).all()

@app.get("/analytics/users")
def user_analytics(session: Annotated[Session, Depends(get_analytics_session)]):
    # Read from analytics database
    return session.exec(select(UserStats)).all()
```

## Migrations with Alembic

### Installation

```bash
pip install alembic
alembic init alembic
```

### Configuration (alembic/env.py)

```python
from app.database import Base
from app.models import User, Item  # Import all models

target_metadata = Base.metadata
```

### Create Migration

```bash
alembic revision --autogenerate -m "Create users table"
alembic upgrade head
```

### Programmatic Migrations

```python
from alembic import command
from alembic.config import Config

@app.on_event("startup")
def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

## Best Practices

### 1. Session Management

✅ **DO**: Use dependency injection for sessions
```python
@app.get("/users/")
def list_users(session: SessionDep):
    return session.exec(select(User)).all()
```

❌ **DON'T**: Create sessions manually in routes
```python
@app.get("/users/")
def list_users():
    session = Session(engine)  # Don't do this
    users = session.exec(select(User)).all()
    session.close()
    return users
```

### 2. Error Handling

```python
from sqlalchemy.exc import IntegrityError

@app.post("/users/")
def create_user(user: UserCreate, session: SessionDep):
    try:
        db_user = User(**user.model_dump())
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
```

### 3. Query Optimization

```python
from sqlmodel import select

# Avoid N+1 queries - use eager loading
@app.get("/heroes/")
def list_heroes_with_teams(session: SessionDep):
    statement = select(Hero).options(
        joinedload(Hero.team)  # Eager load relationships
    )
    heroes = session.exec(statement).unique().all()
    return heroes
```

### 4. Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True  # Verify connections before use
)
```

### 5. Testing with Database

```python
from sqlmodel import create_engine, Session

@pytest.fixture
def session():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

def test_create_user(session: Session):
    user = User(username="test", email="test@example.com")
    session.add(user)
    session.commit()
    assert user.id is not None
```

## Project Structure

```
app/
├── __init__.py
├── main.py
├── database.py          # Engine, session factory
├── models/
│   ├── __init__.py
│   ├── user.py          # User table model
│   └── item.py          # Item table model
├── schemas/
│   ├── __init__.py
│   ├── user.py          # UserCreate, UserResponse
│   └── item.py          # ItemCreate, ItemResponse
├── crud/
│   ├── __init__.py
│   ├── user.py          # User CRUD operations
│   └── item.py          # Item CRUD operations
└── routers/
    ├── __init__.py
    ├── users.py         # User endpoints
    └── items.py         # Item endpoints
```

### database.py

```python
from sqlmodel import create_engine, Session
from typing import Annotated
from fastapi import Depends

DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

### crud/user.py

```python
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)

def get_users(session: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return session.exec(select(User).offset(skip).limit(limit)).all()

def create_user(session: Session, user: UserCreate) -> User:
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def update_user(session: Session, user_id: int, user: UserUpdate) -> User | None:
    db_user = session.get(User, user_id)
    if not db_user:
        return None
    user_data = user.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True
```

## Summary

- **Use SQLModel** for new projects (combines SQLAlchemy + Pydantic)
- **Use dependency injection** for database sessions
- **Separate models**: Table models, request models, response models
- **Handle errors**: Catch integrity errors and return appropriate HTTP status
- **Use Alembic** for database migrations
- **Optimize queries**: Avoid N+1 problems with eager loading
- **Test with in-memory databases**: Fast and isolated tests
- **Structure CRUD operations**: Separate business logic from route handlers
