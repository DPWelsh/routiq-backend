#!/usr/bin/env python3
"""
Test all current API endpoints and show their full responses
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
TIMEOUT = 30

def pretty_print_response(name: str, response: requests.Response, start_time: float):
    """Pretty print the response data"""
    response_time = round((time.time() - start_time) * 1000, 2)
    
    print(f"\n{'='*80}")
    print(f"🔍 {name}")
    print(f"{'='*80}")
    print(f"Status: {response.status_code}")
    print(f"Response Time: {response_time}ms")
    print(f"URL: {response.url}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\n📄 Response Data:")
            print(json.dumps(data, indent=2, default=str))
        except:
            print(f"\n📄 Response Text:")
            print(response.text)
    else:
        print(f"\n❌ Error Response:")
        print(response.text)

def test_endpoint(name: str, url: str, method: str = "GET", data: Dict = None):
    """Test a single endpoint and show full response"""
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            print(f"❌ Unsupported method: {method}")
            return
        
        pretty_print_response(name, response, start_time)
        
    except requests.exceptions.Timeout:
        print(f"\n{'='*80}")
        print(f"⏱️ {name} - TIMEOUT")
        print(f"{'='*80}")
        print(f"URL: {url}")
        print("Request timed out after 30 seconds")
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ {name} - ERROR")
        print(f"{'='*80}")
        print(f"URL: {url}")
        print(f"Error: {str(e)}")

def main():
    """Test all current API endpoints"""
    print("🚀 TESTING ALL CURRENT API ENDPOINTS")
    print(f"Base URL: {BASE_URL}")
    print(f"Organization ID: {ORG_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Current Core API Endpoints
    endpoints = [
        {
            "name": "1. Sync Trigger (POST)",
            "url": f"{BASE_URL}/api/v1/cliniko/sync/{ORG_ID}",
            "method": "POST"
        },
        {
            "name": "2. Status Basic",
            "url": f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}",
            "method": "GET"
        },
        {
            "name": "3. Status with Logs",
            "url": f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}?include_logs=true&logs_limit=3",
            "method": "GET"
        },
        {
            "name": "4. Status with Health Check",
            "url": f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}?include_health_check=true",
            "method": "GET"
        },
        {
            "name": "5. Status Full (Logs + Health)",
            "url": f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}?include_logs=true&include_health_check=true&logs_limit=2",
            "method": "GET"
        },
        {
            "name": "6. Patient Stats Basic",
            "url": f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats",
            "method": "GET"
        },
        {
            "name": "7. Patient Stats with Details",
            "url": f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats?include_details=true&limit=3",
            "method": "GET"
        },
        {
            "name": "8. Patient Stats Appointments Only",
            "url": f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats?include_details=true&with_appointments_only=true&limit=2",
            "method": "GET"
        },
        {
            "name": "9. Health Check",
            "url": f"{BASE_URL}/health",
            "method": "GET"
        }
    ]
    
    # Test each endpoint
    for endpoint in endpoints:
        test_endpoint(
            endpoint["name"],
            endpoint["url"], 
            endpoint["method"],
            endpoint.get("data")
        )
        time.sleep(1)  # Small delay between requests
    
    print(f"\n{'='*80}")
    print("✅ ALL TESTS COMPLETED")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 