"""Pydantic schemas for request/response models"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# Item Schemas
class ItemBase(BaseModel):
    """Base schema with shared item fields"""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(gt=0)


class ItemCreate(ItemBase):
    """Schema for creating items"""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating items (all fields optional)"""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(None, gt=0)


class ItemResponse(ItemBase):
    """Schema for item responses"""

    id: int
    created_at: datetime


# User Schemas
class UserBase(BaseModel):
    """Base schema with shared user fields"""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating users"""

    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating users (all fields optional)"""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)


class UserResponse(UserBase):
    """Schema for user responses"""

    id: int
    is_active: bool
    created_at: datetime
