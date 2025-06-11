"""
Cliniko Integration API Router
Complete Cliniko sync management, patient import, monitoring and debugging endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.services.cliniko_sync_service import cliniko_sync_service
from src.database import db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Cliniko"])

# Pydantic models
class ClinikoSyncResponse(BaseModel):
    success: bool
    message: str
    organization_id: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class ClinikoStatusResponse(BaseModel):
    organization_id: str
    last_sync_time: Optional[datetime] = None
    total_contacts: int
    active_patients: int
    upcoming_appointments: int
    message: str

async def run_cliniko_sync_background(organization_id: str):
    """Background task to run Cliniko sync"""
    try:
        result = cliniko_sync_service.sync_organization_active_patients(organization_id)
        logger.info(f"✅ Cliniko sync completed for organization {organization_id}: {result}")
    except Exception as e:
        logger.error(f"❌ Cliniko sync failed for organization {organization_id}: {e}")

@router.post("/sync/{organization_id}", response_model=ClinikoSyncResponse)
async def trigger_cliniko_sync(
    organization_id: str,
    background_tasks: BackgroundTasks
):
    """
    Trigger Cliniko patient sync for an organization
    This will sync patients, appointments, and contacts from Cliniko
    """
    try:
        logger.info(f"🔄 Starting Cliniko sync for organization {organization_id}")
        
        # Add sync task to background
        background_tasks.add_task(run_cliniko_sync_background, organization_id)
        
        return ClinikoSyncResponse(
            success=True,
            message="Cliniko sync started successfully",
            organization_id=organization_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to start Cliniko sync for {organization_id}: {e}")
        return ClinikoSyncResponse(
            success=False,
            message=f"Failed to start Cliniko sync: {str(e)}",
            organization_id=organization_id,
            timestamp=datetime.now().isoformat()
        )

@router.get("/status/{organization_id}", response_model=ClinikoStatusResponse)
async def get_cliniko_status(organization_id: str):
    """
    Get Cliniko sync status and data counts for an organization
    """
    try:
        with db.get_cursor() as cursor:
            # Get contact count
            cursor.execute(
                "SELECT COUNT(*) as total FROM contacts WHERE organization_id = %s",
                [organization_id]
            )
            contacts_result = cursor.fetchone()
            total_contacts = contacts_result['total'] if contacts_result else 0
            
            # Get active patients count
            cursor.execute(
                "SELECT COUNT(*) as total FROM active_patients WHERE organization_id = %s",
                [organization_id]
            )
            patients_result = cursor.fetchone()
            active_patients = patients_result['total'] if patients_result else 0
            
            # Get upcoming appointments count (from active_patients table)
            cursor.execute(
                "SELECT COUNT(*) as total FROM active_patients WHERE organization_id = %s AND upcoming_appointment_count > 0",
                [organization_id]
            )
            upcoming_result = cursor.fetchone()
            upcoming_appointments = upcoming_result['total'] if upcoming_result else 0
            
            # Get last sync time (from active_patients table)
            cursor.execute(
                "SELECT MAX(updated_at) as last_sync FROM active_patients WHERE organization_id = %s",
                [organization_id]
            )
            last_sync_result = cursor.fetchone()
            last_sync = last_sync_result['last_sync'] if last_sync_result else None
            
            return ClinikoStatusResponse(
                organization_id=organization_id,
                last_sync_time=last_sync,
                total_contacts=total_contacts or 0,
                active_patients=active_patients or 0,
                upcoming_appointments=upcoming_appointments or 0,
                message="Status retrieved successfully"
            )
                
    except Exception as e:
        logger.error(f"Failed to get Cliniko status for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Cliniko status: {str(e)}")

@router.get("/test-connection/{organization_id}")
async def test_cliniko_connection(organization_id: str):
    """
    Test Cliniko API connection for an organization
    """
    try:
        # Get organization credentials
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        
        if not credentials:
            return {
                "success": False,
                "message": "No Cliniko credentials found for organization",
                "organization_id": organization_id
            }
        
        # Test API connection
        headers = cliniko_sync_service._create_auth_headers(credentials["api_key"])
        api_url = credentials["api_url"]
        
        # Try fetching a small sample of patients
        url = f"{api_url}/patients"
        params = {"page[limit]": 1}
        
        data = cliniko_sync_service._make_cliniko_request(url, headers, params)
        
        if data and "data" in data:
            return {
                "success": True,
                "message": "Cliniko API connection successful",
                "organization_id": organization_id,
                "api_url": api_url,
                "sample_data_available": len(data["data"]) > 0
            }
        else:
            return {
                "success": False,
                "message": "Cliniko API connection failed - no data returned",
                "organization_id": organization_id
            }
            
    except Exception as e:
        logger.error(f"Failed to test Cliniko connection for {organization_id}: {e}")
        return {
            "success": False,
            "message": f"Cliniko connection test failed: {str(e)}",
            "organization_id": organization_id
        }

@router.post("/import-patients/{organization_id}")
async def import_cliniko_patients(organization_id: str) -> Dict[str, Any]:
    """
    Import all Cliniko patients into the contacts table for unified contact management
    """
    try:
        from src.services.cliniko_patient_import_service import ClinikoPatientImportService
        
        # Initialize the import service
        import_service = ClinikoPatientImportService(organization_id)
        
        # Run the import
        result = await import_service.import_all_patients()
        
        return {
            "operation": "cliniko_patient_import",
            "organization_id": organization_id,
            "import_result": result,
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Patient import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Patient import failed: {str(e)}")

@router.post("/test-sync/{organization_id}")
async def test_cliniko_sync(organization_id: str) -> Dict[str, Any]:
    """
    Test Cliniko sync for a specific organization - step by step validation
    """
    try:
        # Run the actual sync
        result = cliniko_sync_service.sync_organization_active_patients(organization_id)
        
        return {
            "test_type": "cliniko_sync_test",
            "organization_id": organization_id,
            "sync_result": result,
            "test_completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Test sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test sync failed: {str(e)}")

@router.get("/sync-logs/{organization_id}")
async def get_cliniko_sync_logs(organization_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get recent Cliniko sync logs for an organization
    """
    try:
        query = """
        SELECT *
        FROM sync_logs
        WHERE organization_id = %s AND source_system = 'cliniko'
        ORDER BY created_at DESC
        LIMIT %s;
        """
        
        logs = db.execute_query(query, (organization_id, limit))
        
        return {
            "organization_id": organization_id,
            "logs": logs,
            "total_logs": len(logs),
            "source_system": "cliniko"
        }
        
    except Exception as e:
        logger.error(f"Failed to get Cliniko sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-patients/{organization_id}")
