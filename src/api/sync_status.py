"""
Sync Status and Progress Tracking API
Provides real-time feedback on sync operations for dashboard integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime, timezone
import logging
from pydantic import BaseModel

from src.database import db
from src.services.cliniko_sync_service import cliniko_sync_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Global sync status storage (in production, use Redis or similar)
_sync_status_store = {}
_sync_progress_store = {}

class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    organization_id: str
    sync_id: str
    status: str  # 'idle', 'starting', 'fetching_patients', 'fetching_appointments', 'analyzing', 'storing', 'completed', 'failed'
    progress_percentage: int
    current_step: str
    total_steps: int
    current_step_number: int
    patients_found: int
    appointments_found: int
    active_patients_identified: int
    active_patients_stored: int
    started_at: Optional[str]
    completed_at: Optional[str]
    estimated_completion: Optional[str]
    errors: List[str]
    last_updated: str

class SyncHistoryResponse(BaseModel):
    """Response model for sync history"""
    organization_id: str
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    last_sync_at: Optional[str]
    last_successful_sync_at: Optional[str]
    average_sync_duration_seconds: Optional[float]
    recent_syncs: List[Dict[str, Any]]

def generate_sync_id(organization_id: str) -> str:
    """Generate a unique sync ID"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"sync_{organization_id}_{timestamp}"

def update_sync_progress(sync_id: str, status: str, step: str, step_number: int, 
                        total_steps: int, **kwargs):
    """Update sync progress in the store"""
    progress_percentage = int((step_number / total_steps) * 100) if total_steps > 0 else 0
    
    current_status = _sync_progress_store.get(sync_id, {})
    current_status.update({
        'status': status,
        'current_step': step,
        'current_step_number': step_number,
        'total_steps': total_steps,
        'progress_percentage': progress_percentage,
        'last_updated': datetime.now(timezone.utc).isoformat(),
        **kwargs
    })
    
    _sync_progress_store[sync_id] = current_status
    logger.info(f"Sync {sync_id}: {status} - {step} ({step_number}/{total_steps}) - {progress_percentage}%")

