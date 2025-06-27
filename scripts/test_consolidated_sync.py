#!/usr/bin/env python3
"""
Test Consolidated Sync Endpoint
Verify the new unified sync endpoint with different modes
"""

import requests
import json
import time

BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def test_sync_modes():
    """Test different sync modes"""
    print("🧪 Testing Consolidated Sync Endpoint")
    print("=" * 50)
    
    modes = [
        ("comprehensive", "Recommended mode with full analysis"),
        ("basic", "Legacy mode - patients only"),
        ("patients-only", "Alias for basic mode")
    ]
    
    for mode, description in modes:
        print(f"\n🔄 Testing mode: {mode}")
        print(f"📝 Description: {description}")
        
        try:
            # Test the new unified endpoint
            url = f"{BASE_URL}/api/v1/cliniko/sync/{ORG_ID}"
            params = {"mode": mode}
            
            print(f"📡 Calling: {url}?mode={mode}")
            response = requests.post(url, params=params, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('message', 'No message')}")
                
                if data.get('result'):
                    print(f"📋 Mode: {data['result'].get('sync_mode', 'unknown')}")
                    if data['result'].get('recommendation'):
                        print(f"💡 Recommendation: {data['result']['recommendation']}")
                    if data['result'].get('deprecation_warning'):
                        print(f"⚠️  Warning: {data['result']['deprecation_warning']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 30)
    
    # Test invalid mode
    print(f"\n🚫 Testing invalid mode: 'invalid'")
    try:
        url = f"{BASE_URL}/api/v1/cliniko/sync/{ORG_ID}"
        params = {"mode": "invalid"}
        
        response = requests.post(url, params=params, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Correctly rejected: {data.get('detail', 'No detail')}")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_deprecated_endpoint():
    """Test the deprecated endpoint"""
    print(f"\n🗂️  Testing Deprecated Endpoint")
    print("=" * 50)
    
    try:
        url = f"{BASE_URL}/api/v1/cliniko/sync-comprehensive/{ORG_ID}"
        print(f"📡 Calling deprecated endpoint: {url}")
        
        response = requests.post(url, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('message', 'No message')}")
            
            if data.get('result', {}).get('deprecation_warning'):
                print(f"⚠️  Deprecation Warning: {data['result']['deprecation_warning']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_default_mode():
    """Test default mode (should be comprehensive)"""
    print(f"\n🎯 Testing Default Mode")
    print("=" * 50)
    
    try:
        # Call without mode parameter - should default to comprehensive
        url = f"{BASE_URL}/api/v1/cliniko/sync/{ORG_ID}"
        print(f"📡 Calling without mode parameter: {url}")
        
        response = requests.post(url, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('message', 'No message')}")
            
            if data.get('result'):
                mode = data['result'].get('sync_mode', 'unknown')
                print(f"📋 Default mode detected: {mode}")
                
                if mode == "comprehensive":
                    print("✅ Correct! Default mode is comprehensive")
                else:
                    print(f"❌ Unexpected default mode: {mode}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🚀 Consolidated Sync Endpoint Test Suite")
    print("🎯 This will test the new unified sync endpoint")
    print("⚠️  Note: This will trigger actual sync operations!")
    print()
    
    # Run tests
    test_default_mode()
    test_sync_modes() 
    test_deprecated_endpoint()
    
    print(f"\n🎉 Test Suite Complete!")
    print(f"💡 Recommendation: Update frontend to use mode=comprehensive") 