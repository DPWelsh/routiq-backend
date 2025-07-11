"""
Comprehensive Cliniko Sync Service
Syncs ALL patients AND their appointments to both patients and appointments tables
Updated: 2025-06-30 - Added incremental sync for efficiency
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid
import time

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
            'errors': [],
            # Performance metrics
            'timing': {
                'total_duration': 0,
                'fetch_patients_duration': 0,
                'fetch_appointments_duration': 0,
                'process_data_duration': 0,
                'database_operations_duration': 0,
                'patients_per_second': 0,
                'appointments_per_second': 0
            }
        }
        
    def sync_incremental(self, organization_id: str, force_full: bool = False) -> Dict[str, Any]:
        """
        Incremental sync: Only fetch data updated since last sync
        Falls back to full sync if no last sync time found or if force_full=True
        """
        logger.info(f"🔄 Starting incremental Cliniko sync for organization {organization_id}")
        
        start_time = datetime.now(timezone.utc)
        result = {
            "organization_id": organization_id,
            "started_at": start_time.isoformat(),
            "success": False,
            "sync_type": "incremental",
            "errors": [],
            "stats": {}
        }
        
        # Create initial sync log entry
        sync_log_id = self._create_sync_log_entry(organization_id, "incremental_sync", "running", start_time)
        
        try:
            # Get last sync time
            last_sync_time = self._get_last_sync_time(organization_id)
            
            # If no last sync or force_full, do full sync
            if not last_sync_time or force_full:
                logger.info(f"📊 No previous sync found or force_full=True - performing full sync")
                result["sync_type"] = "full_fallback"
                return self.sync_all_data(organization_id)
            
            # Check if last sync was recent (within 5 minutes) to avoid unnecessary syncs
            # BUT allow force_full to bypass this cooldown
            time_since_last_sync = start_time - last_sync_time
            if time_since_last_sync.total_seconds() < 300 and not force_full:  # 5 minutes
                logger.info(f"📊 Last sync was {time_since_last_sync.total_seconds()//60:.0f} minutes ago - skipping")
                result["success"] = True
                result["sync_type"] = "skipped_recent"
                result["completed_at"] = datetime.now(timezone.utc).isoformat()
                result["stats"] = {"patients_processed": 0, "appointments_processed": 0}
                self._update_sync_log_completion(sync_log_id, "skipped", result)
                return result
            
            logger.info(f"📊 Last sync: {last_sync_time.isoformat()} ({time_since_last_sync.total_seconds()//3600:.1f} hours ago)")
            
            # Get Cliniko credentials
            credentials = self.cliniko_service.get_organization_cliniko_credentials(organization_id)
            if not credentials:
                raise Exception("No Cliniko credentials found")
            
            api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
            headers = self.cliniko_service._create_auth_headers(credentials["api_key"])
            
            logger.info(f"📡 Connected to Cliniko API: {api_url}")
            
            # Fetch only updated patients since last sync
            logger.info(f"👥 Fetching patients updated since {last_sync_time.isoformat()}...")
            fetch_start = time.time()
            patients = self.cliniko_service.get_cliniko_patients_incremental(api_url, headers, last_sync_time)
            fetch_patients_duration = time.time() - fetch_start
            self.stats['timing']['fetch_patients_duration'] = fetch_patients_duration
            logger.info(f"✅ Fetched {len(patients)} updated patients in {fetch_patients_duration:.2f}s")
            
            # Fetch only updated appointments (last 7 days + next 30 days for efficiency)
            appointment_start = start_time - timedelta(days=7)
            appointment_end = start_time + timedelta(days=30)
            logger.info(f"📅 Fetching appointments from {appointment_start.date()} to {appointment_end.date()}...")
            fetch_appointments_start = time.time()
            appointments = self._get_appointments_incremental(api_url, headers, last_sync_time, appointment_start, appointment_end)
            fetch_appointments_duration = time.time() - fetch_appointments_start
            self.stats['timing']['fetch_appointments_duration'] = fetch_appointments_duration
            logger.info(f"✅ Fetched {len(appointments)} appointments in {fetch_appointments_duration:.2f}s")
            
            # Get appointment types (cached/lightweight)
            logger.info("📋 Loading appointment types...")
            appointment_type_lookup = self.cliniko_service.get_cliniko_appointment_types(api_url, headers)
            
            # Process incremental data
            logger.info("💾 Processing incremental sync data...")
            logger.info(f"📊 About to process: {len(patients)} patients, {len(appointments)} appointments")
            
            process_start = time.time()
            # Use optimized batch processing for incremental sync too
            if len(patients) > 20:  # Use batch processing for larger sets
                self._sync_patients_and_appointments_optimized(
                    organization_id, 
                    patients, 
                    appointments, 
                    appointment_type_lookup
                )
            else:
                # Use individual processing for small sets (faster for < 20 patients)
                self._sync_patients_and_appointments_incremental(
                    organization_id, 
                    patients, 
                    appointments, 
                    appointment_type_lookup
                )
            
            process_duration = time.time() - process_start
            self.stats['timing']['process_data_duration'] = process_duration
            
            # Calculate performance metrics
            total_duration = time.time() - start_time.timestamp()
            self.stats['timing']['total_duration'] = total_duration
            if len(patients) > 0:
                self.stats['timing']['patients_per_second'] = len(patients) / process_duration
            if len(appointments) > 0:
                self.stats['timing']['appointments_per_second'] = len(appointments) / process_duration
            
            logger.info("✅ Completed incremental sync processing")
            logger.info(f"🚀 Performance: {len(patients)} patients in {process_duration:.2f}s ({self.stats['timing']['patients_per_second']:.1f} patients/sec)")
            
            # Update service last sync time
            self._update_last_sync_time(organization_id)
            
            # Success!
            result["success"] = True
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            result["stats"] = self.stats
            result["efficiency_gain"] = f"Processed {len(patients)} patients vs full sync of 650+"
            
            # Log successful completion
            self._update_sync_log_completion(sync_log_id, "completed", result)
            
            logger.info(f"✅ Incremental sync completed successfully:")
            logger.info(f"   - Updated patients: {len(patients)}")
            logger.info(f"   - Appointments in window: {len(appointments)}")
            logger.info(f"   - Efficiency: {len(patients)}/650+ patients processed")
            
        except Exception as e:
            logger.error(f"❌ Incremental sync failed: {e}")
            result["errors"].append(str(e))
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            result["stats"] = self.stats
            
            # Log failure
            self._update_sync_log_completion(sync_log_id, "failed", result)
        
        return result
        
    def _get_appointments_incremental(self, api_url: str, headers: Dict[str, str], 
                                    last_sync: datetime, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get appointments with both date range and update time filtering
        """
        logger.info(f"📅 Fetching appointments updated since {last_sync.isoformat()} in date range...")
        
        all_appointments = []
        page = 1
        per_page = 100
        
        # Format dates for API
        start_date_str = start_date.strftime('%Y-%m-%dT00:00:00Z')
        end_date_str = end_date.strftime('%Y-%m-%dT23:59:59Z')
        last_sync_str = last_sync.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        while True:
            logger.info(f"  Fetching incremental appointments page {page}...")
            
            url = f"{api_url}/appointments"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'updated_at:desc',
                'q[]': [
                    f'starts_at:>={start_date_str}',
                    f'starts_at:<={end_date_str}',
                    f'updated_at:>={last_sync_str}'
                ]
            }
            
            data = self.cliniko_service._make_cliniko_request(url, headers, params)
            if not data:
                break
                
            appointments = data.get('appointments', [])
            if not appointments:
                break
                
            all_appointments.extend(appointments)
            logger.info(f"    ✅ Added {len(appointments)} appointments (total: {len(all_appointments)})")
            
            # Check if there are more pages
            links = data.get('links', {})
            if 'next' not in links:
                break
                
            page += 1
            
        logger.info(f"📊 Total incremental appointments: {len(all_appointments)}")
        return all_appointments
        
    def _sync_patients_and_appointments_incremental(self, organization_id: str, patients: List[Dict], 
                                                  appointments: List[Dict], appointment_type_lookup: Dict[str, str]):
        """
        Incremental sync: Only update changed patients and their appointment data
        """
        logger.info("🔄 Syncing incremental patient and appointment updates...")
        
        # If no patients to update, still process appointments for existing patients
        if not patients:
            logger.info("📊 No patient updates, processing appointments for existing patients...")
            self._process_appointments_only(organization_id, appointments, appointment_type_lookup)
            return
        
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
        
        logger.info(f"📊 Processing {len(patients)} updated patients with {len(appointments)} appointments")
        
        # Process each updated patient
        for cliniko_patient_id, patient_data in patient_lookup.items():
            try:
                with db.get_cursor() as cursor:
                    # Get all appointments for this patient (not just recent ones)
                    # This ensures appointment stats are accurate
                    patient_appointments = self._get_all_patient_appointments(organization_id, cliniko_patient_id)
                    
                    # Add any new/updated appointments from this sync
                    new_appointments = appointments_by_patient.get(cliniko_patient_id, [])
                    if new_appointments:
                        patient_appointments.extend(new_appointments)
                    
                    # Calculate fresh appointment statistics
                    appointment_stats = self._calculate_appointment_stats(patient_appointments, appointment_type_lookup)
                    
                    # Update patient record
                    patient_uuid = self._upsert_patient(cursor, organization_id, patient_data, appointment_stats)
                    
                    # Update appointment records (only the new/changed ones)
                    if new_appointments:
                        self._upsert_appointments(cursor, organization_id, patient_uuid, new_appointments, appointment_type_lookup)
                    
                    self.stats['patients_processed'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing patient {cliniko_patient_id}: {e}")
                self.stats['errors'].append(f"Patient {cliniko_patient_id}: {str(e)}")
                continue
        
        logger.info("✅ Completed incremental sync processing")
        
    def _process_appointments_only(self, organization_id: str, appointments: List[Dict], appointment_type_lookup: Dict[str, str]):
        """
        Process appointment updates when no patient changes occurred
        """
        logger.info("📅 Processing appointment updates only...")
        
        appointments_by_patient = {}
        for appointment in appointments:
            patient_id = self._extract_patient_id_from_appointment(appointment)
            if patient_id:
                if patient_id not in appointments_by_patient:
                    appointments_by_patient[patient_id] = []
                appointments_by_patient[patient_id].append(appointment)
        
        for cliniko_patient_id, patient_appointments in appointments_by_patient.items():
            try:
                with db.get_cursor() as cursor:
                    # Find the patient UUID for this cliniko_patient_id
                    cursor.execute("""
                        SELECT id FROM patients 
                        WHERE organization_id = %s AND cliniko_patient_id = %s
                    """, (organization_id, cliniko_patient_id))
                    
                    patient_row = cursor.fetchone()
                    if not patient_row:
                        logger.warning(f"Patient {cliniko_patient_id} not found in database, skipping appointments")
                        continue
                    
                    patient_uuid = patient_row['id']
                    
                    # Update appointments for this patient
                    self._upsert_appointments(cursor, organization_id, patient_uuid, patient_appointments, appointment_type_lookup)
                    
                    # Recalculate appointment stats for this patient
                    all_appointments = self._get_all_patient_appointments(organization_id, cliniko_patient_id)
                    appointment_stats = self._calculate_appointment_stats(all_appointments, appointment_type_lookup)
                    
                    # Update patient's appointment statistics
                    self._update_patient_appointment_stats(cursor, patient_uuid, appointment_stats)
                    
                    self.stats['appointments_processed'] += len(patient_appointments)
                    
            except Exception as e:
                logger.error(f"Error processing appointments for patient {cliniko_patient_id}: {e}")
                continue
    
    def _get_all_patient_appointments(self, organization_id: str, cliniko_patient_id: str) -> List[Dict]:
        """
        Get all appointments for a patient from the database (for stats calculation)
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT appointment_date, status, type, metadata, created_at
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.id
                    WHERE p.organization_id = %s AND p.cliniko_patient_id = %s
                    AND a.deleted_at IS NULL
                    ORDER BY appointment_date DESC
                """, (organization_id, cliniko_patient_id))
                
                rows = cursor.fetchall()
                
                # Convert to format expected by stats calculation
                appointments = []
                for row in rows:
                    appointments.append({
                        'starts_at': row['appointment_date'].isoformat(),
                        'appointment_type': {'name': row['type']},
                        'notes': row.get('metadata', {}).get('notes', ''),
                        'deleted_at': None
                    })
                
                return appointments
                
        except Exception as e:
            logger.error(f"Error fetching patient appointments: {e}")
            return []
    
    def _update_patient_appointment_stats(self, cursor, patient_uuid: str, appointment_stats: Dict[str, Any]):
        """
        Update patient's appointment statistics without changing other fields
        """
        cursor.execute("""
            UPDATE patients SET 
                recent_appointment_count = %s,
                upcoming_appointment_count = %s,
                total_appointment_count = %s,
                first_appointment_date = %s,
                last_appointment_date = %s,
                next_appointment_time = %s,
                next_appointment_type = %s,
                primary_appointment_type = %s,
                recent_appointments = %s,
                upcoming_appointments = %s,
                updated_at = %s
            WHERE id = %s
        """, (
            appointment_stats['recent_appointment_count'],
            appointment_stats['upcoming_appointment_count'],
            appointment_stats['total_appointment_count'],
            appointment_stats['first_appointment_date'],
            appointment_stats['last_appointment_date'],
            appointment_stats['next_appointment_time'],
            appointment_stats['next_appointment_type'],
            appointment_stats['primary_appointment_type'],
            json.dumps(appointment_stats['recent_appointments']),
            json.dumps(appointment_stats['upcoming_appointments']),
            datetime.now(timezone.utc),
            patient_uuid
        ))
        
    def _get_last_sync_time(self, organization_id: str) -> Optional[datetime]:
        """
        Get the last successful sync time for an organization
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT last_sync_at FROM service_integrations
                    WHERE organization_id = %s AND service_name = 'cliniko'
                    AND is_active = true
                """, (organization_id,))
                
                result = cursor.fetchone()
                if result and result['last_sync_at']:
                    return result['last_sync_at']
                
                # Fallback: check sync logs
                cursor.execute("""
                    SELECT completed_at FROM sync_logs
                    WHERE organization_id = %s 
                    AND source_system = 'cliniko'
                    AND status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 1
                """, (organization_id,))
                
                result = cursor.fetchone()
                if result and result['completed_at']:
                    return result['completed_at']
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting last sync time: {e}")
            return None
    
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
            fetch_patients_start = time.time()
            patients = self.cliniko_service.get_cliniko_patients(api_url, headers)
            fetch_patients_duration = time.time() - fetch_patients_start
            self.stats['timing']['fetch_patients_duration'] = fetch_patients_duration
            logger.info(f"✅ Fetched {len(patients)} patients in {fetch_patients_duration:.2f}s")
            
            # Step 3: Fetch ALL appointments (last 6 months + next 6 months)
            logger.info("📅 Fetching ALL appointments from Cliniko...")
            fetch_appointments_start = time.time()
            appointments = self.cliniko_service.get_cliniko_appointments(
                api_url, 
                headers, 
                self.six_months_ago.date(), 
                self.six_months_future.date()
            )
            fetch_appointments_duration = time.time() - fetch_appointments_start
            self.stats['timing']['fetch_appointments_duration'] = fetch_appointments_duration
            logger.info(f"✅ Fetched {len(appointments)} appointments in {fetch_appointments_duration:.2f}s")
            
            # Step 4: Get appointment types for proper resolution
            logger.info("📋 Loading appointment types...")
            appointment_type_lookup = self.cliniko_service.get_cliniko_appointment_types(api_url, headers)
            
            # Step 5: Process and sync all data
            logger.info("💾 Processing and syncing all data...")
            logger.info(f"📊 About to process: {len(patients)} patients, {len(appointments)} appointments")
            
            process_start = time.time()
            self._sync_patients_and_appointments_optimized(
                organization_id, 
                patients, 
                appointments, 
                appointment_type_lookup
            )
            process_duration = time.time() - process_start
            self.stats['timing']['process_data_duration'] = process_duration
            
            # Calculate performance metrics
            total_duration = time.time() - start_time.timestamp()
            self.stats['timing']['total_duration'] = total_duration
            if len(patients) > 0:
                self.stats['timing']['patients_per_second'] = len(patients) / process_duration
            if len(appointments) > 0:
                self.stats['timing']['appointments_per_second'] = len(appointments) / process_duration
            
            logger.info("✅ Completed processing and syncing all data")
            logger.info(f"🚀 Performance: {len(patients)} patients in {process_duration:.2f}s ({self.stats['timing']['patients_per_second']:.1f} patients/sec)")
            
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
    
    def _sync_patients_and_appointments_optimized(self, organization_id: str, patients: List[Dict], 
                                      appointments: List[Dict], appointment_type_lookup: Dict[str, str]):
        """
        OPTIMIZED: Process patients and appointments in batches for 10-20x performance improvement
        """
        logger.info("🚀 Starting OPTIMIZED batch sync (much faster!)...")
        
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
        
        # Process patients in batches for massive performance improvement
        batch_size = 50
        total_patients = len(patient_lookup)
        processed_count = 0
        
        patient_items = list(patient_lookup.items())
        
        for i in range(0, len(patient_items), batch_size):
            batch = patient_items[i:i+batch_size]
            
            try:
                # Process entire batch in single transaction
                with db.get_cursor() as cursor:
                    batch_patients = []
                    batch_appointments = []
                    
                    # Prepare batch data
                    for cliniko_patient_id, patient_data in batch:
                        try:
                            # Get appointments for this patient
                            patient_appointments = appointments_by_patient.get(cliniko_patient_id, [])
                            
                            # Calculate appointment statistics
                            appointment_stats = self._calculate_appointment_stats(patient_appointments, appointment_type_lookup)
                            
                            # Prepare patient data for batch insert
                            patient_record = self._prepare_patient_record(organization_id, patient_data, appointment_stats)
                            batch_patients.append(patient_record)
                            
                            # Prepare appointment data for batch insert
                            for appointment in patient_appointments:
                                if not appointment.get('archived_at'):
                                    appointment_record = self._prepare_appointment_record(
                                        organization_id, cliniko_patient_id, appointment, appointment_type_lookup
                                    )
                                    batch_appointments.append(appointment_record)
                                    
                        except Exception as e:
                            logger.error(f"Error preparing patient {cliniko_patient_id}: {e}")
                            continue
                    
                    # Batch insert patients
                    if batch_patients:
                        self._batch_upsert_patients(cursor, batch_patients)
                        
                    # Batch insert appointments
                    if batch_appointments:
                        self._batch_upsert_appointments(cursor, batch_appointments)
                    
                    processed_count += len(batch)
                    self.stats['patients_processed'] += len(batch)
                    
                    # Log progress
                    progress_percent = (processed_count / total_patients) * 100
                    logger.info(f"🚀 BATCH Progress: {processed_count}/{total_patients} patients processed ({progress_percent:.1f}%)")
                    
            except Exception as e:
                logger.error(f"Error processing batch starting at patient {i}: {e}")
                self.stats['errors'].append(f"Batch {i}: {str(e)}")
                continue
        
        logger.info("✅ Completed OPTIMIZED batch sync")
        
    def _prepare_patient_record(self, organization_id: str, patient_data: Dict, appointment_stats: Dict) -> Dict:
        """Prepare patient record for batch insert"""
        # Extract patient info
        name = patient_data.get('first_name', '') + ' ' + patient_data.get('last_name', '')
        name = name.strip() or f"Patient {patient_data.get('id')}"
        
        # Extract phone number
        phone = None
        phone_numbers = patient_data.get('patient_phone_numbers', [])
        if phone_numbers:
            mobile_phone = next((p for p in phone_numbers if p.get('phone_type') == 'Mobile'), None)
            if mobile_phone:
                phone = mobile_phone.get('number')
            else:
                first_phone = phone_numbers[0]
                phone = first_phone.get('number')
        
        email = patient_data.get('email')
        cliniko_patient_id = str(patient_data.get('id'))
        
        return {
            'organization_id': organization_id,
            'name': name,
            'email': email,
            'phone': phone,
            'cliniko_patient_id': cliniko_patient_id,
            'contact_type': 'cliniko_patient',
            'is_active': appointment_stats.get('is_active', False),
            'activity_status': appointment_stats.get('activity_status', 'imported'),
            'recent_appointment_count': appointment_stats.get('recent_appointment_count', 0),
            'upcoming_appointment_count': appointment_stats.get('upcoming_appointment_count', 0),
            'total_appointment_count': appointment_stats.get('total_appointment_count', 0),
            'first_appointment_date': appointment_stats.get('first_appointment_date'),
            'last_appointment_date': appointment_stats.get('last_appointment_date'),
            'next_appointment_time': appointment_stats.get('next_appointment_time'),
            'next_appointment_type': appointment_stats.get('next_appointment_type'),
            'primary_appointment_type': appointment_stats.get('primary_appointment_type'),
            'treatment_notes': appointment_stats.get('treatment_notes'),
            'recent_appointments': json.dumps(appointment_stats.get('recent_appointments', [])),
            'upcoming_appointments': json.dumps(appointment_stats.get('upcoming_appointments', [])),
            'search_date_from': self.six_months_ago,
            'search_date_to': self.six_months_future,
            'last_synced_at': datetime.now(timezone.utc)
        }
    
    def _prepare_appointment_record(self, organization_id: str, cliniko_patient_id: str, appointment: Dict, appointment_type_lookup: Dict[str, str]) -> Dict:
        """Prepare appointment record for batch insert"""
        cliniko_appointment_id = str(appointment.get('id'))
        appointment_date = datetime.fromisoformat(appointment['starts_at'].replace('Z', '+00:00'))
        status = appointment.get('status', 'scheduled')
        appt_type = self._extract_appointment_type(appointment, appointment_type_lookup)
        notes = appointment.get('notes', '')
        
        return {
            'organization_id': organization_id,
            'cliniko_patient_id': cliniko_patient_id,
            'cliniko_appointment_id': cliniko_appointment_id,
            'appointment_date': appointment_date,
            'status': status,
            'type': appt_type,
            'notes': notes,
            'metadata': json.dumps(appointment)
        }
    
    def _batch_upsert_patients(self, cursor, batch_patients: List[Dict]):
        """Optimized batch upsert for patients using execute_values"""
        if not batch_patients:
            return
            
        # Use psycopg2.extras.execute_values for fast batch operations
        from psycopg2.extras import execute_values
        
        query = """
        INSERT INTO patients (
            organization_id, name, email, phone, cliniko_patient_id, contact_type,
            is_active, activity_status, recent_appointment_count, upcoming_appointment_count,
            total_appointment_count, first_appointment_date, last_appointment_date,
            next_appointment_time, next_appointment_type, primary_appointment_type,
            treatment_notes, recent_appointments, upcoming_appointments,
            search_date_from, search_date_to, last_synced_at
        ) VALUES %s
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
        """
        
        # Prepare values for batch insert
        values = []
        for patient in batch_patients:
            values.append((
                patient['organization_id'], patient['name'], patient['email'], patient['phone'],
                patient['cliniko_patient_id'], patient['contact_type'], patient['is_active'],
                patient['activity_status'], patient['recent_appointment_count'],
                patient['upcoming_appointment_count'], patient['total_appointment_count'],
                patient['first_appointment_date'], patient['last_appointment_date'],
                patient['next_appointment_time'], patient['next_appointment_type'],
                patient['primary_appointment_type'], patient['treatment_notes'],
                patient['recent_appointments'], patient['upcoming_appointments'],
                patient['search_date_from'], patient['search_date_to'], patient['last_synced_at']
            ))
        
        execute_values(cursor, query, values, page_size=50)
        logger.info(f"📊 Batch inserted {len(batch_patients)} patients")
    
    def _batch_upsert_appointments(self, cursor, batch_appointments: List[Dict]):
        """Optimized batch upsert for appointments"""
        if not batch_appointments:
            return
            
        from psycopg2.extras import execute_values
        
        # First, get patient UUIDs for all appointments
        patient_uuid_map = {}
        unique_patient_ids = set(apt['cliniko_patient_id'] for apt in batch_appointments)
        
        if unique_patient_ids:
            placeholders = ','.join(['%s'] * len(unique_patient_ids))
            cursor.execute(f"""
                SELECT cliniko_patient_id, id FROM patients 
                WHERE organization_id = %s AND cliniko_patient_id IN ({placeholders})
            """, [batch_appointments[0]['organization_id']] + list(unique_patient_ids))
            
            for row in cursor.fetchall():
                patient_uuid_map[row['cliniko_patient_id']] = row['id']
        
        # Prepare appointments with patient UUIDs
        valid_appointments = []
        for appointment in batch_appointments:
            patient_uuid = patient_uuid_map.get(appointment['cliniko_patient_id'])
            if patient_uuid:
                valid_appointments.append({
                    **appointment,
                    'patient_uuid': patient_uuid
                })
        
        if not valid_appointments:
            return
        
        # Batch upsert appointments
        query = """
        INSERT INTO appointments (
            organization_id, patient_id, cliniko_appointment_id,
            appointment_date, status, type, notes, metadata
        ) VALUES %s
        ON CONFLICT (cliniko_appointment_id) 
        DO UPDATE SET
            organization_id = EXCLUDED.organization_id,
            patient_id = EXCLUDED.patient_id,
            appointment_date = EXCLUDED.appointment_date,
            status = EXCLUDED.status,
            type = EXCLUDED.type,
            notes = EXCLUDED.notes,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """
        
        values = []
        for appointment in valid_appointments:
            values.append((
                appointment['organization_id'], appointment['patient_uuid'],
                appointment['cliniko_appointment_id'], appointment['appointment_date'],
                appointment['status'], appointment['type'], appointment['notes'],
                appointment['metadata']
            ))
        
        execute_values(cursor, query, values, page_size=100)
        logger.info(f"📊 Batch inserted {len(valid_appointments)} appointments")
    
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

# Create singleton instance
comprehensive_sync_service = ComprehensiveClinikoSync() 