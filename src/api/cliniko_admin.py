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
    """Background task to run Cliniko sync - ALL PATIENTS"""
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
    This will sync ALL patients from Cliniko (not just active ones)
    """
    try:
        logger.info(f"🔄 Starting Cliniko sync for organization {organization_id}")
        
        # Add sync task to background
        background_tasks.add_task(run_cliniko_sync_background, organization_id)
        
        return ClinikoSyncResponse(
            success=True,
            message="Cliniko ALL patients sync started successfully",
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



@router.get("/active-patients-summary/{organization_id}")
async def get_active_patients_summary(
    organization_id: str, 
    include_details: bool = False,
    with_appointments_only: bool = False,
    limit: int = 50
):
    """
    Get summary and/or detailed data of active patients for an organization
    
    Query Parameters:
    - include_details: If true, include full patient records in addition to summary
    - with_appointments_only: If true, only include patients with appointments  
    - limit: Number of patient records to return (when include_details=true)
    """
    try:
        with db.get_cursor() as cursor:
            # Build WHERE clause based on filters
            where_conditions = ["organization_id = %s"]
            params = [organization_id]
            
            if not with_appointments_only:
                where_conditions.append("is_active = true")
            else:
                where_conditions.append("(recent_appointment_count > 0 OR upcoming_appointment_count > 0)")
            
            where_clause = " AND ".join(where_conditions)
            
            # Get summary statistics
            summary_query = f"""
            SELECT 
                COUNT(*) as total_active_patients,
                AVG(recent_appointment_count) as avg_recent_appointments,
                AVG(upcoming_appointment_count) as avg_upcoming_appointments,
                AVG(total_appointment_count) as avg_total_appointments
            FROM patients
            WHERE {where_clause}
            """
            
            cursor.execute(summary_query, params)
            summary_row = cursor.fetchone()
            
            # Build response with summary
            response = {
                "total_active_patients": summary_row['total_active_patients'] if summary_row else 0,
                "avg_recent_appointments": round(float(summary_row['avg_recent_appointments']), 2) if summary_row and summary_row['avg_recent_appointments'] else 0,
                "avg_upcoming_appointments": round(float(summary_row['avg_upcoming_appointments']), 2) if summary_row and summary_row['avg_upcoming_appointments'] else 0,
                "avg_total_appointments": round(float(summary_row['avg_total_appointments']), 2) if summary_row and summary_row['avg_total_appointments'] else 0,
                "organization_id": organization_id,
                "filters": {
                    "with_appointments_only": with_appointments_only,
                    "include_details": include_details
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add detailed patient records if requested
            if include_details:
                details_query = f"""
                SELECT 
                    id, name, phone, email, cliniko_patient_id, is_active,
                    activity_status, recent_appointment_count, upcoming_appointment_count,
                    total_appointment_count, first_appointment_date, last_appointment_date,
                    next_appointment_time, next_appointment_type, primary_appointment_type,
                    treatment_notes, recent_appointments, upcoming_appointments,
                    last_synced_at, created_at, updated_at
                FROM patients 
                WHERE {where_clause}
                ORDER BY 
                    CASE 
                        WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                        ELSE last_appointment_date 
                    END DESC
                LIMIT %s
                """
                
                cursor.execute(details_query, params + [limit])
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
                
                response["patient_details"] = patients
                response["patient_details_count"] = len(patients)
            
            return response
            
    except Exception as e:
        logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")





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
            FROM patients 
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







 