# Pytest Parametrization Guide

## Basic Parametrization

### Single Parameter
```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

### Multiple Parameters
```python
@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (5, 5, 10),
    (10, -5, 5),
])
def test_addition(x, y, expected):
    assert x + y == expected
```

### Using pytest.param
```python
@pytest.mark.parametrize("value,expected", [
    pytest.param(1, 2, id="one"),
    pytest.param(2, 4, id="two"),
    pytest.param(3, 6, id="three"),
])
def test_with_ids(value, expected):
    assert value * 2 == expected
```

## Parametrize with IDs

### String IDs
```python
@pytest.mark.parametrize("value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
], ids=["one", "two", "three"])
def test_with_string_ids(value, expected):
    assert value * 2 == expected
```

### Function-Generated IDs
```python
def id_func(param):
    if isinstance(param, dict):
        return f"user_{param['name']}"
    return str(param)

@pytest.mark.parametrize("user_data", [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
], ids=id_func)
def test_with_id_function(user_data):
    assert user_data["age"] > 0
```

### Automatic IDs from repr
```python
@pytest.mark.parametrize("data", [
    {"name": "Alice"},
    {"name": "Bob"},
])
def test_with_auto_ids(data):
    # IDs will be generated from repr(data)
    assert "name" in data
```

## Parametrizing Multiple Arguments

### Stacked Parametrize
```python
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [3, 4])
def test_stacked(x, y):
    # Runs 4 times: (1,3), (1,4), (2,3), (2,4)
    assert x * y > 0
```

### Cartesian Product
```python
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", ["a", "b"])
def test_cartesian(x, y):
    # Runs 6 times: all combinations
    assert x > 0
    assert y in ["a", "b"]
```

## Complex Parameter Types

### Parametrize with Dictionaries
```python
@pytest.mark.parametrize("config", [
    {"host": "localhost", "port": 8000},
    {"host": "0.0.0.0", "port": 8080},
])
def test_config(config):
    assert "host" in config
    assert config["port"] > 0
```

### Parametrize with Objects
```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

@pytest.mark.parametrize("user", [
    User("Alice", 30),
    User("Bob", 25),
], ids=lambda u: u.name)
def test_user(user):
    assert user.age > 0
```

### Parametrize with Functions
```python
@pytest.mark.parametrize("func,input,expected", [
    (str.upper, "hello", "HELLO"),
    (str.lower, "HELLO", "hello"),
    (str.title, "hello world", "Hello World"),
])
def test_string_functions(func, input, expected):
    assert func(input) == expected
```

## Indirect Parametrization

### Indirect Fixtures
```python
@pytest.fixture
def user(request):
    # request.param comes from parametrize
    username = request.param
    return create_user(username)

@pytest.mark.parametrize("user", ["alice", "bob"], indirect=True)
def test_user_creation(user):
    assert user.is_active
```

### Indirect with Multiple Parameters
```python
@pytest.fixture
def db(request):
    db_type = request.param
    return connect_to_db(db_type)

@pytest.fixture
def user(request):
    return create_user(request.param)

@pytest.mark.parametrize("db,user", [
    ("sqlite", "alice"),
    ("postgres", "bob"),
], indirect=["db", "user"])
def test_with_indirect(db, user):
    db.save(user)
    assert db.find(user.name) is not None
```

## Parametrize Class Methods

### Parametrize All Methods in Class
```python
@pytest.mark.parametrize("value", [1, 2, 3])
class TestCalculator:
    def test_double(self, value):
        assert value * 2 == value + value

    def test_square(self, value):
        assert value ** 2 == value * value
```

### Parametrize Specific Methods
```python
class TestMath:
    @pytest.mark.parametrize("x,y,expected", [
        (1, 2, 3),
        (5, 5, 10),
    ])
    def test_add(self, x, y, expected):
        assert x + y == expected

    @pytest.mark.parametrize("x,y,expected", [
        (5, 2, 3),
        (10, 5, 5),
    ])
    def test_subtract(self, x, y, expected):
        assert x - y == expected
```

## Parametrize from External Data

### Load from JSON
```python
import json
from pathlib import Path

def load_test_data():
    data_file = Path(__file__).parent / "test_data.json"
    with open(data_file) as f:
        return json.load(f)

@pytest.mark.parametrize("case", load_test_data())
def test_from_json(case):
    assert process(case["input"]) == case["expected"]
```

### Load from CSV
```python
import csv

def load_csv_data():
    with open("test_data.csv") as f:
        reader = csv.DictReader(f)
        return list(reader)

@pytest.mark.parametrize("row", load_csv_data())
def test_from_csv(row):
    assert validate(row["email"])
```

### Load from YAML
```python
import yaml

def load_yaml_data():
    with open("test_data.yaml") as f:
        return yaml.safe_load(f)["test_cases"]

@pytest.mark.parametrize("case", load_yaml_data())
def test_from_yaml(case):
    assert process(case["input"]) == case["output"]
```

## Conditional Parametrization

### Skip Certain Parameters
```python
@pytest.mark.parametrize("value,expected", [
    (1, 2),
    pytest.param(2, 4, marks=pytest.mark.skip(reason="Not ready")),
    (3, 6),
])
def test_with_skip(value, expected):
    assert value * 2 == expected
