# Testing Guide for Universal API Template

This guide covers how to run, understand, and extend the test suite for the Universal API Template.

## Quick Start

### Install Test Dependencies

```bash
# Install development dependencies (includes testing tools)
./scripts/setup.sh
pip install -r requirements-dev.txt

# Or install just pytest and essentials
pip install pytest pytest-cov pytest-asyncio httpx
```

### Run Tests Locally

```bash
# Run all tests
./scripts/test.sh

# Run with verbose output
./scripts/test.sh -v

# Run specific test file
./scripts/test.sh test/test_api_endpoints.py -v

# Run specific test class
./scripts/test.sh test/test_api_endpoints.py::TestHealthCheck -v

# Run specific test
./scripts/test.sh test/test_api_endpoints.py::TestHealthCheck::test_health_check -v
```

### Run Tests with Coverage

```bash
# Generate coverage report
./scripts/test-coverage.sh

# Generate HTML coverage report
./scripts/test-coverage.sh
# Open htmlcov/index.html in your browser
```

### Run Tests by Category

```bash
# Run only health check tests
./scripts/test.sh -m health -v

# Run only authentication tests
./scripts/test.sh -m auth -v

# Run only integration tests
./scripts/test.sh -m integration -v

# Run all tests except slow tests
./scripts/test.sh -m "not slow" -v

# Run tests in parallel (faster)
./scripts/test.sh -n auto
```

## Test Structure

### Test Files

- **test_api_endpoints.py**: Main test suite for API endpoints
  - Health check tests
  - Root endpoint tests
  - Template router tests
  - Airports router tests
  - Admin router tests
  - Documentation endpoint tests
  - CORS configuration tests
  - Error handling tests
  - Response format tests
  - Performance tests
  - API structure tests

### Test Classes

| Class | Purpose | Tests |
|-------|---------|-------|
| `TestHealthCheck` | Health status endpoint | `/health` response code |
| `TestRootEndpoint` | API root endpoint | `/` info endpoint |
| `TestTemplateRouter` | Template router examples | Endpoints, auth, rate limiting |
| `TestAirportsRouter` | Airports router examples | Endpoint availability |
| `TestAdminRouter` | Admin management endpoints | Admin functionality |
| `TestDocumentation` | API documentation | Swagger, ReDoc, OpenAPI schema |
| `TestCORSHeaders` | CORS configuration | CORS header validation |
| `TestErrorHandling` | Error responses | 404, 405, etc. |
| `TestResponseFormats` | Response standards | JSON format, error structure |
| `TestPerformance` | Response time | Performance benchmarks |
| `TestApiStructure` | API conventions | Router registration |

## Fixtures

Common pytest fixtures available for tests:

```python
@pytest.fixture
def client():
    """FastAPI TestClient with full app context"""
    
@pytest.fixture
def api_headers(valid_api_key):
    """Valid API key headers"""
    
@pytest.fixture
def invalid_api_headers(invalid_api_key):
    """Invalid API key headers"""
    
@pytest.fixture
def test_user_data():
    """Sample test data for resources"""
    
@pytest.fixture
def test_env(tmp_path_factory):
    """Temporary test environment with isolated databases"""
```

## Writing New Tests

### Basic Test Example

```python
import pytest
from fastapi.testclient import TestClient

def test_new_endpoint(client):
    """Test a new endpoint"""
    response = client.get("/api/new-endpoint/")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Test with Authentication

```python
def test_protected_endpoint(client, api_headers):
    """Test endpoint that requires authentication"""
    response = client.get(
        "/api/protected/",
        headers=api_headers
    )
    assert response.status_code == 200
```

### Test with Parameters

```python
@pytest.mark.parametrize("path,expected_status", [
    ("/health", 200),
    ("/docs", 200),
    ("/redoc", 200),
    ("/nonexistent", 404),
])
def test_multiple_paths(client, path, expected_status):
    """Test multiple endpoints at once"""
    response = client.get(path)
    assert response.status_code == expected_status
```

### Marking Tests

```python
@pytest.mark.health
def test_health_endpoint(client):
    """Test marked with health category"""
    ...

@pytest.mark.slow
def test_slow_operation(client):
    """Test marked as slow (can be skipped)"""
    ...

@pytest.mark.integration
def test_full_workflow(client):
    """Integration test spanning multiple components"""
    ...
```

## CI/CD Integration

Tests are automatically run by GitHub Actions on:

- **Push to main or develop**: Full test suite
- **Pull requests**: Full test suite + coverage
- **Manual trigger**: `workflow_dispatch`

### Test Workflow Jobs

1. **Test** (Matrix: Python 3.8-3.12)
   - Install dependencies
   - Run pytest with coverage
   - Upload coverage reports

2. **Lint**
   - Code formatting check (black)
   - Import sorting check (isort)
   - Linting (flake8)

3. **Integration Test**
   - PostgreSQL service setup
   - Integration test execution
   - Cleanup

See `.github/workflows/test.yml` for full workflow definition.

## Coverage Requirements

- **Minimum**: 50% coverage (orange threshold)
- **Target**: 70%+ coverage (green threshold)
- **Goal**: >80% coverage for critical paths

Coverage reports are:
- Generated on each test run
- Uploaded as artifacts in CI
- Commented on pull requests

## Performance Benchmarks

Tests verify:

- **Health check**: <1 second response time
- **OpenAPI schema**: <2 seconds generation time
- **General endpoints**: <5 seconds (typical)

## Debugging Tests

### Verbose Output

```bash
# Very verbose output
pytest test/ -vv

# Show print statements
pytest test/ -s

# Show local variables on failure
pytest test/ -l
```

### Stop on First Failure

```bash
# Stop at first failure
pytest test/ -x

# Stop at first failure, rerun from there
pytest test/ --lf
```

### Debug in IDE

Add breakpoint in test:

```python
def test_something(client):
    response = client.get("/api/endpoint/")
    breakpoint()  # Debugger will pause here
    assert response.status_code == 200
```

## Troubleshooting

### Tests Can't Import App

```bash
# Make sure you have the project root in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest test/
```

### Database Errors in Tests

Tests use temporary SQLite databases. If you see database errors:

```bash
# Clean up any leftover test databases
rm -f test*.db

# Run tests again
pytest test/
```

### CORS or Auth Failures

Some tests intentionally get auth failures with invalid keys. This is expected:

```python
def test_invalid_auth(client, invalid_api_headers):
    response = client.get("/api/endpoint/", headers=invalid_api_headers)
    assert response.status_code == 403  # Expected to fail auth
```

## Extending Tests

### Adding New Endpoint Tests

1. Create test class: `class TestNewRouter`
2. Add test methods: `def test_new_endpoint(self, client)`
3. Use fixtures: `def test_with_auth(self, client, api_headers)`
4. Run: `pytest test/ -v`

### Adding Performance Tests

```python
@pytest.mark.slow
def test_query_performance(client):
    import time
    start = time.time()
    response = client.get("/api/expensive-query/")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 5.0  # Must complete in 5 seconds
```

### Adding Database Tests

```python
def test_database_operation(client, test_user_data):
    # Test data is available
    response = client.post(
        "/api/resources/",
        json=test_user_data,
        headers={"X-API-Key": "test"}
    )
    assert response.status_code == 201
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Coverage.py](https://coverage.readthedocs.io/)

## Contributing

When contributing to the project:

1. Add tests for new features
2. Ensure all tests pass: `pytest test/ -v`
3. Maintain or improve coverage: `pytest test/ --cov=app`
4. Follow test naming conventions
5. Comment complex test logic
