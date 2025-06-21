#!/usr/bin/env python3
"""
Simple Cliniko API Debug - Check appointment types directly
"""

import os
import sys
import json
import requests
import base64
from pathlib import Path
from datetime import datetime, timedelta

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def get_cliniko_credentials():
    """Get Cliniko credentials from database"""
    org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    
    # Get service config
    config = db.execute_query("""
        SELECT service_config 
        FROM organization_services 
        WHERE organization_id = %s AND service_name = 'cliniko'
    """, (org_id,))
    
    if not config:
        return None
    
    service_config = config[0]['service_config']
    
    # Decrypt credentials (simplified)
    encrypted_data = service_config.get('encrypted_credentials')
    if not encrypted_data:
        return None
    
    # For now, let's try to get the credentials directly
    # This is a simplified version - in production you'd decrypt properly
    return {
        'api_url': service_config.get('api_url', 'https://api.cliniko.com/v1'),
        'api_key': 'your_api_key_here'  # We'll need to get this properly
    }

def make_cliniko_request(url, api_key, params=None):
    """Make a request to Cliniko API"""
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Routiq (daniel@routiq.com)'
    }
    
    # Use basic auth with API key
    auth = (api_key, '')
    
    try:
        response = requests.get(url, headers=headers, auth=auth, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

def debug_appointment_types():
    """Debug appointment types from Cliniko API"""
    print("🔍 SIMPLE CLINIKO API DEBUG")
    print("=" * 50)
    
    # First, let's check what we have in the database
    print("1️⃣ Checking database for API credentials...")
    
    org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    
    # Get service config
    config = db.execute_query("""
        SELECT service_config 
        FROM organization_services 
        WHERE organization_id = %s AND service_name = 'cliniko'
    """, (org_id,))
    
    if not config:
        print("❌ No Cliniko service config found")
        return
    
    service_config = config[0]['service_config']
    print(f"✅ Found service config")
    print(f"   API URL: {service_config.get('api_url', 'Not found')}")
    print(f"   Has encrypted credentials: {bool(service_config.get('encrypted_credentials'))}")
    
    # For debugging, let's check what appointment data we currently have
    print(f"\n2️⃣ Checking current appointment data in database...")
    
    sample_appts = db.execute_query("""
        SELECT 
            c.name,
            ap.recent_appointments::text,
            ap.upcoming_appointments::text
        FROM active_patients ap
        JOIN contacts c ON c.id = ap.contact_id
        WHERE ap.organization_id = %s
        AND (ap.recent_appointments != '[]' OR ap.upcoming_appointments != '[]')
        LIMIT 1
    """, (org_id,))
    
    if sample_appts:
        patient = sample_appts[0]
        print(f"📋 Sample patient: {patient['name']}")
        
        if patient['recent_appointments'] and patient['recent_appointments'] != '[]':
            recent_data = json.loads(patient['recent_appointments'])
            if recent_data:
                print(f"📅 Sample recent appointment structure:")
                appt = recent_data[0]
                print(f"   Keys: {list(appt.keys())}")
                print(f"   Full data: {json.dumps(appt, indent=2)}")
    
    # Try to determine the actual API key (this is tricky without proper decryption)
    print(f"\n3️⃣ ANALYSIS")
    print("-" * 30)
    print("Current appointment data shows type: 'Unknown'")
    print("This suggests either:")
    print("1. Cliniko API doesn't return appointment_type field")
    print("2. The field structure is different than expected")
    print("3. Additional API calls are needed to get type names")
    
    print(f"\n4️⃣ RECOMMENDATIONS")
    print("-" * 30)
    print("To fix appointment types:")
    print("1. Check Cliniko API documentation for appointment type field")
    print("2. Verify if appointment types are linked by ID rather than embedded")
    print("3. Test with a sample API call to see actual response structure")
    print("4. Update sync logic based on actual API response")
    
    # Show what we would need to test
    print(f"\n5️⃣ NEXT STEPS")
    print("-" * 30)
    print("To properly debug, we need to:")
    print("1. Get the actual API key from encrypted credentials")
    print("2. Make a test call to /appointments endpoint")
    print("3. Check /appointment_types endpoint")
    print("4. Compare with current sync logic")

if __name__ == "__main__":
    try:
        debug_appointment_types()
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc() 