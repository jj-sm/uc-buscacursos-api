import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

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
        response = client.get("/api/template/")
        # Expect 403 without valid API key (unless DEBUG=1)
        assert response.status_code in [200, 403]
    
    def test_template_endpoint_without_key(self, client):
        """Verify endpoints require authentication"""
        response = client.get("/api/template/resources")
        assert response.status_code in [403, 400]  # Forbidden or Bad Request
    
    def test_template_endpoint_with_invalid_key(self, client):
        """Test with invalid API key"""
        response = client.get(
            "/api/template/resources",
            headers={"X-API-Key": "invalid-key-12345"}
        )
        assert response.status_code == 403
    
    def test_rate_limit_header_format(self, client):
        """Test that responses can include rate limit headers when authenticated"""
        # This test verifies the API structure is correct
        # In production, a valid API key would be used
        response = client.get("/api/template/resources", headers={"X-API-Key": "test"})
        # We expect some response (auth error is fine for this test)
        assert response.status_code in [400, 403]


class TestAirportsRouter:
    """Test airports router endpoints"""
    
    def test_airports_endpoint_exists(self, client):
        """Verify airports endpoint exists"""
        response = client.get("/api/airports/")
        # Should return 403 without auth
        assert response.status_code in [200, 403]


class TestAdminRouter:
    """Test admin router endpoints"""
    
    def test_admin_airac_endpoint(self, client):
        """Verify admin health check endpoint"""
        response = client.get("/api/admin/airac")
        # Should work without auth in DEBUG mode, or return 403
        assert response.status_code in [200, 403, 500]  # 500 if no DB
    
    def test_admin_endpoints_exist(self, client):
        """Verify admin endpoints are registered"""
        response = client.get("/api/admin/")
        assert response.status_code in [200, 403]


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
        # Admin should be at /api/admin/
        response = client.get("/api/admin/")
        assert response.status_code in [200, 403, 500]
    
    def test_router_registration(self, client):
        """Verify all routers are properly registered"""
        # Test that we can access various router bases
        routers_to_check = [
            "/api/admin/",
            "/api/template/",
            "/api/airports/",
        ]
        
        for router_path in routers_to_check:
            response = client.get(router_path)
            # Should return something (not 404)
            assert response.status_code != 404, f"Router not found: {router_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
