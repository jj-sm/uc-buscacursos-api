"""
Pytest configuration and fixtures for API tests
"""
import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_env(tmp_path_factory):
    """
    Configure test environment with temporary databases
    """
    # Use temporary directories for test databases
    tmp_dir = tmp_path_factory.mktemp("test_data")
    
    os.environ["DEBUG"] = "1"
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_dir / 'test.db'}"
    os.environ["AUTH_DATABASE_URL"] = f"sqlite:///{tmp_dir / 'test_auth.db'}"
    
    yield {
        "tmp_dir": tmp_dir,
        "db_url": f"sqlite:///{tmp_dir / 'test.db'}",
        "auth_db_url": f"sqlite:///{tmp_dir / 'test_auth.db'}",
    }


@pytest.fixture
def client():
    """
    Create a FastAPI TestClient for testing
    """
    from app.main import app
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """
    Provide a valid test API key (would be created in real scenarios)
    """
    return "test-api-key-12345"


@pytest.fixture
def invalid_api_key():
    """
    Provide an invalid test API key
    """
    return "invalid-key-abc123"


@pytest.fixture
def api_headers(valid_api_key):
    """
    Provide valid API headers
    """
    return {"X-API-Key": valid_api_key}


@pytest.fixture
def invalid_api_headers(invalid_api_key):
    """
    Provide invalid API headers
    """
    return {"X-API-Key": invalid_api_key}


@pytest.fixture
def test_user_data():
    """
    Provide test data for creating users/resources
    """
    return {
        "name": "Test Resource",
        "description": "A test resource for unit testing",
        "email": "test@example.com",
    }


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset app state before each test
    """
    yield
    # Cleanup after test if needed


def pytest_configure(config):
    """
    Configure pytest with custom settings
    """
    # Add parent directory to path for imports
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers
    """
    for item in items:
        # Auto-mark slow tests
        if "response_time" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Auto-mark auth tests
        if "auth" in item.nodeid.lower():
            item.add_marker(pytest.mark.auth)
        
        # Auto-mark health tests
        if "health" in item.nodeid.lower():
            item.add_marker(pytest.mark.health)
