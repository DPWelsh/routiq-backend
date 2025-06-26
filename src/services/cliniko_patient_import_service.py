"""
Cliniko Patient Import Service
Imports all Cliniko patients into the unified patients table with appointment data.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import re

from ..database import db
from .cliniko_sync_service import ClinikoSyncService

logger = logging.getLogger(__name__)

class ClinikoPatientImportService:
    """Service to import Cliniko patients with appointment data into unified patients table"""
    
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.sync_service = ClinikoSyncService()
        
        # Define date ranges for appointment analysis (same as sync service)
        self.current_date = datetime.now(timezone.utc)
        self.thirty_days_ago = self.current_date - timedelta(days=30)
        self.forty_five_days_ago = self.current_date - timedelta(days=45)
        self.thirty_days_future = self.current_date + timedelta(days=30)
        
        self.stats = {
            'patients_fetched': 0,
            'appointments_fetched': 0,
            'patients_created': 0,
            'patients_updated': 0,
            'patients_skipped': 0,
            'active_patients': 0,
            'inactive_patients': 0,
            'errors': []
        }
        
        logger.info(f"🗓️ Import service date ranges:")
        logger.info(f"   Recent (active): {self.thirty_days_ago} to {self.current_date}")
        logger.info(f"   Upcoming: {self.current_date} to {self.thirty_days_future}")
        logger.info(f"   Full range: {self.forty_five_days_ago} to {self.thirty_days_future}")
    
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
    
    def _extract_appointment_type(self, appointment: Dict, appointment_type_lookup: Dict[str, str] = None) -> str:
        """Extract appointment type from appointment data using multiple strategies"""
        
        # Strategy 1: Direct embedded appointment_type with name
        if 'appointment_type' in appointment:
            appt_type_data = appointment['appointment_type']
            if isinstance(appt_type_data, dict):
                # Direct name field
                if 'name' in appt_type_data:
                    return appt_type_data['name']
                
                # Extract ID and lookup name
                if 'id' in appt_type_data and appointment_type_lookup:
                    type_id = appt_type_data['id']
                    return appointment_type_lookup.get(type_id, f'Type-{type_id}')
                
                # Extract ID from links
                if 'links' in appt_type_data and 'self' in appt_type_data['links']:
                    self_link = appt_type_data['links']['self']
                    type_id = self_link.split('/')[-1]
                    if appointment_type_lookup:
                        return appointment_type_lookup.get(type_id, f'Type-{type_id}')
            
            # If appointment_type is just an ID string
            elif isinstance(appt_type_data, str) and appointment_type_lookup:
                return appointment_type_lookup.get(appt_type_data, f'Type-{appt_type_data}')
        
        # Strategy 2: Direct appointment_type_id field
        if 'appointment_type_id' in appointment and appointment_type_lookup:
            type_id = appointment['appointment_type_id']
            return appointment_type_lookup.get(type_id, f'Type-{type_id}')
        
        # Strategy 3: Check for other possible type fields
        for field in ['type', 'service_type', 'treatment_type']:
            if field in appointment:
                return appointment[field]
        
        # Fallback
        return 'Unknown'

    def analyze_patient_appointments(self, patient: Dict, appointments: List[Dict], 
                                   appointment_type_lookup: Dict[str, str] = None) -> Dict[str, Any]:
        """Analyze a single patient's appointments and return appointment data"""
        patient_id = str(patient.get('id'))
        
        # Filter appointments for this patient
        patient_appointments = []
        for appointment in appointments:
            # Skip archived appointments
            if appointment.get('archived_at'):
                continue
            
            # Extract patient ID from appointment
            appt_patient_id = None
            if 'patient' in appointment and appointment['patient']:
                if isinstance(appointment['patient'], dict):
                    appt_patient_id = str(appointment['patient'].get('id', ''))
                    # If no direct ID, extract from links URL
                    if not appt_patient_id and 'links' in appointment['patient']:
                        self_link = appointment['patient']['links'].get('self', '')
                        if self_link:
                            appt_patient_id = self_link.split('/')[-1]
                else:
                    appt_patient_id = str(appointment['patient'])
            elif 'patient_id' in appointment:
                appt_patient_id = str(appointment['patient_id'])
                
            if appt_patient_id == patient_id:
                patient_appointments.append(appointment)
        
        if not patient_appointments:
            # No appointments for this patient
            return {
                'is_active': False,  # Patients with no appointments are not active
                'recent_appointment_count': 0,
                'upcoming_appointment_count': 0,
                'total_appointment_count': 0,
                'first_appointment_date': None,
                'last_appointment_date': None,
                'next_appointment_time': None,
                'next_appointment_type': None,
                'primary_appointment_type': None,
                'treatment_notes': None,
                'recent_appointments': [],
                'upcoming_appointments': [],
                'search_date_from': self.forty_five_days_ago,
                'search_date_to': self.thirty_days_future,
                'activity_status': 'imported'
            }
        
        # Sort appointments by date for easier processing
        patient_appointments.sort(key=lambda x: x['starts_at'])
        
        # Count recent (last 30 days) and upcoming appointments
        recent_count = 0
        upcoming_count = 0
        recent_appointments = []
        upcoming_appointments = []
        
        # Track appointment types for analysis
        appointment_types = {}
        next_appointment = None
        latest_treatment_note = None
        
        for appt in patient_appointments:
            appt_date = datetime.fromisoformat(appt['starts_at'].replace('Z', '+00:00'))
            
            # Extract appointment type
            appt_type = self._extract_appointment_type(appt, appointment_type_lookup)
            
            # Count appointment types
            appointment_types[appt_type] = appointment_types.get(appt_type, 0) + 1
            
            # Extract treatment notes if available
            if appt.get('notes'):
                latest_treatment_note = appt['notes']
            
            # Check if appointment is in the LAST 30 DAYS
            if self.thirty_days_ago <= appt_date <= self.current_date:
                recent_count += 1
                recent_appointments.append({
                    'date': appt['starts_at'],
                    'type': appt_type,
                    'id': appt.get('id'),
                    'notes': appt.get('notes', '')
                })
            
            # Check if appointment is upcoming
            if appt_date > self.current_date:
                upcoming_count += 1
                upcoming_appointments.append({
                    'date': appt['starts_at'],
                    'type': appt_type,
                    'id': appt.get('id'),
                    'notes': appt.get('notes', '')
                })
                
                # Set next appointment (earliest upcoming)
                if next_appointment is None:
                    next_appointment = {
                        'date': appt_date,
                        'type': appt_type,
                        'id': appt.get('id')
                    }
        
        # Determine primary appointment type (most common)
        primary_appointment_type = max(appointment_types.keys(), key=appointment_types.get) if appointment_types else None
        
        # Calculate first and last appointment dates
        appointment_dates = []
        for appt in patient_appointments:
            appt_date = datetime.fromisoformat(appt['starts_at'].replace('Z', '+00:00'))
            appointment_dates.append(appt_date)
        
        first_appointment_date = min(appointment_dates) if appointment_dates else None
        last_appointment_date = max(appointment_dates) if appointment_dates else None
        
        # Determine activity status and is_active flag
        # Patient is ACTIVE only if they have appointments in LAST 30 DAYS OR upcoming appointments
        is_active = (recent_count > 0 or upcoming_count > 0)
        
        activity_status = "imported"  # Default for patients with no qualifying appointments
        if upcoming_count > 0 and recent_count > 0:
            activity_status = "active"  # Both recent and upcoming
        elif upcoming_count > 0:
            activity_status = "has_upcoming"  # Only upcoming
        elif recent_count > 0:
            activity_status = "recent_activity"  # Only recent
        
        return {
            'is_active': is_active,  # NEW: Active only if recent OR upcoming appointments
            'recent_appointment_count': recent_count,
            'upcoming_appointment_count': upcoming_count,
            'total_appointment_count': len(patient_appointments),
            'first_appointment_date': first_appointment_date,
            'last_appointment_date': last_appointment_date,
            'next_appointment_time': next_appointment['date'] if next_appointment else None,
            'next_appointment_type': next_appointment['type'] if next_appointment else None,
            'primary_appointment_type': primary_appointment_type,
            'treatment_notes': latest_treatment_note,
            'recent_appointments': recent_appointments,
            'upcoming_appointments': upcoming_appointments,
            'search_date_from': self.forty_five_days_ago,
            'search_date_to': self.thirty_days_future,
            'activity_status': activity_status
        }

    def transform_patient_to_patients_table(self, patient: Dict[str, Any], appointment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transform Cliniko patient data to unified patients table format with appointment data"""
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
        
        # Use appointment data if provided, otherwise default to empty
        if appointment_data:
            appointment_fields = appointment_data
        else:
            appointment_fields = {
                'is_active': False,  # Patients with no appointments are not active
                'recent_appointment_count': 0,
                'upcoming_appointment_count': 0,
                'total_appointment_count': 0,
                'first_appointment_date': None,
                'last_appointment_date': None,
                'next_appointment_time': None,
                'next_appointment_type': None,
                'primary_appointment_type': None,
                'treatment_notes': None,
                'recent_appointments': [],
                'upcoming_appointments': [],
                'search_date_from': None,
                'search_date_to': None,
                'activity_status': 'imported'
            }
        
        return {
            'organization_id': self.organization_id,
            'name': name if name else f"Patient {patient.get('id')}",
            'email': email,
            'phone': phone,
            'cliniko_patient_id': str(patient.get('id')),
            'contact_type': 'cliniko_patient',
            'is_active': appointment_fields.get('is_active', False),
            'activity_status': appointment_fields.get('activity_status', 'imported'),
            'recent_appointment_count': appointment_fields.get('recent_appointment_count', 0),
            'upcoming_appointment_count': appointment_fields.get('upcoming_appointment_count', 0),
            'total_appointment_count': appointment_fields.get('total_appointment_count', 0),
            'first_appointment_date': appointment_fields.get('first_appointment_date'),
            'last_appointment_date': appointment_fields.get('last_appointment_date'),
            'next_appointment_time': appointment_fields.get('next_appointment_time'),
            'next_appointment_type': appointment_fields.get('next_appointment_type'),
            'primary_appointment_type': appointment_fields.get('primary_appointment_type'),
            'treatment_notes': appointment_fields.get('treatment_notes'),
            'recent_appointments': json.dumps(appointment_fields.get('recent_appointments', [])),
            'upcoming_appointments': json.dumps(appointment_fields.get('upcoming_appointments', [])),
            'search_date_from': appointment_fields.get('search_date_from'),
            'search_date_to': appointment_fields.get('search_date_to'),
            'last_synced_at': datetime.now(timezone.utc)
        }

    def import_patient(self, patient: Dict[str, Any], appointment_data: Dict[str, Any] = None) -> bool:
        """Import a single patient into unified patients table with appointment data"""
        try:
            patient_data = self.transform_patient_to_patients_table(patient, appointment_data)
            
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
                    recent_appointment_count = EXCLUDED.recent_appointment_count,
                    upcoming_appointment_count = EXCLUDED.upcoming_appointment_count,
                    total_appointment_count = EXCLUDED.total_appointment_count,
                    first_appointment_date = EXCLUDED.first_appointment_date,
                    last_appointment_date = EXCLUDED.last_appointment_date,
                    next_appointment_time = EXCLUDED.next_appointment_time,
                    next_appointment_type = EXCLUDED.next_appointment_type,
                    primary_appointment_type = EXCLUDED.primary_appointment_type,
                    treatment_notes = EXCLUDED.treatment_notes,
                    recent_appointments = EXCLUDED.recent_appointments,
                    upcoming_appointments = EXCLUDED.upcoming_appointments,
                    search_date_from = EXCLUDED.search_date_from,
                    search_date_to = EXCLUDED.search_date_to,
                    last_synced_at = EXCLUDED.last_synced_at,
                    updated_at = NOW()
                RETURNING id, (xmax = 0) as inserted
            """
            
            with db.get_cursor() as cursor:
                cursor.execute(query, patient_data)
                result = cursor.fetchone()
                
                if result['inserted']:
                    self.stats['patients_created'] += 1
                    logger.debug(f"Created patient {patient.get('id')}: {patient_data['name']}")
                else:
                    self.stats['patients_updated'] += 1
                    logger.debug(f"Updated patient {patient.get('id')}: {patient_data['name']}")
                
                # Track active vs inactive
                if patient_data['is_active']:
                    self.stats['active_patients'] += 1
                else:
                    self.stats['inactive_patients'] += 1
                
                return True
                
        except Exception as e:
            error_msg = f"Error importing patient {patient.get('id')}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False

    async def import_all_patients(self) -> Dict[str, Any]:
        """Import all Cliniko patients with appointment data for the organization"""
        logger.info(f"🔄 Starting Cliniko patient + appointment import for organization {self.organization_id}")
        
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
            logger.info(f"✅ Fetched {len(patients)} patients from Cliniko")
            
            # Step 4: Fetch appointments from last 45 days + next 30 days
            logger.info("📅 Fetching appointments from last 45 days + next 30 days...")
            appointments = self.sync_service.get_cliniko_appointments(
                api_url, 
                headers, 
                self.forty_five_days_ago, 
                self.thirty_days_future
            )
            self.stats['appointments_fetched'] = len(appointments)
            logger.info(f"✅ Fetched {len(appointments)} appointments from Cliniko")
            
            # Step 5: Get appointment types for proper type resolution
            logger.info("📋 Loading appointment types...")
            appointment_type_lookup = self.sync_service.get_cliniko_appointment_types(api_url, headers)
            logger.info(f"✅ Loaded {len(appointment_type_lookup)} appointment types")
            
            # Step 6: Import each patient with appointment analysis
            logger.info("💾 Importing patients with appointment data into unified patients table...")
            for i, patient in enumerate(patients, 1):
                if i % 50 == 0:
                    logger.info(f"Processed {i}/{len(patients)} patients...")
                
                # Analyze appointments for this patient
                appointment_data = self.analyze_patient_appointments(patient, appointments, appointment_type_lookup)
                
                # Import patient with appointment data
                self.import_patient(patient, appointment_data)
            
            # Log final stats
            logger.info(f"✅ Patient + appointment import complete!")
            logger.info(f"   Patients fetched: {self.stats['patients_fetched']}")
            logger.info(f"   Appointments fetched: {self.stats['appointments_fetched']}")
            logger.info(f"   Patients created: {self.stats['patients_created']}")
            logger.info(f"   Patients updated: {self.stats['patients_updated']}")
            logger.info(f"   Patients skipped: {self.stats['patients_skipped']}")
            logger.info(f"   Active patients (recent/upcoming appointments): {self.stats['active_patients']}")
            logger.info(f"   Inactive patients (no qualifying appointments): {self.stats['inactive_patients']}")
            logger.info(f"   Errors: {len(self.stats['errors'])}")
            
            return {
                'success': True,
                'message': 'Patient + appointment import completed successfully',
                'stats': self.stats
            }
            
        except Exception as e:
            error_msg = f"Patient + appointment import failed: {e}"
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