# Pytest Mocking Guide

## Mocking with unittest.mock

### Basic Mock Objects
```python
from unittest.mock import Mock

def test_basic_mock():
    mock = Mock()

    # Configure return value
    mock.return_value = 42
    assert mock() == 42

    # Configure method return value
    mock.get_data.return_value = {"key": "value"}
    assert mock.get_data() == {"key": "value"}

    # Verify calls
    mock.get_data()
    mock.get_data.assert_called_once()
```

### Mock with Side Effects
```python
def test_side_effects():
    mock = Mock()

    # Return different values on successive calls
    mock.side_effect = [1, 2, 3]
    assert mock() == 1
    assert mock() == 2
    assert mock() == 3

    # Raise exceptions
    mock.side_effect = ValueError("Invalid input")
    with pytest.raises(ValueError):
        mock()
```

### Mock Attributes and Properties
```python
def test_mock_attributes():
    mock = Mock()
    mock.name = "TestObject"
    mock.value = 100

    assert mock.name == "TestObject"
    assert mock.value == 100

def test_mock_property():
    mock = Mock()
    type(mock).status = PropertyMock(return_value="active")

    assert mock.status == "active"
```

## Patching

### Patch Functions
```python
from unittest.mock import patch

# Patch as decorator
@patch("mymodule.external_api_call")
def test_function(mock_api):
    mock_api.return_value = {"status": "success"}

    result = my_function()
    assert result["status"] == "success"
    mock_api.assert_called_once()

# Patch as context manager
def test_context_manager():
    with patch("mymodule.external_api_call") as mock_api:
        mock_api.return_value = {"status": "success"}
        result = my_function()
        assert result["status"] == "success"
```

### Patch Methods
```python
@patch.object(DatabaseConnection, "query")
def test_database_query(mock_query):
    mock_query.return_value = [{"id": 1, "name": "Alice"}]

    db = DatabaseConnection()
    users = db.query("SELECT * FROM users")

    assert len(users) == 1
    assert users[0]["name"] == "Alice"
```

### Patch Multiple
```python
@patch("mymodule.function_a")
@patch("mymodule.function_b")
@patch("mymodule.function_c")
def test_multiple_patches(mock_c, mock_b, mock_a):
    # Note: patches are applied bottom-up
    mock_a.return_value = "A"
    mock_b.return_value = "B"
    mock_c.return_value = "C"

    result = my_combined_function()
    assert result is not None

# Alternative: patch.multiple
@patch.multiple("mymodule",
    function_a=Mock(return_value="A"),
    function_b=Mock(return_value="B"),
    function_c=Mock(return_value="C")
)
def test_multiple_patches_v2():
    result = my_combined_function()
    assert result is not None
```

### Patch Dictionary
```python
@patch.dict(os.environ, {"API_KEY": "test_key", "ENV": "test"})
def test_environment():
    assert os.getenv("API_KEY") == "test_key"
    assert os.getenv("ENV") == "test"

# Clear dictionary
@patch.dict(os.environ, {}, clear=True)
def test_empty_environment():
    assert os.getenv("PATH") is None
```

## MagicMock

### MagicMock for Magic Methods
```python
from unittest.mock import MagicMock

def test_magic_mock():
    mock = MagicMock()

    # Supports magic methods
    mock.__len__.return_value = 5
    assert len(mock) == 5

    mock.__getitem__.return_value = "value"
    assert mock["key"] == "value"

    # Context manager support
    with mock as m:
        m.do_something()
    mock.__enter__.assert_called_once()
    mock.__exit__.assert_called_once()
```

### Iterable Mock
```python
def test_iterable_mock():
    mock = MagicMock()
    mock.__iter__.return_value = iter([1, 2, 3])

    result = list(mock)
    assert result == [1, 2, 3]
```

## pytest-mock Plugin

### mocker Fixture
```python
# Install: pip install pytest-mock

def test_with_mocker(mocker):
    # Simplified patching
    mock = mocker.patch("mymodule.external_call")
    mock.return_value = "mocked"

    result = my_function()
    assert result == "mocked"

def test_spy(mocker):
    # Spy wraps real object
    spy = mocker.spy(MyClass, "method")

    obj = MyClass()
    obj.method(1, 2)

    # Real method was called
    spy.assert_called_once_with(1, 2)
```

### mocker.patch Variants
```python
def test_mocker_variants(mocker):
    # Patch object
    mock = mocker.patch.object(MyClass, "method")

    # Patch multiple
    mocker.patch.multiple("mymodule",
        func_a=mocker.DEFAULT,
        func_b=mocker.DEFAULT
    )

    # Patch dictionary
    mocker.patch.dict(os.environ, {"KEY": "value"})
```

## Mock Assertions

### Call Assertions
```python
def test_call_assertions():
    mock = Mock()

    mock(1, 2, key="value")

    # Assert called
    mock.assert_called()
    mock.assert_called_once()
    mock.assert_called_with(1, 2, key="value")
    mock.assert_called_once_with(1, 2, key="value")

    # Assert any call
    mock(3, 4)
    mock.assert_any_call(1, 2, key="value")
    mock.assert_any_call(3, 4)

    # Check call count
    assert mock.call_count == 2
```

### Call List Inspection
```python
def test_call_list():
    mock = Mock()

    mock(1)
    mock(2)
    mock(3)

    # Inspect all calls
    assert len(mock.call_args_list) == 3
    assert mock.call_args_list[0][0] == (1,)
    assert mock.call_args_list[1][0] == (2,)

    # Last call
    assert mock.call_args[0] == (3,)
```

