"""
Pytest configuration and shared fixtures.

This conftest.py file contains common fixtures that are available to all tests.
Place this file in your tests/ directory.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


# ============================================================================
# Session-scoped fixtures (created once per test session)
# ============================================================================

@pytest.fixture(scope="session")
def test_data_dir():
    """
    Returns the path to the test data directory.
    Use this to access test data files.
    """
    return Path(__file__).parent / "data"


# ============================================================================
# Module-scoped fixtures (created once per test module)
# ============================================================================

# Example: Database connection shared across a module
# @pytest.fixture(scope="module")
# def database():
#     """Database connection for all tests in the module."""
#     db = Database("test.db")
#     yield db
#     db.close()


# ============================================================================
# Function-scoped fixtures (default - created for each test)
# ============================================================================

@pytest.fixture
def temp_dir():
    """
    Creates a temporary directory for test files.
    Automatically cleaned up after the test.
    """
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def sample_data():
    """
    Provides sample data for tests.
    Modify this to return data relevant to your application.
    """
    return {
        "name": "Test User",
        "email": "test@example.com",
        "age": 30
    }


# ============================================================================
# Factory fixtures (for creating multiple instances)
# ============================================================================

@pytest.fixture
def make_temp_file(temp_dir):
    """
    Factory fixture to create temporary files.

    Usage:
        def test_example(make_temp_file):
            file1 = make_temp_file("test1.txt", "content1")
            file2 = make_temp_file("test2.txt", "content2")
    """
    def _make_file(filename, content=""):
        file_path = temp_dir / filename
        file_path.write_text(content)
        return file_path
    return _make_file


# ============================================================================
# Autouse fixtures (automatically used by all tests)
# ============================================================================

@pytest.fixture(autouse=True)
def reset_state():
    """
    Automatically runs before each test to reset state.
    Modify this to reset any global state your application uses.
    """
    # Setup: runs before each test
    pass

    yield

    # Teardown: runs after each test
    pass


# ============================================================================
# Database fixtures (example - uncomment and modify as needed)
# ============================================================================

# @pytest.fixture
# def db_session():
#     """
#     Provides a database session with automatic rollback.
#     Changes are not committed to the database.
#     """
#     from myapp.database import Session, engine
#     from myapp.models import Base
#
#     # Create tables
#     Base.metadata.create_all(bind=engine)
#
#     # Create session with transaction
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = Session(bind=connection)
#
#     yield session
#
#     # Rollback and cleanup
#     session.close()
#     transaction.rollback()
#     connection.close()


# ============================================================================
# API client fixtures (example for FastAPI)
# ============================================================================

# @pytest.fixture
# def client():
#     """
#     Provides a test client for API testing.
#     """
#     from fastapi.testclient import TestClient
#     from myapp.main import app
#
#     return TestClient(app)


# @pytest.fixture
# def auth_headers(client):
#     """
#     Provides authentication headers for protected endpoints.
#     """
#     # Login and get token
#     response = client.post("/auth/login", json={
#         "username": "testuser",
#         "password": "testpass"
#     })
#     token = response.json()["access_token"]
#
#     return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Mock fixtures (example)
# ============================================================================

# @pytest.fixture
# def mock_external_api(mocker):
#     """
#     Mocks external API calls.
#     Requires pytest-mock plugin.
#     """
#     mock = mocker.patch("myapp.services.external_api.call")
#     mock.return_value = {"status": "success"}
#     return mock


# ============================================================================
# Pytest configuration hooks
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )


# ============================================================================
# Custom pytest options (example)
# ============================================================================

# def pytest_addoption(parser):
#     """Add custom command line options."""
#     parser.addoption(
#         "--run-slow",
#         action="store_true",
#         default=False,
#         help="run slow tests"
#     )
#
#
# def pytest_collection_modifyitems(config, items):
#     """Skip slow tests unless --run-slow is specified."""
#     if config.getoption("--run-slow"):
#         return
#
#     skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
#     for item in items:
#         if "slow" in item.keywords:
#             item.add_marker(skip_slow)
