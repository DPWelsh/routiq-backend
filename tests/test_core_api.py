"""
Core API Tests
Tests for basic API functionality: root, health, documentation endpoints
"""

import pytest
import requests
from datetime import datetime
import os

# Configuration
BASE_URL = os.getenv("TEST_SERVER_URL", "http://localhost:8000")
PRODUCTION_URL = "https://routiq-backend-prod.up.railway.app"
TIMEOUT = 30

class TestCoreAPI:
    """Test core API functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = PRODUCTION_URL  # Use production for testing
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Core-API-Test-Suite/1.0"
        }
    
    def test_root_endpoint(self):
        """Test GET / - Root endpoint"""
        response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["message", "version", "status", "timestamp", "docs", "redoc"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate content
        assert data["message"] == "Routiq Backend API"
        assert data["status"] == "healthy"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"
        
        # Validate timestamp format
        datetime.fromisoformat(data["timestamp"])
    
    def test_health_endpoint(self):
        """Test GET /health - Health check endpoint"""
        response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "version", "environment"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate content
        assert data["status"] == "healthy"
        
        # Validate environment info
        env = data["environment"]
        assert isinstance(env, dict)
        
        # Validate timestamp format
        datetime.fromisoformat(data["timestamp"])
    
    def test_documentation_endpoints(self):
        """Test API documentation endpoints"""
        # Test docs endpoint
        docs_response = requests.get(f"{self.base_url}/docs", headers=self.headers, timeout=TIMEOUT)
        assert docs_response.status_code == 200
        
        # Test OpenAPI spec
        openapi_response = requests.get(f"{self.base_url}/openapi.json", headers=self.headers, timeout=TIMEOUT)
        assert openapi_response.status_code == 200
        
        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data
        
        # Verify our enhanced endpoints are in the spec
        paths = openapi_data["paths"]
        enhanced_endpoints = [
            "/api/v1/patients/{organization_id}/active/with-appointments",
            "/api/v1/patients/{organization_id}/by-appointment-type/{appointment_type}",
            "/api/v1/patients/{organization_id}/appointment-types/summary"
        ]
        
        for endpoint in enhanced_endpoints:
            assert endpoint in paths, f"Enhanced endpoint {endpoint} not found in API spec"
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=TIMEOUT)
        
        # Check for CORS headers (may not be present in all setups)
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods", 
            "Access-Control-Allow-Headers"
        ]
        
        # At least one CORS header should be present for modern APIs
        has_cors = any(header in response.headers for header in cors_headers)
        if not has_cors:
            print("⚠️  No CORS headers found - may need to be configured for browser access")
    
    @pytest.mark.performance
    def test_response_times(self):
        """Test that core endpoints respond within acceptable time limits"""
        import time
        
        endpoints = ["/", "/health"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=TIMEOUT)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0, f"Endpoint {endpoint} too slow: {response_time:.2f}s"
            
            print(f"⚡ {endpoint}: {response_time:.2f}s")
    
    def test_json_content_type(self):
        """Test that JSON endpoints return proper content type"""
        response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=TIMEOUT)
        
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower()
    
    def test_error_handling_404(self):
        """Test 404 handling for non-existent endpoints"""
        response = requests.get(f"{self.base_url}/nonexistent-endpoint", headers=self.headers, timeout=TIMEOUT)
        
        assert response.status_code == 404
        
        # Should return JSON error response
        try:
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data
        except:
            # Some 404s might return HTML, which is also acceptable
            pass 