### Not Called Assertions
```python
def test_not_called():
    mock = Mock()

    mock.assert_not_called()

    mock()
    with pytest.raises(AssertionError):
        mock.assert_not_called()
```

## Mocking Common Scenarios

### Mocking HTTP Requests
```python
@patch("requests.get")
def test_api_call(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "value"}

    mock_get.return_value = mock_response

    response = fetch_data("http://api.example.com")
    assert response["data"] == "value"
    mock_get.assert_called_once_with("http://api.example.com")
```

### Mocking Database
```python
@patch("myapp.database.connect")
def test_database_operation(mock_connect):
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [("Alice",), ("Bob",)]

    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    users = get_all_users()
    assert users == ["Alice", "Bob"]
```

### Mocking File Operations
```python
from unittest.mock import mock_open

@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_file_read(mock_file):
    result = read_config("config.txt")
    assert "file content" in result
    mock_file.assert_called_once_with("config.txt")

@patch("builtins.open", new_callable=mock_open)
def test_file_write(mock_file):
    write_data("output.txt", "test data")

    mock_file.assert_called_once_with("output.txt", "w")
    handle = mock_file()
    handle.write.assert_called_once_with("test data")
```

### Mocking datetime
```python
from datetime import datetime

@patch("mymodule.datetime")
def test_current_time(mock_datetime):
    fake_now = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = fake_now

    result = get_timestamp()
    assert result == fake_now
```

### Mocking External Dependencies
```python
@patch("stripe.Customer.create")
def test_payment_processing(mock_customer_create):
    mock_customer_create.return_value = {
        "id": "cus_123",
        "email": "user@example.com"
    }

    customer = create_customer("user@example.com")
    assert customer["id"] == "cus_123"
```

## Mock Specifications

### spec Parameter
```python
def test_with_spec():
    # Mock will only allow attributes/methods from the spec
    mock = Mock(spec=MyClass)

    # This works if MyClass has 'valid_method'
    mock.valid_method()

    # This raises AttributeError
    with pytest.raises(AttributeError):
        mock.invalid_method()
```

### autospec
```python
@patch("mymodule.MyClass", autospec=True)
def test_autospec(mock_class):
    # Automatically creates spec from the class
    instance = mock_class.return_value
    instance.method.return_value = "result"

    # Method signature is enforced
    result = instance.method(expected_arg)
    assert result == "result"
```

## Advanced Mocking Patterns

### Chained Calls
```python
def test_chained_calls():
    mock = Mock()
    mock.method_a.return_value.method_b.return_value.method_c.return_value = "final"

    result = mock.method_a().method_b().method_c()
    assert result == "final"
```

### Callable Mock
```python
def test_callable_mock():
    mock = Mock(return_value=42)

    # Mock itself is callable
    assert mock() == 42
    assert mock(1, 2, 3) == 42
```

### Mock Class Instances
```python
@patch("mymodule.MyClass")
def test_class_instance(MockClass):
    # Configure the instance
    instance = MockClass.return_value
    instance.method.return_value = "result"

    # Use the class
    obj = MyClass()
    result = obj.method()

    assert result == "result"
    MockClass.assert_called_once()
```

### Partial Mocking
```python
def test_partial_mock(mocker):
    # Mock only specific methods, keep others real
    real_obj = MyClass()
    mocker.patch.object(real_obj, "external_call", return_value="mocked")

    # external_call is mocked, other methods work normally
    result = real_obj.do_something()
    assert result is not None
```

## Mock Best Practices

### Mock at the Right Level
```python
# Good: Mock at the boundary
@patch("myapp.services.external_api.call")
def test_service(mock_api):
    # Test service logic, mock external API
    pass

# Avoid: Mocking internal implementation details
@patch("myapp.services.user_service._internal_helper")
def test_service(mock_helper):
    # Too granular, tests become fragile
    pass
```

### Reset Mocks Between Tests
```python
@pytest.fixture
def mock_api():
    with patch("mymodule.api_call") as mock:
        yield mock

def test_first(mock_api):
    mock_api.return_value = "A"
    assert call_function() == "A"

def test_second(mock_api):
    # Mock is automatically reset between tests
    mock_api.return_value = "B"
    assert call_function() == "B"
```

### Use return_value vs side_effect
```python
# return_value: For consistent results
mock.method.return_value = "always this"

# side_effect: For dynamic behavior
def dynamic_behavior(arg):
    return f"processed {arg}"

mock.method.side_effect = dynamic_behavior

# side_effect: For sequences
mock.method.side_effect = [1, 2, 3, ValueError("error")]
```

### Verify Important Interactions
```python
def test_important_calls():
    mock = Mock()

    perform_operation(mock)

    # Verify critical interactions
    mock.save.assert_called_once()
    mock.notify.assert_called_with(status="success")

    # Don't verify every single call
    # Focus on behavior, not implementation
```

## Common Pitfalls

### Patching in Wrong Module
```python
# mymodule.py imports datetime
from datetime import datetime

# Wrong: Patches datetime module, not mymodule's import
@patch("datetime.datetime")
def test_wrong(mock):
    pass

# Correct: Patch where it's used
@patch("mymodule.datetime")
def test_correct(mock):
    pass
```

### Order of Decorators
```python
# Decorators are applied bottom-up
@patch("module.c")
@patch("module.b")
@patch("module.a")
def test_order(mock_a, mock_b, mock_c):
    # Parameters match decorator order (reversed)
    pass
```

### Mocking Immutable Built-ins
```python
# Can't patch built-in types directly
# Use patch where they're used in your code

# Wrong
@patch("int")
def test_wrong(mock_int):
    pass

# Correct
@patch("mymodule.int")
def test_correct(mock_int):
    pass
```
