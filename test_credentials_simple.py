#!/usr/bin/env python3
"""
Simple test script to verify credential encryption/decryption without database
"""

import sys
import os
import json
import base64
import logging
from cryptography.fernet import Fernet

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_credential_encryption():
    """Test the credential encryption/decryption mechanism"""
    
    # Set up encryption key
    encryption_key = "LZNPDKzSRIiW8iap2C-0VQKe9wewNfnCvCScNKy_7xY="
    cipher_suite = Fernet(encryption_key.encode())
    
    # Sample credentials (like what we store for Surf Rehab)
    test_credentials = {
        "api_key": "MS0xNjUyNzI0NDI2Njk4OTI1ODQ0LXVKOUR0aHU0SDFUTlJ6NncxUlFhdzY1U0g4OTIveWJN-au4",
        "region": "au4",
        "api_url": "https://api.au4.cliniko.com/v1",
        "base64_credentials": "TVMweE5qVXlOekkwTkRJMk5qazRPVEkxT0RRMExYVktPVVIwYUhVMFNERlVUbEo2Tm5jeFVsRmhkelkxVTBnNE9USXZlV0pOLWF1NDo="
    }
    
    try:
        logger.info("🧪 Testing credential encryption/decryption")
        
        # Test 1: Encrypt credentials
        logger.info("🔐 Test 1: Encrypting credentials...")
        json_data = json.dumps(test_credentials)
        encrypted_data = cipher_suite.encrypt(json_data.encode())
        encrypted_base64 = base64.b64encode(encrypted_data).decode()
        
        # Format as stored in database
        encrypted_json = {"encrypted_data": encrypted_base64}
        logger.info("✅ Credentials encrypted successfully")
        
        # Test 2: Decrypt credentials
        logger.info("🔓 Test 2: Decrypting credentials...")
        
        # Simulate retrieval from database
        encrypted_bytes = base64.b64decode(encrypted_json["encrypted_data"].encode())
        decrypted_data = cipher_suite.decrypt(encrypted_bytes)
        decrypted_credentials = json.loads(decrypted_data.decode())
        
        logger.info("✅ Credentials decrypted successfully")
        
        # Test 3: Verify data integrity
        logger.info("🔍 Test 3: Verifying data integrity...")
        
        if decrypted_credentials == test_credentials:
            logger.info("✅ Data integrity verified - original and decrypted credentials match")
        else:
            logger.error("❌ Data integrity check failed")
            return False
        
        # Test 4: Test Basic Auth header creation
        logger.info("🔑 Test 4: Creating Cliniko auth headers...")
        
        api_key = decrypted_credentials["api_key"]
        auth_string = f"{api_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Routiq-Backend-ActivePatients"
        }
        
        logger.info("✅ Auth headers created successfully")
        logger.info(f"   - Authorization: Basic {encoded_auth[:20]}...")
        logger.info(f"   - User-Agent: {headers['User-Agent']}")
        
        logger.info("🎉 All credential tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_credential_encryption()
    sys.exit(0 if success else 1) 