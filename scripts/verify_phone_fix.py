#!/usr/bin/env python3
"""
Verify Phone Number Fix
Check if phone numbers are now properly populated after the fix
"""

import requests
import json

def verify_phone_fix():
    """Verify that phone numbers are now properly populated"""
    
    org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    api_url = 'https://routiq-backend-prod.up.railway.app'
    
    print('🔍 VERIFYING PHONE NUMBER FIX')
    print('=' * 50)
    
    try:
        # Get dashboard data to check phone numbers
        print('📊 Fetching dashboard data...')
        response = requests.get(f'{api_url}/api/v1/dashboard/{org_id}')
        
        if response.status_code == 200:
            dashboard_data = response.json()
            print('✅ Dashboard data retrieved successfully')
            
            # Check patient counts
            total_patients = dashboard_data.get('total_patients', 0)
            active_patients = dashboard_data.get('active_patients', 0)
            
            print(f'📋 Patient Summary:')
            print(f'   Total Patients: {total_patients}')
            print(f'   Active Patients: {active_patients}')
            print()
            
        else:
            print(f'❌ Could not fetch dashboard: {response.status_code}')
            return
        
        # Get patient list to check phone numbers
        print('👥 Fetching patient list...')
        patients_response = requests.get(f'{api_url}/api/v1/patients/{org_id}?limit=20')
        
        if patients_response.status_code == 200:
            patients_data = patients_response.json()
            patients = patients_data.get('patients', [])
            
            print(f'✅ Retrieved {len(patients)} patients')
            print()
            
            # Check phone number statistics
            patients_with_phone = 0
            patients_without_phone = 0
            sample_phones = []
            
            print('📞 Phone Number Analysis:')
            print('-' * 30)
            
            for patient in patients[:10]:  # Check first 10 patients
                name = patient.get('name', 'Unknown')
                phone = patient.get('phone')
                cliniko_id = patient.get('cliniko_patient_id')
                
                if phone:
                    patients_with_phone += 1
                    sample_phones.append(phone)
                    status = '✅'
                else:
                    patients_without_phone += 1
                    status = '❌'
                
                print(f'   {status} {name}: {phone or "No phone"} (ID: {cliniko_id})')
            
            print()
            print('📊 Phone Number Statistics:')
            print(f'   With Phone: {patients_with_phone}/{len(patients[:10])}')
            print(f'   Without Phone: {patients_without_phone}/{len(patients[:10])}')
            print(f'   Coverage: {(patients_with_phone/len(patients[:10])*100):.1f}%' if len(patients[:10]) > 0 else '0%')
            
            if sample_phones:
                print()
                print('📱 Sample Phone Numbers:')
                for phone in sample_phones[:5]:
                    print(f'   {phone}')
            
            # Look specifically for Daniel Harris
            print()
            print('🔍 Looking for Daniel Harris...')
            daniel_found = False
            for patient in patients:
                if 'daniel' in patient.get('name', '').lower() and 'harris' in patient.get('name', '').lower():
                    print(f'✅ Found Daniel Harris:')
                    print(f'   Name: {patient.get("name")}')
                    print(f'   Phone: {patient.get("phone") or "No phone"}')
                    print(f'   Email: {patient.get("email") or "No email"}')
                    print(f'   Cliniko ID: {patient.get("cliniko_patient_id")}')
                    daniel_found = True
                    break
            
            if not daniel_found:
                print('❌ Daniel Harris not found in first 20 patients')
            
        else:
            print(f'❌ Could not fetch patients: {patients_response.status_code}')
            print(f'   Response: {patients_response.text}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
    
    print()
    print('🏁 VERIFICATION COMPLETE')
    print('=' * 30)

if __name__ == "__main__":
    verify_phone_fix() 