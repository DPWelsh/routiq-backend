#!/usr/bin/env python3
"""
Test ALL Patients Sync with Real-Time Progress Monitoring
Demonstrates live progress tracking for frontend implementation
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"📋 STEP {step_num}: {title}")
    print(f"{'='*60}")

def print_progress_update(log_data):
    """Print detailed progress information"""
    if not log_data.get('logs'):
        return
        
    log = log_data['logs'][0]
    status = log.get('status', 'unknown')
    metadata = log.get('metadata', {})
    
    # Parse metadata if it's a string
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            pass
    
    step = metadata.get('step', 'unknown')
    progress_percent = metadata.get('progress_percent', 0)
    
    # Different displays based on current step
    if step == "checking_config":
        print(f"   🔍 Validating service configuration...")
    elif step == "validating_credentials":  
        print(f"   🔑 Checking Cliniko API credentials...")
    elif step == "fetching_patients":
        current_page = metadata.get('current_page', 0)
        patients_loaded = metadata.get('patients_loaded', 0)
        print(f"   📡 Fetching from Cliniko API - Page {current_page} ({patients_loaded} patients loaded)")
    elif step == "patients_fetched":
        total_pages = metadata.get('total_pages', 0)
        patients_found = metadata.get('patients_found', 0)
        print(f"   ✅ API Fetch Complete - {patients_found} patients from {total_pages} pages")
    elif step == "processing_patients":
        patients_found = metadata.get('patients_found', 0)
        print(f"   🔍 Processing {patients_found} patients for database...")
    elif step == "storing_patients":
        patients_processed = metadata.get('patients_processed', 0)
        patients_stored = metadata.get('patients_stored', 0)
        total_patients = metadata.get('total_patients', 0)
        if total_patients > 0:
            print(f"   💾 Storing in database: {patients_stored}/{total_patients} patients ({progress_percent:.1f}%)")
        else:
            print(f"   💾 Storing patients in database...")
    elif step == "completed":
        patients_found = metadata.get('patients_found', 0)
        patients_stored = metadata.get('patients_stored', 0)
        success_rate = metadata.get('success_rate', 0)
        print(f"   ✅ COMPLETED: {patients_stored}/{patients_found} patients stored ({success_rate:.1f}% success)")
    else:
        print(f"   🔄 {step} ({progress_percent:.1f}%)")

def main():
    print("🧪 REAL-TIME SYNC MONITORING TEST")
    print("="*60)
    print("This test demonstrates live progress tracking for frontend teams")
    
    # Step 1: Get baseline counts
    print_step(1, "Getting Baseline Patient Counts")
    
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
        last_sync = db_data.get('last_sync_time', 'Never')
        print(f"📅 Last Sync: {last_sync}")
    else:
        print(f"❌ Failed to get DB count: {db_response.status_code}")
        return
    
    # Step 2: Run ALL patients sync
    print_step(2, "Starting ALL Patients Sync with Live Monitoring")
    print("🚀 Initiating sync...")
    
    sync_response = requests.post(f"{BASE_URL}/api/v1/cliniko/sync-all/{ORG_ID}")
    
    if sync_response.status_code != 200:
        print(f"❌ Failed to start sync: {sync_response.status_code}")
        print(f"Response: {sync_response.text}")
        return
    
    sync_data = sync_response.json()
    print(f"✅ Sync Started: {sync_data.get('message')}")
    print(f"⏳ Note: Sync runs in background - waiting 3 seconds for background task to start...")
    
    # Wait for background task to initialize
    time.sleep(3)
    
    # Step 3: Real-time monitoring with detailed progress
    print_step(3, "Real-Time Progress Monitoring")
    print("⏳ Monitoring sync progress (polling every 2 seconds)...")
    print("   Frontend teams: This is the data you can poll from /sync-logs/ endpoint")
    print()
    
    max_wait = 180  # 3 minutes max for real sync
    wait_time = 3    # Already waited 3 seconds
    check_interval = 2  # Check every 2 seconds for responsive updates
    last_step = ""
    last_progress = 0
    
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
                
                # Get current step and progress
                metadata = latest_log.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                
                current_step = metadata.get('step', 'unknown')
                current_progress = metadata.get('progress_percent', 0)
                
                # Only print updates when step or significant progress changes
                if current_step != last_step or abs(current_progress - last_progress) >= 5:
                    print(f"[{wait_time:3d}s] ", end="")
                    print_progress_update(logs_data)
                    last_step = current_step
                    last_progress = current_progress
                
                if status in ['completed', 'failed']:
                    if status == 'completed':
                        # Parse final results
                        records_processed = latest_log.get('records_processed', 0)
                        records_success = latest_log.get('records_success', 0)
                        sync_type = metadata.get('sync_type', 'unknown')
                        success_rate = metadata.get('success_rate', 0)
                        
                        print(f"\n🎉 SYNC COMPLETED SUCCESSFULLY!")
                        print(f"   - Type: {sync_type}")
                        print(f"   - Processed: {records_processed}")
                        print(f"   - Success: {records_success}")
                        print(f"   - Success Rate: {success_rate:.1f}%")
                        
                        if sync_type == 'full_patients':
                            print(f"✅ Confirmed: FULL patients sync used!")
                        else:
                            print(f"⚠️  Warning: Expected 'full_patients' but got '{sync_type}'")
                        
                        break
                    else:
                        print(f"\n❌ SYNC FAILED!")
                        error_details = latest_log.get('error_details', 'Unknown error')
                        print(f"   Error: {error_details}")
                        return
        
        if wait_time >= max_wait:
            print(f"\n⏰ Timeout after {max_wait}s - sync may still be running")
            return
    
    # Step 4: Verify final counts
    print_step(4, "Verifying Final Results")
    
    # Get final database count
    final_db_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
    if final_db_response.status_code == 200:
        final_db_data = final_db_response.json()
        db_after = final_db_data.get('total_patients', 0)
        last_sync = final_db_data.get('last_sync_time', 'Unknown')
        print(f"📊 Database After Sync: {db_after} patients")
        print(f"📈 Change: {db_after - db_before:+d} patients")
        print(f"📅 Last Sync Time: {last_sync}")
    else:
        print(f"❌ Failed to get final DB count")
        return
    
    # Step 5: Results analysis with frontend recommendations
    print_step(5, "Results Analysis & Frontend Recommendations")
    print(f"📊 Summary:")
    print(f"   - Cliniko Total:    {cliniko_total}")
    print(f"   - Database Before:  {db_before}")  
    print(f"   - Database After:   {db_after}")
    print(f"   - Expected Change:  {cliniko_total - db_before:+d}")
    print(f"   - Actual Change:    {db_after - db_before:+d}")
    
    # Success criteria
    if db_after >= cliniko_total * 0.95:  # Allow 5% tolerance
        print(f"\n🎉 SUCCESS! Full patient sync working perfectly!")
        print(f"   ✅ {db_after}/{cliniko_total} patients synced ({db_after/cliniko_total*100:.1f}%)")
        
        print(f"\n💡 FRONTEND IMPLEMENTATION NOTES:")
        print(f"   🔄 Poll /sync-logs/{{orgId}}?limit=1 every 2-3 seconds")
        print(f"   📊 Use metadata.progress_percent for progress bars")
        print(f"   📝 Use metadata.step to show current operation")
        print(f"   ⏱️  Typical sync time: 30-120 seconds for {cliniko_total} patients")
        print(f"   ✅ Expected success rate: 100% (all patients stored)")
    else:
        print(f"\n❌ ISSUE: Not all patients synced")
        print(f"   📉 {db_after}/{cliniko_total} patients synced ({db_after/cliniko_total*100:.1f}%)")
        missing = cliniko_total - db_after
        print(f"   🚨 {missing} patients missing from database")

if __name__ == "__main__":
    main() 