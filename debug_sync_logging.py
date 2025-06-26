#!/usr/bin/env python3
"""
Debug Sync Logging Issue
Tests why sync results aren't being recorded in the database
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def check_database_before_sync():
    """Check database state before sync"""
    print("📊 Checking database state BEFORE sync...")
    
    # Get sync history
    history_response = requests.get(f"{BASE_URL}/api/v1/sync/history/{ORG_ID}")
    if history_response.status_code == 200:
        data = history_response.json()
        print(f"   Total syncs: {data.get('total_syncs')}")
        print(f"   Last sync: {data.get('recent_syncs', [{}])[0].get('started_at', 'None')}")
        return data.get('total_syncs', 0)
    else:
        print(f"   ❌ Failed to get history: {history_response.status_code}")
        return 0

def start_sync_and_monitor():
    """Start a sync and monitor it closely"""
    print("\n🚀 Starting monitored sync...")
    
    # Start sync
    response = requests.post(f"{BASE_URL}/api/v1/sync/start/{ORG_ID}?sync_mode=active")
    if response.status_code != 200:
        print(f"❌ Failed to start sync: {response.status_code} - {response.text}")
        return None
    
    sync_data = response.json()
    sync_id = sync_data.get('sync_id')
    print(f"✅ Sync started: {sync_id}")
    print(f"   Started at: {sync_data.get('started_at')}")
    
    # Monitor with detailed logging
    for attempt in range(1, 31):  # 5 minutes max
        time.sleep(10)
        
        # Check sync status via specific endpoint
        status_response = requests.get(f"{BASE_URL}/api/v1/sync/status/{sync_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"🔄 [{attempt:2d}/30] Status endpoint: {status_data.get('status')} - {status_data.get('current_step')}")
        else:
            print(f"🔄 [{attempt:2d}/30] Status endpoint: {status_response.status_code} - {status_response.text[:100]}")
        
        # Also check via dashboard
        dashboard_response = requests.get(f"{BASE_URL}/api/v1/sync/dashboard/{ORG_ID}")
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            current_sync = dashboard_data.get('current_sync')
            if current_sync:
                print(f"           Dashboard: {current_sync.get('status')} - {current_sync.get('current_step')}")
                
                # If completed or failed, break
                if current_sync.get('status') in ['completed', 'failed']:
                    print(f"✅ Sync finished with status: {current_sync.get('status')}")
                    return sync_id
            else:
                print(f"           Dashboard: No current sync (completed)")
                return sync_id
        else:
            print(f"           Dashboard: {dashboard_response.status_code}")
    
    print("⏰ Sync monitoring timed out")
    return sync_id

def check_database_after_sync(before_count):
    """Check database state after sync"""
    print(f"\n📊 Checking database state AFTER sync...")
    
    # Wait a bit for database to update
    time.sleep(5)
    
    # Get sync history again
    history_response = requests.get(f"{BASE_URL}/api/v1/sync/history/{ORG_ID}")
    if history_response.status_code == 200:
        data = history_response.json()
        after_count = data.get('total_syncs', 0)
        print(f"   Total syncs: {before_count} → {after_count} (change: {after_count - before_count})")
        
        if after_count > before_count:
            print("✅ New sync was recorded!")
            latest = data.get('recent_syncs', [{}])[0]
            print(f"   Latest sync:")
            print(f"     Status: {latest.get('status')}")
            print(f"     Started: {latest.get('started_at')}")
            print(f"     Completed: {latest.get('completed_at')}")
            
            metadata = latest.get('metadata', {})
            print(f"     Patients found: {metadata.get('patients_found')}")
            print(f"     Appointments found: {metadata.get('appointments_found')}")
            print(f"     Active patients stored: {metadata.get('active_patients_stored')}")
            print(f"     Errors: {metadata.get('errors', [])}")
            return True
        else:
            print("❌ Sync was NOT recorded in database!")
            return False
    else:
        print(f"   ❌ Failed to get history: {history_response.status_code}")
        return False

def check_patient_counts():
    """Check if patient counts actually changed"""
    print(f"\n👥 Checking patient counts...")
    
    dashboard_response = requests.get(f"{BASE_URL}/api/v1/sync/dashboard/{ORG_ID}")
    if dashboard_response.status_code == 200:
        data = dashboard_response.json()
        stats = data.get('patient_stats', {})
        print(f"   Total patients: {stats.get('total_patients')}")
        print(f"   Active patients: {stats.get('active_patients')}")
        print(f"   With upcoming: {stats.get('patients_with_upcoming')}")
        print(f"   With recent: {stats.get('patients_with_recent')}")
        print(f"   Last sync time: {stats.get('last_sync_time')}")
        return stats
    else:
        print(f"   ❌ Failed to get dashboard: {dashboard_response.status_code}")
        return None

def main():
    """Run focused sync logging debug"""
    print("🔍 SYNC LOGGING DEBUG")
    print("=" * 50)
    
    # Step 1: Check initial state
    before_count = check_database_before_sync()
    before_stats = check_patient_counts()
    
    # Step 2: Run monitored sync
    sync_id = start_sync_and_monitor()
    
    # Step 3: Check if sync was recorded
    sync_recorded = check_database_after_sync(before_count)
    after_stats = check_patient_counts()
    
    # Step 4: Analysis
    print("\n" + "=" * 50)
    print("🔍 ANALYSIS")
    print("=" * 50)
    
    print(f"🆔 Sync ID: {sync_id}")
    print(f"📝 Sync recorded in DB: {'✅ YES' if sync_recorded else '❌ NO'}")
    
    if before_stats and after_stats:
        total_change = after_stats.get('total_patients', 0) - before_stats.get('total_patients', 0)
        active_change = after_stats.get('active_patients', 0) - before_stats.get('active_patients', 0)
        print(f"📊 Patient count changes:")
        print(f"   Total: {total_change}")
        print(f"   Active: {active_change}")
        
        # Check if last_sync_time updated
        before_time = before_stats.get('last_sync_time')
        after_time = after_stats.get('last_sync_time')
        time_updated = before_time != after_time
        print(f"🕐 Last sync time updated: {'✅ YES' if time_updated else '❌ NO'}")
        print(f"   Before: {before_time}")
        print(f"   After:  {after_time}")
    
    # Conclusions
    print(f"\n🎯 CONCLUSIONS:")
    if not sync_recorded:
        print("❌ ISSUE: Sync is not being logged to database")
        print("   - This means _log_sync_result() is failing silently")
        print("   - Need to check database connection in sync process")
        print("   - Check for async/await issues in logging function")
    
    if before_stats and after_stats and before_stats.get('last_sync_time') == after_stats.get('last_sync_time'):
        print("❌ ISSUE: Dashboard last_sync_time not updating")
        print("   - This means sync may be failing before completion")
        print("   - Or dashboard query is not getting latest data")

if __name__ == "__main__":
    main() 