async def enhanced_sync_with_progress(organization_id: str, sync_id: str, sync_mode: str = "active"):
    """Enhanced sync function with detailed progress tracking
    
    Args:
        organization_id: Organization to sync
        sync_id: Unique sync identifier
        sync_mode: "active" (default) or "full" - determines which patients to sync
    """
    total_steps = 8
    
    # Initialize result tracking
    result = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'sync_mode': sync_mode,
        'patients_found': 0,
        'appointments_found': 0,
        'active_patients_identified': 0,
        'active_patients_stored': 0,
        'errors': []
    }
    
    try:
        # Step 1: Initialize
        sync_type_desc = "all patients" if sync_mode == "full" else "active patients"
        update_sync_progress(sync_id, 'starting', f'Initializing {sync_type_desc} sync...', 1, total_steps, 
                           organization_id=organization_id, started_at=result['started_at'])
        
        # Step 2: Check configuration
        update_sync_progress(sync_id, 'checking_config', 'Checking service configuration...', 2, total_steps)
        service_config = cliniko_sync_service.get_organization_service_config(organization_id)
        if not service_config or not service_config.get('sync_enabled'):
            raise Exception("Cliniko sync not enabled for this organization")
        
        # Step 3: Get credentials
        update_sync_progress(sync_id, 'checking_credentials', 'Validating credentials...', 3, total_steps)
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        if not credentials:
            raise Exception("No Cliniko credentials found")
        
        # Step 4: Fetch patients
        update_sync_progress(sync_id, 'fetching_patients', 'Fetching patients from Cliniko...', 4, total_steps)
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        api_key = credentials["api_key"]
        headers = cliniko_sync_service._create_auth_headers(api_key)
        
        patients = cliniko_sync_service.get_cliniko_patients(api_url, headers)
        result['patients_found'] = len(patients)
        update_sync_progress(sync_id, 'fetching_patients', f'Found {len(patients)} patients', 4, total_steps, 
                           patients_found=len(patients))
        
        if sync_mode == "full":
            # Full sync mode - sync ALL patients regardless of appointments
            # Step 5: Skip appointments for full sync
            update_sync_progress(sync_id, 'skipping_appointments', 'Skipping appointments (full sync mode)...', 5, total_steps)
            result['appointments_found'] = 0
            
            # Step 6: Skip appointment types
            update_sync_progress(sync_id, 'skipping_types', 'Skipping appointment types (full sync mode)...', 6, total_steps)
            
            # Step 7: Analyze ALL patients
            update_sync_progress(sync_id, 'analyzing', 'Analyzing all patients...', 7, total_steps)
            active_patients_data = cliniko_sync_service.analyze_all_patients(patients, organization_id)
            result['active_patients_identified'] = len(active_patients_data)
            update_sync_progress(sync_id, 'analyzing', f'Prepared {len(active_patients_data)} patients for sync', 7, total_steps,
                               active_patients_identified=len(active_patients_data))
            
            # Step 8: Store data
            update_sync_progress(sync_id, 'storing', 'Storing all patient data...', 8, total_steps)
            stored_count = 0
            if active_patients_data:
                stored_count = cliniko_sync_service.store_all_patients(active_patients_data)
        else:
            # Active sync mode - only sync patients with appointments (original behavior)
            # Step 5: Fetch appointments
            update_sync_progress(sync_id, 'fetching_appointments', 'Fetching appointments...', 5, total_steps)
            appointments = cliniko_sync_service.get_cliniko_appointments(
                api_url, headers, 
                cliniko_sync_service.forty_five_days_ago, 
                cliniko_sync_service.thirty_days_future
            )
            result['appointments_found'] = len(appointments)
            update_sync_progress(sync_id, 'fetching_appointments', f'Found {len(appointments)} appointments', 5, total_steps,
                               appointments_found=len(appointments))
            
            # Step 6: Get appointment types
            update_sync_progress(sync_id, 'loading_types', 'Loading appointment types...', 6, total_steps)
            appointment_type_lookup = cliniko_sync_service.get_cliniko_appointment_types(api_url, headers)
            
            # Step 7: Analyze active patients
            update_sync_progress(sync_id, 'analyzing', 'Analyzing active patients...', 7, total_steps)
            active_patients_data = cliniko_sync_service.analyze_active_patients(
                patients, appointments, organization_id, appointment_type_lookup
            )
            result['active_patients_identified'] = len(active_patients_data)
            update_sync_progress(sync_id, 'analyzing', f'Identified {len(active_patients_data)} active patients', 7, total_steps,
                               active_patients_identified=len(active_patients_data))
            
            # Step 8: Store data
            update_sync_progress(sync_id, 'storing', 'Storing active patient data...', 8, total_steps)
            stored_count = 0
            if active_patients_data:
                stored_count = cliniko_sync_service.store_active_patients(active_patients_data)
        
        result['active_patients_stored'] = stored_count
        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        # Complete progress tracking
        completion_msg = f'{sync_type_desc.title()} sync completed successfully!'
        update_sync_progress(sync_id, 'completed', completion_msg, 8, total_steps,
                           active_patients_stored=stored_count, 
                           completed_at=result['completed_at'])
        
        # Update last sync timestamp
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_integrations 
                    SET last_sync_at = NOW()
                    WHERE organization_id = %s AND service_name = 'cliniko'
                """, (organization_id,))
        except Exception as e:
            logger.warning(f"Could not update last_sync_at: {e}")
        
        # 🔥 FIX: Log successful sync to database
        _log_sync_completion(organization_id, result, True)
        
        return {
            'success': True,
            'sync_mode': sync_mode,
            'patients_found': result['patients_found'],
            'appointments_found': result['appointments_found'],
            'active_patients_identified': result['active_patients_identified'],
            'active_patients_stored': result['active_patients_stored']
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Sync {sync_id} failed: {error_msg}")
        
        result['errors'].append(error_msg)
        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        update_sync_progress(sync_id, 'failed', f'Sync failed: {error_msg}', 8, total_steps,
                           errors=[error_msg], completed_at=result['completed_at'])
        
        # 🔥 FIX: Log failed sync to database
        _log_sync_completion(organization_id, result, False)
        
        return {
            'success': False,
            'error': error_msg
        }

def _log_sync_completion(organization_id: str, result: Dict[str, Any], success: bool):
    """Log sync completion to sync_logs table"""
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
            
            logger.info(f"✅ Logged sync completion to database: {organization_id} - {'SUCCESS' if success else 'FAILED'}")
            
    except Exception as e:
        logger.error(f"❌ Failed to log sync completion: {e}")

@router.post("/sync/start/{organization_id}")
async def start_sync_with_progress(
    organization_id: str, 
    background_tasks: BackgroundTasks,
    sync_mode: str = Query("active", description="Sync mode: 'active' (patients with appointments) or 'full' (all patients)")
):
    """Start a sync operation with progress tracking
    
    Args:
        organization_id: Organization to sync
        sync_mode: 'active' (default) syncs only patients with appointments, 'full' syncs all patients
    """
    
    # Validate sync_mode
    if sync_mode not in ["active", "full"]:
        raise HTTPException(status_code=400, detail="sync_mode must be 'active' or 'full'")
    
    # Check if sync is already running
    existing_sync = None
    for sync_id, progress in _sync_progress_store.items():
        if (progress.get('organization_id') == organization_id and 
            progress.get('status') not in ['completed', 'failed']):
            existing_sync = sync_id
            break
    
    if existing_sync:
        return {
            "message": "Sync already in progress",
            "sync_id": existing_sync,
            "status": _sync_progress_store[existing_sync].get('status')
        }
    
    # Generate new sync ID
    sync_id = generate_sync_id(organization_id)
    
    # Start sync in background with specified mode
    background_tasks.add_task(enhanced_sync_with_progress, organization_id, sync_id, sync_mode)
    
    sync_type_desc = "all patients" if sync_mode == "full" else "active patients"
    return {
        "message": f"Sync started ({sync_type_desc})",
        "sync_id": sync_id,
        "organization_id": organization_id,
        "sync_mode": sync_mode,
        "status": "starting"
    }

@router.get("/sync/status/{sync_id}")
async def get_sync_status(sync_id: str) -> SyncStatusResponse:
    """Get current status of a sync operation"""
    
    if sync_id not in _sync_progress_store:
        raise HTTPException(status_code=404, detail="Sync not found")
    
    progress = _sync_progress_store[sync_id]
    
    return SyncStatusResponse(
        organization_id=progress.get('organization_id', ''),
        sync_id=sync_id,
        status=progress.get('status', 'unknown'),
        progress_percentage=progress.get('progress_percentage', 0),
        current_step=progress.get('current_step', ''),
        total_steps=progress.get('total_steps', 0),
        current_step_number=progress.get('current_step_number', 0),
        patients_found=progress.get('patients_found', 0),
        appointments_found=progress.get('appointments_found', 0),
        active_patients_identified=progress.get('active_patients_identified', 0),
        active_patients_stored=progress.get('active_patients_stored', 0),
        started_at=progress.get('started_at'),
        completed_at=progress.get('completed_at'),
        estimated_completion=None,  # TODO: Calculate based on progress
        errors=progress.get('errors', []),
        last_updated=progress.get('last_updated', '')
    )

@router.get("/sync/status/organization/{organization_id}")
async def get_organization_sync_status(organization_id: str):
    """Get current sync status for an organization"""
    
    # Find latest sync for this organization
    latest_sync = None
    latest_time = None
    
    for sync_id, progress in _sync_progress_store.items():
        if progress.get('organization_id') == organization_id:
            sync_time = progress.get('started_at')
            if sync_time and (not latest_time or sync_time > latest_time):
                latest_time = sync_time
                latest_sync = sync_id
    
    if not latest_sync:
        return {
            "organization_id": organization_id,
            "status": "no_sync_found",
            "message": "No sync operations found for this organization"
        }
    
    return await get_sync_status(latest_sync)

@router.get("/sync/history/{organization_id}")
async def get_sync_history(organization_id: str, limit: int = Query(10, ge=1, le=100)) -> SyncHistoryResponse:
    """Get sync history for an organization"""
    
    try:
        with db.get_cursor() as cursor:
            # Get sync statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_syncs,
                    COUNT(*) FILTER (WHERE status = 'completed') as successful_syncs,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_syncs,
                    MAX(started_at) as last_sync_at,
                    MAX(started_at) FILTER (WHERE status = 'completed') as last_successful_sync_at,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE completed_at IS NOT NULL) as avg_duration
                FROM sync_logs 
                WHERE organization_id = %s AND source_system = 'cliniko'
            """, (organization_id,))
            
            stats = cursor.fetchone()
            
            # Get recent syncs
            cursor.execute("""
                SELECT 
                    started_at, completed_at, status, records_processed, 
                    records_success, records_failed, metadata
                FROM sync_logs 
                WHERE organization_id = %s AND source_system = 'cliniko'
                ORDER BY started_at DESC 
                LIMIT %s
            """, (organization_id, limit))
            
            recent_syncs = cursor.fetchall()
            
            return SyncHistoryResponse(
                organization_id=organization_id,
                total_syncs=stats.get('total_syncs', 0),
                successful_syncs=stats.get('successful_syncs', 0),
                failed_syncs=stats.get('failed_syncs', 0),
                last_sync_at=stats.get('last_sync_at').isoformat() if stats.get('last_sync_at') else None,
                last_successful_sync_at=stats.get('last_successful_sync_at').isoformat() if stats.get('last_successful_sync_at') else None,
                average_sync_duration_seconds=stats.get('avg_duration'),
                recent_syncs=[dict(sync) for sync in recent_syncs]
            )
            
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sync history")

