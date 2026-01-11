# Pytest Fixtures Guide

## Fixture Basics

### Simple Fixture
```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "email": "alice@example.com"}

def test_user_data(sample_user):
    assert sample_user["name"] == "Alice"
```

### Fixture with Setup and Teardown
```python
@pytest.fixture
def database_connection():
    # Setup
    conn = connect_to_database()
    yield conn
    # Teardown
    conn.close()

def test_query(database_connection):
    result = database_connection.query("SELECT * FROM users")
    assert result is not None
```

## Fixture Scopes

### Function Scope (Default)
```python
@pytest.fixture(scope="function")
def temp_file():
    """Created and destroyed for each test function"""
    f = open("temp.txt", "w")
    yield f
    f.close()
    os.remove("temp.txt")
```

### Class Scope
```python
@pytest.fixture(scope="class")
def database():
    """Shared across all methods in a test class"""
    db = Database()
    yield db
    db.cleanup()

class TestUserOperations:
    def test_create_user(self, database):
        user = database.create_user("Alice")
        assert user is not None

    def test_find_user(self, database):
        user = database.find_user("Alice")
        assert user is not None
```

### Module Scope
```python
@pytest.fixture(scope="module")
def api_client():
    """Created once per test module"""
    client = APIClient()
    client.authenticate()
    yield client
    client.close()
```

### Session Scope
```python
@pytest.fixture(scope="session")
def docker_container():
    """Created once for entire test session"""
    container = start_docker_container()
    yield container
    container.stop()
```

## Fixture Dependencies

### Fixtures Using Other Fixtures
```python
@pytest.fixture
def database():
    return Database()

@pytest.fixture
def user_repository(database):
    return UserRepository(database)

@pytest.fixture
def user_service(user_repository):
    return UserService(user_repository)

def test_create_user(user_service):
    user = user_service.create("Alice")
    assert user.name == "Alice"
```

## Fixture Factories

### Basic Factory Pattern
```python
@pytest.fixture
def make_user():
    def _make_user(name, email=None):
        return User(name=name, email=email or f"{name}@example.com")
    return _make_user

def test_multiple_users(make_user):
    alice = make_user("Alice")
    bob = make_user("Bob", "bob@work.com")
    assert alice.email == "alice@example.com"
    assert bob.email == "bob@work.com"
```

### Factory with Cleanup
```python
@pytest.fixture
def user_factory(database):
    created_users = []

    def _create_user(name):
        user = database.create_user(name)
        created_users.append(user)
        return user

    yield _create_user

    # Cleanup all created users
    for user in created_users:
        database.delete_user(user.id)
```

## Autouse Fixtures

### Automatic Setup
```python
@pytest.fixture(autouse=True)
def reset_database():
    """Runs before every test automatically"""
    database.clear()
    database.seed_test_data()

def test_user_count():
    # Database is already reset
    assert database.count_users() == 0
```

### Module-Level Autouse
```python
@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    os.environ["ENV"] = "test"
    yield
    del os.environ["ENV"]
```

## Parametrized Fixtures

### Multiple Fixture Values
```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database(request):
    """Test will run once for each database type"""
    db = Database(request.param)
    yield db
    db.close()

def test_query(database):
    # This test runs 3 times, once for each database
    result = database.query("SELECT 1")
    assert result is not None
```

### Parametrized with IDs
```python
@pytest.fixture(params=[
    ("Alice", 30),
    ("Bob", 25),
    ("Charlie", 35),
], ids=["Alice-30", "Bob-25", "Charlie-35"])
def user_data(request):
    return request.param

def test_user_creation(user_data):
    name, age = user_data
    user = User(name, age)
    assert user.name == name
    assert user.age == age
```

## Fixture Request Object

### Accessing Test Information
```python
@pytest.fixture
def test_context(request):
    print(f"Running test: {request.node.name}")
    print(f"Test module: {request.module.__name__}")
    print(f"Test function: {request.function.__name__}")
    return {"test_name": request.node.name}
```

### Dynamic Fixture Behavior
```python
@pytest.fixture
def database(request):
    # Access markers
    if "slow" in request.keywords:
        return SlowDatabase()
    return FastDatabase()
```

## Common Fixture Patterns

