#!/usr/bin/env python3
"""
Careful API testing with rate limit respect
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
TIMEOUT = 10  # Shorter timeout
DELAY = 5     # Wait 5 seconds between requests

def test_single_endpoint(name: str, url: str, method: str = "GET"):
    """Test one endpoint carefully"""
    print(f"\n🔍 Testing: {name}")
    print(f"URL: {url}")
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, timeout=TIMEOUT)
        else:
            print(f"❌ Unsupported method: {method}")
            return
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        print(f"Status: {response.status_code} | Time: {response_time}ms")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ SUCCESS")
                print("📄 Response:")
                print(json.dumps(data, indent=2, default=str)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2, default=str))
            except:
                print("✅ SUCCESS (Non-JSON)")
                print(f"Response: {response.text[:200]}...")
        elif response.status_code == 429:
            print("⚠️ RATE LIMITED")
            print(f"Response: {response.text}")
        else:
            print(f"❌ FAILED ({response.status_code})")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("⏱️ TIMEOUT")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    print("🚀 CAREFUL API TESTING (Rate Limit Aware)")
    print(f"Organization: {ORG_ID}")
    print(f"Delay between tests: {DELAY}s")
    print("="*60)
    
    # Test endpoints one by one with delays
    endpoints = [
        ("Health Check", f"{BASE_URL}/health", "GET"),
        ("Status Basic", f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}", "GET"),
        ("Patient Stats Basic", f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats", "GET"),
        ("Status with Health Check", f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}?include_health_check=true", "GET"),
        ("Patient Stats with Details (limit=2)", f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats?include_details=true&limit=2", "GET"),
    ]
    
    for i, (name, url, method) in enumerate(endpoints):
        test_single_endpoint(name, url, method)
        
        if i < len(endpoints) - 1:  # Don't delay after last test
            print(f"\n⏳ Waiting {DELAY}s to respect rate limits...")
            time.sleep(DELAY)
    
    print(f"\n{'='*60}")
    print("✅ CAREFUL TESTING COMPLETED")

if __name__ == "__main__":
    main() 