@router.get("/sync/stream/{sync_id}")
async def stream_sync_progress(sync_id: str):
    """Stream real-time sync progress using Server-Sent Events"""
    
    async def event_stream():
        last_status = None
        
        while True:
            if sync_id in _sync_progress_store:
                current_progress = _sync_progress_store[sync_id]
                current_status = current_progress.get('status')
                
                # Only send update if status changed
                if current_status != last_status:
                    data = json.dumps(current_progress)
                    yield f"data: {data}\n\n"
                    last_status = current_status
                    
                    # Stop streaming if sync is completed or failed
                    if current_status in ['completed', 'failed']:
                        break
            
            await asyncio.sleep(1)  # Check every second
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("/sync/active")
async def get_active_syncs():
    """Get all currently active sync operations"""
    
    active_syncs = []
    
    for sync_id, progress in _sync_progress_store.items():
        if progress.get('status') not in ['completed', 'failed']:
            active_syncs.append({
                'sync_id': sync_id,
                'organization_id': progress.get('organization_id'),
                'status': progress.get('status'),
                'progress_percentage': progress.get('progress_percentage', 0),
                'current_step': progress.get('current_step'),
                'started_at': progress.get('started_at')
            })
    
    return {
        "active_syncs": active_syncs,
        "total_active": len(active_syncs)
    }

