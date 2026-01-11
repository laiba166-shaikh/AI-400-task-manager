"""
SQLAlchemy 2.x Base Model Templates

Provides base classes for both sync and async ORM models following
SQLAlchemy 2.0 declarative patterns with type annotations.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ============================================================================
# BASE CLASSES
# ============================================================================

class Base(DeclarativeBase):
    """
    Synchronous base class for all ORM models.

    Usage:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
    """
    pass


class AsyncBase(AsyncAttrs, DeclarativeBase):
    """
    Async base class for all ORM models with async attribute loading.

    Usage:
        class User(AsyncBase):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
            posts: Mapped[List["Post"]] = relationship()

        # Async attribute access
        async with session.begin():
            user = await session.get(User, 1)
            posts = await user.awaitable_attrs.posts
    """
    pass


# ============================================================================
# TIMESTAMPED MIXIN
# ============================================================================

class TimestampMixin:
    """
    Adds created_at and updated_at timestamp fields.

    Usage:
        class User(TimestampMixin, Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
    """
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        onupdate=func.now(),
        nullable=True
    )


# ============================================================================
# SOFT DELETE MIXIN
# ============================================================================

class SoftDeleteMixin:
    """
    Adds soft delete capability via deleted_at timestamp.

    Usage:
        class User(SoftDeleteMixin, Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        # Soft delete
        user.deleted_at = datetime.utcnow()

        # Query only active records
        stmt = select(User).where(User.deleted_at.is_(None))
    """
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        default=None,
        nullable=True
    )


# ============================================================================
# EXAMPLE MODEL TEMPLATES
# ============================================================================

# Example 1: Basic sync model with timestamps
class UserExample(TimestampMixin, Base):
    """Example user model with timestamps"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    full_name: Mapped[Optional[str]]
    is_active: Mapped[bool] = mapped_column(default=True)


# Example 2: Async model with relationships
"""
from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class PostExample(AsyncBase):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Async relationship
    user: Mapped["UserExample"] = relationship(back_populates="posts")
    comments: Mapped[List["CommentExample"]] = relationship(back_populates="post")
"""
