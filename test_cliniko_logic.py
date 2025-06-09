#!/usr/bin/env python3
"""
Test script to validate Cliniko active patients sync logic
Tests each component step by step before running full sync
"""

import os
import sys
import json
from datetime import datetime, timezone

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.cliniko_sync_service import ClinikoSyncService

def test_all_patients():
    """Test fetching all patients from Cliniko"""
    print("=" * 50)
    print("🧪 TEST 1: Fetching All Patients")
    print("=" * 50)
    
    service = ClinikoSyncService()
    org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"  # Surf Rehab
    
    try:
        # Get credentials
        print("📋 Getting Cliniko credentials...")
        credentials = service.get_organization_cliniko_credentials(org_id)
        
        if not credentials:
            print("❌ No credentials found")
            return False
            
        print(f"✅ Credentials retrieved for region: {credentials.get('region', 'unknown')}")
        
        # Set up API
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = service._create_auth_headers(credentials["api_key"])
        
        print(f"📡 Connecting to: {api_url}")
        
        # Fetch patients
        print("👥 Fetching patients...")
        patients = service.get_cliniko_patients(api_url, headers)
        
        print(f"📊 Results:")
        print(f"   - Total patients found: {len(patients)}")
        
        if patients:
            # Show sample patient structure
            sample_patient = patients[0]
            print(f"   - Sample patient structure:")
            print(f"     * ID: {sample_patient.get('id')}")
            print(f"     * Name: {sample_patient.get('first_name')} {sample_patient.get('last_name')}")
            print(f"     * Email: {sample_patient.get('email', 'N/A')}")
            print(f"     * Created: {sample_patient.get('created_at', 'N/A')}")
            
        return len(patients) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_appointments_45_days():
    """Test fetching appointments from last 45 days"""
    print("\n" + "=" * 50)
    print("🧪 TEST 2: Fetching Appointments (Last 45 Days)")
    print("=" * 50)
    
    service = ClinikoSyncService()
    org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"  # Surf Rehab
    
    try:
        # Get credentials
        credentials = service.get_organization_cliniko_credentials(org_id)
        if not credentials:
            print("❌ No credentials found")
            return False
            
        # Set up API
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = service._create_auth_headers(credentials["api_key"])
        
        # Date range info
        print(f"📅 Date range:")
        print(f"   - From: {service.forty_five_days_ago.strftime('%Y-%m-%d')}")
        print(f"   - To: {service.current_date.strftime('%Y-%m-%d')}")
        print(f"   - Days: 45")
        
        # Fetch appointments
        print("📅 Fetching appointments...")
        appointments = service.get_cliniko_appointments(
            api_url, 
            headers, 
            service.forty_five_days_ago, 
            service.current_date
        )
        
        print(f"📊 Results:")
        print(f"   - Total appointments found: {len(appointments)}")
        
        if appointments:
            # Analyze appointment dates
            dates = []
            for appt in appointments[:10]:  # Sample first 10
                date_str = appt.get('starts_at', '')
                if date_str:
                    appt_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(appt_date)
            
            if dates:
                dates.sort()
                print(f"   - Date range in results:")
                print(f"     * Earliest: {dates[0].strftime('%Y-%m-%d')}")
                print(f"     * Latest: {dates[-1].strftime('%Y-%m-%d')}")
                
            # Show sample appointment structure
            sample_appt = appointments[0]
            print(f"   - Sample appointment structure:")
            print(f"     * ID: {sample_appt.get('id')}")
            print(f"     * Date: {sample_appt.get('starts_at')}")
            print(f"     * Patient ID: {sample_appt.get('patient', {}).get('id', 'N/A')}")
            print(f"     * Type: {sample_appt.get('appointment_type', {}).get('name', 'N/A')}")
            
        return len(appointments) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 CLINIKO ACTIVE PATIENTS - LOGIC VALIDATION")
    print("Testing Surf Rehab organization")
    print("Organization ID: org_2xwHiNrj68eaRUlX10anlXGvzX7")
    
    tests = [
        ("All Patients Fetch", test_all_patients),
        ("45-Day Appointments Fetch", test_appointments_45_days)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Ready for full sync.")
    else:
        print("⚠️  Some tests failed. Check errors above.")

if __name__ == "__main__":
    main() 