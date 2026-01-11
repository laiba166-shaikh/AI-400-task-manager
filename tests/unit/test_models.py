"""Unit tests for SQLModel models."""
import pytest
from datetime import datetime
from app.models import Task, TaskCreate, TaskUpdate, TaskRead


@pytest.mark.unit
def test_task_base_fields():
    """Test TaskCreate schema validation."""
    task_data = TaskCreate(
        title="Test Task",
        description="Test description",
        completed=False
    )

    assert task_data.title == "Test Task"
    assert task_data.description == "Test description"
    assert task_data.completed is False


@pytest.mark.unit
def test_task_create_minimal():
    """Test TaskCreate with only required field."""
    task_data = TaskCreate(title="Minimal Task")

    assert task_data.title == "Minimal Task"
    assert task_data.description is None
    assert task_data.completed is False


@pytest.mark.unit
def test_task_create_validation():
    """Test TaskCreate validation (title too short)."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        TaskCreate(title="")  # Empty title should fail


@pytest.mark.unit
def test_task_update_partial():
    """Test TaskUpdate with partial fields."""
    update_data = TaskUpdate(completed=True)

    assert update_data.completed is True
    assert update_data.title is None
    assert update_data.description is None


@pytest.mark.unit
def test_task_update_all_fields():
    """Test TaskUpdate with all fields."""
    update_data = TaskUpdate(
        title="Updated",
        description="New description",
        completed=True
    )

    assert update_data.title == "Updated"
    assert update_data.description == "New description"
    assert update_data.completed is True


@pytest.mark.unit
def test_task_read_structure():
    """Test TaskRead schema structure."""
    task_data = TaskRead(
        id=1,
        title="Test Task",
        description="Description",
        completed=False,
        created_at=datetime.utcnow(),
        updated_at=None
    )

    assert task_data.id == 1
    assert task_data.title == "Test Task"
    assert isinstance(task_data.created_at, datetime)
    assert task_data.updated_at is None


@pytest.mark.unit
def test_task_model_dump():
    """Test converting TaskCreate to dict."""
    task_data = TaskCreate(
        title="Test Task",
        description="Description",
        completed=True
    )

    dumped = task_data.model_dump()

    assert isinstance(dumped, dict)
    assert dumped["title"] == "Test Task"
    assert dumped["description"] == "Description"
    assert dumped["completed"] is True


@pytest.mark.unit
def test_task_update_exclude_unset():
    """Test TaskUpdate with exclude_unset for partial updates."""
    update_data = TaskUpdate(completed=True)

    # Only completed should be in the dict
    dumped = update_data.model_dump(exclude_unset=True)

    assert "completed" in dumped
    assert dumped["completed"] is True
    assert "title" not in dumped
    assert "description" not in dumped
