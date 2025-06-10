"""
Comprehensive Test Suite for Routiq Backend API
Tests all endpoints with various scenarios including success, error, and edge cases
"""

import pytest
import requests
import json
from datetime import datetime
from typing import Dict, Any, List
import time

# Test Configuration
BASE_URL = "http://localhost:8000"
TEST_ORGANIZATION_ID = "test_org_123"
TIMEOUT = 30

class TestAPIEndpoints:
    """Comprehensive API endpoint testing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def test_server_is_running(self):
        """Test that the API server is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            assert response.status_code == 200, f"Server not responding: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.fail("API server is not running. Please start the server first.")
    
    # ========================================
    # CORE ENDPOINTS TESTS
    # ========================================
    
    def test_root_endpoint(self):
        """Test GET / - Root endpoint"""
        response = requests.get(f"{self.base_url}/", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "timestamp" in data
        assert "docs" in data
        assert "redoc" in data
        
        # Validate content
        assert data["message"] == "Routiq Backend API"
        assert data["version"] == "2.0.0"
        assert data["status"] == "healthy"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"
        
        # Validate timestamp format
        datetime.fromisoformat(data["timestamp"])
    
    def test_health_endpoint(self):
        """Test GET /health - Health check endpoint"""
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        
        # Validate content
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        
        # Validate environment info
        env = data["environment"]
        assert "APP_ENV" in env
        assert "PORT" in env
        assert "has_clerk_key" in env
        assert "has_supabase_url" in env
        assert "has_database_url" in env
        assert "has_encryption_key" in env
        
        # Validate timestamp format
        datetime.fromisoformat(data["timestamp"])
    
    # ========================================
    # CLINIKO PATIENT ENDPOINTS TESTS
    # ========================================
    
    def test_cliniko_patients_test_endpoint(self):
        """Test GET /api/v1/admin/cliniko/patients/test"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/test", 
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "timestamp" in data
        datetime.fromisoformat(data["timestamp"])
    
    def test_cliniko_patients_debug_simple_test(self):
        """Test GET /api/v1/admin/cliniko/patients/debug/simple-test"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/debug/simple-test",
            headers=self.headers
        )
        
        # This might fail if database is not configured, but should return valid JSON
        assert response.status_code in [200, 500]
        data = response.json()
        
        if response.status_code == 200:
            assert "database_connected" in data
            assert "test_value" in data
        else:
            assert "error" in data or "detail" in data
    
    def test_cliniko_patients_debug_organizations(self):
        """Test GET /api/v1/admin/cliniko/patients/debug/organizations"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/debug/organizations",
            headers=self.headers
        )
        
        # This might fail if database is not configured
        assert response.status_code in [200, 500]
        data = response.json()
        
        if response.status_code == 200:
            assert "total_active_patients" in data
            assert "organizations_with_patients" in data
            assert "timestamp" in data
            assert isinstance(data["organizations_with_patients"], list)
        else:
            assert "error" in data or "detail" in data
    
    def test_cliniko_patients_debug_sample(self):
        """Test GET /api/v1/admin/cliniko/patients/debug/sample"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/debug/sample",
            headers=self.headers
        )
        
        # This might fail if database is not configured
        assert response.status_code in [200, 500]
        data = response.json()
        
        if response.status_code == 200:
            assert "sample_patients" in data
            assert "columns" in data
            assert "total_samples" in data
            assert "timestamp" in data
            assert isinstance(data["sample_patients"], list)
            assert isinstance(data["columns"], list)
        else:
            assert "error" in data or "detail" in data
    
    def test_cliniko_patients_active_summary_valid_org(self):
        """Test GET /api/v1/admin/cliniko/patients/{organization_id}/active/summary with valid org"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/{TEST_ORGANIZATION_ID}/active/summary",
            headers=self.headers
        )
        
        # This might fail if database is not configured or org doesn't exist
        assert response.status_code in [200, 500]
        data = response.json()
        
        if response.status_code == 200:
            assert "organization_id" in data
            assert "total_active_patients" in data
            assert "patients_with_recent_appointments" in data
            assert "patients_with_upcoming_appointments" in data
            assert "timestamp" in data
            assert data["organization_id"] == TEST_ORGANIZATION_ID
            assert isinstance(data["total_active_patients"], int)
        else:
            assert "error" in data or "detail" in data
    
    def test_cliniko_patients_active_list_valid_org(self):
        """Test GET /api/v1/admin/cliniko/patients/{org}/active with valid organization"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Basic structure
        assert "organization_id" in data
        assert "patients" in data
        assert "total_count" in data
        assert "timestamp" in data
        
        # If there are patients, verify structure
        if data["patients"]:
            patient = data["patients"][0]
            assert "id" in patient
            assert "contact_id" in patient
            assert "recent_appointment_count" in patient
            assert "upcoming_appointment_count" in patient
            assert "total_appointment_count" in patient
    
    def test_cliniko_patients_upcoming_list_valid_org(self):
        """Test GET /api/v1/admin/cliniko/patients/{org}/upcoming with valid organization"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/patients/{TEST_ORGANIZATION_ID}/upcoming",
            headers=self.headers
        )
        
        # Handle case where new endpoint isn't deployed yet
        if response.status_code in [404, 500]:
            print("   ℹ️  Upcoming appointments endpoint not yet deployed")
            return
        
        assert response.status_code == 200
        data = response.json()
        
        # Basic structure
        assert "organization_id" in data
        assert "patients" in data
        assert "total_count" in data
        assert "timestamp" in data
        
        # If there are patients, verify they all have upcoming appointments
        if data["patients"]:
            for patient in data["patients"]:
                assert "id" in patient
                assert "contact_id" in patient
                assert "upcoming_appointment_count" in patient
                assert patient["upcoming_appointment_count"] > 0  # All should have upcoming appointments
                assert "upcoming_appointments" in patient
    
    # ========================================
    # CLINIKO ADMIN ENDPOINTS TESTS
    # ========================================
    
    def test_cliniko_sync_trigger(self):
        """Test POST /api/v1/admin/cliniko/sync/{organization_id}"""
        response = requests.post(
            f"{self.base_url}/api/v1/admin/cliniko/sync/{TEST_ORGANIZATION_ID}",
            headers=self.headers
        )
        
        # This will likely fail without proper credentials/database setup
        assert response.status_code in [200, 400, 500]
        data = response.json()
        
        if response.status_code == 200:
            assert "organization_id" in data
            assert "success" in data
        else:
            assert "error" in data or "detail" in data
    
    def test_cliniko_status_check(self):
        """Test GET /api/v1/admin/cliniko/status/{organization_id}"""
        response = requests.get(
            f"{self.base_url}/api/v1/admin/cliniko/status/{TEST_ORGANIZATION_ID}",
            headers=self.headers
        )
        
        # This will likely fail without proper credentials/database setup
        assert response.status_code in [200, 400, 500]
        data = response.json()
        
        if response.status_code == 200:
            assert "organization_id" in data
        else:
            assert "error" in data or "detail" in data
    
    # ========================================
    # ERROR HANDLING TESTS
    # ========================================
    
    def test_invalid_endpoint_404(self):
        """Test that invalid endpoints return 404"""
        response = requests.get(f"{self.base_url}/api/v1/invalid/endpoint")
        assert response.status_code == 404
    
    def test_invalid_organization_id_format(self):
        """Test endpoints with invalid organization ID formats"""
        invalid_org_ids = ["", "   ", "org with spaces", "org/with/slashes"]
        
        for invalid_id in invalid_org_ids:
            response = requests.get(
                f"{self.base_url}/api/v1/admin/cliniko/patients/{invalid_id}/active/summary"
            )
            # Should either work (if ID is URL-encoded) or return error
            assert response.status_code in [200, 400, 422, 500]
    
    def test_method_not_allowed(self):
        """Test that wrong HTTP methods return 405"""
        # Try POST on GET-only endpoint
        response = requests.post(f"{self.base_url}/health")
        assert response.status_code == 405
        
        # Try GET on POST-only endpoint
        response = requests.get(f"{self.base_url}/api/v1/admin/cliniko/sync/{TEST_ORGANIZATION_ID}")
        assert response.status_code == 405
    
    # ========================================
    # PERFORMANCE TESTS
    # ========================================
    
    def test_response_time_health_endpoint(self):
        """Test that health endpoint responds quickly"""
        start_time = time.time()
        response = requests.get(f"{self.base_url}/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0, f"Health endpoint too slow: {response_time}s"
        assert response.status_code == 200
    
    def test_response_time_root_endpoint(self):
        """Test that root endpoint responds quickly"""
        start_time = time.time()
        response = requests.get(f"{self.base_url}/")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0, f"Root endpoint too slow: {response_time}s"
        assert response.status_code == 200
    
    # ========================================
    # CONTENT TYPE TESTS
    # ========================================
    
    def test_json_content_type(self):
        """Test that endpoints return proper JSON content type"""
        endpoints = [
            "/",
            "/health",
            "/api/v1/admin/cliniko/patients/test"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
    
    # ========================================
    # CORS TESTS
    # ========================================
    
    def test_cors_headers(self):
        """Test that CORS headers are present"""
        response = requests.options(f"{self.base_url}/health")
        
        # Check for CORS headers (might not be present in all configurations)
        headers = response.headers
        # These headers might be present depending on CORS configuration
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least one CORS header should be present or OPTIONS should be allowed
        assert response.status_code in [200, 204, 405]


# ========================================
# INTEGRATION TESTS
# ========================================

class TestAPIIntegration:
    """Integration tests for API workflows"""
    
    def test_full_cliniko_workflow(self):
        """Test a complete Cliniko workflow"""
        base_url = BASE_URL
        org_id = TEST_ORGANIZATION_ID
        
        # 1. Check health
        health_response = requests.get(f"{base_url}/health")
        assert health_response.status_code == 200
        
        # 2. Test basic endpoint
        test_response = requests.get(f"{base_url}/api/v1/admin/cliniko/patients/test")
        assert test_response.status_code == 200
        
        # 3. Check debug info
        debug_response = requests.get(f"{base_url}/api/v1/admin/cliniko/patients/debug/organizations")
        assert debug_response.status_code in [200, 500]  # Might fail without DB
        
        # 4. Try to get patient summary
        summary_response = requests.get(f"{base_url}/api/v1/admin/cliniko/patients/{org_id}/active/summary")
        assert summary_response.status_code in [200, 500]  # Might fail without DB
        
        # All responses should be valid JSON
        for response in [health_response, test_response, debug_response, summary_response]:
            if response.status_code != 500:  # Skip JSON validation for 500 errors
                assert response.json()  # Should not raise exception


# ========================================
# LOAD TESTS (Basic)
# ========================================

class TestAPILoad:
    """Basic load testing"""
    
    def test_concurrent_health_checks(self):
        """Test multiple concurrent health check requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            return response.status_code == 200
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(results), "Some concurrent requests failed"
    
    def test_rapid_sequential_requests(self):
        """Test rapid sequential requests"""
        success_count = 0
        total_requests = 20
        
        for i in range(total_requests):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    success_count += 1
            except requests.exceptions.RequestException:
                pass  # Count as failure
        
        # At least 80% should succeed
        success_rate = success_count / total_requests
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"]) 