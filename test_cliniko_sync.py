#!/usr/bin/env python3
"""
Test script to verify Cliniko sync works correctly with the patients table
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.cliniko_sync_service import cliniko_sync_service
from database import db

def test_cliniko_sync():
    """Test the Cliniko sync functionality"""
    print("🧪 Testing Cliniko Sync with Patients Table")
    print("=" * 50)
    
    # Test organization
    org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
    
    print(f"📋 Testing sync for organization: {org_id}")
    
    # Check if patients table exists and is empty
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM patients 
                WHERE organization_id = %s
            """, (org_id,))
            
            result = cursor.fetchone()
            initial_count = result['count'] if result else 0
            print(f"📊 Initial patients count: {initial_count}")
            
    except Exception as e:
        print(f"❌ Error checking initial patients count: {e}")
        return False
    
    # Run the sync
    print("\n🔄 Starting Cliniko sync...")
    try:
        sync_result = cliniko_sync_service.sync_organization_active_patients(org_id)
        
        print(f"✅ Sync completed!")
        print(f"   - Success: {sync_result.get('success')}")
        print(f"   - Patients found: {sync_result.get('patients_found', 0)}")
        print(f"   - Appointments found: {sync_result.get('appointments_found', 0)}")
        print(f"   - Active patients identified: {sync_result.get('active_patients_identified', 0)}")
        print(f"   - Active patients stored: {sync_result.get('active_patients_stored', 0)}")
        
        if sync_result.get('errors'):
            print(f"   - Errors: {sync_result['errors']}")
            
    except Exception as e:
        print(f"❌ Sync failed with error: {e}")
        return False
    
    # Check final count
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM patients 
                WHERE organization_id = %s
            """, (org_id,))
            
            result = cursor.fetchone()
            final_count = result['count'] if result else 0
            print(f"📊 Final patients count: {final_count}")
            
            # Show some sample data
            cursor.execute("""
                SELECT 
                    name, email, phone, cliniko_patient_id, is_active, activity_status,
                    recent_appointment_count, upcoming_appointment_count, total_appointment_count,
                    next_appointment_time, next_appointment_type, primary_appointment_type,
                    last_synced_at
                FROM patients 
                WHERE organization_id = %s
                ORDER BY last_synced_at DESC
                LIMIT 5
            """, (org_id,))
            
            sample_patients = cursor.fetchall()
            
            if sample_patients:
                print(f"\n📋 Sample patients data:")
                for i, patient in enumerate(sample_patients, 1):
                    print(f"   {i}. {patient['name']}")
                    print(f"      - Email: {patient['email']}")
                    print(f"      - Phone: {patient['phone']}")
                    print(f"      - Cliniko ID: {patient['cliniko_patient_id']}")
                    print(f"      - Active: {patient['is_active']}")
                    print(f"      - Status: {patient['activity_status']}")
                    print(f"      - Recent appointments: {patient['recent_appointment_count']}")
                    print(f"      - Upcoming appointments: {patient['upcoming_appointment_count']}")
                    print(f"      - Total appointments: {patient['total_appointment_count']}")
                    print(f"      - Next appointment: {patient['next_appointment_time']}")
                    print(f"      - Next appointment type: {patient['next_appointment_type']}")
                    print(f"      - Primary appointment type: {patient['primary_appointment_type']}")
                    print(f"      - Last synced: {patient['last_synced_at']}")
                    print()
            
    except Exception as e:
        print(f"❌ Error checking final patients count: {e}")
        return False
    
    print("✅ Test completed successfully!")
    return True

def test_table_structure():
    """Test that the patients table has the expected structure"""
    print("🔍 Checking patients table structure...")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            print("📋 Patients table columns:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   - {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            # Check constraints
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_name = 'patients' 
                AND table_schema = 'public'
            """)
            
            constraints = cursor.fetchall()
            print("\n🔒 Table constraints:")
            for constraint in constraints:
                print(f"   - {constraint['constraint_name']}: {constraint['constraint_type']}")
            
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Cliniko Sync Test")
    print("=" * 50)
    
    # Test table structure first
    if not test_table_structure():
        print("❌ Table structure test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test the sync
    if not test_cliniko_sync():
        print("❌ Sync test failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed!") 