async def get_active_patients(organization_id: str):
    """
    Get active patients for an organization from Cliniko sync
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                ap.*,
                c.name as contact_name,
                c.phone as contact_phone
            FROM active_patients ap
            JOIN contacts c ON ap.contact_id = c.id
            WHERE ap.organization_id = %s
            ORDER BY ap.last_appointment_date DESC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": row['id'],
                    "contact_id": str(row['contact_id']),
                    "contact_name": row['contact_name'],
                    "contact_phone": row['contact_phone'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "organization_id": organization_id,
                "active_patients": patients,
                "total_count": len(patients),
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to get active patients for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active patients: {str(e)}")

@router.get("/active-patients/{organization_id}/summary")
async def get_active_patients_summary(organization_id: str):
    """
    Get active patients summary for an organization from Cliniko
    """
    try:
        with db.get_cursor() as cursor:
            summary_query = """
            SELECT 
                COUNT(*) as total_active_patients,
                COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                MAX(updated_at) as last_sync_date,
                AVG(recent_appointment_count) as avg_recent_appointments,
                AVG(total_appointment_count) as avg_total_appointments
            FROM active_patients 
            WHERE organization_id = %s
            """
            
            cursor.execute(summary_query, [organization_id])
            row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "total_active_patients": row['total_active_patients'] if row else 0,
                "patients_with_recent_appointments": row['patients_with_recent'] if row else 0,
                "patients_with_upcoming_appointments": row['patients_with_upcoming'] if row else 0,
                "last_sync_date": row['last_sync_date'].isoformat() if row and row['last_sync_date'] else None,
                "avg_recent_appointments": float(row['avg_recent_appointments']) if row and row['avg_recent_appointments'] else 0.0,
                "avg_total_appointments": float(row['avg_total_appointments']) if row and row['avg_total_appointments'] else 0.0,
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

@router.get("/contacts/{organization_id}/with-appointments")
async def get_contacts_with_appointments(organization_id: str):
    """
    Get contacts that have appointments (active patients with contact details) from Cliniko
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                c.id,
                c.name,
                c.phone,
                c.email,
                c.cliniko_patient_id,
                ap.recent_appointment_count,
                ap.upcoming_appointment_count,
                ap.last_appointment_date,
                ap.recent_appointments
            FROM contacts c
            JOIN active_patients ap ON c.id = ap.contact_id
            WHERE c.organization_id = %s
            ORDER BY ap.last_appointment_date DESC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            contacts = []
            for row in rows:
                contacts.append({
                    "contact_id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "recent_appointments": row['recent_appointments']
                })
            
            return {
                "organization_id": organization_id,
                "contacts_with_appointments": contacts,
                "total_count": len(contacts),
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to get contacts with appointments for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contacts: {str(e)}")

@router.post("/sync/schedule/{organization_id}")
async def schedule_cliniko_sync(organization_id: str):
    """
    Schedule or trigger a Cliniko sync for an organization
    """
    try:
        from src.services.sync_scheduler import scheduler
        
        # Use the scheduler's safe sync method
        success = await scheduler.sync_organization_safe(organization_id)
        
        return {
            "organization_id": organization_id,
            "sync_scheduled": success,
            "message": "Cliniko sync started successfully" if success else "Sync already running or failed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule Cliniko sync for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule sync: {str(e)}")

@router.get("/sync/dashboard/{organization_id}")
async def get_cliniko_sync_dashboard(organization_id: str):
    """
    Comprehensive Cliniko sync status dashboard with metrics and recent activity
    """
    try:
        with db.get_cursor() as cursor:
            # Get overall sync metrics
            metrics_query = """
            SELECT 
                COUNT(*) as total_contacts,
                COUNT(CASE WHEN cliniko_patient_id IS NOT NULL THEN 1 END) as cliniko_linked,
                COUNT(*) - COUNT(CASE WHEN cliniko_patient_id IS NOT NULL THEN 1 END) as unlinked
            FROM contacts 
            WHERE organization_id = %s
            """
            cursor.execute(metrics_query, [organization_id])
            contact_metrics = cursor.fetchone()
            
            # Get active patients metrics
            active_query = """
            SELECT 
                COUNT(*) as total_active,
                AVG(recent_appointment_count) as avg_recent,
                AVG(total_appointment_count) as avg_total,
                MAX(last_appointment_date) as most_recent_appointment,
                MAX(updated_at) as last_sync
            FROM active_patients 
            WHERE organization_id = %s
            """
            cursor.execute(active_query, [organization_id])
            active_metrics = cursor.fetchone()
            
            # Get recent sync history (if sync_logs table exists)
            try:
                history_query = """
                SELECT 
                    status, started_at, completed_at, 
                    records_processed, records_success, records_failed
                FROM sync_logs 
                WHERE organization_id = %s AND source_system = 'cliniko'
                ORDER BY started_at DESC 
                LIMIT 10
                """
                cursor.execute(history_query, [organization_id])
                sync_history = cursor.fetchall()
            except:
                # Table doesn't exist yet
                sync_history = []
            
            # Get organization service config
            service_query = """
            SELECT service_config, is_active, sync_enabled, last_sync_at
            FROM organization_services 
            WHERE organization_id = %s AND service_name = 'cliniko'
            """
            cursor.execute(service_query, [organization_id])
            service_config = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "dashboard_generated_at": datetime.now().isoformat(),
                "contact_metrics": {
                    "total_contacts": contact_metrics['total_contacts'] if contact_metrics else 0,
                    "cliniko_linked": contact_metrics['cliniko_linked'] if contact_metrics else 0,
                    "unlinked": contact_metrics['unlinked'] if contact_metrics else 0,
                    "link_percentage": (contact_metrics['cliniko_linked'] / contact_metrics['total_contacts'] * 100) if contact_metrics and contact_metrics['total_contacts'] else 0
                },
                "active_patient_metrics": {
                    "total_active": active_metrics['total_active'] if active_metrics else 0,
                    "avg_recent_appointments": float(active_metrics['avg_recent']) if active_metrics and active_metrics['avg_recent'] else 0,
                    "avg_total_appointments": float(active_metrics['avg_total']) if active_metrics and active_metrics['avg_total'] else 0,
                    "most_recent_appointment": active_metrics['most_recent_appointment'].isoformat() if active_metrics and active_metrics['most_recent_appointment'] else None,
                    "last_sync": active_metrics['last_sync'].isoformat() if active_metrics and active_metrics['last_sync'] else None
                },
                "service_status": {
                    "cliniko_configured": service_config is not None,
                    "sync_enabled": service_config['sync_enabled'] if service_config else False,
                    "is_active": service_config['is_active'] if service_config else False,
                    "last_service_sync": service_config['last_sync_at'].isoformat() if service_config and service_config['last_sync_at'] else None
                },
                "sync_history": [
                    {
                        "status": row['status'],
                        "started_at": row['started_at'].isoformat() if row['started_at'] else None,
                        "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None,
                        "records_processed": row['records_processed'],
                        "records_success": row['records_success'],
                        "records_failed": row['records_failed']
                    } for row in sync_history
                ],
                "health_indicators": {
                    "has_contacts": (contact_metrics['total_contacts'] if contact_metrics else 0) > 0,
                    "has_active_patients": (active_metrics['total_active'] if active_metrics else 0) > 0,
                    "recent_sync": active_metrics and active_metrics['last_sync'] and (datetime.now() - active_metrics['last_sync']).days < 1 if active_metrics and active_metrics['last_sync'] else False,
                    "high_link_rate": (contact_metrics['cliniko_linked'] / contact_metrics['total_contacts'] * 100) > 90 if contact_metrics and contact_metrics['total_contacts'] else False
                }
            }
                
    except Exception as e:
        logger.error(f"Failed to generate Cliniko sync dashboard for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

# Debug endpoints for troubleshooting Cliniko integration
@router.get("/debug/contacts/{organization_id}")
async def debug_cliniko_contacts(organization_id: str) -> Dict[str, Any]:
    """
    Debug contacts for an organization to understand Cliniko sync issues
    """
    try:
        # Check total contacts for organization
        total_query = """
        SELECT COUNT(*) as total_contacts
        FROM contacts 
        WHERE organization_id = %s;
        """
        
        total_result = db.execute_query(total_query, (organization_id,))
        total_contacts = total_result[0]['total_contacts'] if total_result else 0
        
        # Get sample contacts
        sample_query = """
        SELECT id, name, email, cliniko_patient_id, created_at
        FROM contacts 
        WHERE organization_id = %s
        ORDER BY created_at DESC
        LIMIT 5;
        """
        
        sample_contacts = db.execute_query(sample_query, (organization_id,))
        
        # Check contacts with cliniko_patient_id
        cliniko_query = """
        SELECT COUNT(*) as cliniko_linked_contacts
        FROM contacts 
        WHERE organization_id = %s AND cliniko_patient_id IS NOT NULL;
        """
        
        cliniko_result = db.execute_query(cliniko_query, (organization_id,))
        cliniko_linked = cliniko_result[0]['cliniko_linked_contacts'] if cliniko_result else 0
        
        return {
            "organization_id": organization_id,
            "total_contacts": total_contacts,
            "cliniko_linked_contacts": cliniko_linked,
            "sample_contacts": sample_contacts,
            "debug_info": {
                "has_contacts": total_contacts > 0,
                "has_cliniko_links": cliniko_linked > 0,
                "contact_structure": "id, name, email, cliniko_patient_id"
            }
        }
        
    except Exception as e:
        logger.error(f"Debug contacts failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/patient-raw/{organization_id}")
async def debug_cliniko_patient_raw(organization_id: str) -> Dict[str, Any]:
    """
    Get raw Cliniko patient data to see all available fields including phone numbers
    """
    try:
        # Get credentials and set up API
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        if not credentials:
            return {"error": "No credentials found"}
            
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = cliniko_sync_service._create_auth_headers(credentials["api_key"])
        
        # Get first patient with full raw data
        url = f"{api_url}/patients"
        params = {'page': 1, 'per_page': 1}
        
        data = cliniko_sync_service._make_cliniko_request(url, headers, params)
        
        if not data or not data.get('patients'):
            return {"error": "No patients found"}
        
        raw_patient = data['patients'][0]
        
        return {
            "organization_id": organization_id,
            "raw_cliniko_patient": raw_patient,
            "available_fields": list(raw_patient.keys()),
            "phone_fields_check": {
                "phone_mobile": raw_patient.get('phone_mobile'),
                "phone_home": raw_patient.get('phone_home'),
                "phone": raw_patient.get('phone'),
                "mobile": raw_patient.get('mobile'),
                "home_phone": raw_patient.get('home_phone'),
                "mobile_phone": raw_patient.get('mobile_phone')
            }
        }
        
    except Exception as e:
        logger.error(f"Raw patient debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/contacts-full/{organization_id}")
async def debug_cliniko_contacts_full(organization_id: str, limit: int = 3) -> Dict[str, Any]:
    """
    Debug full contact records including phone numbers and external_ids from Cliniko sync
    """
    try:
        # Get full contact records
        query = """
        SELECT id, name, email, phone, cliniko_patient_id, 
               external_ids, primary_source, source_systems, 
               metadata, created_at
        FROM contacts 
        WHERE organization_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """
        
        contacts = db.execute_query(query, (organization_id, limit))
        
        # Check phone number statistics
        phone_stats_query = """
        SELECT 
            COUNT(*) as total_contacts,
            COUNT(phone) as contacts_with_phone,
            COUNT(CASE WHEN phone IS NULL THEN 1 END) as contacts_without_phone
        FROM contacts 
        WHERE organization_id = %s;
        """
        
        phone_stats = db.execute_query(phone_stats_query, (organization_id,))
        
        return {
            "organization_id": organization_id,
            "phone_statistics": phone_stats[0] if phone_stats else {},
            "sample_full_contacts": contacts,
            "analysis": {
                "total_sampled": len(contacts),
                "phone_extraction_issue": "Check if phone numbers exist in external_ids vs phone field"
            }
        }
        
    except Exception as e:
        logger.error(f"Full debug contacts failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug/sync-detailed/{organization_id}")
async def debug_cliniko_sync_detailed(organization_id: str) -> Dict[str, Any]:
    """
    Detailed Cliniko sync debug - show matching attempts and data flow
    """
    try:
        # Get credentials and set up API
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        if not credentials:
            return {"error": "No credentials found"}
            
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = cliniko_sync_service._create_auth_headers(credentials["api_key"])
        
        # Get first 5 patients and 5 appointments for testing
        print("Getting sample patients...")
        all_patients = cliniko_sync_service.get_cliniko_patients(api_url, headers)
        patients = all_patients[:5] if len(all_patients) > 5 else all_patients
        
        print("Getting sample appointments...")
        appointments = cliniko_sync_service.get_cliniko_appointments(
            api_url, 
            headers, 
            cliniko_sync_service.forty_five_days_ago, 
            cliniko_sync_service.current_date
        )
        sample_appointments = appointments[:5] if len(appointments) > 5 else appointments
        
        # Test contact matching for each patient
        matching_results = []
        for patient in patients:
            contact_id = cliniko_sync_service._find_contact_id(patient, organization_id)
            
            matching_results.append({
                "cliniko_patient": {
                    "id": patient.get('id'),
                    "name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                    "email": patient.get('email')
                },
                "contact_found": contact_id is not None,
                "contact_id": contact_id
            })
        
        return {
            "organization_id": organization_id,
            "debug_results": {
                "total_patients_available": len(all_patients),
                "total_appointments_45_days": len(appointments),
                "sample_patients_tested": len(patients),
                "sample_appointments": len(sample_appointments),
                "matching_attempts": matching_results
            },
            "sample_cliniko_data": {
                "patients": [
                    {
                        "id": p.get('id'),
                        "name": f"{p.get('first_name', '')} {p.get('last_name', '')}",
                        "email": p.get('email'),
                        "created_at": p.get('created_at')
                    } for p in patients
                ],
                "appointments": [
                    {
                        "id": a.get('id'),
                        "date": a.get('starts_at'),
                        "patient_id": a.get('patient', {}).get('id') if isinstance(a.get('patient'), dict) else a.get('patient')
                    } for a in sample_appointments
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed Cliniko debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 