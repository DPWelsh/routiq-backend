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
        
        # Define date ranges for active patients (last 45 days)
        self.current_date = datetime.now(timezone.utc)
        self.forty_five_days_ago = self.current_date - timedelta(days=45)
        
    def _decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credentials from database storage"""
        try:
            # Handle both string and dict formats from database
            if isinstance(encrypted_data, str):
                encrypted_json = json.loads(encrypted_data)
            else:
                encrypted_json = encrypted_data
                
            encrypted_bytes = base64.b64decode(encrypted_json["encrypted_data"].encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return {}
    
    def get_organization_service_config(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get Cliniko service configuration for organization"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT service_config, is_primary, is_active, sync_enabled, last_sync_at
                    FROM organization_services 
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
                    FROM api_credentials 
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
            
            # Test connection with /account endpoint (lightweight test)
            test_url = f"{api_url}/account"
            response = self._make_cliniko_request(test_url, headers)
            
            if response:
                result["valid"] = True
                result["account_info"] = {
                    "name": response.get("name", "Unknown"),
                    "subdomain": response.get("subdomain", "Unknown"),
                    "region": credentials.get("region", "Unknown")
                }
                logger.info(f"✅ Credentials valid for {result['account_info']['name']}")
            else:
                result["error"] = "API connection failed"
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
    
    def analyze_active_patients(self, patients: List[Dict], appointments: List[Dict], 
                               organization_id: str) -> List[Dict]:
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
                
            # Count recent and upcoming appointments
            recent_count = 0
            upcoming_count = 0
            recent_appointments = []
            upcoming_appointments = []
            
            for appt in patient_appts:
                appt_date = datetime.fromisoformat(appt['starts_at'].replace('Z', '+00:00'))
                
                # Check if appointment is in the last 45 days
                if self.forty_five_days_ago <= appt_date <= self.current_date:
                    recent_count += 1
                    recent_appointments.append({
                        'date': appt['starts_at'],
                        'type': appt.get('appointment_type', {}).get('name', 'Unknown'),
                        'id': appt.get('id')
                    })
                
                # Check if appointment is upcoming
                if appt_date > self.current_date:
                    upcoming_count += 1
                    upcoming_appointments.append({
                        'date': appt['starts_at'],
                        'type': appt.get('appointment_type', {}).get('name', 'Unknown'),
                        'id': appt.get('id')
                    })
            
            # Patient is active if they have recent appointments
            if recent_count > 0:
                # Find corresponding contact_id from contacts table
                contact_id = self._find_contact_id(patient, organization_id)
                if contact_id:
                    active_patient_data = {
                        'contact_id': contact_id,
                        'organization_id': organization_id,
                        'recent_appointment_count': recent_count,
                        'upcoming_appointment_count': upcoming_count,
                        'total_appointment_count': len(patient_appts),
                        'last_appointment_date': max(appt['starts_at'] for appt in patient_appts) if patient_appts else None,
                        'recent_appointments': json.dumps(recent_appointments),
                        'upcoming_appointments': json.dumps(upcoming_appointments),
                        'search_date_from': self.forty_five_days_ago,
                        'search_date_to': self.current_date,
                        'cliniko_patient_id': patient_id  # Store for reference
                    }
                    active_patients_data.append(active_patient_data)
        
        logger.info(f"✅ Found {len(active_patients_data)} active patients for organization {organization_id}")
        return active_patients_data
    
    def _find_contact_id(self, patient: Dict, organization_id: str) -> Optional[str]:
        """Find the contact_id for a Cliniko patient in our contacts table"""
        try:
            # Try to find by Cliniko patient ID first
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM contacts 
                    WHERE organization_id = %s 
                    AND cliniko_patient_id = %s
                """, (organization_id, patient['id']))
                
                result = cursor.fetchone()
                if result:
                    return result['id']
                
                # If not found by ID, try to match by email
                if patient.get('email'):
                    cursor.execute("""
                        SELECT id FROM contacts 
                        WHERE organization_id = %s 
                        AND email = %s
                    """, (organization_id, patient['email']))
                    
                    result = cursor.fetchone()
                    if result:
                        return result['id']
                
                # If still not found, try to match by name
                first_name = patient.get('first_name', '').strip()
                last_name = patient.get('last_name', '').strip()
                if first_name and last_name:
                    cursor.execute("""
                        SELECT id FROM contacts 
                        WHERE organization_id = %s 
                        AND first_name ILIKE %s 
                        AND last_name ILIKE %s
                    """, (organization_id, first_name, last_name))
                    
                    result = cursor.fetchone()
                    if result:
                        return result['id']
            
            logger.warning(f"Could not find contact for Cliniko patient {patient['id']} in organization {organization_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding contact for patient {patient['id']}: {e}")
            return None
    
    def store_active_patients(self, active_patients_data: List[Dict]) -> int:
        """Store active patients data in the database"""
        if not active_patients_data:
            logger.info("No active patients data to store")
            return 0
        
        stored_count = 0
        
        try:
            with db.get_cursor() as cursor:
                for patient_data in active_patients_data:
                    # Use upsert to handle duplicates
                    cursor.execute("""
                        INSERT INTO active_patients (
                            contact_id, organization_id, recent_appointment_count,
                            upcoming_appointment_count, total_appointment_count,
                            last_appointment_date, recent_appointments, upcoming_appointments,
                            search_date_from, search_date_to
                        ) VALUES (
                            %(contact_id)s, %(organization_id)s, %(recent_appointment_count)s,
                            %(upcoming_appointment_count)s, %(total_appointment_count)s,
                            %(last_appointment_date)s, %(recent_appointments)s, %(upcoming_appointments)s,
                            %(search_date_from)s, %(search_date_to)s
                        )
                        ON CONFLICT (contact_id)
                        DO UPDATE SET
                            recent_appointment_count = EXCLUDED.recent_appointment_count,
                            upcoming_appointment_count = EXCLUDED.upcoming_appointment_count,
                            total_appointment_count = EXCLUDED.total_appointment_count,
                            last_appointment_date = EXCLUDED.last_appointment_date,
                            recent_appointments = EXCLUDED.recent_appointments,
                            upcoming_appointments = EXCLUDED.upcoming_appointments,
                            search_date_from = EXCLUDED.search_date_from,
                            search_date_to = EXCLUDED.search_date_to,
                            updated_at = NOW()
                    """, patient_data)
                    
                    stored_count += 1
                
                db.connection.commit()
                
        except Exception as e:
            logger.error(f"Error storing active patients data: {e}")
            db.connection.rollback()
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
            
            # Step 5: Fetch appointments from last 45 days
            logger.info("📅 Fetching appointments from last 45 days...")
            appointments = self.get_cliniko_appointments(
                api_url, 
                headers, 
                self.forty_five_days_ago, 
                self.current_date
            )
            result["appointments_found"] = len(appointments)
            
            # Step 6: Analyze active patients
            logger.info("🔍 Analyzing active patients...")
            active_patients_data = self.analyze_active_patients(patients, appointments, organization_id)
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
                        UPDATE organization_services 
                        SET last_sync_at = NOW()
                        WHERE organization_id = %s AND service_name = 'cliniko'
                    """, (organization_id,))
                    db.connection.commit()
            except Exception as e:
                logger.warning(f"Could not update last_sync_at: {e}")
            
            result["success"] = True
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"✅ Sync completed successfully:")
            logger.info(f"   - Patients found: {result['patients_found']}")
            logger.info(f"   - Appointments found: {result['appointments_found']}")
            logger.info(f"   - Active patients identified: {result['active_patients_identified']}")
            logger.info(f"   - Active patients stored: {result['active_patients_stored']}")
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            result["errors"].append(str(e))
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        return result
    
    def _log_sync_result(self, organization_id: str, result: Dict[str, Any], success: bool):
        """Log sync result to database"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sync_logs (
                        organization_id, sync_type, status, results, 
                        started_at, completed_at, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, NOW()
                    )
                """, (
                    organization_id,
                    "cliniko_active_patients",
                    "completed" if success else "failed",
                    json.dumps(result),
                    result.get("started_at"),
                    result.get("completed_at")
                ))
                
                db.connection.commit()
                
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
                    FROM organization_services os
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

# Global service instance
cliniko_sync_service = ClinikoSyncService() 