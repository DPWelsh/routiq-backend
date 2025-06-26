#!/usr/bin/env python3
"""
Debug script to compare patient IDs between database and Cliniko API
to find why deletion logic isn't working
"""

import requests
import json

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def get_cliniko_patient_ids():
    """Get all patient IDs from Cliniko API via test connection"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
        if response.status_code == 200:
            data = response.json()
            total_patients = data.get('total_patients_available', 0)
            print(f"📊 Cliniko API reports {total_patients} total patients")
            
            # We need to get actual patient data to compare IDs
            # For now, just return the count
            return total_patients
        else:
            print(f"❌ Failed to get Cliniko data: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Error getting Cliniko data: {e}")
        return 0

def get_database_patient_info():
    """Get patient info from database"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cliniko/debug/patients/{ORG_ID}")
        if response.status_code == 200:
            data = response.json()
            total_patients = data.get('total_patients', 0)
            cliniko_linked = data.get('cliniko_linked_patients', 0)
            sample_patients = data.get('sample_patients', [])
            
            print(f"📊 Database has {total_patients} total patients")
            print(f"📊 Database has {cliniko_linked} patients with cliniko_patient_id")
            print(f"📊 Sample patients:")
            for patient in sample_patients:
                print(f"   - {patient['name']}: cliniko_id={patient['cliniko_patient_id']}")
            
            return {
                'total': total_patients,
                'linked': cliniko_linked,
                'samples': sample_patients
            }
        else:
            print(f"❌ Failed to get database data: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting database data: {e}")
        return None

def main():
    print("🔍 DEBUGGING PATIENT ID MISMATCH")
    print("=" * 50)
    
    # Get Cliniko API count
    cliniko_count = get_cliniko_patient_ids()
    
    # Get database info
    db_info = get_database_patient_info()
    
    if db_info:
        print("\n📋 ANALYSIS:")
        print(f"   Cliniko API patients:     {cliniko_count}")
        print(f"   Database total patients:  {db_info['total']}")
        print(f"   Database linked patients: {db_info['linked']}")
        print(f"   Expected deletion target: {db_info['linked'] - cliniko_count} patients")
        
        if db_info['linked'] > cliniko_count:
            print(f"\n🎯 There should be {db_info['linked'] - cliniko_count} patient(s) to deactivate")
            print("   The deletion logic should find patients in database that don't exist in Cliniko")
        elif db_info['linked'] == cliniko_count:
            print(f"\n⚠️  Patient counts match - no patients should be deleted")
            print("   This suggests the 'extra' patient might not have a cliniko_patient_id")
        else:
            print(f"\n🤔 Unexpected: Database has fewer linked patients than Cliniko")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. The deletion logic compares cliniko_patient_ids")
    print(f"   2. If all 649 DB patients have cliniko_patient_id but only 648 exist in Cliniko,")
    print(f"      then 1 patient has an ID that no longer exists in Cliniko")
    print(f"   3. Check for ID format issues (string vs int, leading zeros, etc.)")

if __name__ == "__main__":
    main() 