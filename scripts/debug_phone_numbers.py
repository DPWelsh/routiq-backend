#!/usr/bin/env python3
"""
Debug Phone Number Extraction from Cliniko API
Phase 1: Quick win - Debug phone number issue
"""

import sys
import os
import json
import re
import requests
from typing import Optional

# Add src to path
sys.path.append('src')

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number to international format (same logic as in sync service)"""
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = re.sub(r'[^\d]', '', phone)
    
    # Handle Australian numbers
    if digits.startswith('61'):
        # Already has country code
        return f"+{digits}"
    elif digits.startswith('0'):
        # Remove leading 0 and add +61
        return f"+61{digits[1:]}"
    elif len(digits) == 9:
        # Mobile without leading 0
        return f"+61{digits}"
    elif len(digits) >= 7:
        # Assume it needs +61
        return f"+61{digits}"
    
    print(f"❌ Could not normalize phone: {phone}")
    return None

def extract_phone_from_patient(patient_data: dict) -> Optional[str]:
    """Extract phone number from patient data (same logic as sync service)"""
    phone = None
    phone_numbers = patient_data.get('patient_phone_numbers', [])
    
    print(f"📞 Phone numbers array: {phone_numbers}")
    
    if phone_numbers:
        # Prefer Mobile, then any other type
        mobile_phone = next((p for p in phone_numbers if p.get('phone_type') == 'Mobile'), None)
        if mobile_phone:
            raw_phone = mobile_phone.get('number')
            phone = normalize_phone(raw_phone)
            print(f"✅ Found Mobile phone: {raw_phone} → {phone}")
        else:
            # Use first available phone number
            first_phone = phone_numbers[0]
            raw_phone = first_phone.get('number')
            phone = normalize_phone(raw_phone)
            print(f"📱 Using first available phone: {raw_phone} → {phone}")
    else:
        print("❌ No phone_numbers array found")
    
    return phone

def test_cliniko_api():
    """Test Cliniko API directly to see what data we get"""
    
    # These would normally come from database, but we'll hardcode for testing
    api_url = "https://api.au4.cliniko.com/v1"
    api_key = "your_api_key_here"  # You'll need to provide this
    
    print("🔍 PHASE 1: Debug Phone Number Issue")
    print("=" * 50)
    print()
    
    # Test with known patient ID
    patient_id = "1652720016681870934"  # Daniel Harris
    
    headers = {
        'Authorization': f'Basic {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'Routiq Backend (debug_phone_numbers.py)'
    }
    
    try:
        print(f"🌐 Fetching patient {patient_id} from Cliniko API...")
        patient_url = f"{api_url}/patients/{patient_id}"
        
        response = requests.get(patient_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            patient_data = response.json()
            
            print("✅ API Response received successfully")
            print()
            print("📋 FULL PATIENT DATA:")
            print("=" * 30)
            print(json.dumps(patient_data, indent=2))
            print()
            
            print("🔍 PHONE NUMBER ANALYSIS:")
            print("=" * 30)
            
            # Check different possible phone fields
            phone_fields = [
                'phone', 'phone_number', 'mobile', 'mobile_phone',
                'patient_phone_numbers', 'phone_numbers'
            ]
            
            for field in phone_fields:
                if field in patient_data:
                    value = patient_data[field]
                    print(f"   {field}: {value} (type: {type(value).__name__})")
            
            print()
            print("📞 PHONE EXTRACTION TEST:")
            print("=" * 30)
            
            extracted_phone = extract_phone_from_patient(patient_data)
            print(f"   Final extracted phone: {extracted_phone}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_sample_data():
    """Test with sample data to verify our extraction logic"""
    print()
    print("🧪 TESTING WITH SAMPLE DATA:")
    print("=" * 35)
    
    # Test case 1: Mobile phone preferred
    sample_patient_1 = {
        "id": 12345,
        "first_name": "John",
        "last_name": "Doe",
        "patient_phone_numbers": [
            {
                "phone_type": "Home",
                "number": "0287654321"
            },
            {
                "phone_type": "Mobile", 
                "number": "0412345678"
            }
        ]
    }
    
    print("Test 1: Mobile preferred over Home")
    phone1 = extract_phone_from_patient(sample_patient_1)
    print(f"   Result: {phone1}")
    print()
    
    # Test case 2: Only home phone
    sample_patient_2 = {
        "id": 12346,
        "first_name": "Jane",
        "last_name": "Smith",
        "patient_phone_numbers": [
            {
                "phone_type": "Home",
                "number": "+61287654321"
            }
        ]
    }
    
    print("Test 2: Only Home phone available")
    phone2 = extract_phone_from_patient(sample_patient_2)
    print(f"   Result: {phone2}")
    print()
    
    # Test case 3: No phone numbers
    sample_patient_3 = {
        "id": 12347,
        "first_name": "Bob",
        "last_name": "Wilson",
        "patient_phone_numbers": []
    }
    
    print("Test 3: No phone numbers")
    phone3 = extract_phone_from_patient(sample_patient_3)
    print(f"   Result: {phone3}")
    print()
    
    # Test case 4: Phone number normalization
    test_phones = [
        "0412345678",        # Australian mobile
        "+61412345678",      # Already normalized
        "61412345678",       # Without +
        "412345678",         # Without leading 0
        "02 8765 4321",      # Home with spaces
        "invalid"            # Invalid
    ]
    
    print("Test 4: Phone normalization")
    for test_phone in test_phones:
        normalized = normalize_phone(test_phone)
        print(f"   {test_phone} → {normalized}")

if __name__ == "__main__":
    print("🚀 Starting Phone Number Debug Session")
    print("=" * 50)
    
    # Test our extraction logic with sample data first
    test_sample_data()
    
    print()
    print("=" * 50)
    print("💡 To test with real Cliniko API:")
    print("   1. Get your API key from Cliniko")
    print("   2. Update the api_key variable in test_cliniko_api()")
    print("   3. Uncomment the test_cliniko_api() call below")
    print("=" * 50)
    
    # Uncomment this line after adding your API key
    # test_cliniko_api() 