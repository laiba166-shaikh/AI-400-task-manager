"""Task API endpoints using SQLModel schemas."""
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.database import SessionDep
from app.models import TaskCreate, TaskRead, TaskUpdate
from app.crud import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, session: SessionDep):
    """
    Create a new task.

    Args:
        task: Task creation data (title, description, completed)
        session: Database session (injected)

    Returns:
        Created task with id and timestamps

    Example Request:
        POST /tasks/
        {
            "title": "Buy groceries",
            "description": "Milk, eggs, bread",
            "completed": false
        }

    Example Response (201):
        {
            "id": 1,
            "title": "Buy groceries",
            "description": "Milk, eggs, bread",
            "completed": false,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": null
        }
    """
    repo = TaskRepository(session)
    db_task = await repo.create(task.model_dump())
    await session.commit()
    return db_task


@router.get("/", response_model=List[TaskRead])
async def list_tasks(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    List all tasks with pagination.

    Args:
        session: Database session (injected)
        skip: Number of tasks to skip (default: 0)
        limit: Maximum tasks to return (default: 100, max: 100)

    Returns:
        List of tasks

    Example Request:
        GET /tasks/?skip=0&limit=10

    Example Response (200):
        [
            {
                "id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": false,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": null
            },
            {
                "id": 2,
                "title": "Walk the dog",
                "description": null,
                "completed": true,
                "created_at": "2024-01-15T11:00:00",
                "updated_at": "2024-01-15T12:00:00"
            }
        ]
    """
    repo = TaskRepository(session)
    tasks = await repo.get_all(skip=skip, limit=limit)
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, session: SessionDep):
    """
    Get a specific task by ID.

    Args:
        task_id: Task ID to retrieve
        session: Database session (injected)

    Returns:
        Task details

    Raises:
        HTTPException: 404 if task not found

    Example Request:
        GET /tasks/1

    Example Response (200):
        {
            "id": 1,
            "title": "Buy groceries",
            "description": "Milk, eggs, bread",
            "completed": false,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": null
        }

    Example Error Response (404):
        {
            "detail": "Task 999 not found"
        }
    """
    repo = TaskRepository(session)
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task_update: TaskUpdate, session: SessionDep):
    """
    Update a task (partial update).

    Only fields provided in the request will be updated.

    Args:
        task_id: Task ID to update
        task_update: Fields to update
        session: Database session (injected)

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found
        HTTPException: 400 if no fields provided

    Example Request (partial update):
        PATCH /tasks/1
        {
            "completed": true
        }

    Example Request (full update):
        PATCH /tasks/1
        {
            "title": "Buy groceries - URGENT",
            "description": "Milk, eggs, bread, coffee",
            "completed": true
        }

    Example Response (200):
        {
            "id": 1,
            "title": "Buy groceries - URGENT",
            "description": "Milk, eggs, bread, coffee",
            "completed": true,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T14:30:00"
        }

    Example Error Response (404):
        {
            "detail": "Task 999 not found"
        }

    Example Error Response (400):
        {
            "detail": "No fields to update"
        }
    """
    repo = TaskRepository(session)

    # Get only fields that were actually set (exclude unset fields)
    update_data = task_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    task = await repo.update(task_id, update_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    await session.commit()
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: SessionDep):
    """
    Delete a task.

    Args:
        task_id: Task ID to delete
        session: Database session (injected)

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 404 if task not found

    Example Request:
        DELETE /tasks/1

    Example Response (204):
        No content

    Example Error Response (404):
        {
            "detail": "Task 999 not found"
        }
    """
    repo = TaskRepository(session)
    deleted = await repo.delete(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    await session.commit()
    return None
