#!/usr/bin/env python3
"""
Simple Sync Test with Real-Time Timer
Shows exactly what's happening during sync polling
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def current_time():
    return datetime.now().strftime("%H:%M:%S")

def poll_sync_logs():
    """Get the latest sync log"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=1", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('logs'):
                log = data['logs'][0]
                return {
                    'status': log.get('status', 'unknown'),
                    'started_at': log.get('started_at', 'unknown'),
                    'metadata': log.get('metadata', {}),
                    'records_processed': log.get('records_processed', 0),
                    'records_success': log.get('records_success', 0)
                }
    except Exception as e:
        print(f"[{current_time()}] ❌ Error polling logs: {e}")
    return None

def main():
    print(f"[{current_time()}] 🧪 SYNC TEST WITH REAL-TIME POLLING")
    print("=" * 60)
    
    # Step 1: Get baseline
    print(f"[{current_time()}] 📊 Getting baseline counts...")
    try:
        status_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}", timeout=10)
        if status_response.status_code == 200:
            data = status_response.json()
            print(f"[{current_time()}] ✅ Database Before: {data.get('total_patients', 0)} patients")
        else:
            print(f"[{current_time()}] ❌ Failed to get status: {status_response.status_code}")
            return
    except Exception as e:
        print(f"[{current_time()}] ❌ Error getting status: {e}")
        return
    
    # Step 2: Start sync
    print(f"[{current_time()}] 🚀 Starting sync...")
    try:
        sync_response = requests.post(f"{BASE_URL}/api/v1/cliniko/sync-all/{ORG_ID}", timeout=10)
        if sync_response.status_code == 200:
            sync_data = sync_response.json()
            print(f"[{current_time()}] ✅ Sync started: {sync_data.get('message', 'Unknown')}")
        else:
            print(f"[{current_time()}] ❌ Failed to start sync: {sync_response.status_code}")
            print(f"[{current_time()}] Response: {sync_response.text}")
            return
    except Exception as e:
        print(f"[{current_time()}] ❌ Error starting sync: {e}")
        return
    
    # Step 3: Poll for 2 minutes
    print(f"[{current_time()}] 🔄 Starting real-time monitoring (2 minutes max)...")
    print("=" * 60)
    
    start_time = time.time()
    last_status = None
    last_step = None
    poll_count = 0
    
    while time.time() - start_time < 120:  # 2 minutes max
        poll_count += 1
        current_log = poll_sync_logs()
        
        if current_log:
            status = current_log['status']
            metadata = current_log['metadata']
            step = metadata.get('step', 'unknown') if isinstance(metadata, dict) else 'unknown'
            progress = metadata.get('progress_percent', 0) if isinstance(metadata, dict) else 0
            
            # Only print when something changes
            if status != last_status or step != last_step:
                print(f"[{current_time()}] Poll #{poll_count}: Status={status}, Step={step}, Progress={progress:.1f}%")
                
                # Show detailed metadata for key steps
                if isinstance(metadata, dict):
                    if step == "fetching_patients":
                        current_page = metadata.get('current_page', 0)
                        patients_loaded = metadata.get('patients_loaded', 0)
                        print(f"[{current_time()}]   📄 Fetching: Page {current_page}, {patients_loaded} patients loaded")
                    elif step == "storing_patients":
                        patients_processed = metadata.get('patients_processed', 0)
                        patients_stored = metadata.get('patients_stored', 0)
                        total_patients = metadata.get('total_patients', 0)
                        print(f"[{current_time()}]   💾 Storing: {patients_processed}/{total_patients} processed, {patients_stored} stored")
                    elif step == "checking_deletions":
                        print(f"[{current_time()}]   🗑️ Checking for deleted patients...")
                    elif step == "completed":
                        patients_found = metadata.get('patients_found', 0)
                        patients_stored = metadata.get('patients_stored', 0)
                        patients_deleted = metadata.get('patients_deleted', 0)
                        print(f"[{current_time()}]   ✅ COMPLETED: {patients_found} found, {patients_stored} stored, {patients_deleted} deleted")
                
                last_status = status
                last_step = step
            
            # Check if completed
            if status in ['completed', 'failed']:
                print(f"[{current_time()}] 🎉 Sync finished with status: {status}")
                break
        else:
            print(f"[{current_time()}] Poll #{poll_count}: ⚠️ No logs found")
        
        time.sleep(2)  # Poll every 2 seconds
    
    # Final status check
    print("=" * 60)
    print(f"[{current_time()}] 📊 Final status check...")
    try:
        final_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}", timeout=10)
        if final_response.status_code == 200:
            data = final_response.json()
            print(f"[{current_time()}] ✅ Database After: {data.get('total_patients', 0)} patients")
            print(f"[{current_time()}] ✅ Active Patients: {data.get('active_patients', 0)}")
            print(f"[{current_time()}] ✅ Last Sync: {data.get('last_sync_time', 'Unknown')}")
    except Exception as e:
        print(f"[{current_time()}] ❌ Error getting final status: {e}")

if __name__ == "__main__":
    main() 