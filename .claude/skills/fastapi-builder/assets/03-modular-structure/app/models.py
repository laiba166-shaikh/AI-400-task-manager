"""SQLModel database models"""

from sqlmodel import SQLModel, Field
from datetime import datetime


class Item(SQLModel, table=True):
    """Item database model"""

    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    """User database model"""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
