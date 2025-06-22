#!/usr/bin/env python3
"""
Debug Cliniko Credentials Retrieval
Test the credentials decryption process directly
"""

import os
import sys
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'
os.environ['CREDENTIALS_ENCRYPTION_KEY'] = 'LZNPDKzSRIiW8iap2C-0VQKe9wewNfnCvCScNKy_7xY='

from database import db

def debug_credentials():
    organization_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    
    print(f"🔍 Debugging Cliniko credentials for organization: {organization_id}")
    
    try:
        # 1. Check if organization exists
        org_check = db.execute_query("SELECT id, name FROM organizations WHERE id = %s", (organization_id,))
        if org_check:
            print(f"✅ Organization found: {org_check[0]['name']}")
        else:
            print(f"❌ Organization not found in database")
            return
        
        # 2. Check service_credentials table
        print(f"\n🔍 Checking service_credentials table...")
        creds_query = """
            SELECT organization_id, service_name, credentials_encrypted, is_active, created_at
            FROM service_credentials 
            WHERE organization_id = %s
            ORDER BY created_at DESC
        """
        
        all_creds = db.execute_query(creds_query, (organization_id,))
        
        if not all_creds:
            print(f"❌ No credentials found for organization {organization_id}")
            return
        
        print(f"✅ Found {len(all_creds)} credential entries:")
        for cred in all_creds:
            print(f"  • {cred['service_name']}: active={cred['is_active']}, created={cred['created_at']}")
        
        # 3. Focus on Cliniko credentials
        cliniko_creds = [c for c in all_creds if c['service_name'] == 'cliniko']
        
        if not cliniko_creds:
            print(f"❌ No Cliniko credentials found")
            return
        
        print(f"\n🔍 Cliniko credentials details:")
        cliniko_cred = cliniko_creds[0]
        print(f"  • Active: {cliniko_cred['is_active']}")
        print(f"  • Created: {cliniko_cred['created_at']}")
        print(f"  • Encrypted data type: {type(cliniko_cred['credentials_encrypted'])}")
        print(f"  • Encrypted data preview: {str(cliniko_cred['credentials_encrypted'])[:100]}...")
        
        # 4. Try to decrypt
        print(f"\n🔓 Attempting to decrypt credentials...")
        
        encryption_key = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
        if not encryption_key:
            print(f"❌ No encryption key found")
            return
        
        cipher_suite = Fernet(encryption_key.encode())
        encrypted_data = cliniko_cred['credentials_encrypted']
        
        try:
            # Handle both formats
            if isinstance(encrypted_data, str):
                try:
                    # Try to parse as JSON first (old format)
                    encrypted_json = json.loads(encrypted_data)
                    if isinstance(encrypted_json, dict) and "encrypted_data" in encrypted_json:
                        print(f"  • Format: Old JSON format")
                        encrypted_bytes = base64.b64decode(encrypted_json["encrypted_data"].encode())
                    else:
                        print(f"  • Format: Direct base64 string")
                        encrypted_bytes = base64.b64decode(encrypted_data.encode())
                except json.JSONDecodeError:
                    print(f"  • Format: Direct base64 string (JSON decode failed)")
                    encrypted_bytes = base64.b64decode(encrypted_data.encode())
            else:
                print(f"  • Format: Dict format")
                encrypted_json = encrypted_data
                if "encrypted_data" in encrypted_json:
                    encrypted_bytes = base64.b64decode(encrypted_json["encrypted_data"].encode())
                else:
                    encrypted_bytes = base64.b64decode(str(encrypted_json).encode())
            
            # Decrypt
            decrypted_data = cipher_suite.decrypt(encrypted_bytes)
            credentials = json.loads(decrypted_data.decode())
            
            print(f"✅ Decryption successful!")
            print(f"  • Credentials keys: {list(credentials.keys())}")
            print(f"  • Has api_key: {'api_key' in credentials}")
            
            if 'api_key' in credentials:
                api_key = credentials['api_key']
                print(f"  • API key length: {len(api_key)}")
                print(f"  • API key preview: {api_key[:10]}...")
            
            print(f"  • Full credentials: {json.dumps(credentials, indent=2)}")
            
        except Exception as decrypt_error:
            print(f"❌ Decryption failed: {decrypt_error}")
            print(f"  • Error type: {type(decrypt_error).__name__}")
            
            # Try alternative decryption approaches
            print(f"\n🔄 Trying alternative decryption methods...")
            
            # Method 1: Direct base64 decode
            try:
                if isinstance(encrypted_data, str):
                    direct_bytes = base64.b64decode(encrypted_data.encode())
                    direct_decrypted = cipher_suite.decrypt(direct_bytes)
                    direct_creds = json.loads(direct_decrypted.decode())
                    print(f"✅ Direct method worked: {list(direct_creds.keys())}")
                else:
                    print(f"  • Direct method: Not applicable (not string)")
            except Exception as e:
                print(f"  • Direct method failed: {e}")
            
            # Method 2: Assume JSON wrapper
            try:
                if isinstance(encrypted_data, str):
                    json_data = json.loads(encrypted_data)
                    if "encrypted_data" in json_data:
                        wrapper_bytes = base64.b64decode(json_data["encrypted_data"].encode())
                        wrapper_decrypted = cipher_suite.decrypt(wrapper_bytes)
                        wrapper_creds = json.loads(wrapper_decrypted.decode())
                        print(f"✅ JSON wrapper method worked: {list(wrapper_creds.keys())}")
                    else:
                        print(f"  • JSON wrapper method: No 'encrypted_data' key")
                else:
                    print(f"  • JSON wrapper method: Not applicable (not string)")
            except Exception as e:
                print(f"  • JSON wrapper method failed: {e}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_credentials() 