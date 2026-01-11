---
name: pytest-test-suite
description: Generate comprehensive, well-structured pytest test suites for Python projects. Supports unit, integration, and API testing with fixtures, parametrization, mocking, and coverage reporting. Use when creating test files, setting up test infrastructure, generating test boilerplate, or needing pytest best practices for FastAPI, general Python libraries, or data science projects.
---

# Pytest Test Suite Generator

Generate complete, production-ready pytest test suites following best practices.

## Quick Start

### 1. Install Dependencies

```bash
# Core testing packages
uv add --dev pytest pytest-cov pytest-mock

# For async testing
uv add --dev pytest-asyncio

# For API testing (FastAPI)
uv add --dev httpx fastapi

# For parallel test execution
uv add --dev pytest-xdist
```

### 2. Generate Test Structure

Use the scaffold script to create a complete test directory structure:

```bash
python scripts/scaffold_tests.py --project-name myproject --config pyproject.toml
```

This creates:
- `tests/` directory with subdirectories (unit, integration, api)
- `conftest.py` with common fixtures
- `pytest.ini` or `pyproject.toml` configuration
- Example test files

### 3. Generate Tests for Existing Code

```bash
python scripts/generate_test_file.py src/mymodule.py
```

Generates a test file with boilerplate for all functions and classes in the source file.

## Test Structure

Organize tests by type for clarity and selective execution:

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── data/                    # Test data files
├── unit/                    # Unit tests
│   ├── __init__.py
│   └── test_*.py
├── integration/             # Integration tests
│   ├── __init__.py
│   └── test_*.py
└── api/                     # API tests
    ├── __init__.py
    └── test_*.py
```

## Writing Tests

### Unit Tests

Use the unit test template from `assets/test_unit_template.py`:

```python
import pytest

def test_function():
    # Arrange
    data = {"key": "value"}

    # Act
    result = process(data)

    # Assert
    assert result is not None
```

**See reference:** `references/pytest_patterns.md` for comprehensive patterns.

### Integration Tests

Use the integration test template from `assets/test_integration_template.py` for tests involving:
- Database operations
- File system interactions
- Multiple components working together
- External service calls

**See reference:** `references/pytest_patterns.md` for integration patterns.

### API Tests

Use the API test template from `assets/test_api_template.py` for FastAPI endpoints:

```python
from fastapi.testclient import TestClient

def test_endpoint(client):
    response = client.get("/items/1")
    assert response.status_code == 200
    assert "id" in response.json()
```

**See reference:** `references/api_testing.md` for complete API testing guide.

## Fixtures

### Creating Fixtures

Add fixtures to `conftest.py` for shared test setup:

```python
@pytest.fixture
def database():
    db = Database("test.db")
    yield db
    db.close()

def test_with_db(database):
    result = database.query("SELECT 1")
    assert result is not None
```

**See reference:** `references/fixtures_guide.md` for comprehensive fixture patterns including:
- Fixture scopes (function, class, module, session)
- Fixture factories
- Parametrized fixtures
- Fixture dependencies

## Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
], ids=["one", "two", "three"])
def test_double(input, expected):
    assert input * 2 == expected
```

**See reference:** `references/parametrize_guide.md` for advanced parametrization including:
- Multiple parameters
- Indirect parametrization
- Loading test data from files
- Conditional parametrization

## Mocking

### Basic Mocking

```python
from unittest.mock import Mock, patch

@patch("mymodule.external_call")
def test_with_mock(mock_call):
    mock_call.return_value = {"status": "success"}
    result = my_function()
    assert result["status"] == "success"
```

### Using pytest-mock

```python
def test_with_mocker(mocker):
    mock = mocker.patch("mymodule.api_call")
    mock.return_value = "mocked"
    result = my_function()
    assert result == "mocked"
```

**See reference:** `references/mocking_guide.md` for comprehensive mocking patterns including:
- Mocking HTTP requests
- Mocking databases
- Mocking file operations
- Testing with side effects

## Configuration

### Using pytest.ini

Use the template from `assets/pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -v --cov=src --cov-report=html
markers =
    slow: marks tests as slow
    integration: marks integration tests
```

### Using pyproject.toml (Recommended)

Use the template from `assets/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--cov=src"]
markers = ["slow: marks tests as slow"]
```

## Running Tests

### Basic Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_module.py

# Run specific test function
pytest tests/unit/test_module.py::test_function
```

### With Markers

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run smoke tests
pytest -m smoke
```

### With Coverage

Use the helper script:

```bash
python scripts/run_tests_with_coverage.py
```

Or manually:

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist: uv add --dev pytest-xdist)
pytest -n auto
```

### Show Slowest Tests

```bash
pytest --durations=10
```

## Test Markers

Define custom markers in configuration:

```python
# In conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "api: API tests")

