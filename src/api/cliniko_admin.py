"""
Cliniko Integration API Router
Complete Cliniko sync management, patient import, monitoring and debugging endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from src.services.cliniko_sync_service import cliniko_sync_service
from src.database import db
from ..services.comprehensive_cliniko_sync import comprehensive_sync_service

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
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Cliniko ALL patients sync started successfully",
                "organization_id": "org_123456",
                "result": None,
                "timestamp": "2025-01-26T15:45:22.123Z"
            }
        }

class ClinikoStatusResponse(BaseModel):
    organization_id: str
    last_sync_time: Optional[datetime] = None
    total_patients: int
    active_patients: int
    synced_patients: int
    sync_percentage: float
    status: str

# Enhanced response models with examples
class SyncLogEntry(BaseModel):
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    records_processed: Optional[int]
    records_success: Optional[int]
    records_failed: Optional[int]
    error_message: Optional[str]

class HealthCheck(BaseModel):
    has_credentials: bool
    credentials_active: bool
    sync_enabled: bool
    has_patients: bool
    has_synced_data: bool
    high_sync_rate: bool
    service_last_sync: Optional[str]

class EnhancedStatusResponse(BaseModel):
    organization_id: str
    total_patients: int
    active_patients: int
    synced_patients: int
    sync_percentage: float
    last_sync_time: Optional[str]
    status: str
    timestamp: str
    sync_logs: Optional[List[SyncLogEntry]] = None
    sync_logs_count: Optional[int] = None
    health_check: Optional[HealthCheck] = None
    
    class Config:
        schema_extra = {
            "example": {
                "organization_id": "org_123456",
                "total_patients": 648,
                "active_patients": 421,
                "synced_patients": 645,
                "sync_percentage": 99.54,
                "last_sync_time": "2025-01-26T10:30:00.000Z",
                "status": "connected",
                "timestamp": "2025-01-26T15:45:22.123Z",
                "sync_logs": [
                    {
                        "status": "completed",
                        "started_at": "2025-01-26T10:25:00.000Z",
                        "completed_at": "2025-01-26T10:30:00.000Z",
                        "records_processed": 648,
                        "records_success": 645,
                        "records_failed": 3,
                        "error_message": None
                    }
                ],
                "sync_logs_count": 1,
                "health_check": {
                    "has_credentials": True,
                    "credentials_active": True,
                    "sync_enabled": True,
                    "has_patients": True,
                    "has_synced_data": True,
                    "high_sync_rate": True,
                    "service_last_sync": "2025-01-26T10:30:00.000Z"
                }
            }
        }

class PatientDetail(BaseModel):
    id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    cliniko_patient_id: Optional[str]
    is_active: bool
    recent_appointment_count: int
    upcoming_appointment_count: int
    total_appointment_count: int
    next_appointment_time: Optional[str]
    last_appointment_date: Optional[str]

class PatientStatsResponse(BaseModel):
    total_active_patients: int
    avg_recent_appointments: float
    avg_upcoming_appointments: float
    avg_total_appointments: float
    organization_id: str
    filters: Dict[str, bool]
    timestamp: str
    patient_details: Optional[List[PatientDetail]] = None
    patient_details_count: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "total_active_patients": 421,
                "avg_recent_appointments": 2.4,
                "avg_upcoming_appointments": 1.2,
                "avg_total_appointments": 12.8,
                "organization_id": "org_123456",
                "filters": {
                    "with_appointments_only": False,
                    "include_details": True
                },
                "timestamp": "2025-01-26T15:45:22.123Z",
                "patient_details": [
                    {
                        "id": "pt_789123",
                        "name": "John Smith",
                        "phone": "+1234567890",
                        "email": "john.smith@email.com",
                        "cliniko_patient_id": "ck_456789",
                        "is_active": True,
                        "recent_appointment_count": 3,
                        "upcoming_appointment_count": 2,
                        "total_appointment_count": 15,
                        "next_appointment_time": "2025-01-28T09:00:00.000Z",
                        "last_appointment_date": "2025-01-20T14:30:00.000Z"
                    }
                ],
                "patient_details_count": 50
            }
        }

async def run_cliniko_sync_background(organization_id: str):
    """Background task to run Cliniko sync - ALL PATIENTS"""
    try:
        result = cliniko_sync_service.sync_all_patients(organization_id)
        logger.info(f"✅ Cliniko FULL sync completed for organization {organization_id}: {result}")
    except Exception as e:
        logger.error(f"❌ Cliniko FULL sync failed for organization {organization_id}: {e}")

async def run_comprehensive_sync_background(organization_id: str):
    """Background task to run comprehensive Cliniko sync - ALL PATIENTS + APPOINTMENTS"""
    try:
        result = comprehensive_sync_service.sync_all_data(organization_id)
        if result.get("success"):
            logger.info(f"✅ Comprehensive Cliniko sync completed for organization {organization_id}")
            logger.info(f"   - Patients processed: {result.get('stats', {}).get('patients_processed', 0)}")
            logger.info(f"   - Appointments processed: {result.get('stats', {}).get('appointments_processed', 0)}")
        else:
            logger.error(f"❌ Comprehensive Cliniko sync failed for organization {organization_id}")
            if result.get("errors"):
                for error in result["errors"]:
                    logger.error(f"   - Error: {error}")
    except Exception as e:
        logger.error(f"❌ Comprehensive Cliniko sync failed for organization {organization_id}: {e}")

async def run_incremental_sync_background(organization_id: str, force_full: bool = False):
    """Background task to run incremental Cliniko sync - SMART EFFICIENCY"""
    try:
        result = comprehensive_sync_service.sync_incremental(organization_id, force_full)
        sync_type = result.get("sync_type", "incremental")
        if result.get("success"):
            if sync_type == "skipped_recent":
                logger.info(f"⏭️  Incremental sync skipped for organization {organization_id} (recent sync)")
            else:
                efficiency = result.get("efficiency_gain", "")
                logger.info(f"✅ Incremental Cliniko sync completed for organization {organization_id} ({sync_type})")
                if efficiency:
                    logger.info(f"   - Efficiency: {efficiency}")
                stats = result.get('stats', {})
                logger.info(f"   - Patients processed: {stats.get('patients_processed', 0)}")
                logger.info(f"   - Appointments processed: {stats.get('appointments_processed', 0)}")
        else:
            logger.error(f"❌ Incremental Cliniko sync failed for organization {organization_id}")
            if result.get("errors"):
                for error in result["errors"]:
                    logger.error(f"   - Error: {error}")
    except Exception as e:
        logger.error(f"❌ Incremental Cliniko sync failed for organization {organization_id}: {e}")

@router.post("/sync/{organization_id}", response_model=ClinikoSyncResponse)
async def trigger_cliniko_sync(
    organization_id: str,
    background_tasks: BackgroundTasks,
    mode: str = Query("incremental", description="Sync mode: 'incremental' (recommended), 'comprehensive', 'basic', or 'patients-only'"),
    force_full: bool = Query(False, description="Force full sync even in incremental mode")
):
    """
    Trigger Cliniko sync for an organization with configurable modes
    
    Sync Modes:
    - incremental (default): Smart sync - only fetch changed data (fastest, most efficient)
    - comprehensive: Full patients + appointments sync (slower but complete)
    - basic: Legacy mode - patients only, all marked as active (not recommended)
    - patients-only: Alias for basic mode (deprecated)
    
    Recommendation: Use 'incremental' mode for regular syncing, 'comprehensive' for initial setup
    """
    try:
        # Validate sync mode
        valid_modes = ["incremental", "comprehensive", "basic", "patients-only"]
        if mode not in valid_modes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sync mode '{mode}'. Valid modes: {', '.join(valid_modes)}"
            )
        
        # Log deprecation warning for legacy modes
        if mode in ["basic", "patients-only"]:
            logger.warning(f"⚠️  DEPRECATED: Using legacy sync mode '{mode}' for organization {organization_id}. "
                         f"Consider switching to 'incremental' mode for better efficiency.")
        
        force_info = " (force_full=True)" if force_full else ""
        logger.info(f"🔄 Starting Cliniko sync for organization {organization_id} (mode: {mode}){force_info}")
        
        # Choose sync method based on mode
        if mode == "incremental":
            # Use incremental sync (recommended for efficiency)
            background_tasks.add_task(run_incremental_sync_background, organization_id, force_full)
            sync_type = "full" if force_full else "incremental"
            message = f"Incremental Cliniko sync ({sync_type}) started successfully"
        elif mode == "comprehensive":
            # Use comprehensive sync for complete refresh
            background_tasks.add_task(run_comprehensive_sync_background, organization_id)
            message = "Comprehensive Cliniko sync (patients + appointments) started successfully"
        else:
            # Use legacy sync for backward compatibility
            background_tasks.add_task(run_cliniko_sync_background, organization_id)
            message = f"Legacy Cliniko sync (mode: {mode}) started successfully"
        
        return ClinikoSyncResponse(
            success=True,
            message=message,
            organization_id=organization_id,
            result={
                "sync_mode": mode, 
                "force_full": force_full if mode == "incremental" else None,
                "recommendation": "Use 'incremental' mode for best efficiency"
            },
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        # Re-raise HTTPException so FastAPI handles it properly
        raise
    except Exception as e:
        logger.error(f"Failed to start Cliniko sync for {organization_id}: {e}")
        return ClinikoSyncResponse(
            success=False,
            message=f"Failed to start Cliniko sync: {str(e)}",
            organization_id=organization_id,
            timestamp=datetime.now().isoformat()
        )



@router.get("/status/{organization_id}", response_model=EnhancedStatusResponse)
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

@router.get("/patients/{organization_id}/stats", response_model=PatientStatsResponse)
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













 