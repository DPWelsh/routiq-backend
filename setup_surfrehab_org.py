#!/usr/bin/env python3
"""
Setup script for SurfRehab organization Cliniko integration
This script helps configure the organization for testing upcoming appointments
"""

import os
import json
import base64
from datetime import datetime, timezone
from cryptography.fernet import Fernet

def setup_surfrehab_org():
    """
    Setup SurfRehab organization with Cliniko service configuration
    This is a template script - you'll need to provide actual credentials
    """
    
    organization_id = "surfrehab"
    
    print(f"🏥 Setting up {organization_id} organization for Cliniko integration...")
    print()
    
    # Step 1: Check environment variables
    print("📋 STEP 1: Environment Variables Check")
    required_env_vars = [
        'DATABASE_URL',
        'SUPABASE_DB_URL', 
        'CREDENTIALS_ENCRYPTION_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"   ❌ {var}: Not set")
        else:
            print(f"   ✅ {var}: Set")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your production environment.")
        return False
    
    print("\n✅ All required environment variables are set")
    
    # Step 2: Sample SQL commands
    print("\n📋 STEP 2: Database Setup Commands")
    print("Execute these SQL commands in your production database:")
    print()
    
    # Organization setup
    print("-- 1. Create/Update Organization")
    print(f"""
INSERT INTO organizations (id, name, slug, subscription_status, subscription_plan, created_at, updated_at)
VALUES ('{organization_id}', 'SurfRehab', 'surfrehab', 'active', 'professional', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    updated_at = NOW();
""")
    
    # Service configuration
    print("-- 2. Create Cliniko Service Configuration")
    print(f"""
INSERT INTO organization_services (
    organization_id, service_name, is_active, is_primary, sync_enabled,
    service_config, created_at, updated_at
) VALUES (
    '{organization_id}', 'cliniko', true, true, true,
    '{{"region": "au", "api_version": "v1"}}',
    NOW(), NOW()
) ON CONFLICT (organization_id, service_name) DO UPDATE SET
    is_active = true,
    sync_enabled = true,
    updated_at = NOW();
""")
    
    # Step 3: Credentials setup
    print("\n-- 3. Add Cliniko API Credentials")
    print("⚠️  You'll need to encrypt actual Cliniko credentials using the CREDENTIALS_ENCRYPTION_KEY")
    print()
    
    # Show how to encrypt credentials
    encryption_key = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
    if encryption_key:
        cipher_suite = Fernet(encryption_key.encode())
        
        # Sample credentials structure
        sample_credentials = {
            "api_key": "YOUR_CLINIKO_API_KEY_HERE",
            "api_url": "https://api.au4.cliniko.com/v1",  # Adjust for your Cliniko region
            "region": "au",
            "account_name": "SurfRehab"
        }
        
        # Encrypt sample (don't use in production!)
        encrypted_sample = cipher_suite.encrypt(json.dumps(sample_credentials).encode())
        encrypted_b64 = base64.b64encode(encrypted_sample).decode()
        
        print(f"-- Replace 'YOUR_CLINIKO_API_KEY_HERE' with actual API key")
        print(f"""
INSERT INTO api_credentials (
    organization_id, service_name, is_active,
    credentials_encrypted, created_at, updated_at, last_validated_at
) VALUES (
    '{organization_id}', 'cliniko', true,
    '{{"encrypted_data": "{encrypted_b64}"}}',
    NOW(), NOW(), NOW()
) ON CONFLICT (organization_id, service_name) DO UPDATE SET
    is_active = true,
    credentials_encrypted = EXCLUDED.credentials_encrypted,
    updated_at = NOW();
""")
    
    # Step 4: Testing commands
    print("\n📋 STEP 3: Testing Commands")
    print("Once the database is set up, test with these API calls:")
    print()
    print("# 1. Test sync")
    print(f'curl -X POST "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/sync/{organization_id}"')
    print()
    print("# 2. Check summary")
    print(f'curl -X GET "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/patients/{organization_id}/active/summary"')
    print()
    print("# 3. List upcoming appointments")
    print(f'curl -X GET "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/patients/{organization_id}/upcoming"')
    
    # Step 5: Improved sync logic info
    print("\n📋 STEP 4: Improved Sync Logic")
    print("✅ The sync service has been improved to include patients with:")
    print("   - Recent appointments (last 45 days)")
    print("   - Upcoming appointments (next 30 days)")
    print("   - OR BOTH")
    print()
    print("🎯 Key improvements:")
    print("   - Patients with ONLY upcoming appointments are now included")
    print("   - New /upcoming endpoint shows patients with future appointments")
    print("   - Better visibility of upcoming appointments in summary")
    
    print("\n🎉 Setup guide complete!")
    print(f"Once you've added the actual Cliniko API credentials for {organization_id},")
    print("the sync should automatically detect and include upcoming appointments.")
    
    return True

if __name__ == "__main__":
    setup_surfrehab_org() 