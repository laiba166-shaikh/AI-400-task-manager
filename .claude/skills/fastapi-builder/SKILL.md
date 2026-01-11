---
name: fastapi-builder
description: Build FastAPI projects from hello world to production-ready. Helps with project scaffolding, API structure, best practices, dependency management, testing, deployment configuration, security, and performance optimization. Use when creating FastAPI projects, setting up API endpoints, structuring applications, or asking for production-ready configurations.
---

# FastAPI Builder

Build professional FastAPI applications following official documentation and best practices.

## When to Use This Skill

- Creating new FastAPI projects (any size)
- Adding CRUD endpoints to existing APIs
- Implementing authentication (OAuth2, JWT, API keys)
- Structuring FastAPI applications for scalability
- Setting up database integration (SQLModel, SQLAlchemy)
- Implementing proper error handling and validation
- Designing request/response models with Pydantic
- Configuring production deployments

## Quick Start by Project Size

### Hello World (Single File)

Use template: `assets/01-hello-world/`

```bash
# Copy template
cp -r assets/01-hello-world/* ./

# Install dependencies
pip install -r requirements.txt

# Run
fastapi dev main.py
```

### Simple CRUD (Single File with Database)

Use template: `assets/02-crud-single-file/`

Complete CRUD API in one file with SQLModel. Good for prototypes and simple services (5-15 endpoints).

### Modular Structure (Multiple Files)

Use template: `assets/03-modular-structure/`

Organized into modules with APIRouter. Good for medium APIs (15-50 endpoints).

Structure:
- `app/main.py` - Application entry point
- `app/database.py` - Database configuration
- `app/models.py` - Database models
- `app/schemas.py` - Request/response models
- `app/routers/` - Endpoint definitions by resource

### Production-Ready (Full Structure)

Use template: `assets/04-production-ready/`

Complete production architecture with:
- Environment-based configuration
- Layered architecture (routers, CRUD, models, schemas)
- Authentication and authorization
- Custom exception handling
- Database migrations
- Testing setup

See `assets/04-production-ready/README.md` for details.

## Core Concepts

### 1. Separate Request and Response Models

**Always use separate Pydantic models** for requests and responses:

```python
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # Only in requests

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr  # Never include password in responses
```

**See**: `references/pydantic-patterns.md` for complete patterns

### 2. Proper HTTP Status Codes

Use appropriate status codes for each operation:

```python
@app.post("/items/", status_code=status.HTTP_201_CREATED)  # Create
@app.get("/items/{id}")  # Read (200 OK default)
@app.patch("/items/{id}")  # Update (200 OK)
@app.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)  # Delete
```

**See**: `references/status-codes.md` for complete reference

### 3. Error Handling: 400 vs 422

- **422 (Unprocessable Entity)**: Pydantic validation failures (automatic)
- **400 (Bad Request)**: Business logic validation failures (manual)

```python
# FastAPI automatically returns 422 for type errors
class ItemCreate(BaseModel):
    price: float = Field(gt=0)  # 422 if price <= 0

# Use 400 for business logic
@app.post("/items/")
def create_item(item: ItemCreate):
    if item.price > max_allowed_price:  # Business rule
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price exceeds maximum allowed"
        )
```

**See**: `references/error-handling.md` for comprehensive patterns

### 4. Structured Error Responses

Return consistent error structures:

```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={
        "error_code": "INVALID_PRICE",
        "message": "Price exceeds maximum",
        "max_price": 1000
    }
)
```

### 5. Database Session Management

Use dependency injection for database sessions:

```python
from typing import Annotated
from fastapi import Depends

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.get("/items/")
def list_items(session: SessionDep):
    return session.exec(select(Item)).all()
```

**See**: `references/database-integration.md` for SQLModel and SQLAlchemy patterns

### 6. Type Hints Everywhere

Use proper type hints for validation and documentation:

```python
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from decimal import Decimal

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(decimal_places=2, gt=0)
    url: HttpUrl
    email: EmailStr
    tags: list[str] = []
```

## Reference Documentation

Load these references as needed for detailed guidance:

- **`references/error-handling.md`** - 400 vs 422, HTTPException, custom handlers, structured responses
- **`references/pydantic-patterns.md`** - Request/response models, validation, field constraints, model organization
- **`references/status-codes.md`** - Complete HTTP status code reference and usage guide
- **`references/database-integration.md`** - SQLModel, SQLAlchemy, sessions, CRUD operations, relationships
- **`references/authentication.md`** - OAuth2, JWT, API keys, RBAC, permissions
- **`references/project-structure.md`** - Architecture patterns from single-file to production-ready

