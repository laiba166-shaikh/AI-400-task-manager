"""Unit tests for CRUD operations."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import TaskRepository
from app.models import Task


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task(session: AsyncSession):
    """Test creating a task in the database."""
    repo = TaskRepository(session)

    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "completed": False
    }

    task = await repo.create(task_data)

    assert task.id is not None
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.completed is False
    assert task.created_at is not None
    assert task.updated_at is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task(session: AsyncSession):
    """Test getting a task by ID."""
    repo = TaskRepository(session)

    # Create a task first
    created = await repo.create({"title": "Get Test Task"})
    task_id = created.id

    # Get the task
    task = await repo.get(task_id)

    assert task is not None
    assert task.id == task_id
    assert task.title == "Get Test Task"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_nonexistent_task(session: AsyncSession):
    """Test getting a task that doesn't exist."""
    repo = TaskRepository(session)

    task = await repo.get(9999)

    assert task is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_tasks_empty(session: AsyncSession):
    """Test getting all tasks when database is empty."""
    repo = TaskRepository(session)

    tasks = await repo.get_all()

    assert isinstance(tasks, list)
    assert len(tasks) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_tasks(session: AsyncSession):
    """Test getting all tasks."""
    repo = TaskRepository(session)

    # Create multiple tasks
    await repo.create({"title": "Task 1"})
    await repo.create({"title": "Task 2"})
    await repo.create({"title": "Task 3"})

    tasks = await repo.get_all()

    assert len(tasks) == 3
    assert all(isinstance(task, Task) for task in tasks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_tasks_pagination(session: AsyncSession):
    """Test pagination in get_all."""
    repo = TaskRepository(session)

    # Create 5 tasks
    for i in range(1, 6):
        await repo.create({"title": f"Task {i}"})

    # Get first 2
    tasks = await repo.get_all(skip=0, limit=2)
    assert len(tasks) == 2

    # Get next 2
    tasks = await repo.get_all(skip=2, limit=2)
    assert len(tasks) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task(session: AsyncSession):
    """Test updating a task."""
    repo = TaskRepository(session)

    # Create a task
    created = await repo.create({"title": "Original Title", "completed": False})
    task_id = created.id

    # Update the task
    updated = await repo.update(task_id, {"title": "Updated Title", "completed": True})

    assert updated is not None
    assert updated.id == task_id
    assert updated.title == "Updated Title"
    assert updated.completed is True
    assert updated.updated_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_nonexistent_task(session: AsyncSession):
    """Test updating a task that doesn't exist."""
    repo = TaskRepository(session)

    updated = await repo.update(9999, {"title": "New Title"})

    assert updated is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task(session: AsyncSession):
    """Test deleting a task."""
    repo = TaskRepository(session)

    # Create a task
    created = await repo.create({"title": "To Delete"})
    task_id = created.id

    # Delete the task
    deleted = await repo.delete(task_id)

    assert deleted is True

    # Verify it's gone
    task = await repo.get(task_id)
    assert task is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_nonexistent_task(session: AsyncSession):
    """Test deleting a task that doesn't exist."""
    repo = TaskRepository(session)

    deleted = await repo.delete(9999)

    assert deleted is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_tasks(session: AsyncSession):
    """Test counting total tasks."""
    repo = TaskRepository(session)

    # Initially empty
    count = await repo.count()
    assert count == 0

    # Create some tasks
    await repo.create({"title": "Task 1"})
    await repo.create({"title": "Task 2"})
    await repo.create({"title": "Task 3"})

    count = await repo.count()
    assert count == 3
