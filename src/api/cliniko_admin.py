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





@router.get("/status/{organization_id}")
async def get_cliniko_status(
    organization_id: str, 
    include_logs: bool = False,
    include_health_check: bool = False,
    logs_limit: int = 5
):
    """
    Get comprehensive Cliniko sync status for an organization
    
    Query Parameters:
    - include_logs: If true, include recent sync history
    - include_health_check: If true, include detailed health diagnostics
    - logs_limit: Number of recent sync logs to return (when include_logs=true)
    """
    try:
        with db.get_cursor() as cursor:
            # Get basic patient counts and sync status
            cursor.execute(
                "SELECT COUNT(*) as total FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            total_result = cursor.fetchone()
            total_patients = total_result['total'] if total_result else 0
            
            cursor.execute(
                "SELECT COUNT(*) as active FROM patients WHERE organization_id = %s AND is_active = true",
                [organization_id]
            )
            active_result = cursor.fetchone()
            active_patients = active_result['active'] if active_result else 0
            
            cursor.execute(
                "SELECT COUNT(*) as synced FROM patients WHERE organization_id = %s AND cliniko_patient_id IS NOT NULL",
                [organization_id]
            )
            synced_result = cursor.fetchone()
            synced_patients = synced_result['synced'] if synced_result else 0
            
            cursor.execute(
                "SELECT MAX(last_synced_at) as last_sync FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            sync_result = cursor.fetchone()
            last_sync = sync_result['last_sync'] if sync_result else None
            
            # Build core response
            response = {
                "organization_id": organization_id,
                "total_patients": total_patients,
                "active_patients": active_patients,
                "synced_patients": synced_patients,
                "sync_percentage": round((synced_patients / total_patients * 100), 2) if total_patients > 0 else 0,
                "last_sync_time": last_sync.isoformat() if last_sync else None,
                "status": "connected" if synced_patients > 0 else "no_data",
                "timestamp": datetime.now().isoformat()
            }
            
            # Add sync logs if requested
            if include_logs:
                try:
                    logs_query = """
                    SELECT status, started_at, completed_at, 
                           records_processed, records_success, records_failed, error_message
                    FROM sync_logs 
                    WHERE organization_id = %s AND source_system = 'cliniko'
                    ORDER BY started_at DESC 
                    LIMIT %s
                    """
                    cursor.execute(logs_query, [organization_id, logs_limit])
                    logs = cursor.fetchall()
                    response["sync_logs"] = logs
                    response["sync_logs_count"] = len(logs)
                except Exception as logs_error:
                    logger.warning(f"Could not fetch sync logs: {logs_error}")
                    response["sync_logs"] = []
                    response["sync_logs_count"] = 0
            
            # Add health check if requested
            if include_health_check:
                try:
                    # Get service configuration
                    service_query = """
                    SELECT service_config, is_active, sync_enabled, last_sync_at
                    FROM service_integrations 
                    WHERE organization_id = %s AND service_name = 'cliniko'
                    """
                    cursor.execute(service_query, [organization_id])
                    service_config = cursor.fetchone()
                    
                    response["health_check"] = {
                        "has_credentials": service_config is not None,
                        "credentials_active": service_config['is_active'] if service_config else False,
                        "sync_enabled": service_config['sync_enabled'] if service_config else False,
                        "has_patients": total_patients > 0,
                        "has_synced_data": synced_patients > 0,
                        "high_sync_rate": (synced_patients / total_patients * 100) > 90 if total_patients > 0 else False,
                        "service_last_sync": service_config['last_sync_at'].isoformat() if service_config and service_config['last_sync_at'] else None
                    }
                except Exception as health_error:
                    logger.warning(f"Could not fetch health check data: {health_error}")
                    response["health_check"] = {
                        "has_credentials": False,
                        "credentials_active": False,
                        "sync_enabled": False,
                        "has_patients": total_patients > 0,
                        "has_synced_data": synced_patients > 0,
                        "high_sync_rate": False,
                        "service_last_sync": None
                    }
            
            return response
                
    except Exception as e:
        logger.error(f"Failed to get Cliniko status for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Cliniko status: {str(e)}")










@router.get("/patients/{organization_id}/stats")
async def get_patient_stats(
    organization_id: str, 
    include_details: bool = False,
    with_appointments_only: bool = False,
    limit: int = 50
):
    """
    Get patient statistics and/or detailed patient data for an organization
    
    Query Parameters:
    - include_details: If true, include full patient records in addition to stats
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













 