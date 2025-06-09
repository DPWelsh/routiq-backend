"""
Cliniko Patient Import Service
Imports all Cliniko patients into the contacts table for unified contact management.
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
    """Service to import Cliniko patients into contacts table"""
    
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.sync_service = ClinikoSyncService(organization_id)
        self.stats = {
            'patients_fetched': 0,
            'contacts_created': 0,
            'contacts_updated': 0,
            'contacts_skipped': 0,
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
    
    def transform_patient_to_contact(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Cliniko patient data to contacts table format"""
        # Build full name
        first_name = patient.get('first_name', '').strip()
        last_name = patient.get('last_name', '').strip()
        name = f"{first_name} {last_name}".strip()
        
        # Get phone number (mobile preferred, then home)
        phone_mobile = patient.get('phone_mobile')
        phone_home = patient.get('phone_home')
        phone = self.normalize_phone(phone_mobile) or self.normalize_phone(phone_home)
        
        # Get email
        email = patient.get('email')
        if email:
            email = email.strip().lower()
        
        # External IDs for multi-channel system
        external_ids = {
            'channels': {
                'cliniko': str(patient.get('id'))
            }
        }
        
        # Add phone and email to channels if available
        if phone:
            external_ids['channels']['phone'] = phone
            external_ids['channels']['whatsapp'] = phone  # Same as phone
        
        if email:
            external_ids['channels']['email'] = email
        
        # Store original Cliniko data
        external_ids['original_cliniko_data'] = {
            'id': patient.get('id'),
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': patient.get('date_of_birth'),
            'address': {
                'line_1': patient.get('address_line_1'),
                'line_2': patient.get('address_line_2'),
                'city': patient.get('city'),
                'state': patient.get('state'),
                'post_code': patient.get('post_code'),
                'country': patient.get('country')
            },
            'phones': {
                'mobile': patient.get('phone_mobile'),
                'home': patient.get('phone_home')
            },
            'created_at': patient.get('created_at'),
            'updated_at': patient.get('updated_at')
        }
        
        return {
            'name': name if name else f"Patient {patient.get('id')}",
            'email': email,
            'phone': phone,
            'contact_type': 'cliniko_patient',
            'cliniko_patient_id': str(patient.get('id')),
            'status': 'active',
            'organization_id': self.organization_id,
            'patient_status': 'active',  # All imported patients are active
            'external_ids': json.dumps(external_ids),
            'primary_source': 'cliniko',
            'source_systems': ['cliniko'],
            'metadata': json.dumps({
                'import_source': 'cliniko_patient_import',
                'imported_at': datetime.now(timezone.utc).isoformat(),
                'cliniko_updated_at': patient.get('updated_at')
            })
        }
    
    def import_patient(self, patient: Dict[str, Any]) -> bool:
        """Import a single patient into contacts table"""
        try:
            contact_data = self.transform_patient_to_contact(patient)
            
            # Skip if no name and no contact info
            if not contact_data['name'] and not contact_data['phone'] and not contact_data['email']:
                logger.warning(f"Skipping patient {patient.get('id')} - no usable contact info")
                self.stats['contacts_skipped'] += 1
                return False
            
            # Insert or update contact
            query = """
                INSERT INTO contacts (
                    name, email, phone, contact_type, cliniko_patient_id, 
                    status, organization_id, patient_status, external_ids,
                    primary_source, source_systems, metadata
                )
                VALUES (
                    %(name)s, %(email)s, %(phone)s, %(contact_type)s, %(cliniko_patient_id)s,
                    %(status)s, %(organization_id)s, %(patient_status)s, %(external_ids)s,
                    %(primary_source)s, %(source_systems)s, %(metadata)s
                )
                ON CONFLICT (cliniko_patient_id) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    external_ids = EXCLUDED.external_ids,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING id, (xmax = 0) as inserted
            """
            
            with db.get_cursor() as cursor:
                cursor.execute(query, contact_data)
                result = cursor.fetchone()
                db.connection.commit()
                
                if result['inserted']:
                    self.stats['contacts_created'] += 1
                    logger.debug(f"Created contact for patient {patient.get('id')}: {contact_data['name']}")
                else:
                    self.stats['contacts_updated'] += 1
                    logger.debug(f"Updated contact for patient {patient.get('id')}: {contact_data['name']}")
                
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
            # Get Cliniko credentials and client
            if not await self.sync_service.initialize():
                raise Exception("Failed to initialize Cliniko sync service")
            
            # Fetch all patients
            logger.info("Fetching all patients from Cliniko...")
            patients = await self.sync_service.get_all_patients()
            
            if not patients:
                raise Exception("No patients fetched from Cliniko")
            
            self.stats['patients_fetched'] = len(patients)
            logger.info(f"Fetched {len(patients)} patients from Cliniko")
            
            # Import each patient
            logger.info("Importing patients into contacts table...")
            for i, patient in enumerate(patients, 1):
                if i % 50 == 0:
                    logger.info(f"Processed {i}/{len(patients)} patients...")
                
                self.import_patient(patient)
            
            # Log final stats
            logger.info(f"✅ Patient import complete!")
            logger.info(f"   Patients fetched: {self.stats['patients_fetched']}")
            logger.info(f"   Contacts created: {self.stats['contacts_created']}")
            logger.info(f"   Contacts updated: {self.stats['contacts_updated']}")
            logger.info(f"   Contacts skipped: {self.stats['contacts_skipped']}")
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