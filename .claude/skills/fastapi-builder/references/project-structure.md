# FastAPI Project Structure Patterns

## Overview

FastAPI project structure should scale with your application's complexity. Start simple and refactor as needed.

## Level 1: Hello World (Single File)

**Use for**: Learning, prototypes, very simple APIs (<5 endpoints)

```
project/
├── main.py
└── requirements.txt
```

**main.py**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

## Level 2: Simple CRUD (Single File with Models)

**Use for**: Simple APIs with database (5-15 endpoints)

```
project/
├── main.py
├── database.db
└── requirements.txt
```

**main.py**:
```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Annotated

# Models
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    price: float

class ItemCreate(SQLModel):
    name: str
    description: str | None = None
    price: float

# Database
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# App
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Routes
@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, session: SessionDep):
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@app.get("/items/")
def list_items(session: SessionDep):
    return session.exec(select(Item)).all()

@app.get("/items/{item_id}")
def read_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

## Level 3: Modular Structure (Multiple Modules)

**Use for**: Medium APIs (15-50 endpoints), multiple resources

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
│       ├── __init__.py
│       ├── items.py
│       └── users.py
├── requirements.txt
└── .env
```

### app/database.py

```python
from sqlmodel import create_engine, Session
from typing import Annotated
from fastapi import Depends

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

### app/models.py

```python
from sqlmodel import SQLModel, Field
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(index=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    price: float
    owner_id: int = Field(foreign_key="users.id")
```

### app/schemas.py

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    owner_id: int
```

### app/routers/items.py

```python
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.database import SessionDep
from app.models import Item
from app.schemas import ItemCreate, ItemResponse

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, session: SessionDep):
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@router.get("/", response_model=list[ItemResponse])
def list_items(session: SessionDep):
    return session.exec(select(Item)).all()

@router.get("/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### app/main.py

```python
from fastapi import FastAPI
from app.database import engine
from app.models import SQLModel
from app.routers import items, users

app = FastAPI(title="My API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(items.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Welcome to My API"}
```

## Level 4: Production-Ready Structure

**Use for**: Large APIs (50+ endpoints), microservices, production deployments

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── item.py
│   │   └── base.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── item.py
│   │   └── common.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── items.py
│   └── services/
│       ├── __init__.py
│       ├── auth.py
│       └── email.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_users.py
│   └── test_items.py
├── alembic/
│   ├── versions/
│   └── env.py
├── scripts/
│   └── init_db.py
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── pyproject.toml
└── README.md
```

### app/config.py

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_name: str = "My API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### app/core/database.py

```python
from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated
from fastapi import Depends
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

### app/core/security.py

```python
from datetime import datetime, timedelta
from typing import Any
from jose import jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str | Any) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### app/core/exceptions.py

```python
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None

class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id

class InsufficientPermissionsError(Exception):
    pass

async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error_code="ITEM_NOT_FOUND",
            message=f"Item {exc.item_id} not found"
        ).model_dump()
    )
```

### app/dependencies.py

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.database import SessionDep
from app.core.security import get_settings
from app.models.user import User
from sqlmodel import select

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_current_active_user(current_user: CurrentUser) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: CurrentUser) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user
```

### app/crud/user.py

```python
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)

def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_users(
    session: Session,
    skip: int = 0,
    limit: int = 100
) -> list[User]:
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()

def create_user(session: Session, user: UserCreate) -> User:
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def update_user(
    session: Session,
    user_id: int,
    user: UserUpdate
) -> User | None:
    db_user = session.get(User, user_id)
    if not db_user:
        return None

    user_data = user.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(
            user_data.pop("password")
        )

    for key, value in user_data.items():
        setattr(db_user, key, value)

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

### app/routers/users.py

```python
from fastapi import APIRouter, HTTPException, status
from app.core.database import SessionDep
from app.dependencies import CurrentUser, get_current_admin_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.crud import user as crud_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(user: UserCreate, session: SessionDep):
    db_user = crud_user.get_user_by_email(session, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    return crud_user.create_user(session, user)

@router.get("/", response_model=list[UserResponse])
def list_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
):
    return crud_user.get_users(session, skip=skip, limit=limit)

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser):
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, session: SessionDep):
    user = crud_user.get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    db_user = crud_user.update_user(session, user_id, user)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    session: SessionDep,
    admin_user = Depends(get_current_admin_user)
):
    if not crud_user.delete_user(session, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None
```

### app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.core.database import create_db_and_tables
from app.core.exceptions import (
    ItemNotFoundError,
    item_not_found_handler
)
from app.routers import users, items, auth

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(ItemNotFoundError, item_not_found_handler)

# Startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.app_name}"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## Best Practices

1. **Start simple**: Begin with single-file structure, refactor as needed
2. **Separate concerns**: Models, schemas, CRUD, routes, business logic
3. **Use dependency injection**: For database sessions, authentication, configuration
4. **Environment configuration**: Use .env files and pydantic-settings
5. **Organize by feature**: Group related files (user models, user schemas, user routes)
6. **Keep routers thin**: Move business logic to CRUD/services layer
7. **Type annotations**: Use everywhere for editor support and validation
8. **Testing structure**: Mirror app structure in tests directory
9. **Documentation**: Include docstrings and OpenAPI metadata
10. **Version control**: Use .gitignore for sensitive files and generated artifacts

## Summary

| Project Size | Endpoints | Structure | Files |
|--------------|-----------|-----------|-------|
| **Tiny** | <5 | Single file | 1-2 files |
| **Small** | 5-15 | Single file with models | 1-3 files |
| **Medium** | 15-50 | Modular with routers | 5-10 files |
| **Large** | 50+ | Production with layers | 20+ files |
