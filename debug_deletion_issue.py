#!/usr/bin/env python3
"""
Debug why patient deletion isn't working
"""
import requests
import json

BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def main():
    print("🔍 DEBUG: Why isn't patient deletion working?")
    print("=" * 60)
    
    # 1. Check Cliniko patient count
    cliniko_response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
    if cliniko_response.status_code == 200:
        cliniko_data = cliniko_response.json()
        cliniko_total = cliniko_data.get('total_patients_available', 0)
        print(f"✅ Cliniko has: {cliniko_total} patients")
    else:
        print(f"❌ Failed to get Cliniko count")
        return
    
    # 2. Check database count
    db_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
    if db_response.status_code == 200:
        db_data = db_response.json()
        db_total = db_data.get('total_patients', 0)
        db_active = db_data.get('active_patients', 0)
        print(f"📊 Database has: {db_total} total, {db_active} active")
    else:
        print(f"❌ Failed to get DB count")
        return
    
    # 3. Analysis
    print(f"\n🧮 ANALYSIS:")
    print(f"   Expected: Database should have {cliniko_total} patients")
    print(f"   Actual: Database has {db_total} patients")
    print(f"   Difference: {db_total - cliniko_total} extra patients")
    
    if db_total == cliniko_total:
        print(f"✅ PERFECT SYNC! Database matches Cliniko exactly.")
    else:
        print(f"❌ SYNC ISSUE: Database has {db_total - cliniko_total} extra patients that need to be deleted")
        print(f"\n🤔 POSSIBLE REASONS:")
        print(f"   1. Deletion logic not finding the right patients")
        print(f"   2. The 'extra' patient actually EXISTS in Cliniko")
        print(f"   3. Database constraint preventing deletion")
        print(f"   4. Transaction rollback issue")
        
        # Let's try to identify the issue
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Check if all {db_total} patients in DB have valid Cliniko IDs")
        print(f"   2. Verify that deletion query is actually running")
        print(f"   3. Check for foreign key constraints that might prevent deletion")

if __name__ == "__main__":
    main() 