"""
Cliniko Admin API Router
Cliniko sync management and monitoring endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.services.cliniko_sync_service import cliniko_sync_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

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
        from src.database import db
        
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