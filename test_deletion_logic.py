#!/usr/bin/env python3
"""
Test the deletion logic manually to see what patients would be deactivated
"""

import requests
import json

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def main():
    print("🧪 TESTING DELETION LOGIC MANUALLY")
    print("=" * 50)
    
    # Step 1: Get current counts
    print("📊 Getting current status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
        data = response.json()
        db_total = data.get('total_patients', 0)
        db_active = data.get('active_patients', 0)
        print(f"   Database: {db_total} total, {db_active} active")
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return
    
    # Step 2: Get Cliniko count
    print("📊 Getting Cliniko count...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
        data = response.json()
        cliniko_total = data.get('total_patients_available', 0)
        print(f"   Cliniko API: {cliniko_total} patients")
    except Exception as e:
        print(f"❌ Error getting Cliniko count: {e}")
        return
    
    # Step 3: Analysis
    print(f"\n🔍 ANALYSIS:")
    print(f"   Expected database total after sync: {cliniko_total}")
    print(f"   Actual database total: {db_total}")
    print(f"   Patients that should be deactivated: {db_total - cliniko_total}")
    
    if db_total > cliniko_total:
        print(f"\n🎯 ISSUE CONFIRMED:")
        print(f"   The deletion logic should deactivate {db_total - cliniko_total} patient(s)")
        print(f"   But all {db_active} patients are still active")
        
        print(f"\n🔧 POSSIBLE CAUSES:")
        print(f"   1. ID format mismatch (string vs int)")
        print(f"   2. Deletion logic not being called")
        print(f"   3. Deletion SQL query failing silently")
        print(f"   4. Transaction rollback")
        
        print(f"\n🛠️ NEXT STEPS:")
        print(f"   1. Check if the deletion step actually runs")
        print(f"   2. Compare actual patient IDs from both sources")
        print(f"   3. Test the SQL query manually")
        
        # Try to run a sync and immediately check logs
        print(f"\n🚀 RUNNING A QUICK SYNC TEST...")
        try:
            sync_response = requests.post(f"{BASE_URL}/api/v1/cliniko/sync-all/{ORG_ID}")
            if sync_response.status_code == 200:
                print(f"   ✅ Sync started successfully")
                print(f"   💡 Check the server logs for debug output from deletion logic")
            else:
                print(f"   ❌ Failed to start sync: {sync_response.status_code}")
        except Exception as e:
            print(f"   ❌ Error starting sync: {e}")
            
    else:
        print(f"\n✅ COUNTS MATCH:")
        print(f"   Database and Cliniko have same number of patients")
        print(f"   No deletion should occur")

if __name__ == "__main__":
    main() 