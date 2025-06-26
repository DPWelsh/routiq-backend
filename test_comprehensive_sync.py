#!/usr/bin/env python3
"""
Test the new comprehensive sync endpoint that syncs patients AND appointments
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
TIMEOUT = 60

def test_comprehensive_sync():
    """Test the comprehensive sync endpoint"""
    
    print("🚀 TESTING COMPREHENSIVE CLINIKO SYNC")
    print("=" * 60)
    print(f"Organization: {ORG_ID}")
    print(f"API URL: {BASE_URL}")
    print()
    
    # Test the new comprehensive sync endpoint
    sync_url = f"{BASE_URL}/api/v1/cliniko/sync-comprehensive/{ORG_ID}"
    
    print(f"🔄 Starting comprehensive sync...")
    print(f"URL: {sync_url}")
    
    try:
        start_time = time.time()
        response = requests.post(sync_url, timeout=TIMEOUT)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        print(f"Status: {response.status_code}")
        print(f"Response Time: {response_time}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Message: {data.get('message')}")
            print(f"Timestamp: {data.get('timestamp')}")
            print()
            
            # Wait a bit and then check status
            print("⏳ Waiting 10 seconds for sync to process...")
            time.sleep(10)
            
            # Check status to see if we have appointment data now
            print("📊 Checking status after sync...")
            status_url = f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}?include_health_check=true"
            
            status_response = requests.get(status_url, timeout=30)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Total Patients: {status_data.get('total_patients')}")
                print(f"Active Patients: {status_data.get('active_patients')}")
                print(f"Sync Percentage: {status_data.get('sync_percentage')}%")
                print(f"Last Sync: {status_data.get('last_sync_time')}")
                
                # Check patient stats for appointment data
                print()
                print("📈 Checking patient stats for appointment data...")
                stats_url = f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats"
                
                stats_response = requests.get(stats_url, timeout=30)
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    print(f"Avg Recent Appointments: {stats_data.get('avg_recent_appointments')}")
                    print(f"Avg Upcoming Appointments: {stats_data.get('avg_upcoming_appointments')}")
                    print(f"Avg Total Appointments: {stats_data.get('avg_total_appointments')}")
                    
                    # Check if we now have appointment data
                    if (stats_data.get('avg_total_appointments', 0) > 0):
                        print("🎉 SUCCESS! Appointment data is now being synced!")
                    else:
                        print("⚠️  Still no appointment data - sync may need more time")
                else:
                    print(f"❌ Could not get patient stats: {stats_response.status_code}")
            else:
                print(f"❌ Could not get status: {status_response.status_code}")
                
        else:
            print(f"❌ FAILED!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️  TIMEOUT - Sync may still be running in background")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def check_database_appointments():
    """Check if appointments are in the database via API"""
    print()
    print("🗄️  CHECKING DATABASE FOR APPOINTMENTS")
    print("=" * 60)
    
    # We'll check this by looking at patient stats
    stats_url = f"{BASE_URL}/api/v1/cliniko/patients/{ORG_ID}/stats?include_details=true&limit=10"
    
    try:
        response = requests.get(stats_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print(f"Total Active Patients: {data.get('total_active_patients')}")
            print(f"Avg Recent Appointments: {data.get('avg_recent_appointments')}")
            print(f"Avg Total Appointments: {data.get('avg_total_appointments')}")
            
            if data.get('patient_details'):
                print()
                print("📋 Sample Patient Data:")
                for patient in data['patient_details'][:3]:  # Show first 3
                    print(f"  - {patient.get('name')}: {patient.get('total_appointment_count')} appointments")
                    print(f"    Recent: {patient.get('recent_appointment_count')}, Upcoming: {patient.get('upcoming_appointment_count')}")
                    if patient.get('next_appointment_time'):
                        print(f"    Next: {patient.get('next_appointment_time')}")
                    print()
            
            # Check if we have meaningful appointment data
            has_appointments = data.get('avg_total_appointments', 0) > 0
            print(f"🎯 Appointment Data Status: {'✅ FOUND' if has_appointments else '❌ MISSING'}")
            
        else:
            print(f"❌ Could not check database: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    # First check current state
    check_database_appointments()
    
    print()
    input("Press Enter to start comprehensive sync...")
    
    # Run the comprehensive sync
    test_comprehensive_sync()
    
    print()
    print("🔍 Final check after sync...")
    check_database_appointments()  
    # ads