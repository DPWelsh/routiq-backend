#!/usr/bin/env python3
"""
Test ALL Patients Sync
Verifies that ALL patients from Cliniko are synced to the database
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def main():
    print("🧪 TESTING ALL PATIENTS SYNC")
    print("="*50)
    
    # Step 1: Get baseline counts
    print("\n📊 STEP 1: Getting Baseline Counts")
    
    # Cliniko API count
    cliniko_response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
    if cliniko_response.status_code == 200:
        cliniko_data = cliniko_response.json()
        cliniko_total = cliniko_data.get('total_patients_available', 0)
        print(f"✅ Cliniko Total Patients: {cliniko_total}")
    else:
        print(f"❌ Failed to get Cliniko count: {cliniko_response.status_code}")
        return
    
    # Database count before sync
    db_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
    if db_response.status_code == 200:
        db_data = db_response.json()
        db_before = db_data.get('total_patients', 0)
        print(f"📊 Database Before Sync: {db_before} patients")
    else:
        print(f"❌ Failed to get DB count: {db_response.status_code}")
        return
    
    # Step 2: Run ALL patients sync
    print(f"\n🚀 STEP 2: Running ALL Patients Sync")
    sync_response = requests.post(f"{BASE_URL}/api/v1/cliniko/sync-all/{ORG_ID}")
    
    if sync_response.status_code != 200:
        print(f"❌ Failed to start sync: {sync_response.status_code}")
        print(f"Response: {sync_response.text}")
        return
    
    sync_data = sync_response.json()
    print(f"✅ Sync Started: {sync_data.get('message')}")
    
    # Step 3: Wait for completion
    print(f"\n⏳ STEP 3: Waiting for Sync Completion")
    max_wait = 120  # 2 minutes max
    wait_time = 0
    check_interval = 5  # Check every 5 seconds for more responsive updates
    
    while wait_time < max_wait:
        time.sleep(check_interval)
        wait_time += check_interval
        
        # Check latest sync log
        logs_response = requests.get(f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=1")
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            if logs_data.get('logs'):
                latest_log = logs_data['logs'][0]
                status = latest_log.get('status')
                operation_type = latest_log.get('operation_type')
                
                progress_dots = "." * (wait_time // check_interval % 4)
                print(f"   [{wait_time:3d}s] Status: {status} | Type: {operation_type} | Monitoring{progress_dots}")
                
                if status in ['completed', 'failed']:
                    if status == 'completed':
                        # Parse metadata
                        metadata = latest_log.get('metadata', {})
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except:
                                pass
                        
                        records_processed = latest_log.get('records_processed', 0)
                        records_success = latest_log.get('records_success', 0)
                        sync_type = metadata.get('sync_type', 'unknown') if isinstance(metadata, dict) else 'unknown'
                        
                        print(f"✅ Sync Completed!")
                        print(f"   - Type: {sync_type}")
                        print(f"   - Processed: {records_processed}")
                        print(f"   - Success: {records_success}")
                        print(f"   - Success Rate: {records_success/records_processed*100:.1f}%" if records_processed > 0 else "0%")
                        
                        if sync_type == 'full_patients':
                            print(f"✅ Confirmed: FULL patients sync used!")
                        else:
                            print(f"⚠️  Warning: Expected 'full_patients' but got '{sync_type}'")
                        
                        break
                    else:
                        print(f"❌ Sync Failed!")
                        return
        
        if wait_time >= max_wait:
            print(f"⏰ Timeout after {max_wait}s")
            return
    
    # Step 4: Verify final counts
    print(f"\n📊 STEP 4: Verifying Final Counts")
    
    # Get final database count
    final_db_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
    if final_db_response.status_code == 200:
        final_db_data = final_db_response.json()
        db_after = final_db_data.get('total_patients', 0)
        print(f"📊 Database After Sync: {db_after} patients")
        print(f"📈 Change: {db_after - db_before:+d} patients")
    else:
        print(f"❌ Failed to get final DB count")
        return
    
    # Step 5: Results analysis
    print(f"\n🎯 STEP 5: Results Analysis")
    print(f"📊 Summary:")
    print(f"   - Cliniko Total:    {cliniko_total}")
    print(f"   - Database Before:  {db_before}")  
    print(f"   - Database After:   {db_after}")
    print(f"   - Expected Change:  {cliniko_total - db_before:+d}")
    print(f"   - Actual Change:    {db_after - db_before:+d}")
    
    # Success criteria
    if db_after >= cliniko_total * 0.95:  # Allow 5% tolerance
        print(f"\n🎉 SUCCESS! ALL patients sync working correctly!")
        print(f"   ✅ {db_after}/{cliniko_total} patients synced ({db_after/cliniko_total*100:.1f}%)")
    else:
        print(f"\n❌ ISSUE: Not all patients synced")
        print(f"   📉 {db_after}/{cliniko_total} patients synced ({db_after/cliniko_total*100:.1f}%)")
        missing = cliniko_total - db_after
        print(f"   🚨 {missing} patients missing from database")

if __name__ == "__main__":
    main() 