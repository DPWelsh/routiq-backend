"""
Comprehensive Cliniko Sync Service
Syncs ALL patients AND their appointments to both patients and appointments tables
Updated: 2025-06-26 - Fixed contact_id nullable constraint
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid

from ..database import db
from .cliniko_sync_service import ClinikoSyncService

logger = logging.getLogger(__name__)

class ComprehensiveClinikoSync:
    """
    Comprehensive sync that populates both patients and appointments tables
    with ALL data from Cliniko (not just active patients)
    """
    
    def __init__(self):
        self.cliniko_service = ClinikoSyncService()
        
        # Date ranges for appointment fetching
        self.current_date = datetime.now(timezone.utc)
        self.six_months_ago = self.current_date - timedelta(days=180)
        self.six_months_future = self.current_date + timedelta(days=180)
        
        self.stats = {
            'patients_processed': 0,
            'patients_created': 0,
            'patients_updated': 0,
            'appointments_processed': 0,
            'appointments_created': 0,
            'appointments_updated': 0,
            'errors': []
        }
        
    def sync_all_data(self, organization_id: str) -> Dict[str, Any]:
        """
        Comprehensive sync: ALL patients + ALL their appointments
        """
        logger.info(f"🔄 Starting comprehensive Cliniko sync for organization {organization_id}")
        
        start_time = datetime.now(timezone.utc)
        result = {
            "organization_id": organization_id,
            "started_at": start_time.isoformat(),
            "success": False,
            "sync_type": "comprehensive",
            "errors": [],
            "stats": {}
        }
        
        # Create initial sync log entry
        sync_log_id = self._create_sync_log_entry(organization_id, "comprehensive_sync", "running", start_time)
        
        try:
            # Step 1: Get Cliniko credentials
            credentials = self.cliniko_service.get_organization_cliniko_credentials(organization_id)
            if not credentials:
                raise Exception("No Cliniko credentials found")
            
            api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
            headers = self.cliniko_service._create_auth_headers(credentials["api_key"])
            
            logger.info(f"📡 Connected to Cliniko API: {api_url}")
            
            # Step 2: Fetch ALL patients
            logger.info("👥 Fetching ALL patients from Cliniko...")
            patients = self.cliniko_service.get_cliniko_patients(api_url, headers)
            logger.info(f"✅ Fetched {len(patients)} patients")
            
            # Step 3: Fetch ALL appointments (last 6 months + next 6 months)
            logger.info("📅 Fetching ALL appointments from Cliniko...")
            appointments = self.cliniko_service.get_cliniko_appointments(
                api_url, 
                headers, 
                self.six_months_ago.date(), 
                self.six_months_future.date()
            )
            logger.info(f"✅ Fetched {len(appointments)} appointments")
            
            # Step 4: Get appointment types for proper resolution
            logger.info("📋 Loading appointment types...")
            appointment_type_lookup = self.cliniko_service.get_cliniko_appointment_types(api_url, headers)
            
            # Step 5: Process and sync all data
            logger.info("💾 Processing and syncing all data...")
            logger.info(f"📊 About to process: {len(patients)} patients, {len(appointments)} appointments")
            
            self._sync_patients_and_appointments(
                organization_id, 
                patients, 
                appointments, 
                appointment_type_lookup
            )
            
            logger.info("✅ Completed processing and syncing all data")
            
            # Step 6: Update service last sync time
            self._update_last_sync_time(organization_id)
            
            # Success!
            result["success"] = True
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            result["stats"] = self.stats
            
            # Log successful completion
            self._update_sync_log_completion(sync_log_id, "completed", result)
            
            logger.info(f"✅ Comprehensive sync completed:")
            logger.info(f"   - Patients: {self.stats['patients_processed']} processed")
            logger.info(f"   - Appointments: {self.stats['appointments_processed']} processed")
            
        except Exception as e:
            logger.error(f"❌ Comprehensive sync failed: {e}")
            result["errors"].append(str(e))
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            result["stats"] = self.stats
            
            # Log failure
            self._update_sync_log_completion(sync_log_id, "failed", result)
        
        return result
    
    def _sync_patients_and_appointments(self, organization_id: str, patients: List[Dict], 
                                      appointments: List[Dict], appointment_type_lookup: Dict[str, str]):
        """
        Sync patients and appointments to both tables with proper relationships
        """
        logger.info("🔄 Syncing patients and appointments to database...")
        
        # Create patient lookup by cliniko_patient_id
        patient_lookup = {str(patient['id']): patient for patient in patients}
        
        # Group appointments by patient
        appointments_by_patient = {}
        for appointment in appointments:
            patient_id = self._extract_patient_id_from_appointment(appointment)
            if patient_id:
                if patient_id not in appointments_by_patient:
                    appointments_by_patient[patient_id] = []
                appointments_by_patient[patient_id].append(appointment)
        
        logger.info(f"📊 Grouped {len(appointments)} appointments for {len(appointments_by_patient)} patients")
        
        # Process each patient with their appointments
        total_patients = len(patient_lookup)
        processed_count = 0
        
        for cliniko_patient_id, patient_data in patient_lookup.items():
            try:
                # Process each patient in its own transaction
                with db.get_cursor() as cursor:
                    # Get appointments for this patient
                    patient_appointments = appointments_by_patient.get(cliniko_patient_id, [])
                    
                    # Calculate appointment statistics
                    appointment_stats = self._calculate_appointment_stats(patient_appointments, appointment_type_lookup)
                    
                    # Create/update patient record
                    patient_uuid = self._upsert_patient(cursor, organization_id, patient_data, appointment_stats)
                    
                    # Create/update appointment records
                    self._upsert_appointments(cursor, organization_id, patient_uuid, patient_appointments, appointment_type_lookup)
                    
                    self.stats['patients_processed'] += 1
                    processed_count += 1
                    
                    # Log progress every 50 patients
                    if processed_count % 50 == 0 or processed_count == total_patients:
                        progress_percent = (processed_count / total_patients) * 100
                        logger.info(f"📊 Progress: {processed_count}/{total_patients} patients processed ({progress_percent:.1f}%)")
                    
            except Exception as e:
                logger.error(f"Error processing patient {cliniko_patient_id}: {e}")
                self.stats['errors'].append(f"Patient {cliniko_patient_id}: {str(e)}")
                processed_count += 1
                continue
        
        logger.info("✅ Completed syncing patients and appointments")
    
    def _calculate_appointment_stats(self, appointments: List[Dict], appointment_type_lookup: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate appointment statistics for a patient
        """
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        
        recent_count = 0
        upcoming_count = 0
        recent_appointments = []
        upcoming_appointments = []
        
        first_appointment_date = None
        last_appointment_date = None
        next_appointment_time = None
        next_appointment_type = None
        primary_appointment_type = None
        latest_treatment_note = None
        
        # Count appointment types
        appointment_types = {}
        
        for appointment in appointments:
            # Skip archived appointments
            if appointment.get('archived_at'):
                continue
                
            appt_date = datetime.fromisoformat(appointment['starts_at'].replace('Z', '+00:00'))
            appt_type = self._extract_appointment_type(appointment, appointment_type_lookup)
            
            # Count appointment types
            appointment_types[appt_type] = appointment_types.get(appt_type, 0) + 1
            
            # Track date ranges
            if first_appointment_date is None or appt_date < first_appointment_date:
                first_appointment_date = appt_date
            if last_appointment_date is None or appt_date > last_appointment_date:
                last_appointment_date = appt_date
            
            # Extract treatment notes
            if appointment.get('notes'):
                latest_treatment_note = appointment['notes']
            
            # Check if recent (last 30 days)
            if thirty_days_ago <= appt_date <= now:
                recent_count += 1
                recent_appointments.append({
                    'date': appointment['starts_at'],
                    'type': appt_type,
                    'id': appointment.get('id'),
                    'notes': appointment.get('notes', '')
                })
            
            # Check if upcoming
            elif appt_date > now:
                upcoming_count += 1
                upcoming_appointments.append({
                    'date': appointment['starts_at'],
                    'type': appt_type,
                    'id': appointment.get('id'),
                    'notes': appointment.get('notes', '')
                })
                
                # Set next appointment (earliest upcoming)
                if next_appointment_time is None or appt_date < next_appointment_time:
                    next_appointment_time = appt_date
                    next_appointment_type = appt_type
        
        # Determine primary appointment type (most common)
        if appointment_types:
            primary_appointment_type = max(appointment_types, key=appointment_types.get)
        
        # Determine activity status
        if recent_count > 0 and upcoming_count > 0:
            activity_status = 'active'
        elif recent_count > 0:
            activity_status = 'recently_active'
        elif upcoming_count > 0:
            activity_status = 'upcoming_only'
        else:
            activity_status = 'inactive'
        
        return {
            'is_active': recent_count > 0 or upcoming_count > 0,
            'activity_status': activity_status,
            'recent_appointment_count': recent_count,
            'upcoming_appointment_count': upcoming_count,
            'total_appointment_count': len(appointments),
            'first_appointment_date': first_appointment_date,
            'last_appointment_date': last_appointment_date,
            'next_appointment_time': next_appointment_time,
            'next_appointment_type': next_appointment_type,
            'primary_appointment_type': primary_appointment_type,
            'treatment_notes': latest_treatment_note,
            'recent_appointments': recent_appointments,
            'upcoming_appointments': upcoming_appointments
        }
    
    def _upsert_patient(self, cursor, organization_id: str, patient_data: Dict, appointment_stats: Dict) -> str:
        """
        Create or update patient record with appointment statistics
        Returns the patient UUID
        """
        try:
            # Extract patient info
            name = patient_data.get('first_name', '') + ' ' + patient_data.get('last_name', '')
            name = name.strip() or f"Patient {patient_data.get('id')}"
            
            # Extract phone number from patient_phone_numbers array (correct Cliniko API structure)
            phone = None
            phone_numbers = patient_data.get('patient_phone_numbers', [])
            if phone_numbers:
                # Prefer Mobile, then any other type
                mobile_phone = next((p for p in phone_numbers if p.get('phone_type') == 'Mobile'), None)
                if mobile_phone:
                    phone = self.cliniko_service._normalize_phone_number(mobile_phone.get('number'))
                else:
                    # Use first available phone number
                    first_phone = phone_numbers[0]
                    phone = self.cliniko_service._normalize_phone_number(first_phone.get('number'))
            
            email = patient_data.get('email')
            cliniko_patient_id = str(patient_data.get('id'))
            
            # Upsert patient
            query = """
            INSERT INTO patients (
                organization_id, name, email, phone, cliniko_patient_id, contact_type,
                is_active, activity_status, recent_appointment_count, upcoming_appointment_count,
                total_appointment_count, first_appointment_date, last_appointment_date,
                next_appointment_time, next_appointment_type, primary_appointment_type,
                treatment_notes, recent_appointments, upcoming_appointments,
                search_date_from, search_date_to, last_synced_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            RETURNING id
            """
            
            cursor.execute(query, [
                organization_id, name, email, phone, cliniko_patient_id, 'cliniko_patient',
                appointment_stats.get('is_active', False),
                appointment_stats.get('activity_status', 'imported'),
                appointment_stats.get('recent_appointment_count', 0),
                appointment_stats.get('upcoming_appointment_count', 0),
                appointment_stats.get('total_appointment_count', 0),
                appointment_stats.get('first_appointment_date'),
                appointment_stats.get('last_appointment_date'),
                appointment_stats.get('next_appointment_time'),
                appointment_stats.get('next_appointment_type'),
                appointment_stats.get('primary_appointment_type'),
                appointment_stats.get('treatment_notes'),
                json.dumps(appointment_stats.get('recent_appointments', [])),
                json.dumps(appointment_stats.get('upcoming_appointments', [])),
                self.six_months_ago,
                self.six_months_future,
                datetime.now(timezone.utc)
            ])
            
            result = cursor.fetchone()
            return str(result['id'])
            
        except Exception as e:
            logger.error(f"Error upserting patient {cliniko_patient_id}: {e}")
            raise
    
    def _upsert_appointments(self, cursor, organization_id: str, patient_uuid: str, 
                           appointments: List[Dict], appointment_type_lookup: Dict[str, str]):
        """
        Create or update individual appointment records
        """
        for appointment in appointments:
            try:
                # Skip archived appointments
                if appointment.get('archived_at'):
                    continue
                
                cliniko_appointment_id = str(appointment.get('id'))
                appointment_date = datetime.fromisoformat(appointment['starts_at'].replace('Z', '+00:00'))
                status = appointment.get('status', 'scheduled')
                appt_type = self._extract_appointment_type(appointment, appointment_type_lookup)
                notes = appointment.get('notes', '')
                
                # Check if appointment already exists first
                check_query = """
                SELECT id FROM appointments 
                WHERE cliniko_appointment_id = %s 
                LIMIT 1
                """
                cursor.execute(check_query, [cliniko_appointment_id])
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing appointment
                    update_query = """
                    UPDATE appointments SET
                        organization_id = %s,
                        patient_id = %s,
                        appointment_date = %s,
                        status = %s,
                        type = %s,
                        notes = %s,
                        metadata = %s,
                        updated_at = NOW()
                    WHERE cliniko_appointment_id = %s
                    """
                    cursor.execute(update_query, [
                        organization_id, 
                        patient_uuid,
                        appointment_date,
                        status,
                        appt_type,
                        notes,
                        json.dumps(appointment),
                        cliniko_appointment_id
                    ])
                else:
                    # Insert new appointment
                    insert_query = """
                    INSERT INTO appointments (
                        organization_id, patient_id, cliniko_appointment_id,
                        appointment_date, status, type, notes, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """
                    cursor.execute(insert_query, [
                        organization_id, 
                        patient_uuid,
                        cliniko_appointment_id,
                        appointment_date,
                        status,
                        appt_type,
                        notes,
                        json.dumps(appointment)
                    ])
                
                self.stats['appointments_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error upserting appointment {appointment.get('id')}: {e}")
                continue
    
    def _extract_patient_id_from_appointment(self, appointment: Dict) -> Optional[str]:
        """Extract patient ID from appointment data"""
        if 'patient' in appointment and appointment['patient']:
            if isinstance(appointment['patient'], dict):
                patient_id = appointment['patient'].get('id')
                if not patient_id and 'links' in appointment['patient']:
                    self_link = appointment['patient']['links'].get('self', '')
                    if self_link:
                        patient_id = self_link.split('/')[-1]
                return str(patient_id) if patient_id else None
            else:
                return str(appointment['patient'])
        elif 'patient_id' in appointment:
            return str(appointment['patient_id'])
        return None
    
    def _extract_appointment_type(self, appointment: Dict, appointment_type_lookup: Dict[str, str]) -> str:
        """Extract appointment type name"""
        # Use the same logic as ClinikoSyncService
        return self.cliniko_service._extract_appointment_type(appointment, appointment_type_lookup)
    
    def _update_last_sync_time(self, organization_id: str):
        """Update the last sync time for the organization"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_integrations 
                    SET last_sync_at = NOW()
                    WHERE organization_id = %s AND service_name = 'cliniko'
                """, (organization_id,))
        except Exception as e:
            logger.warning(f"Could not update last_sync_at: {e}")
    
    def _create_sync_log_entry(self, organization_id: str, operation_type: str, status: str, started_at: datetime) -> str:
        """Create initial sync log entry and return its ID for updates"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sync_logs (
                        organization_id, source_system, operation_type, status, 
                        records_processed, records_success, records_failed,
                        started_at, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """, (
                    organization_id,
                    "cliniko",
                    operation_type,
                    status,
                    0, 0, 0,
                    started_at.isoformat(),
                    json.dumps({"sync_type": operation_type, "step": "initializing"})
                ))
                
                sync_log_id = cursor.fetchone()["id"]
                return str(sync_log_id)
                
        except Exception as e:
            logger.error(f"Failed to create sync log entry: {e}")
            return ""
    
    def _update_sync_log_completion(self, sync_log_id: str, status: str, result: Dict[str, Any]):
        """Update sync log with completion status and results"""
        if not sync_log_id:
            return
            
        try:
            with db.get_cursor() as cursor:
                # Prepare metadata
                metadata = {
                    "sync_type": "comprehensive",
                    "step": "completed" if status == "completed" else "failed",
                    "patients_processed": self.stats.get('patients_processed', 0),
                    "appointments_processed": self.stats.get('appointments_processed', 0),
                    "patients_created": self.stats.get('patients_created', 0),
                    "patients_updated": self.stats.get('patients_updated', 0),
                    "appointments_created": self.stats.get('appointments_created', 0),
                    "appointments_updated": self.stats.get('appointments_updated', 0),
                    "errors": result.get('errors', []),
                    "completed_at": result.get('completed_at')
                }
                
                cursor.execute("""
                    UPDATE sync_logs SET
                        status = %s,
                        records_processed = %s,
                        records_success = %s,
                        records_failed = %s,
                        completed_at = %s,
                        error_details = %s,
                        metadata = %s
                    WHERE id = %s
                """, (
                    status,
                    self.stats.get('patients_processed', 0),
                    self.stats.get('patients_processed', 0) if status == "completed" else 0,
                    len(result.get('errors', [])),
                    datetime.now(timezone.utc) if status in ["completed", "failed"] else None,
                    json.dumps({"errors": result.get('errors', [])}) if result.get('errors') else json.dumps({}),
                    json.dumps(metadata),
                    sync_log_id
                ))
                
                logger.info(f"📊 Updated sync log {sync_log_id}: {status}")
                
        except Exception as e:
            logger.error(f"Failed to update sync log completion: {e}")

# Create singleton instance
comprehensive_sync_service = ComprehensiveClinikoSync() 