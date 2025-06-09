#!/usr/bin/env python3
"""
Test script to verify Cliniko credential retrieval and validation
"""

import sys
import os
import logging

# Add src to path
sys.path.append('src')

from services.cliniko_sync_service import ClinikoSyncService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_surf_rehab_credentials():
    """Test credential retrieval and validation for Surf Rehab organization"""
    
    # Surf Rehab organization ID
    surf_rehab_org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
    
    try:
        logger.info("🧪 Starting Cliniko credential test for Surf Rehab")
        
        # Initialize the service
        service = ClinikoSyncService()
        
        # Test 1: Retrieve credentials
        logger.info("📥 Test 1: Retrieving credentials...")
        credentials = service.get_organization_cliniko_credentials(surf_rehab_org_id)
        
        if credentials:
            logger.info("✅ Credentials retrieved successfully")
            logger.info(f"   - API Key: {credentials.get('api_key', 'N/A')[:20]}...")
            logger.info(f"   - Region: {credentials.get('region', 'N/A')}")
            logger.info(f"   - API URL: {credentials.get('api_url', 'N/A')}")
        else:
            logger.error("❌ Failed to retrieve credentials")
            return False
        
        # Test 2: Validate credentials against Cliniko API
        logger.info("🔍 Test 2: Validating credentials...")
        validation_result = service.validate_cliniko_credentials(surf_rehab_org_id)
        
        if validation_result["valid"]:
            logger.info("✅ Credentials validated successfully")
            account_info = validation_result["account_info"]
            logger.info(f"   - Account Name: {account_info['name']}")
            logger.info(f"   - Subdomain: {account_info['subdomain']}")
            logger.info(f"   - Region: {account_info['region']}")
        else:
            logger.error(f"❌ Credential validation failed: {validation_result['error']}")
            return False
        
        logger.info("🎉 All tests passed! Cliniko credentials are working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_surf_rehab_credentials()
    sys.exit(0 if success else 1) 