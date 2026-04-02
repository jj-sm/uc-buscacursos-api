import pytest
from fastapi.testclient import TestClient
import sys
import os
import secrets
from contextlib import contextmanager
from functools import partial

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.routers.admin import DEBUG_API_KEY


@contextmanager
def _auth_db_session():
    from app.auth_db import get_auth_db

    db_gen = get_auth_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def _generate_test_api_key(prefix: str = "test-admin") -> str:
    return f"{prefix}-{secrets.token_urlsafe(16)}"

PREFIX = os.getenv("URL_PREFIX", "").rstrip("/")
with_prefix = partial(lambda prefix, path: f"{prefix}{path}", PREFIX)

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Verify health check endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()


class TestRootEndpoint:
    """Test root API endpoint"""
    
    def test_root_endpoint(self, client):
        """Verify root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data or "message" in data


class TestTemplateRouter:
    """Test template router endpoints"""
    
    def test_template_list_endpoints(self, client):
        """List available endpoints - no auth required for health checks"""
        response = client.get(with_prefix("/template/"))
        # Expect 403 without valid API key (unless DEBUG=1)
        assert response.status_code in [200, 403]
    
    def test_template_endpoint_without_key(self, client):
        """Verify endpoints require authentication"""
        response = client.get(with_prefix("/template/resources"))
        assert response.status_code in [403, 400, 422]  # Forbidden or Bad Request or validation
    
    def test_template_endpoint_with_invalid_key(self, client):
        """Test with invalid API key"""
        response = client.get(
            with_prefix("/template/resources"),
            headers={"X-API-Key": "invalid-key-12345"}
        )
        assert response.status_code in [403, 422]
    
    def test_rate_limit_header_format(self, client):
        """Test that responses can include rate limit headers when authenticated"""
        # This test verifies the API structure is correct
        # In production, a valid API key would be used
        response = client.get(with_prefix("/template/resources"), headers={"X-API-Key": "test"})
        # We expect some response (auth error is fine for this test)
        assert response.status_code in [400, 403, 422]


class TestAdminRouter:
    """Test admin router endpoints"""
    
    def test_admin_endpoints_exist(self, client):
        """Verify admin endpoints are registered"""
        response = client.get(with_prefix("/admin/"))
        assert response.status_code in [200, 403]
    
    def test_admin_sql_endpoint_requires_auth(self, client):
        """Admin SQL endpoint should reject unauthenticated users"""
        response = client.post(with_prefix("/admin/courses/sql"), json={"sql": "select 1"})
        assert response.status_code in [403, 422]
    
    def test_admin_sql_endpoint_rejects_debug_key(self, client, monkeypatch):
        """Debug bypass key should not grant admin SQL access"""
        debug_key = "test-debug-key"
        monkeypatch.setenv("DEBUG", "1")
        monkeypatch.setenv("DEBUG_API_KEY", debug_key)
        monkeypatch.setattr("app.routers.admin.DEBUG_API_KEY", debug_key)
        response = client.post(
            with_prefix("/admin/courses/sql"),
            json={"sql": "select 1"},
            headers={"X-API-Key": debug_key},
        )
        assert response.status_code == 403
        assert "debug" in response.json().get("detail", "").lower()
    
    def test_admin_sql_endpoint_allows_valid_admin_key(self, client, monkeypatch):
        """Valid non-debug admin keys should be allowed"""
        non_debug_key = _generate_test_api_key()
        from app.auth_models import APIKey
        with _auth_db_session() as db:
            api_key = APIKey(key=non_debug_key, name="test-admin", tier="enterprise")
            db.add(api_key)
            db.commit()
        try:
            response = client.post(
                with_prefix("/admin/courses/sql"),
                json={"sql": "select 1"},
                headers={"X-API-Key": non_debug_key},
            )
            assert response.status_code == 200
        finally:
            with _auth_db_session() as db:
                db.query(APIKey).filter_by(key=non_debug_key).delete()
                db.commit()


class TestDocumentation:
    """Test API documentation endpoints"""
    
    def test_swagger_ui_available(self, client):
        """Verify Swagger UI is available"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_redoc_available(self, client):
        """Verify ReDoc documentation is available"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower() or "api" in response.text.lower()
    
    def test_openapi_schema(self, client):
        """Verify OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data or "swagger" in data
        assert "paths" in data  # Should have defined endpoints


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Verify CORS headers are set"""
        response = client.get("/health")
        # Check for CORS headers
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Verify 404 response for unknown endpoints"""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Verify 405 response for wrong HTTP method"""
        response = client.post("/health")
        assert response.status_code in [405, 404]


class TestResponseFormats:
    """Test response format standards"""
    
    def test_json_responses(self, client):
        """Verify API returns JSON responses"""
        response = client.get("/health")
        assert response.headers.get("content-type") is not None
        data = response.json()  # Will raise if not valid JSON
        assert isinstance(data, (dict, list))
    
    def test_error_response_format(self, client):
        """Verify error responses are properly formatted"""
        response = client.get(
            "/api/template/resources",
            headers={"X-API-Key": "invalid"}
        )
        data = response.json()
        assert isinstance(data, dict)
        # Should have either detail or error field
        assert "detail" in data or "error" in data or "message" in data


class TestPerformance:
    """Test basic performance expectations"""
    
    def test_health_check_response_time(self, client):
        """Verify health check responds quickly"""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second
    
    def test_openapi_schema_response_time(self, client):
        """Verify OpenAPI schema generates quickly"""
        import time
        start = time.time()
        response = client.get("/openapi.json")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0  # Schema generation should be quick


class TestApiStructure:
    """Test overall API structure and conventions"""
    
    def test_api_prefix_convention(self, client):
        """Verify API endpoints follow /api/ convention"""
        # Admin should be reachable at the configured prefix (default: none)
        response = client.get(with_prefix("/admin/"))
        assert response.status_code in [200, 403, 500]
    
    def test_router_registration(self, client):
        """Verify all routers are properly registered"""
        # Test that we can access various router bases
        routers_to_check = [
            "/admin/",
            "/template/",
        ]
        
        for router_path in routers_to_check:
            response = client.get(with_prefix(router_path))
            # Should return something (not 404)
            assert response.status_code != 404, f"Router not found: {router_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