```

### Expected Failures
```python
@pytest.mark.parametrize("value,expected", [
    (1, 2),
    pytest.param(2, 5, marks=pytest.mark.xfail(reason="Known bug")),
    (3, 6),
])
def test_with_xfail(value, expected):
    assert value * 2 == expected
```

### Platform-Specific Parameters
```python
import sys

@pytest.mark.parametrize("cmd", [
    "ls",
    pytest.param("dir", marks=pytest.mark.skipif(
        sys.platform != "win32",
        reason="Windows only"
    )),
])
def test_commands(cmd):
    assert isinstance(cmd, str)
```

## Combining Parametrize with Fixtures

### Parametrized Fixture
```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database(request):
    db = Database(request.param)
    yield db
    db.close()

def test_query(database):
    # Runs 3 times with different databases
    result = database.query("SELECT 1")
    assert result is not None
```

### Parametrize Test Using Fixture
```python
@pytest.fixture
def calculator():
    return Calculator()

@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (5, 5, 10),
])
def test_addition(calculator, x, y, expected):
    assert calculator.add(x, y) == expected
```

## Advanced Parametrization Patterns

### Nested Parametrization
```python
@pytest.mark.parametrize("outer", [
    pytest.param(
        [1, 2, 3],
        id="list_1"
    ),
    pytest.param(
        [4, 5, 6],
        id="list_2"
    ),
])
@pytest.mark.parametrize("inner", [10, 20])
def test_nested(outer, inner):
    # outer is a list, inner is a number
    assert all(x * inner > 0 for x in outer)
```

### Dynamic Parametrization
```python
def get_test_cases():
    # Dynamically generate test cases
    cases = []
    for i in range(1, 4):
        cases.append((i, i * 2))
    return cases

@pytest.mark.parametrize("value,expected", get_test_cases())
def test_dynamic(value, expected):
    assert value * 2 == expected
```

### Parametrize with Hypothesis
```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_commutative(a, b):
    assert a + b == b + a
```

## Error Testing with Parametrize

### Test Multiple Exceptions
```python
@pytest.mark.parametrize("input,exception", [
    ("", ValueError),
    (None, TypeError),
    (-1, ValueError),
])
def test_exceptions(input, exception):
    with pytest.raises(exception):
        process(input)
```

### Test Exception Messages
```python
@pytest.mark.parametrize("input,message", [
    ("", "Empty input"),
    (None, "None not allowed"),
])
def test_exception_messages(input, message):
    with pytest.raises(ValueError, match=message):
        process(input)
```

## Performance Testing with Parametrize

### Benchmark Different Implementations
```python
def implementation_a(data):
    return sorted(data)

def implementation_b(data):
    return list(sorted(data))

@pytest.mark.parametrize("impl", [implementation_a, implementation_b])
def test_performance(benchmark, impl):
    data = list(range(1000))
    result = benchmark(impl, data)
    assert result is not None
```

### Test with Different Data Sizes
```python
@pytest.mark.parametrize("size", [10, 100, 1000, 10000])
def test_scalability(size):
    data = list(range(size))
    result = process(data)
    assert len(result) == size
```

## Parametrize Best Practices

### Descriptive Test IDs
```python
# Good: Clear test IDs
@pytest.mark.parametrize("email,valid", [
    ("user@example.com", True),
    ("invalid-email", False),
], ids=["valid_email", "invalid_email"])
def test_email_validation(email, valid):
    assert is_valid_email(email) == valid
```

### Group Related Test Cases
```python
# Good: Related cases grouped together
@pytest.mark.parametrize("age,category", [
    (0, "infant"),
    (5, "child"),
    (13, "teenager"),
    (18, "adult"),
    (65, "senior"),
])
def test_age_categories(age, category):
    assert categorize_age(age) == category
```

### Use pytest.param for Complex Cases
```python
@pytest.mark.parametrize("input,expected", [
    pytest.param(
        {"name": "Alice", "age": 30},
        "Alice (30)",
        id="standard_case"
    ),
    pytest.param(
        {"name": "Bob"},
        "Bob (unknown)",
        id="missing_age"
    ),
])
def test_format_user(input, expected):
    assert format_user(input) == expected
```

### Avoid Over-Parametrization
```python
# Avoid: Too many combinations
@pytest.mark.parametrize("a", range(100))
@pytest.mark.parametrize("b", range(100))
def test_too_many(a, b):
    # 10,000 test cases!
    pass

# Better: Use representative samples
@pytest.mark.parametrize("a,b", [
    (0, 0),
    (1, 1),
    (50, 50),
    (99, 99),
])
def test_representative(a, b):
    pass
```

## Debugging Parametrized Tests

### Run Specific Parameter
```bash
# Run test with specific parameter by test ID
pytest test_file.py::test_function[param_id]

# Example
pytest test_math.py::test_addition[1-2-3]
```

### Verbose Output
```bash
# Show parameter values in output
pytest -v

# Show even more detail
pytest -vv
```

### Print Parameter Values
```python
@pytest.mark.parametrize("value", [1, 2, 3])
def test_with_print(value):
    print(f"Testing with value: {value}")
    assert value > 0
```
