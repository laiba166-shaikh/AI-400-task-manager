#!/usr/bin/env python3
"""
Scaffold a complete pytest test structure for a Python project.

This script creates:
- tests/ directory with subdirectories (unit, integration, api)
- conftest.py with common fixtures
- pytest.ini or pyproject.toml configuration
- Example test files
- __init__.py files

Usage:
    python scaffold_tests.py
    python scaffold_tests.py --project-name myproject
    python scaffold_tests.py --config pyproject.toml
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


CONFTEST_TEMPLATE = '''"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Returns the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_data():
    """Provides sample test data."""
    return {
        "name": "Test User",
        "email": "test@example.com"
    }
'''


PYTEST_INI_TEMPLATE = '''[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
minversion = 3.8

addopts =
    -v
    -ra
    --strict-markers
    --showlocals
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
'''


PYPROJECT_TOML_TEMPLATE = '''[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
minversion = "3.8"

addopts = [
    "-v",
    "-ra",
    "--strict-markers",
    "--showlocals",
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]

markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "api: marks tests as API tests",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
fail_under = 80
'''


UNIT_TEST_TEMPLATE = '''"""
Unit tests.
"""

import pytest


def test_example():
    """Example unit test."""
    assert 1 + 1 == 2


@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_parametrized(input, expected):
    """Example parametrized test."""
    assert input * 2 == expected
'''


INTEGRATION_TEST_TEMPLATE = '''"""
Integration tests.
"""

import pytest


@pytest.mark.integration
def test_integration_example():
    """Example integration test."""
    # Test multiple components working together
    pass
'''


API_TEST_TEMPLATE = '''"""
API tests.
"""

import pytest
# from fastapi.testclient import TestClient
# from myapp.main import app


# @pytest.fixture(scope="module")
# def client():
#     """FastAPI test client."""
#     return TestClient(app)


# @pytest.mark.api
# def test_api_endpoint(client):
#     """Test API endpoint."""
#     response = client.get("/")
#     assert response.status_code == 200
'''


README_TEMPLATE = '''# Tests

This directory contains all tests for the project.

## Structure

- `unit/` - Unit tests for individual functions and classes
- `integration/` - Integration tests for multiple components
- `api/` - API endpoint tests
- `conftest.py` - Shared fixtures and configuration

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test type
pytest -m unit
pytest -m integration
pytest -m api

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Show slowest tests
pytest --durations=10
```

## Installing Dependencies

```bash
# Install pytest and common plugins
uv add --dev pytest pytest-cov pytest-mock pytest-asyncio

# For API testing
uv add --dev httpx fastapi

# For parallel execution
uv add --dev pytest-xdist
```
'''


def create_directory(path: Path, description: str):
    """Create a directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True)
        print(f"[+] Created {description}: {path}")
    else:
        print(f"  {description} already exists: {path}")


def create_file(path: Path, content: str, description: str, force: bool = False):
    """Create a file with content."""
    if path.exists() and not force:
        print(f"  {description} already exists: {path}")
        return

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Created {description}: {path}")


def scaffold_tests(
    project_name: str = "myproject",
    config_type: str = "pytest.ini",
    force: bool = False
):
    """
    Scaffold complete test structure.

    Args:
        project_name: Name of the project
        config_type: Configuration file type ('pytest.ini' or 'pyproject.toml')
        force: Overwrite existing files
    """
    print(f"Scaffolding test structure for '{project_name}'...\n")

    # Create main tests directory
    tests_dir = Path('tests')
    create_directory(tests_dir, "tests directory")

    # Create subdirectories
    unit_dir = tests_dir / 'unit'
    integration_dir = tests_dir / 'integration'
    api_dir = tests_dir / 'api'
    data_dir = tests_dir / 'data'

    create_directory(unit_dir, "unit tests directory")
    create_directory(integration_dir, "integration tests directory")
    create_directory(api_dir, "API tests directory")
    create_directory(data_dir, "test data directory")

    print()

    # Create __init__.py files
    create_file(tests_dir / '__init__.py', '', "tests __init__.py")
    create_file(unit_dir / '__init__.py', '', "unit __init__.py")
    create_file(integration_dir / '__init__.py', '', "integration __init__.py")
    create_file(api_dir / '__init__.py', '', "API __init__.py")

    print()

    # Create conftest.py
    create_file(
        tests_dir / 'conftest.py',
        CONFTEST_TEMPLATE,
        "conftest.py",
        force
    )

    # Create example test files
    create_file(
        unit_dir / 'test_example.py',
        UNIT_TEST_TEMPLATE,
        "unit test example",
        force
    )

    create_file(
        integration_dir / 'test_example.py',
        INTEGRATION_TEST_TEMPLATE,
        "integration test example",
        force
    )

    create_file(
        api_dir / 'test_example.py',
        API_TEST_TEMPLATE,
        "API test example",
        force
    )

    print()

    # Create configuration file
    if config_type == "pytest.ini":
        create_file(
            Path('pytest.ini'),
            PYTEST_INI_TEMPLATE,
            "pytest.ini configuration",
            force
        )
    elif config_type == "pyproject.toml":
        pyproject_path = Path('pyproject.toml')
        if pyproject_path.exists():
            print(f"  pyproject.toml already exists. Append pytest configuration manually.")
        else:
            create_file(
                pyproject_path,
                PYPROJECT_TOML_TEMPLATE,
                "pyproject.toml configuration",
                force
            )

    # Create README
    create_file(
        tests_dir / 'README.md',
        README_TEMPLATE,
        "tests README",
        force
    )

    print("\n" + "=" * 70)
    print("[OK] Test structure scaffolding complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Install dependencies: uv add --dev pytest pytest-cov pytest-mock")
    print("2. Review and customize tests/conftest.py")
    print("3. Add your test cases to the appropriate directories")
    print("4. Run tests: pytest")
    print("\nFor more information, see: tests/README.md")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scaffold pytest test structure for a Python project'
    )

    parser.add_argument(
        '--project-name',
        type=str,
        default='myproject',
        help='Name of the project (default: myproject)'
    )

    parser.add_argument(
        '--config',
        type=str,
        choices=['pytest.ini', 'pyproject.toml'],
        default='pytest.ini',
        help='Configuration file type (default: pytest.ini)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing files'
    )

    args = parser.parse_args()

    scaffold_tests(
        project_name=args.project_name,
        config_type=args.config,
        force=args.force
    )


if __name__ == '__main__':
    main()