# In tests
@pytest.mark.slow
def test_heavy_operation():
    pass

@pytest.mark.integration
@pytest.mark.db
def test_database_integration():
    pass
```

## Best Practices

### Test Organization
- Group related tests in classes
- Use descriptive test names
- One assertion per test (when possible)
- Follow AAA pattern: Arrange, Act, Assert

### Fixtures
- Keep fixtures focused and single-purpose
- Use appropriate fixture scopes
- Avoid long fixture dependency chains
- Document complex fixtures

### Parametrization
- Use descriptive IDs for test cases
- Group related test cases
- Avoid over-parametrization (too many combinations)

### Mocking
- Mock at the right level (boundaries, not internals)
- Verify important interactions
- Reset mocks between tests
- Use `spec` parameter for safety

### Coverage
- Aim for 80%+ coverage
- Focus on business logic and critical paths
- Don't chase 100% coverage blindly
- Test edge cases and error handling

## Bundled Resources

### Templates (assets/)
- `conftest_template.py` - Shared fixtures template
- `test_unit_template.py` - Unit test template
- `test_integration_template.py` - Integration test template
- `test_api_template.py` - API test template
- `pytest.ini` - Pytest configuration
- `pyproject.toml` - Modern pytest configuration

### Scripts (scripts/)
- `scaffold_tests.py` - Generate complete test structure
- `generate_test_file.py` - Generate test file from source
- `run_tests_with_coverage.py` - Run tests with coverage reporting

### Reference Guides (references/)
- `pytest_patterns.md` - Common testing patterns and best practices
- `fixtures_guide.md` - Comprehensive fixture examples
- `mocking_guide.md` - Mocking and patching strategies
- `api_testing.md` - FastAPI/web API testing patterns
- `parametrize_guide.md` - Parametrized testing examples

## Workflow

### For New Projects

1. **Scaffold test structure:**
   ```bash
   python scripts/scaffold_tests.py --config pyproject.toml
   ```

2. **Install dependencies:**
   ```bash
   uv add --dev pytest pytest-cov pytest-mock pytest-asyncio
   ```

3. **Copy conftest template:**
   Copy `assets/conftest_template.py` content to `tests/conftest.py` and customize.

4. **Write tests:**
   Use templates from `assets/` as starting points.

5. **Run tests:**
   ```bash
   python scripts/run_tests_with_coverage.py
   ```

### For Existing Code

1. **Generate test file:**
   ```bash
   python scripts/generate_test_file.py src/mymodule.py
   ```

2. **Review generated tests:**
   - Add specific test cases
   - Fill in TODOs
   - Add assertions

3. **Add fixtures as needed:**
   Add to `tests/conftest.py` or local conftest files.

4. **Run and iterate:**
   ```bash
   pytest tests/test_mymodule.py -v
   ```

### For FastAPI Projects

1. **Install API testing dependencies:**
   ```bash
   uv add --dev httpx fastapi
   ```

2. **Copy API test template:**
   Use `assets/test_api_template.py` as a starting point.

3. **Create test client fixture:**
   ```python
   @pytest.fixture
   def client():
       from myapp.main import app
       return TestClient(app)
   ```

4. **Write endpoint tests:**
   Test GET, POST, PUT, DELETE operations.

5. **See reference:**
   `references/api_testing.md` for comprehensive API testing patterns.

## Common Patterns

### Database Testing

```python
@pytest.fixture
def db_session():
    session = Session()
    session.begin()
    yield session
    session.rollback()
    session.close()
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### Exception Testing

```python
def test_exception():
    with pytest.raises(ValueError, match="Invalid input"):
        risky_function("")
```

### Temporary Files

```python
def test_file_operation(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")
    assert file.read_text() == "content"
```

## Troubleshooting

### Import Errors
- Ensure `__init__.py` files exist in test directories
- Check `PYTHONPATH` or use `uv add -e .` for editable install

### Fixture Not Found
- Verify fixture is in `conftest.py` in the same or parent directory
- Check fixture scope matches usage

### Coverage Too Low
- Run `pytest --cov=src --cov-report=html` to see missed lines
- Focus on untested branches and edge cases
- Update `--cov-fail-under` threshold in configuration

### Slow Tests
- Mark slow tests: `@pytest.mark.slow`
- Run without slow tests: `pytest -m "not slow"`
- Use `pytest-xdist` for parallel execution: `uv add --dev pytest-xdist`

## Additional Resources

For detailed patterns and examples, see the reference guides:
- **pytest_patterns.md** - Test organization, markers, assertions
- **fixtures_guide.md** - Fixture scopes, factories, built-in fixtures
- **mocking_guide.md** - Mocking strategies, patching, test doubles
- **api_testing.md** - FastAPI testing, authentication, CRUD operations
- **parametrize_guide.md** - Data-driven testing, test case generation
