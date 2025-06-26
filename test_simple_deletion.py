#!/usr/bin/env python3
"""
Quick test to verify deletion logic without full sync
"""
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.cliniko_sync_service import cliniko_sync_service
from src.database import db


def test_deletion_logic_simple():
    """Test just the deletion logic part"""
    print("🧪 SIMPLE DELETION LOGIC TEST")
    print("=" * 50)
    
    # Get organization ID
    org_id = 'org_2ifkR2FDLiVRz6XFhVPIz7DYBXX'
    
    # Step 1: Get current patient counts
    print("📊 Current database status:")
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE is_active = true) as active FROM patients WHERE organization_id = %s", (org_id,))
        result = cursor.fetchone()
        total_db = result['total']
        active_db = result['active']
        print(f"   Database: {total_db} total, {active_db} active")
    
    # Step 2: Simulate what happens in deletion check
    print("\n🔍 Testing deletion logic...")
    
    # Get Cliniko credentials
    try:
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(org_id)
        if not credentials:
            print("❌ No credentials found")
            return
        
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = cliniko_sync_service._create_auth_headers(credentials["api_key"])
        
        print("📡 Fetching just 10 patients from Cliniko (quick test)...")
        url = f"{api_url}/patients"
        params = {'per_page': 10}  # Just get 10 for testing
        
        data = cliniko_sync_service._make_cliniko_request(url, headers, params)
        if not data:
            print("❌ No data from Cliniko")
            return
        
        patients = data.get('patients', [])
        print(f"✅ Got {len(patients)} patients from Cliniko API")
        
        # Test the deletion logic with just these few patients
        print("\n🔧 Testing deletion logic (with limited dataset)...")
        start_time = time.time()
        
        deleted_count = cliniko_sync_service._handle_deleted_patients(org_id, patients, 0)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"✅ Deletion logic completed in {elapsed:.2f} seconds")
        print(f"📊 Deleted/Deactivated: {deleted_count} patients")
        
        # Check final status
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE is_active = true) as active FROM patients WHERE organization_id = %s", (org_id,))
            result = cursor.fetchone()
            final_total = result['total']
            final_active = result['active']
            print(f"📊 Final status: {final_total} total, {final_active} active")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_deletion_logic_simple() 