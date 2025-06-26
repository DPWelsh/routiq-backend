#!/usr/bin/env python3
"""
Test script to verify the full sync functionality includes all patients
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-production.up.railway.app"  # Replace with your actual API URL
ORGANIZATION_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
TEST_PATIENT_ID = "1716280232295540460"

def test_full_sync():
    """Test the full sync functionality"""
    
    print("🧪 Testing Full Patient Sync")
    print("=" * 50)
    
    # Step 1: Start a full sync
    print("📤 Starting full sync...")
    sync_response = requests.post(
        f"{BASE_URL}/api/sync/start/{ORGANIZATION_ID}?sync_mode=full"
    )
    
    if sync_response.status_code != 200:
        print(f"❌ Failed to start sync: {sync_response.status_code}")
        print(sync_response.text)
        return False
    
    sync_data = sync_response.json()
    sync_id = sync_data.get("sync_id")
    print(f"✅ Sync started: {sync_id}")
    print(f"   Mode: {sync_data.get('sync_mode')}")
    print(f"   Message: {sync_data.get('message')}")
    
    # Step 2: Monitor sync progress
    print("\n⏳ Monitoring sync progress...")
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_response = requests.get(f"{BASE_URL}/api/sync/status/{sync_id}")
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            break
        
        status_data = status_response.json()
        status = status_data.get("status")
        progress = status_data.get("progress_percentage", 0)
        current_step = status_data.get("current_step", "")
        
        print(f"   {progress}% - {status}: {current_step}")
        
        if status in ["completed", "failed"]:
            break
        
        time.sleep(5)  # Wait 5 seconds before checking again
    
    # Step 3: Check final results
    if status == "completed":
        print(f"\n✅ Sync completed successfully!")
        print(f"   Patients found: {status_data.get('patients_found', 0)}")
        print(f"   Patients stored: {status_data.get('active_patients_stored', 0)}")
        
        # Step 4: Check if test patient is now in database
        print(f"\n🔍 Checking if test patient {TEST_PATIENT_ID} is now synced...")
        
        # Query the patients endpoint to see if our test patient is there
        patients_response = requests.get(f"{BASE_URL}/api/cliniko/active-patients/{ORGANIZATION_ID}")
        
        if patients_response.status_code == 200:
            patients_data = patients_response.json()
            active_patients = patients_data.get("active_patients", [])
            
            # Look for our test patient
            test_patient_found = False
            for patient in active_patients:
                if patient.get("cliniko_patient_id") == TEST_PATIENT_ID:
                    test_patient_found = True
                    print(f"✅ Test patient found in database!")
                    print(f"   Name: {patient.get('name')}")
                    print(f"   Email: {patient.get('email')}")
                    print(f"   Phone: {patient.get('phone')}")
                    print(f"   Active: {patient.get('is_active')}")
                    print(f"   Last synced: {patient.get('last_synced_at')}")
                    break
            
            if not test_patient_found:
                print(f"❌ Test patient {TEST_PATIENT_ID} not found in synced patients")
                print(f"   Total patients synced: {len(active_patients)}")
                return False
            
            return True
        else:
            print(f"❌ Failed to get patients: {patients_response.status_code}")
            return False
    
    elif status == "failed":
        print(f"❌ Sync failed!")
        errors = status_data.get("errors", [])
        for error in errors:
            print(f"   Error: {error}")
        return False
    
    else:
        print(f"⏰ Sync timed out (status: {status})")
        return False

def test_active_vs_full_comparison():
    """Compare active sync vs full sync results"""
    
    print("\n🔬 Comparing Active vs Full Sync")
    print("=" * 50)
    
    # Test active sync first
    print("📤 Starting active sync...")
    active_response = requests.post(f"{BASE_URL}/api/sync/start/{ORGANIZATION_ID}?sync_mode=active")
    
    if active_response.status_code == 200:
        active_data = active_response.json()
        print(f"✅ Active sync started: {active_data.get('sync_id')}")
        
        # Wait for completion (simplified)
        time.sleep(30)
        
        # Get dashboard data after active sync
        dashboard_response = requests.get(f"{BASE_URL}/api/sync/dashboard/{ORGANIZATION_ID}")
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            active_count = dashboard_data.get("patient_stats", {}).get("total_patients", 0)
            print(f"📊 Active sync result: {active_count} patients")
        
        # Now test full sync
        print("\n📤 Starting full sync...")
        full_response = requests.post(f"{BASE_URL}/api/sync/start/{ORGANIZATION_ID}?sync_mode=full")
        
        if full_response.status_code == 200:
            full_data = full_response.json()
            print(f"✅ Full sync started: {full_data.get('sync_id')}")
            
            # Wait for completion
            time.sleep(60)  # Full sync takes longer
            
            # Get dashboard data after full sync
            dashboard_response = requests.get(f"{BASE_URL}/api/sync/dashboard/{ORGANIZATION_ID}")
            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                full_count = dashboard_data.get("patient_stats", {}).get("total_patients", 0)
                print(f"📊 Full sync result: {full_count} patients")
                
                if full_count > active_count:
                    print(f"✅ Full sync found {full_count - active_count} additional patients!")
                    return True
                else:
                    print(f"⚠️  Full sync didn't find more patients than active sync")
                    return False

if __name__ == "__main__":
    print(f"🚀 Testing Full Sync at {datetime.now()}")
    print(f"🎯 Target: Find test patient {TEST_PATIENT_ID}")
    print(f"🏢 Organization: {ORGANIZATION_ID}")
    
    success = test_full_sync()
    
    if success:
        print(f"\n🎉 SUCCESS: Full sync test passed!")
        print(f"   The new test patient is now properly synced.")
    else:
        print(f"\n❌ FAILED: Full sync test failed!")
        print(f"   The issue may still exist or need more investigation.")
    
    # Optional: Run comparison test
    # test_active_vs_full_comparison() 