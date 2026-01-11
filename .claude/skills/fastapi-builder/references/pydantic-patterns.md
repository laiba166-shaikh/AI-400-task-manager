# Pydantic Model Patterns for FastAPI

## Overview

Pydantic models provide automatic validation, serialization, and documentation generation. Proper model organization is crucial for maintainable FastAPI applications.

## Separate Request and Response Models

### Why Separate Models?

1. **Security**: Prevent sensitive data exposure (passwords, internal IDs)
2. **Clarity**: Different data flows in vs out
3. **Flexibility**: Independent evolution of input/output schemas
4. **Type Safety**: Better editor support and validation

### Anti-Pattern: Shared Model

```python
# DON'T DO THIS
class User(BaseModel):
    username: str
    email: str
    password: str  # Will be exposed in responses!

@app.post("/users/")
async def create_user(user: User) -> User:
    # Exposes password in response
    return user
```

### Pattern 1: Separate Request/Response Models

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Request model for creating users"""
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    username: str
    email: EmailStr

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    # password is used but not returned
    db_user = create_user_in_db(user)
    return db_user
```

### Pattern 2: Model Inheritance (Recommended)

```python
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    """Shared fields across all user models"""
    username: str
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    """Additional fields required for creation"""
    password: str

class UserUpdate(BaseModel):
    """All fields optional for partial updates"""
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None

class UserResponse(UserBase):
    """Fields safe to expose in API"""
    id: int
    is_active: bool
    created_at: datetime

class UserDB(UserBase):
    """Internal database model with all fields"""
    id: int
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## Naming Conventions

### Request Models

- `{Resource}Create` - For POST requests creating new resources
- `{Resource}Update` - For PUT requests replacing resources
- `{Resource}Patch` - For PATCH requests partial updates
- `{Resource}Filter` - For query parameters

### Response Models

- `{Resource}Response` or `{Resource}Public` - Standard response
- `{Resource}Detail` - Detailed response with relationships
- `{Resource}List` - List responses (often wraps pagination)

### Example

```python
# Request models
class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None

class ItemFilter(BaseModel):
    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None

# Response models
class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    created_at: datetime

class ItemDetail(ItemResponse):
    category: CategoryResponse
    reviews: list[ReviewResponse]

class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    page: int
    page_size: int
```

## Type Hints Best Practices

### Use Descriptive Types

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from datetime import datetime
from decimal import Decimal

class Product(BaseModel):
    # Primitive types
    id: int
    name: str
    is_available: bool

    # Email validation
    contact_email: EmailStr

    # URL validation
    product_url: HttpUrl

    # Precise decimal for money
    price: Decimal = Field(decimal_places=2, gt=0)

    # Optional fields (None allowed)
    description: str | None = None

    # Lists
    tags: list[str] = []

    # Nested models
    category: "CategoryResponse"

    # Datetime
    created_at: datetime
```

### Field Constraints

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(
        ...,  # Required (no default)
        min_length=1,
        max_length=100,
        description="Item name",
        examples=["Widget"]
    )

    quantity: int = Field(
        default=1,
        ge=1,  # Greater than or equal
        le=1000,  # Less than or equal
        description="Number of items"
    )

    price: float = Field(
        gt=0,  # Greater than (exclusive)
        description="Price in USD"
    )

    discount_percentage: float = Field(
        default=0,
        ge=0,
        le=100,
        description="Discount as percentage"
    )
```

## Configuration and Behavior

### Model Config

```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model conversion
        str_strip_whitespace=True,  # Strip strings
        validate_assignment=True,  # Validate on attribute assignment
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com"
            }
        }
    )

    id: int
    username: str
    email: str
```

### ORM Mode (from_attributes)

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)

# Pydantic model
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str

# Usage
db_user = session.query(UserDB).first()
user_response = UserResponse.model_validate(db_user)  # Works!
```

## Response Model Parameters

### exclude_unset - Omit Fields Not Explicitly Set

```python
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None

@app.patch(
    "/items/{item_id}",
    response_model=ItemResponse,
    response_model_exclude_unset=True
)
async def update_item(item_id: int, item: ItemUpdate):
    # Only returns fields that were actually updated
    db_item = get_item(item_id)
    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    return db_item
```

### exclude_none - Omit None Values

```python
@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    response_model_exclude_none=True
)
async def read_item(item_id: int):
    # Fields with None values won't appear in response
    return get_item(item_id)
```

## Validators and Computed Fields

### Field Validators

```python
from pydantic import BaseModel, field_validator, model_validator

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    password_confirm: str

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self
```

### Computed Fields

```python
from pydantic import BaseModel, computed_field

class ItemResponse(BaseModel):
    name: str
    price: float
    tax_rate: float = 0.1

    @computed_field
    @property
    def price_with_tax(self) -> float:
        return self.price * (1 + self.tax_rate)
```

## Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class UserCreate(BaseModel):
    username: str
    email: str
    address: Address  # Nested model

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    address: Address  # Same nested model
```

## Generic Models for Pagination

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

# Usage
@app.get("/users/", response_model=PaginatedResponse[UserResponse])
async def list_users(page: int = 1, page_size: int = 10):
    users = get_users_paginated(page, page_size)
    total = count_users()
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        has_previous=page > 1
    )
```

## Organizing Models in Project Structure

### Small Projects (single file)

```python
# models.py
from pydantic import BaseModel

# All Pydantic schemas here
class UserBase(BaseModel): ...
class UserCreate(UserBase): ...
class UserResponse(UserBase): ...
```

### Medium Projects (by resource)

```
app/
├── schemas/
│   ├── __init__.py
│   ├── user.py      # User-related schemas
│   ├── item.py      # Item-related schemas
│   └── order.py     # Order-related schemas
```

### Large Projects (by operation)

```
app/
├── schemas/
│   ├── __init__.py
│   ├── users/
│   │   ├── __init__.py
│   │   ├── requests.py   # UserCreate, UserUpdate
│   │   ├── responses.py  # UserResponse, UserDetail
│   │   └── filters.py    # UserFilter
│   └── items/
│       ├── __init__.py
│       ├── requests.py
│       ├── responses.py
│       └── filters.py
```

## Best Practices Summary

1. **Always separate request and response models** for security and clarity
2. **Use inheritance** to reduce duplication across related models
3. **Follow naming conventions**: `{Resource}Create`, `{Resource}Response`, etc.
4. **Leverage Field()** for constraints and documentation
5. **Use specific types**: `EmailStr`, `HttpUrl`, `Decimal` instead of `str`, `float`
6. **Enable from_attributes** when working with ORMs
7. **Use validators** for complex business logic validation
8. **Keep models close to usage** in project structure
9. **Document with examples** in `json_schema_extra`
10. **Make update models fully optional** for PATCH operations

## Complete Example: CRUD Models

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

# Base model with shared fields
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = None

# Request models
class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8)

# Response models
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime

# Internal database model (not exposed in API)
class UserDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```
