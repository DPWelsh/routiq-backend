"""
Sync Manager API Router
Cliniko sync management and monitoring endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from src.api.auth import verify_organization_access
from src.services.cliniko_sync_service import ClinikoSyncService
from src.services.sync_scheduler import scheduler

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models
class SyncTriggerResponse(BaseModel):
    message: str
    sync_started: bool
    organization_id: str
    timestamp: datetime

class SyncStatusResponse(BaseModel):
    organization_id: str
    last_sync_time: Optional[datetime] = None
    sync_in_progress: bool
    total_contacts: int
    active_patients: int
    message: str

class SyncLogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SyncLogsResponse(BaseModel):
    organization_id: str
    logs: List[SyncLogEntry]
    total_count: int

class SchedulerStatusResponse(BaseModel):
    organization_id: str
    sync_running: bool
    last_sync_time: Optional[datetime] = None
    scheduler_active: bool
    message: str

async def trigger_sync_background(organization_id: str):
    """Background task to run sync"""
    try:
        sync_service = ClinikoSyncService()
        await sync_service.sync_all_patients(organization_id)
        logger.info(f"Sync completed successfully for organization {organization_id}")
    except Exception as e:
        logger.error(f"Sync failed for organization {organization_id}: {e}")

@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    organization_id: str = Depends(verify_organization_access)
):
    """
    Trigger a Cliniko sync for the organization
    """
    try:
        # Add sync task to background
        background_tasks.add_task(trigger_sync_background, organization_id)
        
        return SyncTriggerResponse(
            message="Sync started successfully",
            sync_started=True,
            organization_id=organization_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger sync for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start sync")

@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    organization_id: str = Depends(verify_organization_access)
):
    """
    Get current sync status for the organization
    """
    try:
        from src.database import db
        
        with db.get_cursor() as cursor:
            # Get total patients count (was contacts count)
            cursor.execute(
                "SELECT COUNT(*) FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            patients_result = cursor.fetchone()
            total_contacts = patients_result['total'] if patients_result else 0
            
            # Get active patients count (was active_patients count)
            cursor.execute(
                "SELECT COUNT(*) FROM patients WHERE organization_id = %s AND is_active = true",
                [organization_id]
            )
            active_result = cursor.fetchone()
            active_patients = active_result['total'] if active_result else 0
            
            # Get last sync time (from patients table)
            cursor.execute(
                "SELECT MAX(last_synced_at) FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            sync_result = cursor.fetchone()
            last_sync = sync_result['max'] if sync_result else None
            
            return SyncStatusResponse(
                organization_id=organization_id,
                last_sync_time=last_sync,
                sync_in_progress=False,  # TODO: Implement proper sync status tracking
                total_contacts=total_contacts or 0,
                active_patients=active_patients or 0,
                message="Status retrieved successfully"
            )
            
    except Exception as e:
        logger.error(f"Failed to get sync status for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sync status")

@router.get("/logs", response_model=SyncLogsResponse)
async def get_sync_logs(
    organization_id: str = Depends(verify_organization_access),
    limit: int = 50
):
    """
    Get recent sync logs for the organization
    """
    try:
        # TODO: Implement proper sync logging table
        # For now, return empty logs
        return SyncLogsResponse(
            organization_id=organization_id,
            logs=[],
            total_count=0
        )
        
    except Exception as e:
        logger.error(f"Failed to get sync logs for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sync logs")

@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    organization_id: str = Depends(verify_organization_access)
):
    """
    Get scheduler status for the organization
    """
    try:
        status = scheduler.get_sync_status(organization_id)
        
        return SchedulerStatusResponse(
            organization_id=organization_id,
            sync_running=status["sync_running"],
            last_sync_time=status["last_sync_time"],
            scheduler_active=status["scheduler_active"],
            message="Scheduler status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scheduler status")

@router.post("/scheduler/trigger", response_model=SyncTriggerResponse)
async def trigger_scheduled_sync(
    organization_id: str = Depends(verify_organization_access)
):
    """
    Manually trigger a sync through the scheduler (respects duplicate prevention)
    """
    try:
        success = await scheduler.sync_organization_safe(organization_id)
        
        return SyncTriggerResponse(
            message="Scheduled sync triggered successfully" if success else "Sync already running or failed",
            sync_started=success,
            organization_id=organization_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger scheduled sync for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger scheduled sync") 