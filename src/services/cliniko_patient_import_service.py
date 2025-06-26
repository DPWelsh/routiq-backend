"""
Cliniko Patient Import Service
Imports all Cliniko patients into the unified patients table.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import re

from ..database import db
from .cliniko_sync_service import ClinikoSyncService

logger = logging.getLogger(__name__)

class ClinikoPatientImportService:
    """Service to import Cliniko patients into unified patients table"""
    
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.sync_service = ClinikoSyncService()
        self.stats = {
            'patients_fetched': 0,
            'patients_created': 0,
            'patients_updated': 0,
            'patients_skipped': 0,
            'errors': []
        }
    
    def normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number to international format"""
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
        
        logger.warning(f"Could not normalize phone: {phone}")
        return None
    
    def transform_patient_to_patients_table(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Cliniko patient data to unified patients table format"""
        # Build full name
        first_name = patient.get('first_name', '').strip()
        last_name = patient.get('last_name', '').strip()
        name = f"{first_name} {last_name}".strip()
        
        # Get phone number from patient_phone_numbers array
        phone = None
        phone_numbers = patient.get('patient_phone_numbers', [])
        
        if phone_numbers:
            # Prefer Mobile, then any other type
            mobile_phone = next((p for p in phone_numbers if p.get('phone_type') == 'Mobile'), None)
            if mobile_phone:
                phone = self.normalize_phone(mobile_phone.get('number'))
            else:
                # Use first available phone number
                first_phone = phone_numbers[0]
                phone = self.normalize_phone(first_phone.get('number'))
        
        # Get email
        email = patient.get('email')
        if email:
            email = email.strip().lower()
        
        return {
            'organization_id': self.organization_id,
            'name': name if name else f"Patient {patient.get('id')}",
            'email': email,
            'phone': phone,
            'cliniko_patient_id': str(patient.get('id')),
            'contact_type': 'cliniko_patient',
            'is_active': True,  # All imported patients are active
            'activity_status': 'imported',
            'recent_appointment_count': 0,
            'upcoming_appointment_count': 0,
            'total_appointment_count': 0,
            'first_appointment_date': None,
            'last_appointment_date': None,
            'next_appointment_time': None,
            'next_appointment_type': None,
            'primary_appointment_type': None,
            'treatment_notes': None,
            'recent_appointments': json.dumps([]),
            'upcoming_appointments': json.dumps([]),
            'search_date_from': None,
            'search_date_to': None,
            'last_synced_at': datetime.now(timezone.utc)
        }
    
    def import_patient(self, patient: Dict[str, Any]) -> bool:
        """Import a single patient into unified patients table"""
        try:
            patient_data = self.transform_patient_to_patients_table(patient)
            
            # Skip if no name and no contact info
            if not patient_data['name'] and not patient_data['phone'] and not patient_data['email']:
                logger.warning(f"Skipping patient {patient.get('id')} - no usable contact info")
                self.stats['patients_skipped'] += 1
                return False
            
            # Insert or update patient in unified patients table
            query = """
                INSERT INTO patients (
                    organization_id, 
                    name, 
                    email, 
                    phone, 
                    cliniko_patient_id,
                    contact_type,
                    is_active,
                    activity_status,
                    recent_appointment_count,
                    upcoming_appointment_count,
                    total_appointment_count,
                    first_appointment_date,
                    last_appointment_date,
                    next_appointment_time,
                    next_appointment_type,
                    primary_appointment_type,
                    treatment_notes,
                    recent_appointments,
                    upcoming_appointments,
                    search_date_from,
                    search_date_to,
                    last_synced_at
                ) VALUES (
                    %(organization_id)s, %(name)s, %(email)s, %(phone)s, %(cliniko_patient_id)s,
                    %(contact_type)s, %(is_active)s, %(activity_status)s, %(recent_appointment_count)s,
                    %(upcoming_appointment_count)s, %(total_appointment_count)s, %(first_appointment_date)s,
                    %(last_appointment_date)s, %(next_appointment_time)s, %(next_appointment_type)s,
                    %(primary_appointment_type)s, %(treatment_notes)s, %(recent_appointments)s,
                    %(upcoming_appointments)s, %(search_date_from)s, %(search_date_to)s, %(last_synced_at)s
                )
                ON CONFLICT (organization_id, cliniko_patient_id) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    is_active = EXCLUDED.is_active,
                    activity_status = EXCLUDED.activity_status,
                    last_synced_at = EXCLUDED.last_synced_at,
                    updated_at = NOW()
                RETURNING id, (xmax = 0) as inserted
            """
            
            with db.get_cursor() as cursor:
                cursor.execute(query, patient_data)
                result = cursor.fetchone()
                db.connection.commit()
                
                if result['inserted']:
                    self.stats['patients_created'] += 1
                    logger.debug(f"Created patient {patient.get('id')}: {patient_data['name']}")
                else:
                    self.stats['patients_updated'] += 1
                    logger.debug(f"Updated patient {patient.get('id')}: {patient_data['name']}")
                
                return True
                
        except Exception as e:
            error_msg = f"Error importing patient {patient.get('id')}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False
    
    async def import_all_patients(self) -> Dict[str, Any]:
        """Import all Cliniko patients for the organization"""
        logger.info(f"Starting Cliniko patient import for organization {self.organization_id}")
        
        try:
            # Step 1: Get Cliniko credentials
            credentials = self.sync_service.get_organization_cliniko_credentials(self.organization_id)
            if not credentials:
                raise Exception("No Cliniko credentials found for organization")
            
            # Step 2: Set up API connection
            api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
            api_key = credentials["api_key"]
            headers = self.sync_service._create_auth_headers(api_key)
            
            logger.info(f"📡 Connected to Cliniko API: {api_url}")
            
            # Step 3: Fetch all patients
            logger.info("👥 Fetching all patients from Cliniko...")
            patients = self.sync_service.get_cliniko_patients(api_url, headers)
            
            if not patients:
                raise Exception("No patients fetched from Cliniko")
            
            self.stats['patients_fetched'] = len(patients)
            logger.info(f"Fetched {len(patients)} patients from Cliniko")
            
            # Step 4: Import each patient
            logger.info("💾 Importing patients into unified patients table...")
            for i, patient in enumerate(patients, 1):
                if i % 50 == 0:
                    logger.info(f"Processed {i}/{len(patients)} patients...")
                
                self.import_patient(patient)
            
            # Log final stats
            logger.info(f"✅ Patient import complete!")
            logger.info(f"   Patients fetched: {self.stats['patients_fetched']}")
            logger.info(f"   Patients created: {self.stats['patients_created']}")
            logger.info(f"   Patients updated: {self.stats['patients_updated']}")
            logger.info(f"   Patients skipped: {self.stats['patients_skipped']}")
            logger.info(f"   Errors: {len(self.stats['errors'])}")
            
            return {
                'success': True,
                'message': 'Patient import completed successfully',
                'stats': self.stats
            }
            
        except Exception as e:
            error_msg = f"Patient import failed: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'stats': self.stats
            }
    
    def get_import_summary(self) -> Dict[str, Any]:
        """Get summary of import operation"""
        return {
            'organization_id': self.organization_id,
            'stats': self.stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        } 