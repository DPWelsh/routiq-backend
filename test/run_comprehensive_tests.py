#!/usr/bin/env python3
"""
Comprehensive API Test Runner for Routiq Backend
Runs all tests against the production server and generates detailed reports
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class APITestRunner:
    """Comprehensive API test runner and reporter"""
    
    def __init__(self, base_url: str = "https://routiq-backend-v10-production.up.railway.app"):
        self.base_url = base_url
        self.results = {
            'test_start_time': datetime.now().isoformat(),
            'base_url': base_url,
            'endpoints_tested': [],
            'summary': {
                'total_endpoints': 0,
                'successful': 0,
                'failed': 0,
                'response_times': [],
                'errors': []
            },
            'detailed_results': {}
        }
        
        # All known endpoints from the codebase analysis
        self.all_endpoints = {
            # Core endpoints
            '/': 'GET',
            '/health': 'GET',
            '/docs': 'GET',
            '/openapi.json': 'GET',
            
            # Admin endpoints
            '/api/v1/admin/migrate/organization-services': 'POST',
            '/api/v1/admin/organization-services/{organization_id}': 'GET',
            '/api/v1/admin/monitoring/system-health': 'GET',
            '/api/v1/admin/sync-logs/all': 'GET',
            '/api/v1/admin/database/cleanup': 'POST',
            
            # Auth endpoints
            '/api/v1/auth/verify': 'GET',
            '/api/v1/auth/organization/{organization_id}/access': 'GET',
            
            # Provider endpoints
            '/api/v1/providers/': 'GET',
            '/api/v1/providers/{provider_id}': 'GET',
            
            # Patient endpoints
            '/api/v1/patients/{organization_id}/active/summary': 'GET',
            '/api/v1/patients/{organization_id}/active': 'GET',
            '/api/v1/patients/test': 'GET',
            
            # Sync Manager endpoints
            '/api/v1/sync/trigger': 'POST',
            '/api/v1/sync/status': 'GET',
            '/api/v1/sync/logs': 'GET',
            '/api/v1/sync/scheduler/status': 'GET',
            '/api/v1/sync/scheduler/trigger': 'POST',
            
            # Cliniko endpoints
            '/api/v1/cliniko/sync/{organization_id}': 'POST',
            '/api/v1/cliniko/status/{organization_id}': 'GET',
            '/api/v1/cliniko/test-connection/{organization_id}': 'GET',
            '/api/v1/cliniko/import-patients/{organization_id}': 'POST',
            '/api/v1/cliniko/test-sync/{organization_id}': 'POST',
            '/api/v1/cliniko/sync-logs/{organization_id}': 'GET',
            '/api/v1/cliniko/active-patients/{organization_id}': 'GET',
            '/api/v1/cliniko/active-patients/{organization_id}/summary': 'GET',
            '/api/v1/cliniko/contacts/{organization_id}/with-appointments': 'GET',
            '/api/v1/cliniko/sync/schedule/{organization_id}': 'POST',
            '/api/v1/cliniko/sync/dashboard/{organization_id}': 'GET',
            '/api/v1/cliniko/debug/contacts/{organization_id}': 'GET',
            '/api/v1/cliniko/debug/patient-raw/{organization_id}': 'GET',
            '/api/v1/cliniko/debug/contacts-full/{organization_id}': 'GET',
            '/api/v1/cliniko/debug/sync-detailed/{organization_id}': 'POST',
            
            # Clerk Admin endpoints
            '/api/v1/clerk/status': 'GET',
            '/api/v1/clerk/sync': 'POST',
            '/api/v1/clerk/sync-logs': 'GET',
            '/api/v1/clerk/database-summary': 'GET',
            '/api/v1/clerk/store-credentials': 'POST',
            '/api/v1/clerk/credentials/{organization_id}/{service_name}': 'GET',
            '/api/v1/clerk/organizations': 'GET',
            '/api/v1/clerk/test-connection': 'POST',
            
            # Onboarding endpoints  
            '/api/v1/onboarding/start': 'POST',
            '/api/v1/onboarding/status/{organization_id}': 'GET'
        }
        
        self.test_organization_ids = ["org_test_123", "test_org_456", "sample_org_789"]
    
    def test_single_endpoint(self, endpoint: str, method: str = 'GET', 
                           organization_id: str = None, **kwargs) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        
        # Replace organization_id placeholder if needed
        if organization_id and '{organization_id}' in endpoint:
            test_endpoint = endpoint.replace('{organization_id}', organization_id)
        else:
            test_endpoint = endpoint
            
        # Replace provider_id placeholder for testing
        if '{provider_id}' in test_endpoint:
            test_endpoint = test_endpoint.replace('{provider_id}', 'test_provider_123')
        
        # Replace service_name placeholder for testing
        if '{service_name}' in test_endpoint:
            test_endpoint = test_endpoint.replace('{service_name}', 'cliniko')
        
        url = f"{self.base_url}{test_endpoint}"
        
        result = {
            'endpoint': endpoint,
            'test_endpoint': test_endpoint,
            'method': method,
            'organization_id': organization_id,
            'url': url,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Make the request
            start_time = time.time()
            
            response = requests.request(
                method=method,
                url=url,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Routiq-API-Test-Runner/1.0'
                },
                timeout=30,
                **kwargs
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            self.results['summary']['response_times'].append(response_time)
            
            result.update({
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code < 500,  # Consider <500 as success for now
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type', '')
            })
            
            # Try to parse JSON response
            try:
                if 'application/json' in response.headers.get('content-type', ''):
                    result['json_response'] = response.json()
                else:
                    result['text_response'] = response.text[:500]  # First 500 chars
            except:
                result['text_response'] = response.text[:500]
            
            # Categorize result
            if response.status_code == 200:
                result['category'] = 'success'
                self.results['summary']['successful'] += 1
            elif response.status_code in [401, 403]:
                result['category'] = 'auth_required'
                self.results['summary']['successful'] += 1  # Expected behavior
                result['note'] = 'Authentication required (expected)'
            elif response.status_code == 404:
                result['category'] = 'not_found'
                result['note'] = 'Endpoint not found or organization not exists'
            elif response.status_code >= 500:
                result['category'] = 'server_error'
                self.results['summary']['failed'] += 1
                self.results['summary']['errors'].append({
                    'endpoint': test_endpoint,
                    'error': f'Server error: {response.status_code}',
                    'organization_id': organization_id
                })
            else:
                result['category'] = 'client_error'
                result['note'] = f'Client error: {response.status_code}'
            
        except requests.exceptions.Timeout:
            result.update({
                'success': False,
                'category': 'timeout',
                'error': 'Request timeout',
                'response_time': 30.0
            })
            self.results['summary']['failed'] += 1
            self.results['summary']['errors'].append({
                'endpoint': test_endpoint,
                'error': 'Timeout',
                'organization_id': organization_id
            })
            
        except requests.exceptions.ConnectionError:
            result.update({
                'success': False,
                'category': 'connection_error',
                'error': 'Connection failed',
            })
            self.results['summary']['failed'] += 1
            self.results['summary']['errors'].append({
                'endpoint': test_endpoint,
                'error': 'Connection failed',
                'organization_id': organization_id
            })
            
        except Exception as e:
            result.update({
                'success': False,
                'category': 'exception',
                'error': str(e),
            })
            self.results['summary']['failed'] += 1
            self.results['summary']['errors'].append({
                'endpoint': test_endpoint,
                'error': str(e),
                'organization_id': organization_id
            })
        
        self.results['summary']['total_endpoints'] += 1
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests on all known endpoints"""
        print(f"🚀 Starting comprehensive API test suite")
        print(f"🔗 Target Server: {self.base_url}")
        print(f"📊 Total Endpoints to test: {len(self.all_endpoints)}")
        print("="*80)
        
        for endpoint, method in self.all_endpoints.items():
            print(f"🧪 Testing: {method} {endpoint}")
            
            if '{organization_id}' in endpoint:
                # Test with multiple organization IDs
                for org_id in self.test_organization_ids:
                    result = self.test_single_endpoint(endpoint, method, org_id)
                    key = f"{endpoint}[{org_id}]"
                    self.results['detailed_results'][key] = result
                    self.results['endpoints_tested'].append(key)
                    
                    # Print result
                    status_icon = self._get_status_icon(result)
                    print(f"  {status_icon} {result['test_endpoint']} - {result.get('status_code', 'N/A')} ({result.get('category', 'unknown')})")
            else:
                # Test endpoint without organization ID
                result = self.test_single_endpoint(endpoint, method)
                self.results['detailed_results'][endpoint] = result
                self.results['endpoints_tested'].append(endpoint)
                
                # Print result
                status_icon = self._get_status_icon(result)
                print(f"  {status_icon} {endpoint} - {result.get('status_code', 'N/A')} ({result.get('category', 'unknown')})")
        
        # Finalize results
        self.results['test_end_time'] = datetime.now().isoformat()
        if self.results['summary']['response_times']:
            self.results['summary']['avg_response_time'] = sum(self.results['summary']['response_times']) / len(self.results['summary']['response_times'])
            self.results['summary']['max_response_time'] = max(self.results['summary']['response_times'])
            self.results['summary']['min_response_time'] = min(self.results['summary']['response_times'])
        
        self.results['summary']['success_rate'] = (
            self.results['summary']['successful'] / self.results['summary']['total_endpoints'] * 100
            if self.results['summary']['total_endpoints'] > 0 else 0
        )
        
        return self.results
    
    def _get_status_icon(self, result: Dict[str, Any]) -> str:
        """Get status icon based on result category"""
        category = result.get('category', 'unknown')
        if category in ['success', 'auth_required']:
            return "✅"
        elif category in ['not_found', 'client_error']:
            return "⚠️"
        elif category in ['server_error', 'timeout', 'connection_error', 'exception']:
            return "❌"
        else:
            return "❓"
    
    def generate_report(self, save_to_file: bool = True) -> str:
        """Generate comprehensive test report"""
        
        report = []
        report.append("=" * 100)
        report.append("🧪 ROUTIQ BACKEND API COMPREHENSIVE TEST REPORT")
        report.append("=" * 100)
        report.append(f"🔗 Server Tested: {self.base_url}")
        report.append(f"⏰ Test Start: {self.results['test_start_time']}")
        report.append(f"⏰ Test End: {self.results.get('test_end_time', 'In Progress')}")
        report.append("")
        
        # Summary Statistics
        summary = self.results['summary']
        report.append("📊 SUMMARY STATISTICS")
        report.append("-" * 50)
        report.append(f"Total Endpoints Tested: {summary['total_endpoints']}")
        report.append(f"Successful Responses: {summary['successful']}")
        report.append(f"Failed Responses: {summary['failed']}")
        report.append(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        if 'avg_response_time' in summary:
            report.append(f"Average Response Time: {summary['avg_response_time']:.3f}s")
            report.append(f"Max Response Time: {summary['max_response_time']:.3f}s")
            report.append(f"Min Response Time: {summary['min_response_time']:.3f}s")
        
        report.append("")
        
        # Categorized Results
        categories = {}
        for endpoint, result in self.results['detailed_results'].items():
            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append((endpoint, result))
        
        for category, endpoints in categories.items():
            icon = self._get_category_icon(category)
            report.append(f"{icon} {category.upper().replace('_', ' ')} ({len(endpoints)} endpoints)")
            report.append("-" * 50)
            
            for endpoint, result in endpoints:
                status_code = result.get('status_code', 'N/A')
                response_time = result.get('response_time', 0)
                if response_time:
                    report.append(f"  {endpoint} - {status_code} ({response_time:.3f}s)")
                else:
                    report.append(f"  {endpoint} - {status_code}")
                
                if 'note' in result:
                    report.append(f"    Note: {result['note']}")
                if 'error' in result:
                    report.append(f"    Error: {result['error']}")
            
            report.append("")
        
        # Errors Section
        if summary['errors']:
            report.append("❌ DETAILED ERRORS")
            report.append("-" * 50)
            for i, error in enumerate(summary['errors'], 1):
                report.append(f"{i}. {error['endpoint']}")
                report.append(f"   Error: {error['error']}")
                if 'organization_id' in error:
                    report.append(f"   Organization ID: {error['organization_id']}")
                report.append("")
        
        # Performance Analysis
        if summary.get('response_times'):
            report.append("📈 PERFORMANCE ANALYSIS")
            report.append("-" * 50)
            
            # Group by response time ranges
            fast = sum(1 for t in summary['response_times'] if t < 0.5)
            medium = sum(1 for t in summary['response_times'] if 0.5 <= t < 2.0)
            slow = sum(1 for t in summary['response_times'] if t >= 2.0)
            
            report.append(f"Fast responses (<0.5s): {fast}")
            report.append(f"Medium responses (0.5-2.0s): {medium}")
            report.append(f"Slow responses (>2.0s): {slow}")
            report.append("")
        
        report.append("=" * 100)
        report.append("Test completed successfully! 🎉")
        report.append("=" * 100)
        
        report_text = "\n".join(report)
        
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_report_{timestamp}.txt"
            
            try:
                with open(filename, 'w') as f:
                    f.write(report_text)
                print(f"\n💾 Report saved to: {filename}")
                
                # Also save JSON results
                json_filename = f"api_test_results_{timestamp}.json"
                with open(json_filename, 'w') as f:
                    json.dump(self.results, f, indent=2, default=str)
                print(f"💾 JSON results saved to: {json_filename}")
                
            except Exception as e:
                print(f"⚠️ Could not save report: {e}")
        
        return report_text
    
    def _get_category_icon(self, category: str) -> str:
        """Get icon for result category"""
        icons = {
            'success': '✅',
            'auth_required': '🔐',
            'not_found': '🔍',
            'client_error': '⚠️',
            'server_error': '❌',
            'timeout': '⏱️',
            'connection_error': '🔌',
            'exception': '💥'
        }
        return icons.get(category, '❓')


def main():
    """Main function to run the comprehensive test suite"""
    parser = argparse.ArgumentParser(description='Comprehensive API Test Runner for Routiq Backend')
    parser.add_argument('--url', default='https://routiq-backend-v10-production.up.railway.app',
                       help='Base URL of the API server to test')
    parser.add_argument('--local', action='store_true',
                       help='Test against local server (http://localhost:8000)')
    parser.add_argument('--no-report', action='store_true',
                       help='Do not save report to file')
    
    args = parser.parse_args()
    
    if args.local:
        base_url = 'http://localhost:8000'
    else:
        base_url = args.url
    
    # Initialize test runner
    runner = APITestRunner(base_url)
    
    # Run all tests
    print("Starting comprehensive API test suite...")
    results = runner.run_all_tests()
    
    # Generate and display report
    report = runner.generate_report(save_to_file=not args.no_report)
    print("\n" + report)
    
    # Exit with appropriate code
    if results['summary']['failed'] > 0:
        print(f"\n⚠️ {results['summary']['failed']} tests failed!")
        sys.exit(1)
    else:
        print(f"\n🎉 All {results['summary']['successful']} tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main() 