#!/usr/bin/env python3
"""
Quick Demo Test for the System Health Endpoint
Tests the specific endpoint: /api/v1/admin/monitoring/system-health
"""

import requests
import json
import time
from datetime import datetime

def test_system_health_endpoint():
    """Test the system health endpoint with detailed reporting"""
    
    base_url = "https://routiq-backend-v10-production.up.railway.app"
    endpoint = "/api/v1/admin/monitoring/system-health"
    full_url = f"{base_url}{endpoint}"
    
    print("🔍 Testing System Health Endpoint")
    print("=" * 60)
    print(f"URL: {full_url}")
    print(f"Method: GET")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        print("📡 Making request...")
        start_time = time.time()
        
        response = requests.get(
            full_url,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Routiq-System-Health-Test/1.0'
            },
            timeout=30
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ Request completed in {response_time:.3f}s")
        print()
        
        # Response details
        print("📊 Response Details:")
        print("-" * 30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
        print(f"Response Time: {response_time:.3f}s")
        print()
        
        # Interpret status code
        if response.status_code == 200:
            print("🎉 SUCCESS: Endpoint is accessible and working!")
            
            try:
                data = response.json()
                print("\n📋 Response Data:")
                print("-" * 30)
                print(json.dumps(data, indent=2))
                
                # Analyze system health data
                if isinstance(data, dict):
                    print("\n🔍 Health Analysis:")
                    print("-" * 30)
                    
                    # Check for common health indicators
                    if 'database_connected' in data:
                        db_status = "✅ Connected" if data['database_connected'] else "❌ Disconnected"
                        print(f"Database: {db_status}")
                    
                    if 'connection_pool' in data:
                        pool_info = data['connection_pool']
                        if pool_info:
                            print(f"Connection Pool: ✅ Active")
                            if 'minconn' in pool_info:
                                print(f"  Min Connections: {pool_info['minconn']}")
                            if 'maxconn' in pool_info:
                                print(f"  Max Connections: {pool_info['maxconn']}")
                        else:
                            print("Connection Pool: ⚠️ No info available")
                    
                    if 'status' in data:
                        status = data['status']
                        status_icon = "✅" if status == "healthy" else "⚠️"
                        print(f"System Status: {status_icon} {status}")
                    
                    if 'timestamp' in data:
                        print(f"Server Time: {data['timestamp']}")
                
            except json.JSONDecodeError:
                print("⚠️ Response is not valid JSON")
                print(f"Raw response: {response.text[:500]}")
        
        elif response.status_code == 401:
            print("🔐 AUTHENTICATION REQUIRED")
            print("This endpoint requires proper authentication (expected behavior)")
            print("The endpoint exists and is responding correctly!")
            
        elif response.status_code == 403:
            print("🔒 FORBIDDEN")
            print("This endpoint requires proper authorization (expected behavior)")
            print("The endpoint exists and is responding correctly!")
            
        elif response.status_code == 404:
            print("❌ NOT FOUND")
            print("The endpoint may not exist or the route is not configured")
            
        elif response.status_code >= 500:
            print(f"🚨 SERVER ERROR ({response.status_code})")
            print("There's an issue with the server")
            print(f"Error details: {response.text[:500]}")
            
        else:
            print(f"⚠️ UNEXPECTED STATUS: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        
        print()
        print("🔗 Related Endpoints to Test:")
        print("- GET /health (basic health check)")
        print("- GET /api/v1/admin/sync-logs/all")
        print("- GET /api/v1/admin/organization-services/{org_id}")
        
    except requests.exceptions.Timeout:
        print("⏱️ REQUEST TIMEOUT")
        print("The request took longer than 30 seconds")
        
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR")
        print("Could not connect to the server")
        print("Please check if the server is running and accessible")
        
    except Exception as e:
        print(f"💥 UNEXPECTED ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_system_health_endpoint() 