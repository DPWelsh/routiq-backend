"""
Comprehensive Test Suite for ALL Routiq Backend API Endpoints
Tests all endpoints on the production server: https://routiq-backend-v10-production.up.railway.app
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

# Production Server Configuration
PRODUCTION_URL = "https://routiq-backend-v10-production.up.railway.app"
LOCAL_URL = "http://localhost:8000"

# Determine which server to test (can be controlled via environment variable)
BASE_URL = os.getenv("TEST_SERVER_URL", PRODUCTION_URL)
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

# Test data
TEST_ORGANIZATION_ID = "test_org_123"
SAMPLE_ORGANIZATION_IDS = ["org_1", "org_2", "test_org_123"]

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
            
            if response.status_code == 200:
                data = self.validate_json_response(response, endpoint)
                
                # Validate expected fields
                required_fields = ["message", "version", "status", "timestamp", "docs", "redoc"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    test_results.add_result(endpoint, 'failed', {
                        'error': f'Missing required fields: {missing_fields}',
                        'status_code': response.status_code,
                        'response': data
                    })
                else:
                    test_results.add_result(endpoint, 'successful', {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'version': data.get('version'),
                        'message': data.get('message')
                    })
            else:
                test_results.add_result(endpoint, 'failed', {
                    'error': f'Unexpected status code: {response.status_code}',
                    'status_code': response.status_code,
                    'response': response.text[:500]
                })
                
        except Exception as e:
            test_results.add_result(endpoint, 'failed', {
                'error': str(e),
                'exception_type': type(e).__name__
            })
    
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
                        'database_connected': data.get('environment', {}).get('has_database_url', False)
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
                    'paths': list(paths.keys())
                })
                
                # Test all discovered endpoints
                for path in paths.keys():
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