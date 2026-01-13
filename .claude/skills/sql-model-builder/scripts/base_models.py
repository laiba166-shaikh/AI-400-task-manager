"""SQLModel base classes and common patterns.

Copy and adapt these patterns for your models.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


# ============================================================================
# Base Model Pattern
# ============================================================================

class TaskBase(SQLModel):
    """
    Base model with shared fields.

    Use this pattern to define fields that are common across
    all variants (Create, Read, Update, Table).
    """
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Task title",
        index=True,  # Creates database index
    )
    description: Optional[str] = Field(
        default=None,
        description="Task description"
    )
    completed: bool = Field(
        default=False,
        description="Completion status"
    )


class Task(TaskBase, table=True):
    """
    Database table model.

    table=True indicates this is a database table.
    Inherits all fields from TaskBase.
    """
    __tablename__ = "tasks"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Primary key"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )


class TaskCreate(TaskBase):
    """
    Schema for creating tasks (POST /tasks/).

    Inherits: title, description, completed from TaskBase
    Excludes: id, created_at, updated_at (auto-generated)
    """
    pass


class TaskRead(TaskBase):
    """
    Schema for reading tasks (GET responses).

    Includes all fields including database-generated ones.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime]


class TaskUpdate(SQLModel):
    """
    Schema for updating tasks (PATCH /tasks/{id}).

    All fields optional for partial updates.
    Only fields provided in request will be updated.
    """
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200
    )
    description: Optional[str] = None
    completed: Optional[bool] = None


# ============================================================================
# Timestamp Mixin Pattern (Alternative)
# ============================================================================

class TimestampModel(SQLModel):
    """
    Mixin for models that need timestamps.

    Use this as a base class for models that track creation/update times.
    """
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        nullable=True
    )


class UserBase(SQLModel):
    """Example using TimestampModel"""
    email: str = Field(unique=True, index=True)
    name: str


class User(UserBase, TimestampModel, table=True):
    """
    User table with automatic timestamps.

    Inherits from both UserBase (business fields)
    and TimestampModel (timestamp fields).
    """
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)


# ============================================================================
# Soft Delete Pattern
# ============================================================================

class SoftDeleteModel(SQLModel):
    """
    Mixin for soft-delete functionality.

    Instead of deleting records, mark them as deleted with a timestamp.
    """
    deleted_at: Optional[datetime] = Field(default=None)

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted"""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft-deleted record"""
        self.deleted_at = None


class ProductBase(SQLModel):
    name: str
    price: float = Field(ge=0)


class Product(ProductBase, SoftDeleteModel, table=True):
    """
    Product table with soft-delete support.
    """
    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)


# ============================================================================
# Validation Examples
# ============================================================================

class ValidatedModel(SQLModel, table=True):
    """Examples of various field validations"""
    __tablename__ = "validated"

    id: Optional[int] = Field(default=None, primary_key=True)

    # String validations
    email: str = Field(regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    username: str = Field(min_length=3, max_length=50)

    # Numeric validations
    age: int = Field(ge=0, le=120)  # 0 <= age <= 120
    price: float = Field(gt=0)  # price > 0
    discount: float = Field(ge=0, le=100)  # 0 <= discount <= 100

    # Optional with validation
    phone: Optional[str] = Field(
        default=None,
        regex=r'^\+?1?\d{9,15}$'
    )


# ============================================================================
# Index Examples
# ============================================================================

class IndexedModel(SQLModel, table=True):
    """Examples of various index types"""
    __tablename__ = "indexed"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Simple index
    email: str = Field(unique=True, index=True)

    # Non-unique index
    category: str = Field(index=True)

    # Multiple columns can be indexed
    # (for composite indexes, use sa_column_kwargs or Index in __table_args__)
    status: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# ============================================================================
# Usage Notes
# ============================================================================

"""
1. Base Model Pattern:
   - Define TaskBase with shared fields
   - Task (table=True) is the database table
   - TaskCreate for POST requests (no id/timestamps)
   - TaskRead for GET responses (includes all fields)
   - TaskUpdate for PATCH requests (all optional)

2. Timestamp Pattern:
   - Create TimestampModel mixin
   - Inherit from it in your table models
   - Automatically adds created_at/updated_at

3. Soft Delete Pattern:
   - Create SoftDeleteModel mixin
   - Provides deleted_at field and helper methods
   - Query with .where(Model.deleted_at.is_(None))

4. Validation:
   - Use Field() with validators (min_length, max_length, ge, le, gt, lt)
   - Use regex for pattern matching
   - Pydantic validates on model creation

5. Indexes:
   - index=True for single-column indexes
   - unique=True for unique constraints
   - For composite indexes, use __table_args__
"""