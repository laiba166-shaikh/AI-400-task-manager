"""API endpoint tests for Task CRUD operations."""
import pytest
from httpx import AsyncClient
from app.models import Task


@pytest.mark.api
@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


@pytest.mark.api
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    """Test creating a new task."""
    task_data = {
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "completed": False
    }

    response = await client.post("/tasks/", json=task_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["completed"] == task_data["completed"]
    assert "id" in data
    assert "created_at" in data
    assert data["updated_at"] is None


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_task_minimal(client: AsyncClient):
    """Test creating task with only required field (title)."""
    task_data = {"title": "Minimal task"}

    response = await client.post("/tasks/", json=task_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal task"
    assert data["description"] is None
    assert data["completed"] is False


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_task_validation_error(client: AsyncClient):
    """Test creating task with invalid data (empty title)."""
    task_data = {"title": ""}  # Title too short

    response = await client.post("/tasks/", json=task_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient):
    """Test listing tasks when database is empty."""
    response = await client.get("/tasks/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, multiple_tasks):
    """Test listing all tasks."""
    response = await client.get("/tasks/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    assert all("id" in task for task in data)
    assert all("title" in task for task in data)


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient, multiple_tasks):
    """Test task list pagination."""
    # Get first 2 tasks
    response = await client.get("/tasks/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Get next 2 tasks
    response = await client.get("/tasks/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, sample_task: Task):
    """Test getting a specific task by ID."""
    response = await client.get(f"/tasks/{sample_task.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_task.id
    assert data["title"] == sample_task.title
    assert data["description"] == sample_task.description
    assert data["completed"] == sample_task.completed


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    """Test getting a task that doesn't exist."""
    response = await client.get("/tasks/9999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "9999" in data["detail"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_update_task_partial(client: AsyncClient, sample_task: Task):
    """Test partial update of a task (PATCH)."""
    update_data = {"completed": True}

    response = await client.patch(f"/tasks/{sample_task.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_task.id
    assert data["completed"] is True
    assert data["title"] == sample_task.title  # Unchanged
    assert data["updated_at"] is not None  # Should be updated


@pytest.mark.api
@pytest.mark.asyncio
async def test_update_task_full(client: AsyncClient, sample_task: Task):
    """Test full update of a task."""
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description",
        "completed": True
    }

    response = await client.patch(f"/tasks/{sample_task.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_task.id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["completed"] is True
    assert data["updated_at"] is not None


@pytest.mark.api
@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient):
    """Test updating a task that doesn't exist."""
    update_data = {"completed": True}

    response = await client.patch("/tasks/9999", json=update_data)

    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.asyncio
async def test_update_task_no_fields(client: AsyncClient, sample_task: Task):
    """Test updating task with no fields provided."""
    response = await client.patch(f"/tasks/{sample_task.id}", json={})

    assert response.status_code == 400
    data = response.json()
    assert "No fields to update" in data["detail"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, sample_task: Task):
    """Test deleting a task."""
    task_id = sample_task.id

    response = await client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204  # No content

    # Verify task is deleted
    response = await client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.asyncio
async def test_delete_task_not_found(client: AsyncClient):
    """Test deleting a task that doesn't exist."""
    response = await client.delete("/tasks/9999")

    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.asyncio
async def test_full_crud_cycle(client: AsyncClient):
    """Test complete CRUD lifecycle: Create -> Read -> Update -> Delete."""
    # CREATE
    create_data = {
        "title": "CRUD Test Task",
        "description": "Testing full lifecycle",
        "completed": False
    }
    create_response = await client.post("/tasks/", json=create_data)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # READ
    read_response = await client.get(f"/tasks/{task_id}")
    assert read_response.status_code == 200
    assert read_response.json()["title"] == "CRUD Test Task"

    # UPDATE
    update_data = {"completed": True, "title": "CRUD Test Task - Updated"}
    update_response = await client.patch(f"/tasks/{task_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["completed"] is True
    assert update_response.json()["title"] == "CRUD Test Task - Updated"

    # DELETE
    delete_response = await client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204

    # VERIFY DELETION
    verify_response = await client.get(f"/tasks/{task_id}")
    assert verify_response.status_code == 404
