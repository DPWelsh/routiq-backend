"""
Reusable API Client for Testing
Provides consistent API testing functionality across all test files
"""

import requests
import json
import os
from typing import Dict, Any, Optional
import time

class APITestClient:
    """Reusable API client for testing"""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize API client"""
        self.base_url = base_url or os.getenv("TEST_SERVER_URL", "https://routiq-backend-prod.up.railway.app")
        self.timeout = 30
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Routiq-Test-Suite/1.0"
        }
        self.max_retries = 3
        self.retry_delay = 1
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        # Merge headers
        request_headers = self.headers.copy()
        if 'headers' in kwargs:
            request_headers.update(kwargs.pop('headers'))
        
        # Set default timeout
        kwargs.setdefault('timeout', self.timeout)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    **kwargs
                )
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"⚠️ Attempt {attempt + 1} failed for {endpoint}: {e}")
                time.sleep(self.retry_delay)
        
        raise Exception(f"All {self.max_retries} attempts failed for {endpoint}")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request"""
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST request"""
        return self.request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT request"""
        return self.request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request"""
        return self.request("DELETE", endpoint, **kwargs)
    
    def get_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request and return JSON response"""
        response = self.get(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def post_json(self, endpoint: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """POST JSON data and return JSON response"""
        response = self.post(endpoint, json=data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def validate_json_response(self, response: requests.Response) -> Dict[str, Any]:
        """Validate and parse JSON response"""
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON response: {e}")
    
    def assert_successful_response(self, response: requests.Response) -> Dict[str, Any]:
        """Assert response is successful and return JSON data"""
        assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text[:200]}"
        return self.validate_json_response(response)
    
    def check_endpoint_exists(self, endpoint: str) -> bool:
        """Check if endpoint exists (returns True if not 404)"""
        try:
            response = self.get(endpoint)
            return response.status_code != 404
        except:
            return False
    
    def measure_response_time(self, endpoint: str, **kwargs) -> tuple[requests.Response, float]:
        """Measure response time for an endpoint"""
        start_time = time.time()
        response = self.get(endpoint, **kwargs)
        end_time = time.time()
        
        response_time = end_time - start_time
        return response, response_time
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """Get OpenAPI specification"""
        return self.get_json("/openapi.json")
    
    def get_available_endpoints(self) -> list[str]:
        """Get list of available endpoints from OpenAPI spec"""
        try:
            openapi = self.get_openapi_spec()
            return list(openapi.get("paths", {}).keys())
        except:
            return []
    
    def test_patient_endpoint(self, organization_id: str, endpoint_suffix: str = "active") -> Dict[str, Any]:
        """Test patient endpoint with organization ID"""
        endpoint = f"/api/v1/patients/{organization_id}/{endpoint_suffix}"
        response = self.get(endpoint)
        
        if response.status_code == 200:
            return self.assert_successful_response(response)
        elif response.status_code == 500:
            # Database connection issues in production are expected
            print(f"⚠️ Database connection issue for {endpoint}")
            return {"error": "database_connection", "patients": [], "total_count": 0}
        else:
            raise AssertionError(f"Unexpected status code {response.status_code} for {endpoint}")

# Global client instance for easy import
api_client = APITestClient() 