### Temporary Directory
```python
import tempfile
import shutil

@pytest.fixture
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

def test_file_creation(temp_dir):
    file_path = os.path.join(temp_dir, "test.txt")
    with open(file_path, "w") as f:
        f.write("test")
    assert os.path.exists(file_path)
```

### Mock Configuration
```python
@pytest.fixture
def mock_config():
    return {
        "api_url": "http://localhost:8000",
        "timeout": 30,
        "retry_count": 3
    }

def test_api_client(mock_config):
    client = APIClient(mock_config)
    assert client.base_url == "http://localhost:8000"
```

### Test Data Loader
```python
@pytest.fixture
def load_json():
    def _load(filename):
        path = Path(__file__).parent / "data" / filename
        with open(path) as f:
            return json.load(f)
    return _load

def test_process_data(load_json):
    data = load_json("users.json")
    result = process_users(data)
    assert len(result) > 0
```

### Database Transaction Fixture
```python
@pytest.fixture
def db_session():
    session = Session()
    session.begin()
    yield session
    session.rollback()
    session.close()

def test_user_creation(db_session):
    user = User(name="Alice")
    db_session.add(user)
    db_session.flush()  # Not committed

    assert user.id is not None
    # Rollback happens automatically
```

### Mocked Time
```python
from unittest.mock import patch
from datetime import datetime

@pytest.fixture
def fixed_time():
    fake_time = datetime(2024, 1, 1, 12, 0, 0)
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_time
        yield fake_time

def test_timestamp(fixed_time):
    result = create_timestamp()
    assert result == fixed_time
```

## Fixture Best Practices

### Keep Fixtures Focused
```python
# Good: Single responsibility
@pytest.fixture
def user():
    return User("Alice")

@pytest.fixture
def authenticated_session():
    return Session(authenticated=True)

# Avoid: Kitchen sink fixture
@pytest.fixture
def everything():
    return {
        "user": User("Alice"),
        "session": Session(),
        "database": Database(),
        "api_client": APIClient()
    }
```

### Use Descriptive Names
```python
# Good
@pytest.fixture
def authenticated_admin_user():
    return User("admin", role="admin", authenticated=True)

# Avoid
@pytest.fixture
def user1():
    return User("admin", role="admin", authenticated=True)
```

### Minimize Fixture Dependencies
```python
# Good: Independent fixtures
@pytest.fixture
def database():
    return Database()

@pytest.fixture
def cache():
    return Cache()

# Less ideal: Long dependency chain
@pytest.fixture
def a():
    return A()

@pytest.fixture
def b(a):
    return B(a)

@pytest.fixture
def c(b):
    return C(b)

@pytest.fixture
def d(c):
    return D(c)  # Too deep
```

## Conftest.py Organization

### Project-Wide Fixtures
```python
# conftest.py at project root
import pytest

@pytest.fixture(scope="session")
def config():
    """Available to all tests"""
    return load_config()

@pytest.fixture
def database():
    """Available to all tests"""
    db = Database()
    yield db
    db.cleanup()
```

### Module-Specific Fixtures
```python
# tests/api/conftest.py
import pytest

@pytest.fixture
def api_client():
    """Only available to tests in tests/api/"""
    return APIClient()
```

### Fixture Discovery Order
Pytest searches for fixtures in this order:
1. Test module
2. conftest.py in same directory
3. conftest.py in parent directories
4. Built-in pytest fixtures

## Built-in Pytest Fixtures

### tmp_path (Recommended)
```python
def test_file_operations(tmp_path):
    # tmp_path is a pathlib.Path object
    file = tmp_path / "test.txt"
    file.write_text("content")
    assert file.read_text() == "content"
```

### tmp_path_factory (Session-scoped)
```python
@pytest.fixture(scope="session")
def shared_data_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("shared_data")
```

### capsys (Capture stdout/stderr)
```python
def test_print_output(capsys):
    print("Hello")
    print("World", file=sys.stderr)

    captured = capsys.readouterr()
    assert captured.out == "Hello\n"
    assert captured.err == "World\n"
```

### monkeypatch (Modify objects/environment)
```python
def test_environment_variable(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_key")
    assert os.getenv("API_KEY") == "test_key"

def test_attribute_modification(monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda x: True)
    assert os.path.exists("fake_file")
```

### request (Fixture metadata)
```python
@pytest.fixture
def example(request):
    print(f"Test: {request.node.name}")
    print(f"Markers: {list(request.node.iter_markers())}")
```
