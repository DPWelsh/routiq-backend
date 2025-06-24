"""
Cliniko Sync Service for Multi-Tenant Active Patients
Uses stored credentials to sync active patients data by organization
"""

import os
import logging
import json
import requests
import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet

from src.database import db

logger = logging.getLogger(__name__)

class ClinikoSyncService:
    """Service to sync active patients from Cliniko using stored credentials"""
    
    def __init__(self):
        # Get encryption key for credential decryption
        self.encryption_key = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("CREDENTIALS_ENCRYPTION_KEY environment variable required")
        
        self.cipher_suite = Fernet(self.encryption_key.encode())
        
        # Define date ranges for active patients (last 45 days + next 30 days)
        self.current_date = datetime.now(timezone.utc)
        self.forty_five_days_ago = self.current_date - timedelta(days=45)
        self.thirty_days_future = self.current_date + timedelta(days=30)
        
    def _decrypt_credentials(self, encrypted_data) -> Dict[str, Any]:
        """Decrypt credentials from database storage"""
        try:
            # Handle both formats:
            # 1. Old format: JSON object with {"encrypted_data": "base64string"}
            # 2. New format: Direct base64 string
            # 3. Database dict format: Direct dict from JSONB field
            
            if isinstance(encrypted_data, dict):
                # Direct dict from database JSONB field
                if "encrypted_data" in encrypted_data:
                    # Old format: {"encrypted_data": "base64string"}
                    encrypted_bytes = base64.b64decode(encrypted_data["encrypted_data"].encode())
                else:
                    # Treat the whole dict as base64 somehow - this shouldn't happen
                    logger.error(f"Unexpected dict format: {encrypted_data}")
                    return {}
            elif isinstance(encrypted_data, str):
                try:
                    # Try to parse as JSON first (old format)
                    encrypted_json = json.loads(encrypted_data)
                    if isinstance(encrypted_json, dict) and "encrypted_data" in encrypted_json:
                        # Old format: {"encrypted_data": "base64string"}
                        encrypted_bytes = base64.b64decode(encrypted_json["encrypted_data"].encode())
                    else:
                        # Fallback: treat as direct base64 string
                        encrypted_bytes = base64.b64decode(encrypted_data.encode())
                except json.JSONDecodeError:
                    # New format: Direct base64 string
                    encrypted_bytes = base64.b64decode(encrypted_data.encode())
            else:
                logger.error(f"Unexpected data type: {type(encrypted_data)}")
                return {}
            
            # Decrypt and return
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            logger.error(f"Encrypted data type: {type(encrypted_data)}")
            logger.error(f"Encrypted data preview: {str(encrypted_data)[:100]}...")
            return {}
    
    def get_organization_service_config(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get Cliniko service configuration for organization"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT service_config, is_primary, is_active, sync_enabled, last_sync_at
                    FROM service_integrations 
                    WHERE organization_id = %s AND service_name = 'cliniko' AND is_active = true
                """, (organization_id,))
                
                result = cursor.fetchone()
                
            if not result:
                logger.warning(f"No Cliniko service configuration found for organization {organization_id}")
                return None
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to get service config for organization {organization_id}: {e}")
            return None

    def get_organization_cliniko_credentials(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Cliniko credentials for a specific organization"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT credentials_encrypted, is_active, last_validated_at
                    FROM service_credentials 
                    WHERE organization_id = %s AND service_name = 'cliniko' AND is_active = true
                """, (organization_id,))
                
                result = cursor.fetchone()
                
            if not result:
                logger.warning(f"No Cliniko credentials found for organization {organization_id}")
                return None
            
            # Decrypt credentials
            credentials = self._decrypt_credentials(result["credentials_encrypted"])
            
            if not credentials.get("api_key"):
                logger.error(f"Invalid Cliniko credentials for organization {organization_id}")
                return None
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve Cliniko credentials for org {organization_id}: {e}")
            return None
    
    def validate_cliniko_credentials(self, organization_id: str) -> Dict[str, Any]:
        """Validate Cliniko credentials by testing API connection"""
        logger.info(f"🔍 Validating Cliniko credentials for organization {organization_id}")
        
        result = {
            "organization_id": organization_id,
            "valid": False,
            "error": None,
            "account_info": None
        }
        
        try:
            # Get credentials
            credentials = self.get_organization_cliniko_credentials(organization_id)
            if not credentials:
                result["error"] = "No credentials found"
                return result
            
            # Set up API connection
            api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
            api_key = credentials["api_key"]
            headers = self._create_auth_headers(api_key)
            
            # Test connection with /practitioners endpoint (lightweight test - /account doesn't exist)
            test_url = f"{api_url}/practitioners"
            response = self._make_cliniko_request(test_url, headers)
            
            if response and "practitioners" in response:
                result["valid"] = True
                result["connection_info"] = {
                    "practitioners_count": len(response["practitioners"]),
                    "region": credentials.get("region", "Unknown"),
                    "api_url": api_url
                }
                logger.info(f"✅ Credentials valid - found {len(response['practitioners'])} practitioners")
            else:
                result["error"] = "API connection failed - practitioners endpoint returned no data"
                logger.error(f"❌ Credential validation failed for organization {organization_id}")
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Credential validation error for organization {organization_id}: {e}")
            return result
    
    def _create_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Create authentication headers for Cliniko API"""
        auth_string = f"{api_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_auth}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Routiq-Backend-ActivePatients"
        }
    
    def _make_cliniko_request(self, url: str, headers: Dict[str, str], params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to Cliniko API"""
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Cliniko API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Cliniko request exception: {str(e)}")
            return None
    
    def get_cliniko_patients_incremental(self, api_url: str, headers: Dict[str, str], 
                                        last_sync: Optional[datetime] = None) -> List[Dict]:
        """Get patients updated since last sync for better performance"""
        logger.info("📄 Fetching updated patients from Cliniko...")
        all_patients = []
        page = 1
        per_page = 100
        
        while True:
            logger.info(f"  Fetching updated patients page {page}...")
            
            url = f"{api_url}/patients"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'updated_at:desc'
            }
            
            # Add date filter if last sync available
            if last_sync:
                last_sync_str = last_sync.strftime('%Y-%m-%dT%H:%M:%SZ')
                params['q[]'] = f'updated_at:>={last_sync_str}'
            
            data = self._make_cliniko_request(url, headers, params)
            if not data:
                break
                
            patients = data.get('patients', [])
            if not patients:
                break
                
            all_patients.extend(patients)
            logger.info(f"    ✅ Added {len(patients)} patients (total: {len(all_patients)})")
            
            # Check if there are more pages
            links = data.get('links', {})
            if 'next' not in links:
                break
                
            page += 1
            
        logger.info(f"📊 Total updated patients loaded: {len(all_patients)}")
        return all_patients

    def get_cliniko_patients(self, api_url: str, headers: Dict[str, str]) -> List[Dict]:
        """Get all patients from Cliniko with pagination"""
        logger.info("📄 Fetching all patients from Cliniko...")
        all_patients = []
        page = 1
        per_page = 100
        
        while True:
            logger.info(f"  Fetching patients page {page}...")
            
            url = f"{api_url}/patients"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'created_at:desc'
            }
            
            data = self._make_cliniko_request(url, headers, params)
            if not data:
                break
                
            patients = data.get('patients', [])
            if not patients:
                break
                
            all_patients.extend(patients)
            logger.info(f"    ✅ Added {len(patients)} patients (total: {len(all_patients)})")
            
            # Check if there are more pages
            links = data.get('links', {})
            if 'next' not in links:
                break
                
            page += 1
            
        logger.info(f"📊 Total patients loaded: {len(all_patients)}")
        return all_patients
    
    def get_cliniko_appointments(self, api_url: str, headers: Dict[str, str], 
                               start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get appointments within date range from Cliniko"""
        logger.info(f"📅 Fetching appointments from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        
        all_appointments = []
        page = 1
        per_page = 100
        
        # Format dates for API (UTC)
        start_date_str = start_date.strftime('%Y-%m-%dT00:00:00Z')
        end_date_str = end_date.strftime('%Y-%m-%dT23:59:59Z')
        
        while True:
            logger.info(f"  Fetching appointments page {page}...")
            
            url = f"{api_url}/appointments"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'starts_at:desc',
                'q[]': [
                    f'starts_at:>={start_date_str}',
                    f'starts_at:<={end_date_str}'
                ]
            }
            
            data = self._make_cliniko_request(url, headers, params)
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
            
        logger.info(f"📊 Total appointments in date range: {len(all_appointments)}")
        return all_appointments
    
    def get_cliniko_appointment_types(self, api_url: str, headers: Dict[str, str]) -> Dict[str, str]:
        """Get appointment types from Cliniko and return a lookup dictionary"""
        logger.info("📋 Fetching appointment types from Cliniko...")
        
        appointment_type_lookup = {}
        page = 1
        per_page = 100
        
        while True:
            logger.info(f"  Fetching appointment types page {page}...")
            
            url = f"{api_url}/appointment_types"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'created_at:desc'
            }
            
            data = self._make_cliniko_request(url, headers, params)
            if not data:
                break
                
            appointment_types = data.get('appointment_types', [])
            if not appointment_types:
                break
                
            # Build lookup dictionary
            for appt_type in appointment_types:
                type_id = appt_type.get('id')
                type_name = appt_type.get('name', 'Unknown')
                if type_id:
                    appointment_type_lookup[type_id] = type_name
            
            logger.info(f"    ✅ Added {len(appointment_types)} appointment types (total: {len(appointment_type_lookup)})")
            
            # Check if there are more pages
            links = data.get('links', {})
            if 'next' not in links:
                break
                
            page += 1
            
        logger.info(f"📊 Total appointment types loaded: {len(appointment_type_lookup)}")
        return appointment_type_lookup

    def analyze_active_patients(self, patients: List[Dict], appointments: List[Dict], 
                               organization_id: str, appointment_type_lookup: Dict[str, str] = None) -> List[Dict]:
        """Analyze patients to determine which are active and prepare data for database"""
        logger.info("🔬 Analyzing patient activity...")
        
        # Create patient lookup
        patient_lookup = {patient['id']: patient for patient in patients}
        
        # Group appointments by patient
        patient_appointments = {}
        for appointment in appointments:
            # Skip archived appointments
            if appointment.get('archived_at'):
                continue
            
            # Extract patient ID from appointment
            patient_id = None
            if 'patient' in appointment and appointment['patient']:
                if isinstance(appointment['patient'], dict):
                    patient_id = appointment['patient'].get('id')
                    # If no direct ID, extract from links URL
                    if not patient_id and 'links' in appointment['patient']:
                        self_link = appointment['patient']['links'].get('self', '')
                        if self_link:
                            patient_id = self_link.split('/')[-1]
                else:
                    patient_id = appointment['patient']
            elif 'patient_id' in appointment:
                patient_id = appointment['patient_id']
                
            if patient_id:
                if patient_id not in patient_appointments:
                    patient_appointments[patient_id] = []
                patient_appointments[patient_id].append(appointment)
        
        logger.info(f"📊 Found appointments for {len(patient_appointments)} unique patients")
        
        # Analyze each patient with appointments
        active_patients_data = []
        for patient_id, patient_appts in patient_appointments.items():
            patient = patient_lookup.get(patient_id)
            if not patient:
                continue
                
            # Sort appointments by date for easier processing
            patient_appts.sort(key=lambda x: x['starts_at'])
            
            # Count recent and upcoming appointments
            recent_count = 0
            upcoming_count = 0
            recent_appointments = []
            upcoming_appointments = []
            
            # Track appointment types for analysis
            appointment_types = {}
            next_appointment = None
            latest_treatment_note = None
            
            for appt in patient_appts:
                appt_date = datetime.fromisoformat(appt['starts_at'].replace('Z', '+00:00'))
                
                # Extract appointment type - try multiple approaches
                appt_type = self._extract_appointment_type(appt, appointment_type_lookup)
                
                # Count appointment types
                appointment_types[appt_type] = appointment_types.get(appt_type, 0) + 1
                
                # Extract treatment notes if available
                if appt.get('notes'):
                    latest_treatment_note = appt['notes']
                
                # Check if appointment is in the last 45 days
                if self.forty_five_days_ago <= appt_date <= self.current_date:
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
                            'date': appt['starts_at'],
                            'type': appt_type,
                            'id': appt.get('id')
                        }
            
            # Determine primary appointment type (most common)
            primary_appointment_type = max(appointment_types.keys(), key=appointment_types.get) if appointment_types else None
            
            # Patient is active if they have recent OR upcoming appointments
            if recent_count > 0 or upcoming_count > 0:
                # Prepare patient data for the patients table
                # Combine first and last name for full name
                patient_name = f"{patient.get('first_name', '').strip()} {patient.get('last_name', '').strip()}".strip()
                if not patient_name:
                    patient_name = f"Patient {patient_id}"  # Fallback name
                
                # Calculate first appointment date
                first_appointment_date = min(appt['starts_at'] for appt in patient_appts) if patient_appts else None
                last_appointment_date = max(appt['starts_at'] for appt in patient_appts) if patient_appts else None
                
                # Determine activity status
                activity_status = "active"
                if upcoming_count > 0:
                    activity_status = "has_upcoming"
                elif recent_count > 0:
                    activity_status = "recent_only"
                
                active_patient_data = {
                    'organization_id': organization_id,
                    'name': patient_name,
                    'email': patient.get('email'),
                    'phone': patient.get('phone_number') or patient.get('mobile_phone') or patient.get('home_phone'),
                    'cliniko_patient_id': patient_id,
                    'contact_type': 'cliniko_patient',
                    'is_active': True,
                    'activity_status': activity_status,
                    'recent_appointment_count': recent_count,
                    'upcoming_appointment_count': upcoming_count,
                    'total_appointment_count': len(patient_appts),
                    'first_appointment_date': first_appointment_date,
                    'last_appointment_date': last_appointment_date,
                    'next_appointment_time': next_appointment['date'] if next_appointment else None,
                    'next_appointment_type': next_appointment['type'] if next_appointment else None,
                    'primary_appointment_type': primary_appointment_type,
                    'treatment_notes': latest_treatment_note,
                    'recent_appointments': recent_appointments,  # Will be JSON encoded in upsert
                    'upcoming_appointments': upcoming_appointments,  # Will be JSON encoded in upsert
                    'search_date_from': self.forty_five_days_ago,
                    'search_date_to': self.thirty_days_future
                }
                active_patients_data.append(active_patient_data)
        
        logger.info(f"✅ Found {len(active_patients_data)} active patients for organization {organization_id}")
        return active_patients_data

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

    
    def store_active_patients(self, active_patients_data: List[Dict]) -> int:
        """Store active patients data in the unified patients table"""
        logger.info(f"💾 Storing {len(active_patients_data)} active patients...")
        
        stored_count = 0
        
        try:
            with db.get_cursor() as cursor:
                for patient_data in active_patients_data:
                    success = self._upsert_patient_data(cursor, patient_data, patient_data.get('organization_id'))
                    if success:
                        stored_count += 1
                
                # Commit happens automatically in context manager
                
        except Exception as e:
            logger.error(f"Error storing active patients data: {e}")
            # Rollback happens automatically in context manager
            raise
        
        logger.info(f"✅ Stored {stored_count} active patients")
        return stored_count
    
    def sync_organization_active_patients(self, organization_id: str) -> Dict[str, Any]:
        """Sync active patients for a specific organization"""
        logger.info(f"🔄 Starting Cliniko active patients sync for organization {organization_id}")
        
        start_time = datetime.now(timezone.utc)
        result = {
            "organization_id": organization_id,
            "started_at": start_time.isoformat(),
            "success": False,
            "errors": [],
            "patients_found": 0,
            "appointments_found": 0,
            "active_patients_identified": 0,
            "active_patients_stored": 0
        }
        
        try:
            # Step 1: Check if organization has Cliniko service enabled
            service_config = self.get_organization_service_config(organization_id)
            if not service_config:
                result["errors"].append("No Cliniko service configuration found")
                return result
            
            if not service_config['sync_enabled']:
                result["errors"].append("Cliniko sync is disabled for this organization")
                return result
            
            # Step 2: Get Cliniko credentials
            credentials = self.get_organization_cliniko_credentials(organization_id)
            if not credentials:
                result["errors"].append("No Cliniko credentials found")
                return result
            
            # Step 3: Set up API connection
            api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
            api_key = credentials["api_key"]
            headers = self._create_auth_headers(api_key)
            
            logger.info(f"📡 Connected to Cliniko API: {api_url}")
            
            # Step 4: Fetch all patients
            logger.info("👥 Fetching patients from Cliniko...")
            patients = self.get_cliniko_patients(api_url, headers)
            result["patients_found"] = len(patients)
            
            if not patients:
                result["errors"].append("No patients found in Cliniko")
                return result
            
            # Step 5: Fetch appointments from last 45 days + next 30 days
            logger.info("📅 Fetching appointments from last 45 days + next 30 days...")
            appointments = self.get_cliniko_appointments(
                api_url, 
                headers, 
                self.forty_five_days_ago, 
                self.thirty_days_future
            )
            result["appointments_found"] = len(appointments)
            
            # Step 5: Get appointment types for proper type resolution
            logger.info("📋 Loading appointment types...")
            appointment_type_lookup = self.get_cliniko_appointment_types(api_url, headers)
            result["appointment_types_loaded"] = len(appointment_type_lookup)
            
            # Step 6: Analyze active patients
            logger.info("🔍 Analyzing active patients...")
            active_patients_data = self.analyze_active_patients(patients, appointments, organization_id, appointment_type_lookup)
            result["active_patients_identified"] = len(active_patients_data)
            
            # Step 7: Store active patients data
            if active_patients_data:
                logger.info("💾 Storing active patients data...")
                stored_count = self.store_active_patients(active_patients_data)
                result["active_patients_stored"] = stored_count
            
            # Step 8: Update last sync timestamp
            try:
                with db.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE service_integrations 
                        SET last_sync_at = NOW()
                        WHERE organization_id = %s AND service_name = 'cliniko'
                    """, (organization_id,))
                    # Connection commits automatically with context manager
            except Exception as e:
                logger.warning(f"Could not update last_sync_at: {e}")
            
            result["success"] = True
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Step 9: Log sync result to database
            self._log_sync_result(organization_id, result, True)
            
            logger.info(f"✅ Sync completed successfully:")
            logger.info(f"   - Patients found: {result['patients_found']}")
            logger.info(f"   - Appointments found: {result['appointments_found']}")
            logger.info(f"   - Active patients identified: {result['active_patients_identified']}")
            logger.info(f"   - Active patients stored: {result['active_patients_stored']}")
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            result["errors"].append(str(e))
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Log failed sync result
            self._log_sync_result(organization_id, result, False)
        
        return result
    
    def _log_sync_result(self, organization_id: str, result: Dict[str, Any], success: bool):
        """Log sync result to database"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sync_logs (
                        organization_id, source_system, operation_type, status, 
                        records_processed, records_success, records_failed,
                        started_at, completed_at, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    organization_id,
                    "cliniko",
                    "active_patients",
                    "completed" if success else "failed",
                    result.get("patients_found", 0),
                    result.get("active_patients_stored", 0),
                    len(result.get("errors", [])),
                    result.get("started_at"),
                    result.get("completed_at"),
                    json.dumps(result)
                ))
                
                # Commit happens automatically with context manager
                
        except Exception as e:
            logger.error(f"Failed to log sync result: {e}")
    
    def sync_all_organizations(self) -> List[Dict[str, Any]]:
        """Sync active patients for all organizations with Cliniko service enabled"""
        logger.info("🔄 Starting bulk active patients sync for all organizations")
        
        # Get all organizations with Cliniko service enabled
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT os.organization_id, o.name as organization_name
                    FROM service_integrations os
                    JOIN organizations o ON o.id = os.organization_id
                    WHERE os.service_name = 'cliniko' 
                    AND os.is_active = true 
                    AND os.sync_enabled = true
                """)
                
                organizations = cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to get organizations with Cliniko service: {e}")
            return []
        
        if not organizations:
            logger.warning("No organizations found with active Cliniko service")
            return []
        
        logger.info(f"Found {len(organizations)} organizations with Cliniko service enabled")
        all_results = []
        
        for org in organizations:
            org_id = org['organization_id']
            org_name = org['organization_name']
            logger.info(f"🔄 Processing organization: {org_name} ({org_id})")
            
            result = self.sync_organization_active_patients(org_id)
            all_results.append(result)
            
            # Small delay between organizations to prevent API rate limiting
            import time
            time.sleep(2)
        
        logger.info(f"✅ Completed bulk sync for {len(organizations)} organizations")
        return all_results

    def _upsert_patient_data(self, cursor, patient_data, organization_id):
        """Upsert patient data into the unified patients table"""
        try:
            # Insert or update patient in the unified patients table
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
            """
            
            cursor.execute(query, [
                organization_id,
                patient_data.get('name', ''),
                patient_data.get('email'),
                patient_data.get('phone'),
                patient_data.get('cliniko_patient_id'),
                'cliniko_patient',
                patient_data.get('is_active', False),
                patient_data.get('activity_status'),
                patient_data.get('recent_appointment_count', 0),
                patient_data.get('upcoming_appointment_count', 0),
                patient_data.get('total_appointment_count', 0),
                patient_data.get('first_appointment_date'),
                patient_data.get('last_appointment_date'),
                patient_data.get('next_appointment_time'),
                patient_data.get('next_appointment_type'),
                patient_data.get('primary_appointment_type'),
                patient_data.get('treatment_notes'),
                json.dumps(patient_data.get('recent_appointments', [])),
                json.dumps(patient_data.get('upcoming_appointments', [])),
                patient_data.get('search_date_from'),
                patient_data.get('search_date_to'),
                datetime.now(timezone.utc)
            ])
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting patient data: {e}")
            return False

# Global service instance
cliniko_sync_service = ClinikoSyncService() 