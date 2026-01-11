"""
API test template for FastAPI applications.

These tests use FastAPI's TestClient to test API endpoints.
Install: uv add fastapi httpx
"""

import pytest
from fastapi.testclient import TestClient
# from myapp.main import app


# ============================================================================
# Test client fixture
# ============================================================================

# @pytest.fixture(scope="module")
# def client():
#     """
#     FastAPI test client.
#     Module-scoped for efficiency across tests.
#     """
#     from myapp.main import app
#     return TestClient(app)


# ============================================================================
# Basic endpoint tests
# ============================================================================

# def test_root_endpoint(client):
#     """Test root endpoint."""
#     response = client.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Hello World"}


# def test_health_check(client):
#     """Test health check endpoint."""
#     response = client.get("/health")
#     assert response.status_code == 200
#     assert response.json()["status"] == "healthy"


# ============================================================================
# GET request tests
# ============================================================================

# def test_get_item(client):
#     """Test GET single item."""
#     response = client.get("/items/1")
#     assert response.status_code == 200
#
#     data = response.json()
#     assert "id" in data
#     assert "name" in data
#     assert data["id"] == 1


# def test_get_items_list(client):
#     """Test GET list of items."""
#     response = client.get("/items/")
#     assert response.status_code == 200
#
#     data = response.json()
#     assert isinstance(data, list)
#     assert len(data) > 0


# def test_get_with_query_params(client):
#     """Test GET with query parameters."""
#     response = client.get("/items/", params={"skip": 0, "limit": 10})
#     assert response.status_code == 200
#
#     data = response.json()
#     assert len(data) <= 10


# def test_get_not_found(client):
#     """Test GET non-existent resource."""
#     response = client.get("/items/999999")
#     assert response.status_code == 404


# ============================================================================
# POST request tests
# ============================================================================

# def test_create_item(client):
#     """Test creating a new item."""
#     item_data = {
#         "name": "Test Item",
#         "description": "Test description",
#         "price": 19.99
#     }
#
#     response = client.post("/items/", json=item_data)
#     assert response.status_code == 201
#
#     data = response.json()
#     assert data["name"] == "Test Item"
#     assert data["price"] == 19.99
#     assert "id" in data


# def test_create_item_validation_error(client):
#     """Test validation error on create."""
#     invalid_data = {
#         "name": "",  # Empty name
#         "price": -10  # Negative price
#     }
#
#     response = client.post("/items/", json=invalid_data)
#     assert response.status_code == 422  # Unprocessable Entity
#
#     error = response.json()
#     assert "detail" in error


# ============================================================================
# PUT/PATCH request tests
# ============================================================================

# def test_update_item(client):
#     """Test updating an item."""
#     # First create an item
#     create_response = client.post("/items/", json={
#         "name": "Original Name",
#         "price": 10.0
#     })
#     item_id = create_response.json()["id"]
#
#     # Update the item
#     update_data = {
#         "name": "Updated Name",
#         "price": 15.0
#     }
#     response = client.put(f"/items/{item_id}", json=update_data)
#     assert response.status_code == 200
#
#     data = response.json()
#     assert data["name"] == "Updated Name"
#     assert data["price"] == 15.0


# ============================================================================
# DELETE request tests
# ============================================================================

# def test_delete_item(client):
#     """Test deleting an item."""
#     # Create item
#     create_response = client.post("/items/", json={"name": "To Delete"})
#     item_id = create_response.json()["id"]
#
#     # Delete item
#     response = client.delete(f"/items/{item_id}")
#     assert response.status_code == 204  # No Content
#
#     # Verify deletion
#     get_response = client.get(f"/items/{item_id}")
#     assert get_response.status_code == 404


# ============================================================================
# Authentication tests
# ============================================================================

# @pytest.fixture
# def auth_headers(client):
#     """Get authentication headers."""
#     # Login
#     response = client.post("/auth/login", json={
#         "username": "testuser",
#         "password": "testpass"
#     })
#
#     token = response.json()["access_token"]
#     return {"Authorization": f"Bearer {token}"}


# def test_protected_endpoint_unauthorized(client):
#     """Test protected endpoint without auth."""
#     response = client.get("/protected")
#     assert response.status_code == 401


# def test_protected_endpoint_authorized(client, auth_headers):
#     """Test protected endpoint with auth."""
#     response = client.get("/protected", headers=auth_headers)
#     assert response.status_code == 200


# ============================================================================
# CRUD operation tests
# ============================================================================

# @pytest.mark.api
# class TestItemCRUD:
#     """Test complete CRUD operations for items."""
#
#     def test_create_read_update_delete(self, client):
#         """Test full CRUD cycle."""
#         # CREATE
#         create_response = client.post("/items/", json={
#             "name": "Test Item",
#             "description": "Description",
#             "price": 29.99
#         })
#         assert create_response.status_code == 201
#         item_id = create_response.json()["id"]
#
#         # READ
#         read_response = client.get(f"/items/{item_id}")
#         assert read_response.status_code == 200
#         assert read_response.json()["name"] == "Test Item"
#
#         # UPDATE
#         update_response = client.put(f"/items/{item_id}", json={
#             "name": "Updated Item",
#             "price": 39.99
#         })
#         assert update_response.status_code == 200
#         assert update_response.json()["name"] == "Updated Item"
#
#         # DELETE
#         delete_response = client.delete(f"/items/{item_id}")
#         assert delete_response.status_code == 204
