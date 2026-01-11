"""CRUD operations for Task model using SQLModel."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func as sql_func
from app.models import Task


class TaskRepository:
    """
    Repository for Task CRUD operations.

    Encapsulates all database operations for the Task model,
    providing a clean separation between business logic and data access.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async database session
        """
        self.session = session

    async def create(self, task_data: Dict[str, Any]) -> Task:
        """
        Create a new task.

        Args:
            task_data: Dictionary with task fields (title, description, completed)

        Returns:
            Created Task instance with id and timestamps

        Example:
            task = await repo.create({
                "title": "Buy groceries",
                "description": "Milk and eggs",
                "completed": False
            })
        """
        task = Task(**task_data)
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: int) -> Optional[Task]:
        """
        Get task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task instance or None if not found

        Example:
            task = await repo.get(1)
            if task:
                print(task.title)
        """
        return await self.session.get(Task, task_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Get all tasks with pagination.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Task instances

        Example:
            # Get first 10 tasks
            tasks = await repo.get_all(skip=0, limit=10)

            # Get next 10 tasks
            tasks = await repo.get_all(skip=10, limit=10)
        """
        statement = select(Task).offset(skip).limit(limit).order_by(Task.id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(self, task_id: int, data: Dict[str, Any]) -> Optional[Task]:
        """
        Update task by ID.

        Args:
            task_id: Task ID to update
            data: Dictionary with fields to update

        Returns:
            Updated Task instance or None if not found

        Example:
            task = await repo.update(1, {"completed": True})
            if task:
                print(f"Task {task.id} is now completed")
        """
        task = await self.get(task_id)
        if not task:
            return None

        # Update provided fields
        for key, value in data.items():
            setattr(task, key, value)

        # Update timestamp
        task.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: int) -> bool:
        """
        Delete task by ID.

        Args:
            task_id: Task ID to delete

        Returns:
            True if task was deleted, False if not found

        Example:
            deleted = await repo.delete(1)
            if deleted:
                print("Task deleted successfully")
            else:
                print("Task not found")
        """
        task = await self.get(task_id)
        if not task:
            return False

        await self.session.delete(task)
        await self.session.flush()
        return True

    async def count(self) -> int:
        """
        Count total number of tasks.

        Returns:
            Total count of tasks in database

        Example:
            total = await repo.count()
            print(f"Total tasks: {total}")
        """
        statement = select(sql_func.count()).select_from(Task)
        result = await self.session.execute(statement)
        return result.scalar_one()
