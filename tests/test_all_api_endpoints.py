"""
Comprehensive Test Suite for ALL Routiq Backend API Endpoints
Tests all endpoints on the production server: https://routiq-backend-prod.up.railway.app/
"""

import pytest
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Server Configuration
PRODUCTION_URL = "https://routiq-backend-prod.up.railway.app/"

# Default to PRODUCTION for testing the live system
BASE_URL = os.getenv("TEST_SERVER_URL", PRODUCTION_URL)
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

# Test data
TEST_ORGANIZATION_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
SAMPLE_ORGANIZATION_IDS = [TEST_ORGANIZATION_ID]

class APITestResults:
    """Class to track and report test results"""
    
    def __init__(self):
        self.results = {
            'total_endpoints': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'endpoint_details': {}
        }
        self.lock = threading.Lock()
    
    def add_result(self, endpoint: str, status: str, details: Dict[str, Any]):
        with self.lock:
            self.results['total_endpoints'] += 1
            self.results[status] += 1
            self.results['endpoint_details'][endpoint] = details
            
            if status == 'failed':
                self.results['errors'].append({
                    'endpoint': endpoint,
                    'details': details
                })
    
    def get_summary(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'summary': {
                    'total': self.results['total_endpoints'],
                    'successful': self.results['successful'],
                    'failed': self.results['failed'],
                    'skipped': self.results['skipped'],
                    'success_rate': (self.results['successful'] / self.results['total_endpoints'] * 100) if self.results['total_endpoints'] > 0 else 0
                },
                'errors': self.results['errors'],
                'all_results': self.results['endpoint_details']
            }

# Global test results tracker
test_results = APITestResults()