## Common Workflows

### Creating a New CRUD Resource

1. **Define database model** (`app/models/product.py`):
   ```python
   class Product(SQLModel, table=True):
       id: int | None = Field(default=None, primary_key=True)
       name: str
       price: float
   ```

2. **Create schemas** (`app/schemas/product.py`):
   ```python
   class ProductCreate(BaseModel):
       name: str
       price: float

   class ProductResponse(BaseModel):
       id: int
       name: str
       price: float
   ```

3. **Generate CRUD endpoints**:
   ```bash
   python scripts/generate_crud_endpoints.py Product > app/routers/product.py
   ```

4. **Include router** in `app/main.py`:
   ```python
   from app.routers import product
   app.include_router(product.router)
   ```

### Adding Authentication

See `references/authentication.md` for:
- OAuth2 with JWT tokens
- API key authentication
- Role-based access control (RBAC)
- Permission-based access control

### Implementing Validation

**Field-level validation**:
```python
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    age: int = Field(ge=0, le=150)
```

**Custom validators**:
```python
from pydantic import field_validator

class UserCreate(BaseModel):
    password: str
    password_confirm: str

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

## Best Practices Checklist

**Models and Schemas**:
- [ ] Separate request and response models
- [ ] Use descriptive model names (`UserCreate`, `UserResponse`)
- [ ] Add Field() constraints for validation
- [ ] Use specific types (EmailStr, HttpUrl, Decimal)
- [ ] Enable `from_attributes=True` for ORM models

**Error Handling**:
- [ ] Use `status` module constants (not magic numbers)
- [ ] Return structured error responses with error codes
- [ ] Handle database integrity errors appropriately
- [ ] Document errors in `responses` parameter
- [ ] Use 404 to hide resource existence when needed

**Database**:
- [ ] Use dependency injection for sessions
- [ ] Separate table models from request/response schemas
- [ ] Create indexes on frequently queried fields
- [ ] Use transactions for multi-step operations
- [ ] Handle session cleanup properly

**API Design**:
- [ ] Follow REST conventions for CRUD operations
- [ ] Use appropriate HTTP methods (GET, POST, PATCH, DELETE)
- [ ] Return correct status codes (201 for creation, 204 for deletion)
- [ ] Implement pagination for list endpoints
- [ ] Add filtering and sorting where appropriate

**Security**:
- [ ] Never return passwords or sensitive data
- [ ] Hash passwords with bcrypt
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Validate and sanitize all inputs

**Code Organization**:
- [ ] Start simple, refactor as needed
- [ ] Keep routers thin (move logic to CRUD layer)
- [ ] Group related files by resource
- [ ] Use dependency injection for shared logic
- [ ] Add docstrings for API documentation

## Scripts

### generate_crud_endpoints.py

Generate complete CRUD router code:

```bash
python scripts/generate_crud_endpoints.py Product
```

Outputs router code with all CRUD operations following best practices.

## Testing

Example test structure:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Test", "price": 10.99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test"
    assert "id" in data
```

## Deployment Considerations

- Use environment variables for configuration
- Set up database connection pooling
- Configure CORS for frontend integration
- Implement health check endpoints
- Use uvicorn workers for production
- Set up logging and monitoring
- Use Alembic for database migrations

## Common Patterns

### Pagination Response

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

@app.get("/items/", response_model=PaginatedResponse[ItemResponse])
def list_items(page: int = 1, page_size: int = 10):
    ...
```

### Soft Delete

```python
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_deleted: bool = False

@app.delete("/items/{id}")
def delete_item(id: int, session: SessionDep):
    item = session.get(Item, id)
    item.is_deleted = True
    session.commit()
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Send email logic
    pass

@app.post("/send-notification/")
def create_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Hello!")
    return {"message": "Notification sent"}
```

## Migration Path

1. **Start**: Use `assets/01-hello-world/` for learning
2. **Add Database**: Migrate to `assets/02-crud-single-file/`
3. **Scale Up**: Refactor to `assets/03-modular-structure/`
4. **Production**: Adopt `assets/04-production-ready/` structure

## Additional Resources

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Summary

This skill provides everything needed to build FastAPI applications from simple prototypes to production-ready APIs. Always:
- Use proper type hints
- Separate request/response models
- Return appropriate status codes
- Structure errors consistently
- Follow REST conventions
- Test thoroughly
