# API Testing with Pytest

## FastAPI Testing

### Basic TestClient Setup
```python
from fastapi.testclient import TestClient
from myapp.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

### TestClient as Fixture
```python
import pytest
from fastapi.testclient import TestClient
from myapp.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_endpoint(client):
    response = client.get("/items/1")
    assert response.status_code == 200
```

### Testing POST Requests
```python
def test_create_item(client):
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 10.99
    }

    response = client.post("/items/", json=item_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data
```

### Testing with Headers
```python
def test_protected_endpoint(client):
    headers = {"Authorization": "Bearer test_token"}
    response = client.get("/protected", headers=headers)

    assert response.status_code == 200
```

### Testing File Uploads
```python
def test_file_upload(client):
    files = {"file": ("test.txt", b"file content", "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"
```

### Testing Query Parameters
```python
def test_search(client):
    params = {"q": "search term", "limit": 10}
    response = client.get("/search", params=params)

    assert response.status_code == 200
    results = response.json()
    assert len(results) <= 10
```

## Database Testing with FastAPI

### Override Dependencies
```python
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Clean up
    app.dependency_overrides.clear()
```

### Database Fixture with Setup/Teardown
```python
@pytest.fixture(scope="function")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    yield db

    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_user(client, db):
    response = client.post("/users/", json={"name": "Alice"})
    assert response.status_code == 201

    # Verify in database
    user = db.query(User).filter(User.name == "Alice").first()
    assert user is not None
```

### Transaction Rollback Pattern
```python
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def test_user_operation(db_session):
    user = User(name="Alice")
    db_session.add(user)
    db_session.commit()

    # Test operations...
    # Everything rolls back after test
```

## Authentication Testing

### Mock Authentication
```python
from unittest.mock import patch

def test_with_mock_auth(client):
    with patch("myapp.auth.verify_token") as mock_verify:
        mock_verify.return_value = {"user_id": 123}

        headers = {"Authorization": "Bearer fake_token"}
        response = client.get("/protected", headers=headers)

        assert response.status_code == 200
```

### Test User Fixture
```python
@pytest.fixture
def auth_headers(client):
    # Create test user
    response = client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass"
    })

    # Get token
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_protected_resource(client, auth_headers):
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == 200
```

## Status Code Testing

### Common HTTP Status Codes
```python
def test_status_codes(client):
    # Success
    assert client.get("/").status_code == 200

    # Created
    assert client.post("/items/", json={}).status_code == 201

    # No Content
    assert client.delete("/items/1").status_code == 204

    # Bad Request
    assert client.post("/items/", json={"invalid": True}).status_code == 400

    # Unauthorized
    assert client.get("/protected").status_code == 401

    # Forbidden
    assert client.get("/admin").status_code == 403

    # Not Found
    assert client.get("/nonexistent").status_code == 404

    # Unprocessable Entity
    assert client.post("/items/", json={"bad_field": "value"}).status_code == 422
```

## Response Validation

### JSON Schema Validation
```python
def test_response_schema(client):
    response = client.get("/items/1")

    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "price" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["price"], float)
```

### Response Headers
```python
def test_response_headers(client):
    response = client.get("/items/")

    assert response.headers["content-type"] == "application/json"
    assert "x-request-id" in response.headers
```

### Pagination Testing
```python
def test_pagination(client):
    response = client.get("/items?page=1&size=10")
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert len(data["items"]) <= 10
```

## Error Handling Tests

### Validation Errors
```python
def test_validation_error(client):
    invalid_data = {"price": -10}  # Negative price

    response = client.post("/items/", json=invalid_data)

    assert response.status_code == 422
    error = response.json()
    assert "detail" in error
```

### Custom Error Responses
```python
def test_custom_error(client):
    response = client.get("/items/999999")

    assert response.status_code == 404
    assert response.json() == {
        "error": "Item not found",
        "item_id": 999999
    }
```

## Async Testing

### pytest-asyncio
```python
import pytest
from httpx import AsyncClient
from myapp.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/async-endpoint")
        assert response.status_code == 200
```

### Async Fixtures
```python
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_with_async_client(async_client):
    response = await async_client.post("/items/", json={"name": "Test"})
    assert response.status_code == 201
