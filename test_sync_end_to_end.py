#!/usr/bin/env python3
"""
End-to-End Sync Test
Tests: Cliniko API -> Sync Process -> Database Verification
"""

import os
import sys
import json
import requests
import time
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"  # Surf Rehab

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n📋 STEP {step}: {description}")
    print("-" * 40)

def test_cliniko_connection():
    """Step 1: Test Cliniko API connection and show sample data"""
    print_step(1, "Testing Cliniko Connection")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cliniko API Connection: SUCCESS")
            print(f"   - API URL: {data.get('api_url', 'N/A')}")
            print(f"   - Practitioners: {data.get('practitioners_count', 0)}")
            print(f"   - Total Patients Available: {data.get('total_patients_available', 0)}")
            print(f"   - Sample Patients Available: {data.get('sample_patients_available', False)}")
            return data
        else:
            print(f"❌ Cliniko API Connection: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Cliniko API Connection: ERROR - {e}")
        return None

def get_current_patient_count():
    """Get current patient count in database"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
        if response.status_code == 200:
            data = response.json()
            return {
                'total_patients': data.get('total_patients', 0),
                'active_patients': data.get('active_patients', 0),
                'synced_patients': data.get('synced_patients', 0),
                'last_sync_time': data.get('last_sync_time')
            }
        else:
            print(f"⚠️  Could not get patient count: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Error getting patient count: {e}")
        return None

def run_sync():
    """Step 2: Run the sync process"""
    print_step(2, "Running Cliniko Sync")
    
    try:
        # Start sync
        response = requests.post(f"{BASE_URL}/api/v1/cliniko/sync/{ORG_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync Started: {data.get('message', 'N/A')}")
            
            # Wait for sync to complete (with timeout)
            print("⏳ Waiting for sync to complete...")
            max_wait = 60  # 60 seconds max
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(5)
                wait_time += 5
                
                # Check sync logs
                logs_response = requests.get(f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=1")
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    if logs_data.get('logs'):
                        latest_log = logs_data['logs'][0]
                        status = latest_log.get('status')
                        print(f"   Sync Status: {status} (waited {wait_time}s)")
                        
                        if status in ['completed', 'failed']:
                            if status == 'completed':
                                print(f"✅ Sync Completed Successfully!")
                                print(f"   - Records Processed: {latest_log.get('records_processed', 0)}")
                                print(f"   - Records Success: {latest_log.get('records_success', 0)}")
                                return True
                            else:
                                print(f"❌ Sync Failed!")
                                metadata = latest_log.get('metadata', {})
                                if isinstance(metadata, str):
                                    try:
                                        metadata = json.loads(metadata)
                                    except:
                                        pass
                                errors = metadata.get('errors', []) if isinstance(metadata, dict) else []
                                print(f"   - Errors: {errors}")
                                return False
            
            print(f"⏰ Sync timeout after {max_wait}s")
            return False
            
        else:
            print(f"❌ Failed to start sync: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Sync Error: {e}")
        return False

def verify_database_updates():
    """Step 3: Verify database was updated via API"""
    print_step(3, "Verifying Database Updates")
    
    try:
        # Get active patients
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/active-patients/{ORG_ID}")
        if response.status_code == 200:
            data = response.json()
            active_patients = data.get('active_patients', [])
            total_count = data.get('total_count', 0)
            
            print(f"✅ Active Patients Retrieved: {total_count}")
            
            if active_patients:
                # Show sample patient data
                sample = active_patients[0]
                print(f"\n📋 Sample Patient Data:")
                print(f"   - Name: {sample.get('name', 'N/A')}")
                print(f"   - Phone: {sample.get('phone', 'N/A')}")
                print(f"   - Email: {sample.get('email', 'N/A')}")
                print(f"   - Cliniko ID: {sample.get('cliniko_patient_id', 'N/A')}")
                print(f"   - Activity Status: {sample.get('activity_status', 'N/A')}")
                print(f"   - Recent Appointments: {sample.get('recent_appointment_count', 0)}")
                print(f"   - Upcoming Appointments: {sample.get('upcoming_appointment_count', 0)}")
                print(f"   - Last Synced: {sample.get('last_synced_at', 'N/A')}")
                
                # Count patients with recent sync timestamps
                recent_syncs = 0
                now = datetime.now(timezone.utc)
                for patient in active_patients:
                    last_synced = patient.get('last_synced_at')
                    if last_synced:
                        try:
                            sync_time = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
                            if (now - sync_time).total_seconds() < 300:  # Last 5 minutes
                                recent_syncs += 1
                        except:
                            pass
                
                print(f"   - Recently Synced (last 5 min): {recent_syncs}/{total_count}")
                
                return {
                    'total_active': total_count,
                    'recently_synced': recent_syncs,
                    'sample_patient': sample
                }
            else:
                print("⚠️  No active patients found")
                return {'total_active': 0, 'recently_synced': 0}
                
        else:
            print(f"❌ Failed to get active patients: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Database verification error: {e}")
        return None

def main():
    """Run complete end-to-end test"""
    print_section("END-TO-END SYNC TEST")
    print(f"Organization: {ORG_ID}")
    print(f"API Base URL: {BASE_URL}")
    
    # Step 0: Get baseline
    print_step(0, "Getting Baseline Patient Count")
    baseline = get_current_patient_count()
    if baseline:
        print(f"📊 Current Database State:")
        print(f"   - Total Patients: {baseline['total_patients']}")
        print(f"   - Active Patients: {baseline['active_patients']}")
        print(f"   - Synced Patients: {baseline['synced_patients']}")
        print(f"   - Last Sync: {baseline['last_sync_time']}")
    
    # Step 1: Test Cliniko connection
    cliniko_data = test_cliniko_connection()
    if not cliniko_data:
        print("❌ Test failed at Cliniko connection step")
        return
    
    # Step 2: Run sync
    sync_success = run_sync()
    if not sync_success:
        print("❌ Test failed at sync step")
        return
    
    # Step 3: Verify database
    db_data = verify_database_updates()
    if not db_data:
        print("❌ Test failed at database verification step")
        return
    
    # Final comparison
    print_section("TEST RESULTS SUMMARY")
    print(f"🔍 Cliniko API:")
    print(f"   - Total Patients Available: {cliniko_data.get('total_patients_available', 0)}")
    
    if baseline:
        print(f"📊 Database Changes:")
        final_count = get_current_patient_count()
        if final_count:
            print(f"   - Total Patients: {baseline['total_patients']} → {final_count['total_patients']} (Δ{final_count['total_patients'] - baseline['total_patients']})")
            print(f"   - Active Patients: {baseline['active_patients']} → {final_count['active_patients']} (Δ{final_count['active_patients'] - baseline['active_patients']})")
            print(f"   - Synced Patients: {baseline['synced_patients']} → {final_count['synced_patients']} (Δ{final_count['synced_patients'] - baseline['synced_patients']})")
    
    print(f"✅ Database Verification:")
    print(f"   - Active Patients Retrieved: {db_data['total_active']}")
    print(f"   - Recently Synced: {db_data['recently_synced']}")
    
    # Success criteria
    success_criteria = [
        cliniko_data.get('success', False),
        sync_success,
        db_data['total_active'] > 0,
        db_data['recently_synced'] > 0
    ]
    
    if all(success_criteria):
        print(f"\n🎉 END-TO-END TEST: SUCCESS!")
        print(f"   ✅ Cliniko API connection working")
        print(f"   ✅ Sync process completed")
        print(f"   ✅ Database updated with {db_data['total_active']} active patients")
        print(f"   ✅ {db_data['recently_synced']} patients synced in last 5 minutes")
    else:
        print(f"\n❌ END-TO-END TEST: FAILED!")
        print(f"   - Cliniko API: {'✅' if cliniko_data.get('success', False) else '❌'}")
        print(f"   - Sync Process: {'✅' if sync_success else '❌'}")
        print(f"   - Database Updated: {'✅' if db_data['total_active'] > 0 else '❌'}")
        print(f"   - Recent Sync: {'✅' if db_data['recently_synced'] > 0 else '❌'}")

if __name__ == "__main__":
    main() 