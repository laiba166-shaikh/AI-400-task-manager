"""SQLModel CRUD Repository Pattern

Provides a generic async repository class for common database operations
following the Repository pattern with SQLModel.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func as sql_func

# Import your model here
# from app.models import Task


class TaskRepository:
    """
    Async repository for Task CRUD operations.

    This is a concrete example. For a generic version, see GenericRepository below.

    Usage:
        repo = TaskRepository(session)

        # Create
        task = await repo.create({"title": "Buy groceries", "completed": False})

        # Read
        task = await repo.get(1)
        tasks = await repo.get_all(skip=0, limit=10)

        # Update
        updated = await repo.update(1, {"completed": True})

        # Delete
        deleted = await repo.delete(1)

        # Count
        total = await repo.count()
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async database session
        """
        self.session = session

    async def create(self, task_data: Dict[str, Any]):  # -> Task:
        """
        Create a new task.

        Args:
            task_data: Dictionary with task fields

        Returns:
            Created Task instance
        """
        # from app.models import Task
        # task = Task(**task_data)
        # self.session.add(task)
        # await self.session.flush()
        # await self.session.refresh(task)
        # return task
        pass

    async def get(self, task_id: int):  # -> Optional[Task]:
        """
        Get task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task instance or None if not found
        """
        # from app.models import Task
        # return await self.session.get(Task, task_id)
        pass

    async def get_all(self, skip: int = 0, limit: int = 100):  # -> List[Task]:
        """
        Get all tasks with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Task instances
        """
        # from app.models import Task
        # statement = select(Task).offset(skip).limit(limit).order_by(Task.id)
        # result = await self.session.execute(statement)
        # return list(result.scalars().all())
        pass

    async def update(self, task_id: int, data: Dict[str, Any]):  # -> Optional[Task]:
        """
        Update task by ID.

        Args:
            task_id: Task ID to update
            data: Dictionary with fields to update

        Returns:
            Updated Task instance or None if not found
        """
        # task = await self.get(task_id)
        # if not task:
        #     return None
        #
        # for key, value in data.items():
        #     setattr(task, key, value)
        #
        # # Update timestamp if model has updated_at field
        # if hasattr(task, 'updated_at'):
        #     task.updated_at = datetime.utcnow()
        #
        # await self.session.flush()
        # await self.session.refresh(task)
        # return task
        pass

    async def delete(self, task_id: int) -> bool:
        """
        Delete task by ID.

        Args:
            task_id: Task ID to delete

        Returns:
            True if deleted, False if not found
        """
        # task = await self.get(task_id)
        # if not task:
        #     return False
        #
        # await self.session.delete(task)
        # await self.session.flush()
        # return True
        pass

    async def count(self) -> int:
        """
        Count total number of tasks.

        Returns:
            Total count of tasks
        """
        # from app.models import Task
        # statement = select(sql_func.count()).select_from(Task)
        # result = await self.session.execute(statement)
        # return result.scalar_one()
        pass


# ============================================================================
# WORKING EXAMPLE - Copy and adapt this for your models
# ============================================================================

"""
Here's a complete working example based on the Task model:

```python
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func as sql_func
from app.models import Task


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_data: Dict[str, Any]) -> Task:
        task = Task(**task_data)
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: int) -> Optional[Task]:
        return await self.session.get(Task, task_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        statement = select(Task).offset(skip).limit(limit).order_by(Task.id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(self, task_id: int, data: Dict[str, Any]) -> Optional[Task]:
        task = await self.get(task_id)
        if not task:
            return None

        for key, value in data.items():
            setattr(task, key, value)

        # Update timestamp
        task.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: int) -> bool:
        task = await self.get(task_id)
        if not task:
            return False

        await self.session.delete(task)
        await self.session.flush()
        return True

    async def count(self) -> int:
        statement = select(sql_func.count()).select_from(Task)
        result = await self.session.execute(statement)
        return result.scalar_one()
```
"""


# ============================================================================
# KEY PATTERNS
# ============================================================================

"""
1. Use sqlmodel.select (not sqlalchemy.select) for queries:
   ```python
   from sqlmodel import select
   statement = select(Task).where(Task.completed == False)
   ```

2. Use session.execute() for queries, session.get() for by-ID lookups:
   ```python
   # By ID
   task = await session.get(Task, 1)

   # Query
   result = await session.execute(select(Task))
   tasks = result.scalars().all()
   ```

3. Use flush() in repositories, commit() in route handlers:
   ```python
   # In repository
   await session.flush()

   # In route handler
   await session.commit()
   ```

4. Handle None returns for not found:
   ```python
   task = await repo.get(999)
   if not task:
       raise HTTPException(status_code=404, detail="Task not found")
   ```

5. Update timestamps explicitly:
   ```python
   if hasattr(task, 'updated_at'):
       task.updated_at = datetime.utcnow()
   ```

6. Use scalars() to get model instances:
   ```python
   result = await session.execute(select(Task))
   tasks = list(result.scalars().all())  # Returns List[Task]
   ```

7. Filtering with where():
   ```python
   # Single condition
   statement = select(Task).where(Task.completed == True)

   # Multiple conditions
   statement = select(Task).where(
       Task.completed == False,
       Task.priority > 3
   )
   ```

8. Ordering and pagination:
   ```python
   statement = (
       select(Task)
       .where(Task.completed == False)
       .order_by(Task.created_at.desc())
       .offset(skip)
       .limit(limit)
   )
   ```
"""