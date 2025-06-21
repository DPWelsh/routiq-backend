"""
Pytest configuration for Routiq Backend API tests
"""

import pytest

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "enhanced: Enhanced patient visibility tests")
    config.addinivalue_line("markers", "analytics: Patient analytics tests")
    config.addinivalue_line("markers", "slow: Slow tests that take more time")
import requests
import time
import os
import os

# Test configuration
BASE_URL = os.getenv("TEST_SERVER_URL", "https://routiq-backend-prod.up.railway.app")
TIMEOUT = 30

@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure the API server is running before tests start"""
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"\n✅ API server is running at {BASE_URL}")
                return
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for API server... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                pytest.exit(f"❌ API server not accessible at {BASE_URL} after {max_retries} attempts")

@pytest.fixture
def api_client():
    """Provide a configured API client for tests"""
    class APIClient:
        def __init__(self):
            self.base_url = BASE_URL
            self.headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            self.timeout = TIMEOUT
        
        def get(self, endpoint, **kwargs):
            return requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=self.timeout, **kwargs)
        
        def post(self, endpoint, **kwargs):
            return requests.post(f"{self.base_url}{endpoint}", headers=self.headers, timeout=self.timeout, **kwargs)
        
        def put(self, endpoint, **kwargs):
            return requests.put(f"{self.base_url}{endpoint}", headers=self.headers, timeout=self.timeout, **kwargs)
        
        def delete(self, endpoint, **kwargs):
            return requests.delete(f"{self.base_url}{endpoint}", headers=self.headers, timeout=self.timeout, **kwargs)
    
    return APIClient()

@pytest.fixture
def test_organization_id():
    """Provide a test organization ID"""
    return "test_org_123"

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "load: marks tests as load tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark load tests
        if "load" in item.name.lower() or "concurrent" in item.name.lower():
            item.add_marker(pytest.mark.load)
        
        # Mark integration tests
        if "integration" in item.name.lower() or "workflow" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ["load", "concurrent", "performance"]):
            item.add_marker(pytest.mark.slow) 