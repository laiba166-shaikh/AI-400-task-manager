"""
SQLAlchemy 2.x CRUD Repository Pattern

Provides generic repository classes for common database operations
following the Repository pattern for both sync and async contexts.
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession


# Type variable for model classes
ModelType = TypeVar("ModelType")


# ============================================================================
# SYNCHRONOUS REPOSITORY
# ============================================================================

class SyncRepository(Generic[ModelType]):
    """
    Generic synchronous repository for CRUD operations.

    Usage:
        user_repo = SyncRepository(User, session)

        # Create
        user = user_repo.create({"name": "John", "email": "john@example.com"})

        # Read
        user = user_repo.get(1)
        users = user_repo.get_all(limit=10, offset=0)

        # Update
        updated = user_repo.update(1, {"name": "Jane"})

        # Delete
        user_repo.delete(1)

        # Filter
        active_users = user_repo.filter(is_active=True)

        # Count
        total = user_repo.count()
    """

    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        instance = self.model(**data)
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def create_many(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records"""
        instances = [self.model(**data) for data in data_list]
        self.session.add_all(instances)
        self.session.flush()
        for instance in instances:
            self.session.refresh(instance)
        return instances

    def get(self, id: Any) -> Optional[ModelType]:
        """Get record by primary key"""
        return self.session.get(self.model, id)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get all records with pagination"""
        stmt = select(self.model).offset(skip).limit(limit)

        if order_by:
            stmt = stmt.order_by(order_by)

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def filter(self, **filters) -> List[ModelType]:
        """Filter records by field values"""
        stmt = select(self.model).filter_by(**filters)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def filter_one(self, **filters) -> Optional[ModelType]:
        """Get single record matching filters"""
        stmt = select(self.model).filter_by(**filters)
        result = self.session.execute(stmt)
        return result.scalars().first()

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """Update record by primary key"""
        instance = self.get(id)
        if not instance:
            return None

        for key, value in data.items():
            setattr(instance, key, value)

        self.session.flush()
        self.session.refresh(instance)
        return instance

    def update_many(self, filters: Dict[str, Any], data: Dict[str, Any]) -> int:
        """Update multiple records matching filters"""
        stmt = update(self.model).where(
            *[getattr(self.model, k) == v for k, v in filters.items()]
        ).values(**data)

        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount

    def delete(self, id: Any) -> bool:
        """Delete record by primary key"""
        instance = self.get(id)
        if not instance:
            return False

        self.session.delete(instance)
        self.session.flush()
        return True

    def delete_many(self, **filters) -> int:
        """Delete multiple records matching filters"""
        stmt = delete(self.model).filter_by(**filters)
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount

    def count(self, **filters) -> int:
        """Count records, optionally filtered"""
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)

        result = self.session.execute(stmt)
        return result.scalar_one()

    def exists(self, id: Any) -> bool:
        """Check if record exists by primary key"""
        return self.get(id) is not None


# ============================================================================
# ASYNCHRONOUS REPOSITORY
# ============================================================================

class AsyncRepository(Generic[ModelType]):
    """
    Generic asynchronous repository for CRUD operations.

    Usage:
        user_repo = AsyncRepository(User, session)

        # Create
        user = await user_repo.create({"name": "John", "email": "john@example.com"})

        # Read
        user = await user_repo.get(1)
        users = await user_repo.get_all(limit=10, offset=0)

        # Update
        updated = await user_repo.update(1, {"name": "Jane"})

        # Delete
        await user_repo.delete(1)

        # Filter
        active_users = await user_repo.filter(is_active=True)

        # Count
        total = await user_repo.count()
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def create_many(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records"""
        instances = [self.model(**data) for data in data_list]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def get(self, id: Any) -> Optional[ModelType]:
        """Get record by primary key"""
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get all records with pagination"""
        stmt = select(self.model).offset(skip).limit(limit)

        if order_by:
            stmt = stmt.order_by(order_by)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def filter(self, **filters) -> List[ModelType]:
        """Filter records by field values"""
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def filter_one(self, **filters) -> Optional[ModelType]:
        """Get single record matching filters"""
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """Update record by primary key"""
        instance = await self.get(id)
        if not instance:
            return None

        for key, value in data.items():
            setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update_many(self, filters: Dict[str, Any], data: Dict[str, Any]) -> int:
        """Update multiple records matching filters"""
        stmt = update(self.model).where(
            *[getattr(self.model, k) == v for k, v in filters.items()]
        ).values(**data)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def delete(self, id: Any) -> bool:
        """Delete record by primary key"""
        instance = await self.get(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def delete_many(self, **filters) -> int:
        """Delete multiple records matching filters"""
        stmt = delete(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def count(self, **filters) -> int:
        """Count records, optionally filtered"""
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, id: Any) -> bool:
        """Check if record exists by primary key"""
        return await self.get(id) is not None


# ============================================================================
# FASTAPI SERVICE LAYER EXAMPLE
# ============================================================================

"""
# services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from crud_repository import AsyncRepository

class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = AsyncRepository(User, session)

    async def create_user(self, name: str, email: str) -> User:
        return await self.repo.create({"name": name, "email": email})

    async def get_user(self, user_id: int) -> User | None:
        return await self.repo.get(user_id)

    async def get_active_users(self) -> List[User]:
        return await self.repo.filter(is_active=True)

    async def deactivate_user(self, user_id: int) -> User | None:
        return await self.repo.update(user_id, {"is_active": False})


# routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from session_factory import get_async_db
from services.user_service import UserService

router = APIRouter(prefix="/users")

@router.post("/")
async def create_user(
    name: str,
    email: str,
    db: AsyncSession = Depends(get_async_db)
):
    service = UserService(db)
    return await service.create_user(name, email)

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
"""
