"""
Unit test template.

Unit tests focus on testing individual functions or methods in isolation.
They should be fast and not depend on external resources.
"""

import pytest
# from myapp.module import function_to_test


# ============================================================================
# Basic unit tests
# ============================================================================

def test_basic_assertion():
    """Test with simple assertion."""
    result = 2 + 2
    assert result == 4


def test_with_setup():
    """Test with local setup."""
    # Arrange
    data = {"name": "Alice", "age": 30}

    # Act
    result = data["name"].upper()

    # Assert
    assert result == "ALICE"


# ============================================================================
# Tests with fixtures
# ============================================================================

@pytest.fixture
def sample_user():
    """Fixture providing sample user data."""
    return {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "active": True
    }


def test_with_fixture(sample_user):
    """Test using a fixture."""
    assert sample_user["name"] == "Alice"
    assert sample_user["active"] is True


# ============================================================================
# Parametrized tests
# ============================================================================

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
], ids=["one", "two", "three", "zero", "negative"])
def test_double_function(input, expected):
    """Test function with multiple input values."""
    result = input * 2
    assert result == expected


@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("invalid.email", False),
    ("@example.com", False),
    ("user@", False),
], ids=["valid", "no_at", "no_user", "no_domain"])
def test_email_validation(email, is_valid):
    """Test email validation with different inputs."""
    # Replace with your actual validation function
    def is_valid_email(email):
        return "@" in email and "." in email.split("@")[-1]

    assert is_valid_email(email) == is_valid


# ============================================================================
# Exception testing
# ============================================================================

def test_exception_raised():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError):
        raise ValueError("Invalid input")


def test_exception_message():
    """Test exception message content."""
    with pytest.raises(ValueError, match="Invalid input"):
        raise ValueError("Invalid input")


def test_exception_attributes():
    """Test exception attributes."""
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("Error message")

    assert str(exc_info.value) == "Error message"


# ============================================================================
# Testing with mocks
# ============================================================================

def test_with_mock(mocker):
    """
    Test using pytest-mock.
    Requires: pip install pytest-mock
    """
    # Mock a function
    mock_function = mocker.Mock(return_value=42)

    # Use the mock
    result = mock_function()

    # Verify
    assert result == 42
    mock_function.assert_called_once()


def test_patching_function(mocker):
    """Test by patching an external function."""
    # Patch a function from another module
    # mock_call = mocker.patch("myapp.external.api_call")
    # mock_call.return_value = {"status": "success"}
    #
    # # Call function that uses api_call
    # result = my_function()
    #
    # # Verify
    # assert result["status"] == "success"
    # mock_call.assert_called_once()
    pass


# ============================================================================
# Test class organization
# ============================================================================

class TestUserOperations:
    """Group related tests in a class."""

    @pytest.fixture
    def user(self):
        """Fixture available to all methods in this class."""
        return {"name": "Alice", "role": "admin"}

    def test_user_name(self, user):
        """Test user name."""
        assert user["name"] == "Alice"

    def test_user_role(self, user):
        """Test user role."""
        assert user["role"] == "admin"

    @pytest.mark.parametrize("role", ["admin", "user", "guest"])
    def test_different_roles(self, role):
        """Test with different roles."""
        assert role in ["admin", "user", "guest"]


# ============================================================================
# Edge cases and boundary testing
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self):
        """Test with empty string."""
        result = "".upper()
        assert result == ""

    def test_none_value(self):
        """Test with None value."""
        value = None
        assert value is None

    def test_zero(self):
        """Test with zero."""
        result = 0 * 100
        assert result == 0

    def test_negative_number(self):
        """Test with negative number."""
        result = -5 * 2
        assert result == -10

    def test_large_number(self):
        """Test with large number."""
        result = 10**100
        assert result > 0


# ============================================================================
# Approximate comparisons for floats
# ============================================================================

def test_float_comparison():
    """Test floating point comparison."""
    result = 0.1 + 0.2
    assert result == pytest.approx(0.3)


def test_float_with_tolerance():
    """Test float with custom tolerance."""
    result = 3.14159
    assert result == pytest.approx(3.14, rel=1e-2)


# ============================================================================
# Testing collections
# ============================================================================

def test_list_operations():
    """Test list operations."""
    items = [1, 2, 3, 4, 5]

    assert len(items) == 5
    assert 3 in items
    assert items[0] == 1
    assert items[-1] == 5


def test_dictionary_operations():
    """Test dictionary operations."""
    data = {"name": "Alice", "age": 30}

    assert "name" in data
    assert data["name"] == "Alice"
    assert len(data) == 2


# ============================================================================
# Markers for test organization
# ============================================================================

@pytest.mark.slow
def test_slow_operation():
    """Test marked as slow."""
    # Simulate slow operation
    import time
    time.sleep(0.1)
    assert True


@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """Test for future feature."""
    pass


@pytest.mark.skipif(True, reason="Conditional skip")
def test_conditional():
    """Test that is conditionally skipped."""
    pass


@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    """Test with known failure."""
    assert False


# ============================================================================
# Custom assertions and helper functions
# ============================================================================

def assert_valid_user(user):
    """Custom assertion helper."""
    assert "name" in user
    assert "email" in user
    assert user["name"] != ""
    assert "@" in user["email"]


def test_with_custom_assertion():
    """Test using custom assertion helper."""
    user = {"name": "Alice", "email": "alice@example.com"}
    assert_valid_user(user)
