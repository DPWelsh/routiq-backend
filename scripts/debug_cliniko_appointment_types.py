#!/usr/bin/env python3
"""
Debug Cliniko Appointment Types - Check what data is actually returned
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.cliniko_sync_service import ClinikoSyncService

def debug_cliniko_appointment_types():
    """Debug actual Cliniko API response for appointment types"""
    print("🔍 DEBUGGING CLINIKO APPOINTMENT TYPES")
    print("=" * 60)
    
    org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    sync_service = ClinikoSyncService()
    
    # Get Cliniko credentials
    print("1️⃣ Getting Cliniko credentials...")
    credentials = sync_service.get_organization_cliniko_credentials(org_id)
    if not credentials:
        print("❌ No Cliniko credentials found")
        return
    
    api_url = credentials['api_url']
    api_key = credentials['api_key']
    headers = sync_service._create_auth_headers(api_key)
    
    print(f"✅ Connected to: {api_url}")
    
    # Get a small sample of recent appointments
    print("\n2️⃣ Fetching sample appointments from Cliniko API...")
    
    # Get last 7 days of appointments
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    url = f"{api_url}/appointments"
    params = {
        'page': 1,
        'per_page': 5,  # Just get 5 for debugging
        'sort': 'starts_at:desc',
        'q[]': [
            f'starts_at:>={start_date.strftime("%Y-%m-%dT00:00:00Z")}',
            f'starts_at:<={end_date.strftime("%Y-%m-%dT23:59:59Z")}'
        ]
    }
    
    data = sync_service._make_cliniko_request(url, headers, params)
    
    if not data:
        print("❌ No data returned from Cliniko API")
        return
    
    appointments = data.get('appointments', [])
    print(f"✅ Retrieved {len(appointments)} sample appointments")
    
    if not appointments:
        print("⚠️  No appointments found in the last 7 days")
        return
    
    # Analyze the structure of appointment data
    print("\n3️⃣ ANALYZING APPOINTMENT DATA STRUCTURE")
    print("-" * 50)
    
    for i, appointment in enumerate(appointments[:2], 1):  # Just look at first 2
        print(f"\n📋 Appointment {i}:")
        print(f"   ID: {appointment.get('id')}")
        print(f"   Starts At: {appointment.get('starts_at')}")
        
        # Check for appointment type in various possible locations
        print(f"\n   🔍 Appointment Type Analysis:")
        
        # Direct appointment_type field
        if 'appointment_type' in appointment:
            appt_type = appointment['appointment_type']
            print(f"   ✅ appointment_type field found: {type(appt_type)}")
            if isinstance(appt_type, dict):
                print(f"      • appointment_type.name: {appt_type.get('name', 'NOT FOUND')}")
                print(f"      • appointment_type keys: {list(appt_type.keys())}")
            else:
                print(f"      • appointment_type value: {appt_type}")
        else:
            print(f"   ❌ No 'appointment_type' field found")
        
        # Check for 'type' field
        if 'type' in appointment:
            print(f"   ✅ 'type' field found: {appointment['type']}")
        else:
            print(f"   ❌ No 'type' field found")
        
        # Check for other possible type fields
        type_fields = ['service', 'service_type', 'treatment_type', 'category']
        for field in type_fields:
            if field in appointment:
                print(f"   ✅ '{field}' field found: {appointment[field]}")
        
        # Show all top-level keys for reference
        print(f"\n   📋 All top-level fields in appointment:")
        for key in sorted(appointment.keys()):
            value = appointment[key]
            if isinstance(value, (dict, list)):
                print(f"      • {key}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
            else:
                print(f"      • {key}: {value}")
    
    # Check if there are appointment type resources
    print(f"\n4️⃣ CHECKING APPOINTMENT TYPES RESOURCE")
    print("-" * 50)
    
    # Try to get appointment types from the API
    types_url = f"{api_url}/appointment_types"
    types_data = sync_service._make_cliniko_request(types_url, headers, {'per_page': 10})
    
    if types_data and 'appointment_types' in types_data:
        appointment_types = types_data['appointment_types']
        print(f"✅ Found {len(appointment_types)} appointment types:")
        for appt_type in appointment_types:
            print(f"   • {appt_type.get('name', 'Unnamed')} (ID: {appt_type.get('id')})")
    else:
        print("❌ Could not retrieve appointment types")
    
    print(f"\n5️⃣ RECOMMENDATIONS")
    print("-" * 50)
    
    print("Based on the API response analysis:")
    print("1. Check if appointment_type field exists and has the expected structure")
    print("2. Verify if appointment types are linked via ID rather than embedded")
    print("3. Consider if additional API calls are needed to get appointment type names")
    print("4. Update the sync logic to handle the actual API response structure")
    
    print(f"\n🎉 DEBUG ANALYSIS COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        debug_cliniko_appointment_types()
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc() 