@router.delete("/sync/cancel/{sync_id}")
async def cancel_sync(sync_id: str):
    """Cancel a running sync operation"""
    
    if sync_id not in _sync_progress_store:
        raise HTTPException(status_code=404, detail="Sync not found")
    
    progress = _sync_progress_store[sync_id]
    
    if progress.get('status') in ['completed', 'failed']:
        return {
            "message": "Sync already completed",
            "status": progress.get('status')
        }
    
    # Mark as cancelled
    update_sync_progress(sync_id, 'cancelled', 'Sync cancelled by user', 
                        progress.get('current_step_number', 0), 
                        progress.get('total_steps', 0),
                        completed_at=datetime.now(timezone.utc).isoformat())
    
    return {
        "message": "Sync cancelled",
        "sync_id": sync_id
    }

@router.get("/sync/dashboard/{organization_id}")
async def get_sync_dashboard_data(organization_id: str):
    """Get comprehensive sync dashboard data for an organization"""
    
    try:
        # Get current sync status
        current_sync = None
        for sync_id, progress in _sync_progress_store.items():
            if (progress.get('organization_id') == organization_id and 
                progress.get('status') not in ['completed', 'failed']):
                current_sync = {
                    'sync_id': sync_id,
                    'status': progress.get('status'),
                    'progress_percentage': progress.get('progress_percentage', 0),
                    'current_step': progress.get('current_step'),
                    'patients_found': progress.get('patients_found', 0),
                    'appointments_found': progress.get('appointments_found', 0),
                    'active_patients_identified': progress.get('active_patients_identified', 0),
                    'active_patients_stored': progress.get('active_patients_stored', 0)
                }
                break
        
        # Get patient counts from database
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_patients,
                    COUNT(*) FILTER (WHERE is_active = true) as active_patients,
                    COUNT(*) FILTER (WHERE upcoming_appointment_count > 0) as patients_with_upcoming,
                    COUNT(*) FILTER (WHERE recent_appointment_count > 0) as patients_with_recent,
                    MAX(last_synced_at) as last_sync_time
                FROM patients 
                WHERE organization_id = %s
            """, (organization_id,))
            
            patient_stats = cursor.fetchone()
            
            # Get recent sync summary
            cursor.execute("""
                SELECT status, started_at, completed_at, records_success
                FROM sync_logs 
                WHERE organization_id = %s AND source_system = 'cliniko'
                ORDER BY started_at DESC 
                LIMIT 1
            """, (organization_id,))
            
            last_sync = cursor.fetchone()
        
        return {
            "organization_id": organization_id,
            "current_sync": current_sync,
            "patient_stats": {
                "total_patients": patient_stats.get('total_patients', 0),
                "active_patients": patient_stats.get('active_patients', 0),
                "patients_with_upcoming": patient_stats.get('patients_with_upcoming', 0),
                "patients_with_recent": patient_stats.get('patients_with_recent', 0),
                "last_sync_time": patient_stats.get('last_sync_time').isoformat() if patient_stats.get('last_sync_time') else None
            },
            "last_sync": dict(last_sync) if last_sync else None,
            "sync_available": True
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data") 