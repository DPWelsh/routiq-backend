"""
Sync Status and Progress Tracking API
Provides real-time feedback on sync operations for dashboard integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, List, Any, Optional
import json
import asyncio
import os
from datetime import datetime, timezone, timedelta
import logging
from pydantic import BaseModel

from src.database import db
from src.services.cliniko_sync_service import cliniko_sync_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Global sync status storage (in production, use Redis or similar)
_sync_status_store = {}
_sync_progress_store = {}

# Add timeout configuration
SYNC_TIMEOUT_SECONDS = int(os.getenv('SYNC_TIMEOUT_SECONDS', '300'))  # 5 minutes default
RAILWAY_TIMEOUT_SECONDS = int(os.getenv('RAILWAY_TIMEOUT_SECONDS', '180'))  # 3 minutes for Railway

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
    """Enhanced sync function with detailed progress tracking and timeout handling
    
    Args:
        organization_id: Organization to sync
        sync_id: Unique sync identifier
        sync_mode: "active" (default) or "full" - determines which patients to sync
    """
    total_steps = 8
    sync_start_time = datetime.now(timezone.utc)
    
    # Initialize result tracking
    result = {
        'started_at': sync_start_time.isoformat(),
        'sync_mode': sync_mode,
        'patients_found': 0,
        'appointments_found': 0,
        'active_patients_identified': 0,
        'active_patients_stored': 0,
        'errors': [],
        'timeout_handled': False
    }
    
    try:
        # Step 1: Initialize with timeout check
        update_sync_progress(sync_id, 'starting', 'Initializing sync...', 1, total_steps, 
                           organization_id=organization_id, started_at=result['started_at'])
        
        # Check if we're approaching timeout
        if _check_timeout(sync_start_time):
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
        
                 # Step 2: Check credentials with timeout
         update_sync_progress(sync_id, 'running', 'Checking Cliniko credentials...', 2, total_steps)
         
         cliniko_sync_service = ClinikoSyncService()
         credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        
        if not credentials:
            error_msg = "No Cliniko credentials found for organization"
            result['errors'].append(error_msg)
            update_sync_progress(sync_id, 'failed', error_msg, 2, total_steps)
            await _log_sync_result(organization_id, sync_id, 'failed', result)
            return
        
        # Check timeout before API calls
        if _check_timeout(sync_start_time):
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
            
        # Step 3: Fetch patients with chunking for large datasets
        update_sync_progress(sync_id, 'running', 'Fetching patient data from Cliniko...', 3, total_steps)
        
        api_url = credentials.get('api_url', 'https://api.au4.cliniko.com/v1')
        headers = cliniko_sync_service._create_auth_headers(credentials['api_key'])
        
        # Use async fetching with timeout
        patients = await _fetch_patients_with_timeout(cliniko_sync_service, api_url, headers, sync_start_time)
        
        if patients is None:  # Timeout occurred
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
            
        result['patients_found'] = len(patients)
        update_sync_progress(sync_id, 'running', f'Found {len(patients)} patients. Fetching appointments...', 4, total_steps)
        
        # Check timeout before appointments
        if _check_timeout(sync_start_time):
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
        
        # Step 4: Fetch appointments with timeout
        appointments = await _fetch_appointments_with_timeout(cliniko_sync_service, api_url, headers, sync_start_time)
        
        if appointments is None:  # Timeout occurred
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
            
        result['appointments_found'] = len(appointments)
        update_sync_progress(sync_id, 'running', f'Found {len(appointments)} appointments. Analyzing active patients...', 5, total_steps)
        
        # Check timeout before analysis
        if _check_timeout(sync_start_time):
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
        
        # Step 5: Analyze patients with timeout-aware processing
        if sync_mode == "full":
            active_patients_data = cliniko_sync_service.analyze_all_patients(patients, appointments, organization_id)
            update_sync_progress(sync_id, 'running', f'Analyzed ALL {len(patients)} patients (full sync mode)', 6, total_steps)
        else:
            active_patients_data = cliniko_sync_service.analyze_active_patients(patients, appointments, organization_id)
            update_sync_progress(sync_id, 'running', f'Analyzed active patients from {len(patients)} total patients', 6, total_steps)
        
        result['active_patients_identified'] = len(active_patients_data)
        
        # Check timeout before storage
        if _check_timeout(sync_start_time):
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
        
        # Step 6: Store data with chunked processing
        update_sync_progress(sync_id, 'running', f'Storing {len(active_patients_data)} patients in database...', 7, total_steps)
        
        stored_count = await _store_patients_with_timeout(cliniko_sync_service, active_patients_data, sync_start_time)
        
        if stored_count is None:  # Timeout occurred
            await _handle_sync_timeout(sync_id, organization_id, result)
            return
            
        result['active_patients_stored'] = stored_count
        
        # Step 7: Complete
        completion_time = datetime.now(timezone.utc)
        duration = (completion_time - sync_start_time).total_seconds()
        
        update_sync_progress(sync_id, 'completed', 
                           f'Sync completed! Processed {result["active_patients_stored"]} patients in {duration:.1f}s', 
                           total_steps, total_steps, completed_at=completion_time.isoformat())
        
        # Log successful completion
        await _log_sync_result(organization_id, sync_id, 'completed', result)
        
    except Exception as e:
        error_msg = f"Sync failed: {str(e)}"
        result['errors'].append(error_msg)
        
        update_sync_progress(sync_id, 'failed', error_msg, 
                           _sync_progress_store.get(sync_id, {}).get('current_step', 1), total_steps)
        
        # Log failed completion
        await _log_sync_result(organization_id, sync_id, 'failed', result)
        
        logger.error(f"Sync {sync_id} failed for organization {organization_id}: {e}")

def _check_timeout(start_time: datetime, buffer_seconds: int = 30) -> bool:
    """Check if we're approaching the timeout limit"""
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    return elapsed > (RAILWAY_TIMEOUT_SECONDS - buffer_seconds)

