#!/usr/bin/env python3
"""
Comprehensive Sync Diagnostic Script
Tests and diagnoses sync issues step by step
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def test_credentials():
    """Test Cliniko credentials"""
    print("🔑 Testing Cliniko credentials...")
    response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Credentials working: {data.get('total_patients', 'N/A')} patients available")
        return data
    else:
        print(f"❌ Credential test failed: {response.status_code}")
        return None

def test_dashboard():
    """Test dashboard data"""
    print("\n📊 Testing dashboard...")
    response = requests.get(f"{BASE_URL}/api/v1/sync/dashboard/{ORG_ID}")
    if response.status_code == 200:
        data = response.json()
        stats = data.get('patient_stats', {})
        print(f"✅ Dashboard data:")
        print(f"   Total patients: {stats.get('total_patients')}")
        print(f"   Active patients: {stats.get('active_patients')}")
        print(f"   With upcoming: {stats.get('patients_with_upcoming')}")
        print(f"   With recent: {stats.get('patients_with_recent')}")
        print(f"   Last sync: {stats.get('last_sync_time')}")
        
        current_sync = data.get('current_sync')
        if current_sync:
            print(f"🔄 Current sync: {current_sync.get('status')} - {current_sync.get('current_step')}")
        
        return data
    else:
        print(f"❌ Dashboard test failed: {response.status_code}")
        return None

def start_active_sync():
    """Start an active sync and monitor it"""
    print("\n🚀 Starting active sync...")
    
    # Clean up any stale syncs first
    cleanup_response = requests.post(f"{BASE_URL}/api/v1/sync/cleanup")
    print(f"🧹 Cleanup result: {cleanup_response.status_code}")
    
    # Start sync
    response = requests.post(f"{BASE_URL}/api/v1/sync/start/{ORG_ID}?sync_mode=active")
    if response.status_code != 200:
        print(f"❌ Failed to start sync: {response.status_code} - {response.text}")
        return None
    
    sync_data = response.json()
    sync_id = sync_data.get('sync_id')
    print(f"✅ Sync started: {sync_id}")
    
    # Monitor progress
    max_attempts = 30  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(10)
        attempt += 1
        
        # Check dashboard for current sync
        dashboard = requests.get(f"{BASE_URL}/api/v1/sync/dashboard/{ORG_ID}")
        if dashboard.status_code == 200:
            current_sync = dashboard.json().get('current_sync')
            if current_sync:
                status = current_sync.get('status')
                step = current_sync.get('current_step')
                progress = current_sync.get('progress_percentage', 0)
                print(f"🔄 [{attempt}/30] {status} ({progress}%) - {step}")
                
                if status in ['completed', 'failed']:
                    print(f"✅ Sync finished with status: {status}")
                    return sync_id
            else:
                print(f"✅ Sync completed (no current sync)")
                return sync_id
        else:
            print(f"❌ Failed to check sync status: {dashboard.status_code}")
    
    print("⏰ Sync monitoring timed out")
    return sync_id

def check_sync_history():
    """Check recent sync history"""
    print("\n📜 Checking sync history...")
    response = requests.get(f"{BASE_URL}/api/v1/sync/history/{ORG_ID}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total syncs: {data.get('total_syncs')}")
        print(f"   Successful: {data.get('successful_syncs')}")
        print(f"   Failed: {data.get('failed_syncs')}")
        
        recent = data.get('recent_syncs', [])
        if recent:
            latest = recent[0]
            print(f"\n📋 Latest sync:")
            print(f"   Status: {latest.get('status')}")
            print(f"   Started: {latest.get('started_at')}")
            print(f"   Completed: {latest.get('completed_at')}")
            print(f"   Records processed: {latest.get('records_processed')}")
            print(f"   Records success: {latest.get('records_success')}")
            
            metadata = latest.get('metadata', {})
            print(f"   Sync mode: {metadata.get('sync_mode')}")
            print(f"   Patients found: {metadata.get('patients_found')}")
            print(f"   Appointments found: {metadata.get('appointments_found')}")
            print(f"   Active patients identified: {metadata.get('active_patients_identified')}")
            print(f"   Active patients stored: {metadata.get('active_patients_stored')}")
            print(f"   Errors: {metadata.get('errors', [])}")
        
        return data
    else:
        print(f"❌ History check failed: {response.status_code}")
        return None

def main():
    """Run comprehensive sync tests"""
    print("🔍 COMPREHENSIVE SYNC DIAGNOSTIC")
    print("=" * 50)
    
    # Test 1: Credentials
    creds_result = test_credentials()
    
    # Test 2: Dashboard
    dashboard_result = test_dashboard()
    
    # Test 3: History
    history_result = check_sync_history()
    
    # Test 4: New sync
    print("\n" + "=" * 50)
    print("🧪 RUNNING NEW ACTIVE SYNC TEST")
    print("=" * 50)
    
    sync_id = start_active_sync()
    
    # Test 5: Check results
    print("\n" + "=" * 50)
    print("📊 POST-SYNC RESULTS")
    print("=" * 50)
    
    final_dashboard = test_dashboard()
    final_history = check_sync_history()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if creds_result:
        cliniko_patients = creds_result.get('total_patients', 0)
        print(f"🔑 Cliniko API: {cliniko_patients} patients available")
    
    if dashboard_result and final_dashboard:
        before_total = dashboard_result.get('patient_stats', {}).get('total_patients', 0)
        after_total = final_dashboard.get('patient_stats', {}).get('total_patients', 0)
        before_active = dashboard_result.get('patient_stats', {}).get('active_patients', 0)
        after_active = final_dashboard.get('patient_stats', {}).get('active_patients', 0)
        
        print(f"📊 Patient counts:")
        print(f"   Before sync: {before_total} total, {before_active} active")
        print(f"   After sync:  {after_total} total, {after_active} active")
        print(f"   Change: {after_total - before_total} total, {after_active - before_active} active")
    
    if history_result:
        before_count = history_result.get('total_syncs', 0)
        if final_history:
            after_count = final_history.get('total_syncs', 0)
            print(f"📜 Sync count: {before_count} → {after_count} (change: {after_count - before_count})")

if __name__ == "__main__":
    main() 