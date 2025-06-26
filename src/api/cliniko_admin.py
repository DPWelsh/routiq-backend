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
    total_patients: int
    active_patients: int
    synced_patients: int
    sync_percentage: float
    status: str

async def run_cliniko_sync_background(organization_id: str):
    """Background task to run Cliniko sync"""
    try:
        result = cliniko_sync_service.sync_organization_active_patients(organization_id)
        logger.info(f"✅ Cliniko sync completed for organization {organization_id}: {result}")
    except Exception as e:
        logger.error(f"❌ Cliniko sync failed for organization {organization_id}: {e}")

async def run_cliniko_full_sync_background(organization_id: str):
    """Background task to run Cliniko FULL sync (all patients)"""
    try:
        result = cliniko_sync_service.sync_all_patients(organization_id)
        logger.info(f"✅ Cliniko FULL sync completed for organization {organization_id}: {result}")
    except Exception as e:
        logger.error(f"❌ Cliniko FULL sync failed for organization {organization_id}: {e}")

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

@router.post("/sync-all/{organization_id}", response_model=ClinikoSyncResponse)
async def trigger_cliniko_full_sync(
    organization_id: str,
    background_tasks: BackgroundTasks
):
    """
    Trigger Cliniko FULL patient sync for an organization
    This will sync ALL patients from Cliniko (not just active ones)
    """
    try:
        logger.info(f"🔄 Starting Cliniko FULL sync for organization {organization_id}")
        
        # Add full sync task to background
        background_tasks.add_task(run_cliniko_full_sync_background, organization_id)
        
        return ClinikoSyncResponse(
            success=True,
            message="Cliniko FULL sync started successfully - all patients will be updated",
            organization_id=organization_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to start Cliniko FULL sync for {organization_id}: {e}")
        return ClinikoSyncResponse(
            success=False,
            message=f"Failed to start Cliniko FULL sync: {str(e)}",
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
            # Get total patients count (was contacts)
            cursor.execute(
                "SELECT COUNT(*) as total FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            total_result = cursor.fetchone()
            total_patients = total_result['total'] if total_result else 0
            
            # Get active patients count
            cursor.execute(
                "SELECT COUNT(*) as active FROM patients WHERE organization_id = %s AND is_active = true",
                [organization_id]
            )
            active_result = cursor.fetchone()
            active_patients = active_result['active'] if active_result else 0
            
            # Get patients with Cliniko IDs
            cursor.execute(
                "SELECT COUNT(*) as synced FROM patients WHERE organization_id = %s AND cliniko_patient_id IS NOT NULL",
                [organization_id]
            )
            synced_result = cursor.fetchone()
            synced_patients = synced_result['synced'] if synced_result else 0
            
            # Get last sync time
            cursor.execute(
                "SELECT MAX(last_synced_at) as last_sync FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            sync_result = cursor.fetchone()
            last_sync = sync_result['last_sync'] if sync_result else None
            
            return ClinikoStatusResponse(
                organization_id=organization_id,
                total_patients=total_patients,
                active_patients=active_patients,
                synced_patients=synced_patients,
                sync_percentage=round((synced_patients / total_patients * 100), 2) if total_patients > 0 else 0,
                last_sync_time=last_sync,
                status="connected" if synced_patients > 0 else "no_data"
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
        
        # First try the /practitioners endpoint (lightweight test - /account doesn't exist)
        practitioners_url = f"{api_url}/practitioners"
        practitioners_data = cliniko_sync_service._make_cliniko_request(practitioners_url, headers)
        
        if practitioners_data and "practitioners" in practitioners_data:
            # Practitioners endpoint worked, now try patients endpoint
            patients_url = f"{api_url}/patients"
            params = {"page": 1, "per_page": 1}
            
            patients_data = cliniko_sync_service._make_cliniko_request(patients_url, headers, params)
            
            if patients_data and "patients" in patients_data:
                return {
                    "success": True,
                    "message": "Cliniko API connection successful",
                    "organization_id": organization_id,
                    "api_url": api_url,
                    "practitioners_count": len(practitioners_data["practitioners"]),
                    "total_patients_available": patients_data.get("total_entries", 0),
                    "sample_patients_available": len(patients_data["patients"]) > 0,
                    "sample_patients_count": len(patients_data["patients"])
                }
            else:
                return {
                    "success": False,
                    "message": "Cliniko API connection failed - patients endpoint returned no data",
                    "organization_id": organization_id,
                    "api_url": api_url,
                    "practitioners_count": len(practitioners_data["practitioners"]),
                    "debug_info": "Practitioners endpoint works but patients endpoint failed"
                }
        else:
            return {
                "success": False,
                "message": "Cliniko API connection failed - practitioners endpoint failed",
                "organization_id": organization_id,
                "api_url": api_url,
                "debug_info": "Basic practitioners endpoint test failed (note: /account endpoint doesn't exist in Cliniko API)"
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
        ORDER BY started_at DESC
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
    Get active patients for an organization from the unified patients table
    """
    try:
        with db.get_cursor() as cursor:
            # Use unified patients table
            query = """
            SELECT 
                id,
                name,
                phone,
                email,
                cliniko_patient_id,
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
                last_synced_at,
                created_at,
                updated_at
            FROM patients 
            WHERE organization_id = %s AND is_active = true
            ORDER BY 
                CASE 
                    WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                    ELSE last_appointment_date 
                END DESC
            LIMIT 50
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "is_active": row['is_active'],
                    "activity_status": row['activity_status'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "first_appointment_date": row['first_appointment_date'].isoformat() if row['first_appointment_date'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "next_appointment_type": row['next_appointment_type'],
                    "primary_appointment_type": row['primary_appointment_type'],
                    "treatment_notes": row['treatment_notes'],
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    "last_synced_at": row['last_synced_at'].isoformat() if row['last_synced_at'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "active_patients": patients,
                "total_count": len(patients),
                "organization_id": organization_id
            }
            
    except Exception as e:
        logger.error(f"Failed to get active patients for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active patients: {str(e)}")

@router.get("/active-patients-summary/{organization_id}")
async def get_active_patients_summary(organization_id: str):
    """
    Get summary of active patients for an organization from the unified patients table
    """
    try:
        with db.get_cursor() as cursor:
            # Use unified patients table
            query = """
            SELECT 
                COUNT(*) as total_active_patients,
                AVG(recent_appointment_count) as avg_recent_appointments,
                AVG(upcoming_appointment_count) as avg_upcoming_appointments,
                AVG(total_appointment_count) as avg_total_appointments
            FROM patients
            WHERE organization_id = %s AND is_active = true
            """
            
            cursor.execute(query, [organization_id])
            row = cursor.fetchone()
            
            return {
                "total_active_patients": row['total_active_patients'] if row else 0,
                "avg_recent_appointments": round(float(row['avg_recent_appointments']), 2) if row and row['avg_recent_appointments'] else 0,
                "avg_upcoming_appointments": round(float(row['avg_upcoming_appointments']), 2) if row and row['avg_upcoming_appointments'] else 0,
                "avg_total_appointments": round(float(row['avg_total_appointments']), 2) if row and row['avg_total_appointments'] else 0,
                "organization_id": organization_id,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

@router.get("/patients/{organization_id}/with-appointments")
async def get_patients_with_appointments(organization_id: str):
    """
    Get patients that have appointments (active patients with appointment details) from the unified patients table
    """
    try:
        with db.get_cursor() as cursor:
            # Use unified patients table
            query = """
            SELECT 
                id,
                name,
                phone,
                email,
                cliniko_patient_id,
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
                upcoming_appointments
            FROM patients
            WHERE organization_id = %s 
            AND (recent_appointment_count > 0 OR upcoming_appointment_count > 0)
            ORDER BY 
                CASE 
                    WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                    ELSE last_appointment_date 
                END DESC
            LIMIT 100
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "is_active": row['is_active'],
                    "activity_status": row['activity_status'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "first_appointment_date": row['first_appointment_date'].isoformat() if row['first_appointment_date'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "next_appointment_type": row['next_appointment_type'],
                    "primary_appointment_type": row['primary_appointment_type'],
                    "treatment_notes": row['treatment_notes'],
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments']
                })
            
            return {
                "patients_with_appointments": patients,
                "total_count": len(patients),
                "organization_id": organization_id,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get patients with appointments for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patients: {str(e)}")

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
            
            # Check metrics from unified patients table
            patient_metrics_query = """
            SELECT 
                COUNT(*) as total_patients,
                COUNT(CASE WHEN cliniko_patient_id IS NOT NULL THEN 1 END) as cliniko_linked
            FROM patients
            WHERE organization_id = %s
            """
            patient_metrics_result = db.execute_query(patient_metrics_query, (organization_id,))
            patient_metrics = patient_metrics_result[0] if patient_metrics_result else None
            
            # Check active patients metrics
            active_metrics_query = """
            SELECT 
                COUNT(*) as total_active,
                AVG(recent_appointment_count) as avg_recent,
                AVG(upcoming_appointment_count) as avg_upcoming
            FROM patients
            WHERE organization_id = %s AND is_active = true
            """
            active_metrics_result = db.execute_query(active_metrics_query, (organization_id,))
            active_metrics = active_metrics_result[0] if active_metrics_result else None
            
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
            FROM service_integrations 
            WHERE organization_id = %s AND service_name = 'cliniko'
            """
            cursor.execute(service_query, [organization_id])
            service_config = cursor.fetchone()
            
            # Compile response
            return {
                "organization_id": organization_id,
                "credentials": service_config,
                "data_summary": {
                    "total_patients": patient_metrics['total_patients'] if patient_metrics else 0,
                    "cliniko_linked": patient_metrics['cliniko_linked'] if patient_metrics else 0,
                    "link_percentage": (patient_metrics['cliniko_linked'] / patient_metrics['total_patients'] * 100) if patient_metrics and patient_metrics['total_patients'] else 0
                },
                "active_patients": {
                    "total_active": active_metrics['total_active'] if active_metrics else 0,
                    "avg_recent_appointments": float(active_metrics['avg_recent']) if active_metrics and active_metrics['avg_recent'] else 0,
                    "avg_upcoming_appointments": float(active_metrics['avg_upcoming']) if active_metrics and active_metrics['avg_upcoming'] else 0
                },
                "sync_history": sync_history,
                "health_check": {
                    "has_credentials": service_config is not None,
                    "credentials_valid": service_config['sync_enabled'] if service_config else False,
                    "has_patients": (patient_metrics['total_patients'] if patient_metrics else 0) > 0,
                    "has_active_patients": (active_metrics['total_active'] if active_metrics else 0) > 0,
                    "high_link_rate": (patient_metrics['cliniko_linked'] / patient_metrics['total_patients'] * 100) > 90 if patient_metrics and patient_metrics['total_patients'] else False
                },
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to generate Cliniko sync dashboard for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

# Debug endpoints for troubleshooting Cliniko integration
@router.get("/debug/patients/{organization_id}")
async def debug_cliniko_patients(organization_id: str) -> Dict[str, Any]:
    """
    Debug patients for an organization to understand Cliniko sync issues
    """
    try:
        # Check total patients for organization
        total_query = """
        SELECT COUNT(*) as total_patients
        FROM patients
        WHERE organization_id = %s
        """
        total_result = db.execute_query(total_query, (organization_id,))
        total_patients = total_result[0]['total_patients'] if total_result else 0
        
        # Get sample patients
        sample_query = """
        SELECT id, name, email, phone, cliniko_patient_id, is_active, activity_status
        FROM patients
        WHERE organization_id = %s
        LIMIT 3
        """
        sample_patients = db.execute_query(sample_query, (organization_id,))
        
        # Check patients with cliniko_patient_id
        cliniko_query = """
        SELECT COUNT(*) as cliniko_linked_patients
        FROM patients
        WHERE organization_id = %s AND cliniko_patient_id IS NOT NULL
        """
        cliniko_result = db.execute_query(cliniko_query, (organization_id,))
        cliniko_linked = cliniko_result[0]['cliniko_linked_patients'] if cliniko_result else 0
        
        return {
            "organization_id": organization_id,
            "total_patients": total_patients,
            "cliniko_linked_patients": cliniko_linked,
            "sample_patients": sample_patients,
            "summary": {
                "has_patients": total_patients > 0,
                "link_percentage": (cliniko_linked / total_patients * 100) if total_patients > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug patients failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

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

@router.get("/debug/patients-full/{organization_id}")
async def debug_cliniko_patients_full(organization_id: str, limit: int = 3) -> Dict[str, Any]:
    """
    Get detailed patient data with full fields from the unified patients table
    """
    try:
        # Get detailed patient data
        query = """
        SELECT *
        FROM patients
        WHERE organization_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        patients = db.execute_query(query, (organization_id, limit))
        
        # Get summary stats
        stats_query = """
        SELECT 
            COUNT(*) as total_patients,
            COUNT(phone) as patients_with_phone,
            COUNT(CASE WHEN phone IS NULL THEN 1 END) as patients_without_phone
        FROM patients
        WHERE organization_id = %s
        """
        
        stats_result = db.execute_query(stats_query, (organization_id,))
        stats = stats_result[0] if stats_result else {}
        
        return {
            "organization_id": organization_id,
            "sample_full_patients": patients,
            "stats": stats,
            "total_sampled": len(patients),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Full debug patients failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.get("/debug/db-info/{organization_id}")
async def debug_database_info(organization_id: str):
    """Debug endpoint to check database constraints and patient count"""
    try:
        with db.get_cursor() as cursor:
            # Check constraints on patients table
            cursor.execute("""
                SELECT constraint_name, constraint_type, column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = 'patients' AND tc.table_schema = 'public'
                ORDER BY constraint_type, constraint_name
            """)
            constraints = cursor.fetchall()
            
            # Check indexes on patients table
            cursor.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'patients' AND schemaname = 'public'
                ORDER BY indexname
            """)
            indexes = cursor.fetchall()
            
            # Check patient count
            cursor.execute("SELECT COUNT(*) FROM patients WHERE organization_id = %s", [organization_id])
            patient_count = cursor.fetchone()['count']
            
            # Check total patient count
            cursor.execute("SELECT COUNT(*) FROM patients")
            total_patients = cursor.fetchone()['count']
            
            # Check recent sync attempts
            cursor.execute("""
                SELECT COUNT(*) FROM sync_logs 
                WHERE organization_id = %s AND source_system = 'cliniko'
                ORDER BY started_at DESC
                LIMIT 5
            """)
            sync_count = cursor.fetchone()['count']
            
            return {
                "organization_id": organization_id,
                "constraints": [{"name": c["constraint_name"], "type": c["constraint_type"], "column": c["column_name"]} for c in constraints],
                "indexes": [{"name": i["indexname"], "definition": i["indexdef"]} for i in indexes],
                "patient_count_org": patient_count,
                "total_patients": total_patients,
                "sync_logs_count": sync_count
            }
            
    except Exception as e:
        logger.error(f"Debug database info error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") 