async def _handle_sync_timeout(sync_id: str, organization_id: str, result: Dict[str, Any]):
    """Handle sync timeout gracefully"""
    result['timeout_handled'] = True
    result['errors'].append("Sync timed out - operation too large for current timeout limits")
    
    update_sync_progress(sync_id, 'failed', 'Sync timed out - try with smaller dataset or contact support', 
                        _sync_progress_store.get(sync_id, {}).get('current_step', 1), 8)
    
    await _log_sync_result(organization_id, sync_id, 'timeout', result)

async def _fetch_patients_with_timeout(sync_service, api_url: str, headers: Dict, start_time: datetime) -> Optional[List]:
    """Fetch patients with timeout awareness"""
    if _check_timeout(start_time):
        return None
    
    # Use asyncio.to_thread for blocking operations
    return await asyncio.to_thread(sync_service.get_cliniko_patients, api_url, headers)

async def _fetch_appointments_with_timeout(sync_service, api_url: str, headers: Dict, start_time: datetime) -> Optional[List]:
    """Fetch appointments with timeout awareness"""
    if _check_timeout(start_time):
        return None
    
    return await asyncio.to_thread(sync_service.get_cliniko_appointments, api_url, headers)

async def _store_patients_with_timeout(sync_service, patients_data: List, start_time: datetime) -> Optional[int]:
    """Store patients with timeout awareness and chunking"""
    if _check_timeout(start_time):
        return None
    
    # Process in chunks to avoid long-running operations
    chunk_size = 50
    total_stored = 0
    
    for i in range(0, len(patients_data), chunk_size):
        if _check_timeout(start_time):
            return total_stored  # Return partial count
        
        chunk = patients_data[i:i + chunk_size]
        await asyncio.to_thread(sync_service.store_active_patients, chunk)
        total_stored += len(chunk)
    
    return total_stored

async def _log_sync_result(organization_id: str, sync_id: str, status: str, result: Dict[str, Any]):
    """Log sync completion to database"""
    try:
        from src.database import db
        
        # Convert result to JSON string for metadata
        metadata = {
            'sync_mode': result.get('sync_mode', 'active'),
            'patients_found': result.get('patients_found', 0),
            'appointments_found': result.get('appointments_found', 0),
            'active_patients_identified': result.get('active_patients_identified', 0),
            'active_patients_stored': result.get('active_patients_stored', 0),
            'errors': result.get('errors', []),
            'timeout_handled': result.get('timeout_handled', False)
        }
        
        completed_at = datetime.now(timezone.utc) if status == 'completed' else None
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_logs (
                    organization_id, source_system, operation_type, 
                    status, records_processed, records_success, records_failed,
                    started_at, completed_at, metadata, sync_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                organization_id,
                'cliniko',
                'patient_sync',
                status,
                result.get('patients_found', 0),
                result.get('active_patients_stored', 0),
                len(result.get('errors', [])),
                result.get('started_at'),
                completed_at,
                json.dumps(metadata),
                sync_id
            ))
        
        db.connection.commit()
        logger.info(f"Logged sync result for {organization_id}: {status}")
        
    except Exception as e:
        logger.error(f"Failed to log sync result: {e}")

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