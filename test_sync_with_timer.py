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

def poll_sync_logs(timeout=15):
    """Get the latest sync log with longer timeout"""
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=1", timeout=timeout)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get('logs'):
                log = data['logs'][0]
                return {
                    'status': log.get('status', 'unknown'),
                    'started_at': log.get('started_at', 'unknown'),
                    'metadata': log.get('metadata', {}),
                    'records_processed': log.get('records_processed', 0),
                    'records_success': log.get('records_success', 0),
                    'response_time': response_time
                }
        else:
            print(f"[{current_time()}] ⚠️ API returned {response.status_code}: {response.text[:100]}")
    except requests.exceptions.Timeout:
        print(f"[{current_time()}] ⏰ Logs endpoint timed out after {timeout}s")
    except Exception as e:
        print(f"[{current_time()}] ❌ Error polling logs: {e}")
    return None

def quick_status_check():
    """Quick status check with shorter timeout"""
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}", timeout=8)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                'total_patients': data.get('total_patients', 0),
                'active_patients': data.get('active_patients', 0),
                'response_time': response_time
            }
    except requests.exceptions.Timeout:
        print(f"[{current_time()}] ⏰ Status endpoint timed out")
    except Exception as e:
        print(f"[{current_time()}] ❌ Error getting status: {e}")
    return None

def main():
    print(f"[{current_time()}] 🧪 SYNC TEST WITH REAL-TIME POLLING")
    print("=" * 60)
    
    # Step 1: Get baseline
    print(f"[{current_time()}] 📊 Getting baseline counts...")
    baseline = quick_status_check()
    if baseline:
        print(f"[{current_time()}] ✅ Database Before: {baseline['total_patients']} patients (response: {baseline['response_time']:.1f}s)")
    else:
        print(f"[{current_time()}] ❌ Failed to get baseline status")
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
            return
    except Exception as e:
        print(f"[{current_time()}] ❌ Error starting sync: {e}")
        return
    
    # Step 3: Poll for 3 minutes with adaptive polling
    print(f"[{current_time()}] 🔄 Starting real-time monitoring (3 minutes max)...")
    print("=" * 60)
    
    start_time = time.time()
    last_status = None
    last_step = None
    poll_count = 0
    consecutive_timeouts = 0
    
    while time.time() - start_time < 180:  # 3 minutes max
        poll_count += 1
        
        # Try logs first
        current_log = poll_sync_logs(timeout=15)
        
        if current_log:
            consecutive_timeouts = 0
            status = current_log['status']
            metadata = current_log['metadata']
            step = metadata.get('step', 'unknown') if isinstance(metadata, dict) else 'unknown'
            progress = metadata.get('progress_percent', 0) if isinstance(metadata, dict) else 0
            response_time = current_log.get('response_time', 0)
            
            # Only print when something changes
            if status != last_status or step != last_step:
                print(f"[{current_time()}] Poll #{poll_count}: Status={status}, Step={step}, Progress={progress:.1f}% (API: {response_time:.1f}s)")
                
                # Show detailed metadata for key steps
                if isinstance(metadata, dict):
                    if step == "checking_config":
                        print(f"[{current_time()}]   🔍 Checking service configuration...")
                    elif step == "validating_credentials":
                        print(f"[{current_time()}]   🔑 Validating Cliniko credentials...")
                    elif step == "fetching_patients":
                        current_page = metadata.get('current_page', 0)
                        patients_loaded = metadata.get('patients_loaded', 0)
                        print(f"[{current_time()}]   📄 Fetching: Page {current_page}, {patients_loaded} patients loaded")
                    elif step == "patients_fetched":
                        total_pages = metadata.get('total_pages', 0)
                        patients_found = metadata.get('patients_found', 0)
                        print(f"[{current_time()}]   ✅ API Fetch Complete: {patients_found} patients from {total_pages} pages")
                    elif step == "processing_patients":
                        patients_found = metadata.get('patients_found', 0)
                        print(f"[{current_time()}]   🔍 Processing {patients_found} patients for database...")
                    elif step == "storing_patients":
                        patients_processed = metadata.get('patients_processed', 0)
                        patients_stored = metadata.get('patients_stored', 0)
                        total_patients = metadata.get('total_patients', 0)
                        print(f"[{current_time()}]   💾 Storing: {patients_processed}/{total_patients} processed, {patients_stored} stored")
                    elif step == "checking_deletions":
                        print(f"[{current_time()}]   🗑️ Checking for deleted patients...")
                    elif step == "deletions_handled":
                        patients_deactivated = metadata.get('patients_deactivated', 0)
                        print(f"[{current_time()}]   🗑️ Deactivated {patients_deactivated} deleted patients")
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
            consecutive_timeouts += 1
            print(f"[{current_time()}] Poll #{poll_count}: ⚠️ Logs endpoint not responding (timeout #{consecutive_timeouts})")
            
            # Try status endpoint as backup
            if consecutive_timeouts >= 2:
                status_check = quick_status_check()
                if status_check:
                    print(f"[{current_time()}]   📊 Status fallback: {status_check['total_patients']} patients (response: {status_check['response_time']:.1f}s)")
        
        time.sleep(3)  # Poll every 3 seconds
    
    # Final status check
    print("=" * 60)
    print(f"[{current_time()}] 📊 Final status check...")
    final_status = quick_status_check()
    if final_status:
        print(f"[{current_time()}] ✅ Database After: {final_status['total_patients']} patients")
        print(f"[{current_time()}] ✅ Active Patients: {final_status['active_patients']}")
        print(f"[{current_time()}] ✅ Response Time: {final_status['response_time']:.1f}s")
        
        # Calculate change
        change = final_status['total_patients'] - baseline['total_patients']
        print(f"[{current_time()}] 📈 Change: {change:+d} patients")
        if change != 0:
            print(f"[{current_time()}] 🎉 SUCCESS: Database updated!")
        else:
            print(f"[{current_time()}] ⚠️ No change detected - sync might not have worked")

if __name__ == "__main__":
    main() 