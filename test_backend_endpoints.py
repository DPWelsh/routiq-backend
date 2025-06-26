#!/usr/bin/env python3
"""
Backend API Endpoint Testing Script
Tests all endpoints the frontend uses and exports results
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
TIMEOUT = 30

def test_endpoint(name: str, url: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Test a single API endpoint and return results"""
    print(f"🔍 Testing: {name}")
    
    result = {
        "endpoint_name": name,
        "url": url,
        "method": method,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "status_code": None,
        "response_data": None,
        "error": None,
        "response_time_ms": None
    }
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        end_time = time.time()
        result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
        result["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["success"] = True
            result["response_data"] = response.json()
            print(f"  ✅ SUCCESS ({response.status_code}) - {result['response_time_ms']}ms")
        else:
            result["error"] = response.text
            print(f"  ❌ FAILED ({response.status_code}) - {response.text[:100]}")
            
    except requests.exceptions.Timeout:
        result["error"] = "Request timeout"
        print(f"  ⏱️ TIMEOUT")
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
        print(f"  ❌ REQUEST ERROR: {e}")
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ UNKNOWN ERROR: {e}")
    
    return result

def main():
    """Run all endpoint tests"""
    print("🚀 STARTING BACKEND API ENDPOINT TESTING")
    print("=" * 60)
    
    # Define all endpoints to test
    endpoints = [
        # Patient & Dashboard Endpoints
        {
            "name": "Cliniko Connection Test",
            "url": f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}",
            "method": "GET"
        },
        {
            "name": "Active Patients Summary", 
            "url": f"{BASE_URL}/api/v1/cliniko/active-patients-summary/{ORG_ID}",
            "method": "GET"
        },
        {
            "name": "Sync Dashboard Data",
            "url": f"{BASE_URL}/api/v1/cliniko/sync/dashboard/{ORG_ID}",
            "method": "GET"
        },
        {
            "name": "Sync History/Logs",
            "url": f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=5",
            "method": "GET"
        },
        
        # Organization & Admin Endpoints
        {
            "name": "Organization Services",
            "url": f"{BASE_URL}/api/v1/admin/organization-services/{ORG_ID}",
            "method": "GET"
        },
        {
            "name": "Cliniko Status",
            "url": f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}",
            "method": "GET"
        },
        
        # Sync Control Endpoints (that should work)
        {
            "name": "Start Active Sync",
            "url": f"{BASE_URL}/api/v1/cliniko/sync/{ORG_ID}",
            "method": "POST"
        },
        
        # Missing/Broken Sync Monitoring Endpoints
        {
            "name": "Sync Status by ID (MISSING)",
            "url": f"{BASE_URL}/api/v1/sync/status/test_sync_id",
            "method": "GET"
        },
        {
            "name": "Sync Status Monitoring (MISSING)",
            "url": f"{BASE_URL}/api/v1/sync/status/monitoring",
            "method": "GET"
        },
        {
            "name": "Organization Sync Status (MISSING)",
            "url": f"{BASE_URL}/api/v1/sync/status/organization/{ORG_ID}",
            "method": "GET"
        },
        
        # Alternative Working Endpoints
        {
            "name": "Cliniko Sync All (Alternative)",
            "url": f"{BASE_URL}/api/v1/cliniko/sync-all/{ORG_ID}",
            "method": "POST"
        },
        {
            "name": "Health Check",
            "url": f"{BASE_URL}/health",
            "method": "GET"
        }
    ]
    
    # Run all tests
    results = []
    
    for endpoint in endpoints:
        result = test_endpoint(
            endpoint["name"],
            endpoint["url"], 
            endpoint["method"],
            endpoint.get("data")
        )
        results.append(result)
        print()  # Add spacing
    
    # Generate summary statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    
    # Categorize results
    working_endpoints = [r for r in results if r["success"]]
    broken_endpoints = [r for r in results if not r["success"]]
    missing_endpoints = [r for r in results if r.get("status_code") == 404]
    
    summary = {
        "test_session": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%"
        },
        "endpoint_analysis": {
            "working_count": len(working_endpoints),
            "broken_count": len(broken_endpoints), 
            "missing_count": len(missing_endpoints)
        },
        "detailed_results": results,
        "working_endpoints": [r["endpoint_name"] for r in working_endpoints],
        "broken_endpoints": [r["endpoint_name"] for r in broken_endpoints],
        "missing_endpoints": [r["endpoint_name"] for r in missing_endpoints]
    }
    
    # Export results
    filename = f"backend_api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    # Print summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Working: {successful_tests} ({(successful_tests/total_tests)*100:.1f}%)")
    print(f"❌ Broken: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)")
    print(f"📄 Results exported to: {filename}")
    
    print("\n🟢 WORKING ENDPOINTS:")
    for endpoint in working_endpoints:
        print(f"  ✅ {endpoint['endpoint_name']}")
    
    print("\n🔴 BROKEN/MISSING ENDPOINTS:")
    for endpoint in broken_endpoints:
        status = f"({endpoint['status_code']})" if endpoint['status_code'] else "(ERROR)"
        print(f"  ❌ {endpoint['endpoint_name']} {status}")
    
    print(f"\n📁 Full results saved to: {filename}")
    
    return summary

if __name__ == "__main__":
    main() 