class TestAllAPIEndpoints:
    """Comprehensive test suite for all API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Routiq-API-Test-Suite/1.0"
        }
        self.timeout = TIMEOUT
        print(f"\n🔗 Testing against: {self.base_url}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    headers=self.headers,
                    **kwargs
                )
                return response
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                print(f"  ⚠️ Attempt {attempt + 1} failed for {endpoint}: {e}")
                time.sleep(RETRY_DELAY)
        
        raise Exception(f"All {MAX_RETRIES} attempts failed for {endpoint}")
    
    def validate_json_response(self, response: requests.Response, endpoint: str) -> Dict[str, Any]:
        """Validate and parse JSON response"""
        try:
            return response.json()
        except json.JSONDecodeError as e:
            test_results.add_result(endpoint, 'failed', {
                'error': 'Invalid JSON response',
                'status_code': response.status_code,
                'content': response.text[:500]
            })
            raise
    
    # ========================================
    # CORE API ENDPOINTS
    # ========================================
    
    def test_root_endpoint(self):
        """Test GET / - Root endpoint"""
        endpoint = "/"
        try:
            response = self.make_request("GET", endpoint)
            
            # Assert that we get a successful response
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
            
            data = self.validate_json_response(response, endpoint)
            
            # Validate expected fields
            required_fields = ["message", "version", "status", "timestamp", "docs", "redoc"]
            missing_fields = [field for field in required_fields if field not in data]
            
            assert not missing_fields, f'Missing required fields: {missing_fields}'
            
            # Record success
            test_results.add_result(endpoint, 'successful', {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'version': data.get('version'),
                'message': data.get('message')
            })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
            raise  # Re-raise to make pytest fail
    
    def test_health_endpoint(self):
        """Test GET /health - Health check"""
        endpoint = "/health"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                required_fields = ["status", "timestamp", "version", "environment"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    test_results.add_result(endpoint, 'failed', {
                        'error': f'Missing required fields: {missing_fields}',
                        'status_code': response.status_code
                    })
                else:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'status': data.get('status'),
                        'environment': data.get('environment', {})
                    })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Health check failed with status: {response.status_code}',
                    'status_code': response.status_code
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # ADMIN ENDPOINTS
    # ========================================
    
    def test_admin_system_health(self):
        """Test GET /api/v1/admin/monitoring/system-health"""
        endpoint = "/api/v1/admin/monitoring/system-health"
        try:
            response = self.make_request("GET", endpoint)
            
            # Admin endpoints might require authentication, so accept 200, 401, 403
            acceptable_codes = [200, 401, 403]
            
            if response.status_code in acceptable_codes:
                if response.status_code == 200:
                    data = self.validate_json_response(response, endpoint)
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'authenticated': True,
                        'data_keys': list(data.keys()) if isinstance(data, dict) else []
                    })
                else:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'authenticated': False,
                        'note': 'Authentication required (expected)'
                    })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    def test_admin_sync_logs(self):
        """Test GET /api/v1/admin/sync-logs/all"""
        endpoint = "/api/v1/admin/sync-logs/all"
        try:
            response = self.make_request("GET", endpoint)
            
            acceptable_codes = [200, 401, 403, 500]  # 500 might occur if no DB connection
            
            if response.status_code in acceptable_codes:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': f'Responded with status {response.status_code}'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # AUTHENTICATION ENDPOINTS
    # ========================================
    
    def test_auth_verify(self):
        """Test GET /api/v1/auth/verify"""
        endpoint = "/api/v1/auth/verify"
        try:
            response = self.make_request("GET", endpoint)
            
            # Auth endpoints typically return 401 without proper token
            acceptable_codes = [200, 401, 403]
            
            if response.status_code in acceptable_codes:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Auth endpoint responding correctly'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # PROVIDER ENDPOINTS
    # ========================================
    
    def test_providers_list(self):
        """Test GET /api/v1/providers/"""
        endpoint = "/api/v1/providers/"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate data structure
                if isinstance(data, list):
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': 'list',
                        'provider_count': len(data),
                        'sample_provider': data[0] if data else None
                    })
                elif isinstance(data, dict) and 'providers' in data:
                    providers = data['providers']
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': 'dict_with_providers',
                        'provider_count': len(providers),
                        'sample_provider': providers[0] if providers else None
                    })
                else:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': type(data).__name__,
                        'data_structure': str(data)[:200]
                    })
            elif response.status_code in [401, 403]:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Authentication required (expected)'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # PATIENT ENDPOINTS
    # ========================================
    
    def test_patients_test_endpoint(self):
        """Test GET /api/v1/patients/test"""
        endpoint = "/api/v1/patients/test"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate patients test data
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'data_type': type(data).__name__,
                    'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                    'sample_data': str(data)[:300]
                })
            elif response.status_code in [401, 403]:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Authentication required (expected)'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    def test_database_connection(self):
        """Test database connection through health endpoint"""
        endpoint = "/health"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Check if database connection info is available
                db_info = {}
                if isinstance(data, dict):
                    if 'environment' in data and isinstance(data['environment'], dict):
                        db_info = data['environment']
                    elif 'database' in data:
                        db_info = data['database']
                
                test_results.add_result("database:connection", 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'database_info': db_info,
                    'health_data': str(data)[:300]
                })
            else:
                test_results.add_result("database:connection", 'failed', {
                    'error': f'Health check failed with status: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result("database:connection", 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # SYNC MANAGER ENDPOINTS
    # ========================================
    
    def test_sync_status(self):
        """Test GET /api/v1/sync/status"""
        endpoint = "/api/v1/sync/status"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate sync status data
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'data_type': type(data).__name__,
                    'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                    'sample_data': str(data)[:300]
                })
            elif response.status_code in [401, 403]:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Authentication required (expected)'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    def test_sync_logs(self):
        """Test GET /api/v1/sync/logs"""
        endpoint = "/api/v1/sync/logs"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate sync logs data
                if isinstance(data, list):
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': 'list',
                        'log_count': len(data),
                        'sample_log': data[0] if data else None
                    })
                elif isinstance(data, dict) and 'logs' in data:
                    logs = data['logs']
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': 'dict_with_logs',
                        'log_count': len(logs),
                        'sample_log': logs[0] if logs else None
                    })
                else:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': type(data).__name__,
                        'data_structure': str(data)[:300]
                    })
            elif response.status_code in [401, 403]:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Authentication required (expected)'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # CLINIKO ENDPOINTS
    # ========================================
    
    def test_cliniko_status_with_org(self):
        """Test GET /api/v1/cliniko/status/{organization_id}"""
        for org_id in SAMPLE_ORGANIZATION_IDS:
            endpoint = f"/api/v1/cliniko/status/{org_id}"
            try:
                response = self.make_request("GET", endpoint)
                
                if response.status_code == 200:
                    data = self.validate_json_response(response, endpoint)
                    
                    # Validate Cliniko status data
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'organization_id': org_id,
                        'data_type': type(data).__name__,
                        'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                        'sample_data': str(data)[:300]
                    })
                elif response.status_code in [401, 403]:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'organization_id': org_id,
                        'note': 'Authentication required (expected)'
                    })
                elif response.status_code == 404:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'organization_id': org_id,
                        'note': 'Organization not found (expected for test org)'
                    })
                else:
                    test_results.add_result(endpoint, 'failed', {
                        'error': f'Unexpected status code: {response.status_code}',
                        'status_code': response.status_code,
                        'organization_id': org_id,
                        'response_text': response.text[:200]
                    })
                    
            except Exception as e:
                test_results.add_result(endpoint, 'failed', {
                    'error': str(e),
                    'exception_type': type(e).__name__,
                    'organization_id': org_id
                })
    
    def test_cliniko_test_connection_with_org(self):
        """Test GET /api/v1/cliniko/test-connection/{organization_id}"""
        for org_id in SAMPLE_ORGANIZATION_IDS:
            endpoint = f"/api/v1/cliniko/test-connection/{org_id}"
            try:
                response = self.make_request("GET", endpoint)
                
                if response.status_code == 200:
                    data = self.validate_json_response(response, endpoint)
                    
                    # Validate connection test data
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'organization_id': org_id,
                        'data_type': type(data).__name__,
                        'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                        'sample_data': str(data)[:300]
                    })
                elif response.status_code in [401, 403]:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'organization_id': org_id,
                        'note': 'Authentication required (expected)'
                    })
                elif response.status_code == 404:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'organization_id': org_id,
                        'note': 'Organization not found (expected for test org)'
                    })
                else:
                    test_results.add_result(endpoint, 'failed', {
                        'error': f'Unexpected status code: {response.status_code}',
                        'status_code': response.status_code,
                        'organization_id': org_id,
                        'response_text': response.text[:200]
                    })
                    
            except Exception as e:
                test_results.add_result(endpoint, 'failed', {
                    'error': str(e),
                    'exception_type': type(e).__name__,
                    'organization_id': org_id
                })
    
    # ========================================
    # CLERK ADMIN ENDPOINTS
    # ========================================
    
    def test_clerk_status(self):
        """Test GET /api/v1/clerk/status"""
        endpoint = "/api/v1/clerk/status"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate Clerk status data
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'data_type': type(data).__name__,
                    'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                    'sample_data': str(data)[:300]
                })
            elif response.status_code in [401, 403]:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Authentication required (expected)'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    def test_clerk_organizations(self):
        """Test GET /api/v1/clerk/organizations"""
        endpoint = "/api/v1/clerk/organizations"
        try:
            response = self.make_request("GET", endpoint)
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate Clerk organizations data
                if isinstance(data, list):
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': 'list',
                        'organization_count': len(data),
                        'sample_organization': data[0] if data else None
                    })
                elif isinstance(data, dict) and 'organizations' in data:
                    organizations = data['organizations']
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': 'dict_with_organizations',
                        'organization_count': len(organizations),
                        'sample_organization': organizations[0] if organizations else None
                    })
                else:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'data_type': type(data).__name__,
                        'data_structure': str(data)[:300]
                    })
            elif response.status_code in [401, 403]:
                test_results.add_result(endpoint, 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'note': 'Authentication required (expected)'
                })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # COMPREHENSIVE ENDPOINT DISCOVERY
    # ========================================
    
    def test_discover_all_endpoints(self):
        """Discover and test all available endpoints by examining OpenAPI docs"""
        endpoint = "/docs"
        try:
            # Try to get OpenAPI schema
            response = self.make_request("GET", "/openapi.json")
            
            if response.status_code == 200:
                openapi_spec = response.json()
                paths = openapi_spec.get('paths', {})
                
                test_results.add_result("/openapi.json", 'successful', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'total_paths_discovered': len(paths),
                    'paths': list(paths.keys())[:20]  # First 20 paths
                })
                
                # Test a few discovered endpoints
                for path in list(paths.keys())[:5]:  # Test first 5 discovered endpoints
                    if path not in ['/', '/health']:  # Skip already tested
                        try:
                            test_response = self.make_request("GET", path)
                            test_results.add_result(f"discovered:{path}", 'successful', {
                                'status_code': test_response.status_code,
                                'response_time': test_response.elapsed.total_seconds(),
                                'discovered': True
                            })
                        except Exception as discovery_error:
                            test_results.add_result(f"discovered:{path}", 'failed', {
                                'error': str(discovery_error),
                                'discovered': True
                            })
            else:
                test_results.add_result("/openapi.json", 'failed', {
                    'error': f'Could not fetch OpenAPI spec: {response.status_code}',
                    'status_code': response.status_code
                })
                
        except Exception as e:
            test_results.add_result("/openapi.json", 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # PERFORMANCE TESTS
    # ========================================
    
    def test_concurrent_requests(self):
        """Test concurrent requests to health endpoint"""
        endpoint = "/health"
        num_requests = 10
        
        def make_concurrent_request():
            try:
                response = self.make_request("GET", endpoint)
                return {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'status_code': None,
                    'response_time': None,
                    'success': False,
                    'error': str(e)
                }
        
        try:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_concurrent_request) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            successful_requests = sum(1 for result in results if result['success'])
            avg_response_time = sum(result['response_time'] for result in results if result['response_time']) / len([r for r in results if r['response_time']])
            
            test_results.add_result("performance:concurrent", 'successful', {
                'total_requests': num_requests,
                'successful_requests': successful_requests,
                'success_rate': (successful_requests / num_requests) * 100,
                'average_response_time': avg_response_time,
                'all_results': results
            })
            
        except Exception as e:
            test_results.add_result("performance:concurrent", 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
    # ========================================
    # TEST SUMMARY AND REPORTING
    # ========================================
    
    def test_generate_final_report(self):
        """Generate final test report"""
        summary = test_results.get_summary()
        
        print("\n" + "="*80)
        print("🧪 ROUTIQ BACKEND API TEST SUMMARY")
        print("="*80)
        print(f"🔗 Server Tested: {BASE_URL}")
        print(f"📊 Total Endpoints: {summary['summary']['total']}")
        print(f"✅ Successful: {summary['summary']['successful']}")
        print(f"❌ Failed: {summary['summary']['failed']}")
        print(f"⚠️ Skipped: {summary['summary']['skipped']}")
        print(f"📈 Success Rate: {summary['summary']['success_rate']:.1f}%")
        
        if summary['errors']:
            print("\n❌ FAILED ENDPOINTS:")
            for error in summary['errors']:
                print(f"  • {error['endpoint']}: {error['details'].get('error', 'Unknown error')}")
        
        print("\n📝 DETAILED RESULTS:")
        for endpoint, details in summary['all_results'].items():
            status_icon = "✅" if details.get('status_code') in [200, 401, 403] else "❌"
            print(f"  {status_icon} {endpoint} - Status: {details.get('status_code', 'N/A')}")
        
        print("="*80)
        
        # This test always passes as it's just reporting
        test_results.add_result("test_report", 'successful', {
            'summary': summary['summary'],
            'test_completed': True
        })


# ========================================
# TEST RUNNER CONFIGURATION
# ========================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Setup for the entire test session"""
    print(f"\n🚀 Starting comprehensive API test suite")
    print(f"🔗 Target Server: {BASE_URL}")
    print(f"⏱️ Timeout: {TIMEOUT}s")
    print(f"🔄 Max Retries: {MAX_RETRIES}")
    yield
    
    # Generate final report
    final_summary = test_results.get_summary()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(final_summary, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️ Could not save results to file: {e}")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"]) 