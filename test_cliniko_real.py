#!/usr/bin/env python3
"""
Test script to verify real Cliniko credential retrieval and API validation
"""

import sys
import os
import logging
import requests
import json

# Set environment variables for testing
os.environ['CREDENTIALS_ENCRYPTION_KEY'] = "LZNPDKzSRIiW8iap2C-0VQKe9wewNfnCvCScNKy_7xY="

# Add src to path
sys.path.append('src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_credentials_via_api():
    """Test credential retrieval via the existing API endpoint"""
    surf_rehab_org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
    
    try:
        logger.info("🧪 Testing Cliniko credentials via API endpoint")
        
        # Test 1: Retrieve credentials via API
        logger.info("📥 Test 1: Retrieving credentials via API...")
        
        url = f"https://routiq-backend-v10-production.up.railway.app/api/v1/admin/clerk/credentials/{surf_rehab_org_id}/cliniko"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Credentials retrieved via API")
            
            credentials = data.get('credentials', {})
            api_key = credentials.get('api_key')
            api_url = credentials.get('api_url', 'https://api.au4.cliniko.com/v1')
            
            if api_key:
                logger.info(f"   - API Key: {api_key[:20]}...")
                logger.info(f"   - Region: {credentials.get('region')}")
                logger.info(f"   - API URL: {api_url}")
            else:
                logger.error("❌ No API key found in credentials")
                return False
        else:
            logger.error(f"❌ Failed to retrieve credentials: {response.status_code}")
            return False
        
        # Test 2: Validate credentials against Cliniko API
        logger.info("🔍 Test 2: Validating credentials against Cliniko API...")
        
        # Create auth header
        import base64
        auth_string = f"{api_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Accept": "application/json",
            "User-Agent": "Routiq-Backend-Test"
        }
        
        # Test with patients endpoint (we know this works)
        test_url = f"{api_url}/patients?per_page=1"
        api_response = requests.get(test_url, headers=headers)
        
        if api_response.status_code == 200:
            api_data = api_response.json()
            total_patients = api_data.get('total_entries', 0)
            logger.info("✅ Cliniko API validation successful")
            logger.info(f"   - Total patients in system: {total_patients}")
            
            # Show first patient as example
            if api_data.get('patients'):
                first_patient = api_data['patients'][0]
                logger.info(f"   - Sample patient: {first_patient.get('first_name', 'N/A')} {first_patient.get('last_name', 'N/A')}")
        else:
            logger.error(f"❌ Cliniko API validation failed: {api_response.status_code}")
            logger.error(f"   Response: {api_response.text[:200]}")
            return False
        
        logger.info("🎉 All tests passed! Credentials are working end-to-end.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_credentials_via_api()
    sys.exit(0 if success else 1) 