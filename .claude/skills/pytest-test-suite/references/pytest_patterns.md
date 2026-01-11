# Pytest Patterns and Best Practices

## Test Organization

### Directory Structure
```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── api.py
│       └── models.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── __init__.py
    │   ├── test_models.py
    │   └── test_utils.py
    ├── integration/
    │   ├── __init__.py
    │   └── test_api_integration.py
    └── e2e/
        ├── __init__.py
        └── test_user_flows.py
```

### Naming Conventions
- Test files: `test_*.py` or `*_test.py`
- Test functions: `test_*`
- Test classes: `Test*`
- Fixtures: descriptive names (no prefix needed)

## Test Structure Patterns

### AAA Pattern (Arrange-Act-Assert)
```python
def test_user_creation():
    # Arrange
    user_data = {"name": "Alice", "email": "alice@example.com"}

    # Act
    user = User.create(user_data)

    # Assert
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
```

### Given-When-Then (BDD Style)
```python
def test_order_processing():
    # Given
    order = Order(items=[Item("widget", price=10)])
    payment = Payment(amount=10)

    # When
    result = process_order(order, payment)

    # Then
    assert result.status == "completed"
    assert order.is_paid is True
```

## Common Test Patterns

### Testing Exceptions
```python
import pytest

def test_invalid_input_raises_error():
    with pytest.raises(ValueError, match="Invalid input"):
        process_data("")

def test_custom_exception():
    with pytest.raises(CustomError) as exc_info:
        risky_operation()

    assert exc_info.value.code == 400
```

### Testing Warnings
```python
def test_deprecation_warning():
    with pytest.warns(DeprecationWarning):
        legacy_function()
```

### Approximate Comparisons
```python
def test_float_calculation():
    result = calculate_pi()
    assert result == pytest.approx(3.14159, rel=1e-5)
```

### Testing Multiple Assertions
```python
def test_user_profile():
    user = create_user("Alice", 30)

    # Multiple related assertions
    assert user.name == "Alice"
    assert user.age == 30
    assert user.is_active is True
    assert user.created_at is not None
```

## Markers for Test Organization

### Built-in Markers
```python
@pytest.mark.skip(reason="Feature not implemented")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_pattern_matching():
    pass

@pytest.mark.xfail(reason="Known bug in library")
def test_known_issue():
    pass

@pytest.mark.slow
def test_large_dataset_processing():
    pass
```

### Custom Markers (defined in pytest.ini)
```python
@pytest.mark.database
def test_db_connection():
    pass

@pytest.mark.api
def test_endpoint():
    pass

@pytest.mark.smoke
def test_critical_path():
    pass
```

Run specific markers:
```bash
pytest -m database  # Run only database tests
pytest -m "not slow"  # Skip slow tests
pytest -m "smoke or critical"  # Run smoke OR critical tests
```

## Test Data Management

### Inline Test Data
```python
def test_user_validation():
    valid_user = {"name": "Alice", "age": 30}
    invalid_user = {"name": "", "age": -5}

    assert validate_user(valid_user) is True
    assert validate_user(invalid_user) is False
```

### Fixture-Based Test Data
```python
@pytest.fixture
def sample_users():
    return [
        User("Alice", "alice@example.com"),
        User("Bob", "bob@example.com"),
    ]

def test_user_list(sample_users):
    assert len(sample_users) == 2
```

### External Test Data Files
```python
import json
from pathlib import Path

@pytest.fixture
def test_data():
    data_file = Path(__file__).parent / "data" / "test_users.json"
    with open(data_file) as f:
        return json.load(f)

def test_data_processing(test_data):
    result = process(test_data)
    assert result["status"] == "success"
```

## Assertion Patterns

### Basic Assertions
```python
assert value == expected
assert value is True
assert value is None
assert value in collection
assert isinstance(value, ExpectedType)
```

### Custom Assertion Messages
```python
def test_calculation():
    result = complex_calculation()
    assert result > 0, f"Expected positive result, got {result}"
```

### Multiple Conditions
```python
def test_user_state():
    user = get_user()
    assert all([
        user.is_active,
        user.email_verified,
        user.profile_complete
    ]), "User should be fully active"
```

## Test Isolation

### Setup and Teardown (Function Level)
```python
def setup_function():
    """Run before each test function"""
    initialize_database()

def teardown_function():
    """Run after each test function"""
    cleanup_database()

def test_something():
    # Test code here
    pass
```

### Setup and Teardown (Class Level)
```python
class TestUserAPI:
    @classmethod
    def setup_class(cls):
        """Run once before all tests in class"""
        cls.db = connect_to_database()

    @classmethod
    def teardown_class(cls):
        """Run once after all tests in class"""
        cls.db.close()

    def setup_method(self):
        """Run before each test method"""
        self.db.clear()

    def teardown_method(self):
        """Run after each test method"""
        self.db.rollback()
```

## Conditional Testing

### Platform-Specific Tests
```python
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature():
    pass

@pytest.mark.skipif(not shutil.which("docker"), reason="Docker not available")
def test_docker_integration():
    pass
```

### Environment-Based Tests
```python
@pytest.mark.skipif(os.getenv("CI") is None, reason="Only in CI")
def test_ci_environment():
    pass
```

## Coverage Best Practices

### What to Test
- Public API functions and methods
- Edge cases and boundary conditions
- Error handling paths
- Business logic and calculations
- Integration points

### What NOT to Test
- Third-party library internals
- Simple getters/setters without logic
- Configuration files
- Trivial property access

## Performance Testing

### Time Limits
```python
@pytest.mark.timeout(5)  # Requires pytest-timeout
def test_response_time():
    result = slow_operation()
    assert result is not None
```

### Benchmark Tests
```python
def test_algorithm_performance(benchmark):
    # Requires pytest-benchmark
    result = benchmark(expensive_function, data)
    assert result is not None
```

## Debugging Tests

### Show Print Output
```bash
pytest -s  # Show print statements
pytest --capture=no  # Same as -s
```

### Drop into Debugger
```python
def test_complex_logic():
    result = complex_function()
    breakpoint()  # Python 3.7+
    assert result == expected
```

### Verbose Output
```bash
pytest -v  # Verbose
pytest -vv  # Extra verbose
pytest -vv --tb=long  # Long tracebacks
```

### Run Last Failed Tests
```bash
pytest --lf  # Last failed
pytest --ff  # Failed first, then others
```

## Test Dependencies

### Sequential Tests (use sparingly)
```python
@pytest.mark.dependency()
def test_step_1():
    pass

@pytest.mark.dependency(depends=["test_step_1"])
def test_step_2():
    pass
```

**Note:** Tests should generally be independent. Use fixtures for shared setup instead.