```

## REST API Testing Patterns

### CRUD Operations
```python
class TestItemCRUD:
    def test_create(self, client):
        response = client.post("/items/", json={"name": "New Item"})
        assert response.status_code == 201
        return response.json()["id"]

    def test_read(self, client):
        # Create item first
        create_response = client.post("/items/", json={"name": "Item"})
        item_id = create_response.json()["id"]

        # Read it
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Item"

    def test_update(self, client):
        # Create and update
        create_response = client.post("/items/", json={"name": "Old Name"})
        item_id = create_response.json()["id"]

        update_response = client.put(
            f"/items/{item_id}",
            json={"name": "New Name"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "New Name"

    def test_delete(self, client):
        # Create and delete
        create_response = client.post("/items/", json={"name": "Item"})
        item_id = create_response.json()["id"]

        delete_response = client.delete(f"/items/{item_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 404
```

### Resource Relationships
```python
def test_nested_resources(client):
    # Create user
    user_response = client.post("/users/", json={"name": "Alice"})
    user_id = user_response.json()["id"]

    # Create post for user
    post_response = client.post(
        f"/users/{user_id}/posts/",
        json={"title": "First Post"}
    )
    assert post_response.status_code == 201

    # Get user's posts
    posts_response = client.get(f"/users/{user_id}/posts/")
    posts = posts_response.json()
    assert len(posts) == 1
    assert posts[0]["title"] == "First Post"
```

## Mock External APIs

### Mock HTTP Requests
```python
import responses

@responses.activate
def test_external_api_call(client):
    # Mock external API
    responses.add(
        responses.GET,
        "https://api.external.com/data",
        json={"result": "mocked"},
        status=200
    )

    # Test endpoint that calls external API
    response = client.get("/fetch-external-data")
    assert response.status_code == 200
    assert "result" in response.json()
```

### Mock with requests-mock
```python
import requests_mock

def test_with_requests_mock(client):
    with requests_mock.Mocker() as m:
        m.get("https://api.external.com/data", json={"data": "value"})

        response = client.get("/proxy-data")
        assert response.status_code == 200
```

## Performance Testing

### Response Time Testing
```python
import time

def test_response_time(client):
    start = time.time()
    response = client.get("/items/")
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1.0  # Should respond within 1 second
```

### Load Testing Simulation
```python
@pytest.mark.slow
def test_concurrent_requests(client):
    from concurrent.futures import ThreadPoolExecutor

    def make_request():
        return client.get("/items/")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in results)
```

## WebSocket Testing

### Testing WebSocket Endpoints
```python
def test_websocket(client):
    with client.websocket_connect("/ws") as websocket:
        # Send data
        websocket.send_json({"message": "Hello"})

        # Receive data
        data = websocket.receive_json()
        assert data["message"] == "Hello"
```

## API Versioning Tests

### Multiple API Versions
```python
def test_api_v1(client):
    response = client.get("/api/v1/items/")
    assert response.status_code == 200

def test_api_v2(client):
    response = client.get("/api/v2/items/")
    assert response.status_code == 200
    # v2 might have additional fields
    assert "new_field" in response.json()[0]
```

## Testing Best Practices for APIs

### Use Factories for Test Data
```python
@pytest.fixture
def item_factory(db):
    def _create_item(**kwargs):
        defaults = {"name": "Test Item", "price": 10.0}
        defaults.update(kwargs)
        item = Item(**defaults)
        db.add(item)
        db.commit()
        return item
    return _create_item

def test_with_factory(client, item_factory):
    item = item_factory(name="Custom Item")
    response = client.get(f"/items/{item.id}")
    assert response.json()["name"] == "Custom Item"
```

### Test Edge Cases
```python
def test_edge_cases(client):
    # Empty string
    response = client.post("/items/", json={"name": ""})
    assert response.status_code == 422

    # Very long string
    long_name = "a" * 10000
    response = client.post("/items/", json={"name": long_name})
    assert response.status_code == 422

    # Special characters
    response = client.post("/items/", json={"name": "Test <script>"})
    assert response.status_code in [200, 201, 400]  # Depends on validation
```

### Test Idempotency
```python
def test_idempotent_put(client):
    item_data = {"name": "Item", "price": 10.0}

    # First PUT
    response1 = client.put("/items/1", json=item_data)
    result1 = response1.json()

    # Second PUT with same data
    response2 = client.put("/items/1", json=item_data)
    result2 = response2.json()

    assert result1 == result2
```
