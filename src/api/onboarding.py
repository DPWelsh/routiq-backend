"""
Clerk User Onboarding Flow
Handle new user onboarding with API credential setup and initial data sync
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import httpx
import asyncio

from database import db
from integrations.clerk_client import clerk
from integrations.cliniko_client import ClinikoClient
from integrations.chatwoot_client import ChatwootClient
from sync_manager_multi_tenant import multi_tenant_sync

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

# Pydantic models
class OnboardingRequest(BaseModel):
    organization_id: str = Field(..., description="Organization ID from Clerk")
    cliniko_api_key: str = Field(..., description="Cliniko API key")
    cliniko_region: str = Field(default="au4", description="Cliniko region (e.g., au4, au2)")
    chatwoot_api_token: str = Field(..., description="Chatwoot API token")
    chatwoot_account_id: str = Field(..., description="Chatwoot account ID")
    chatwoot_base_url: str = Field(default="https://app.chatwoot.com", description="Chatwoot base URL")

class OnboardingStatus(BaseModel):
    step: str
    status: str
    message: str
    progress_percentage: int

class OnboardingResponse(BaseModel):
    success: bool
    organization_id: str
    steps_completed: List[OnboardingStatus]
    initial_data_summary: Optional[Dict[str, Any]] = None
    sync_scheduled: bool = False

# Auth dependency (placeholder - integrate with your auth system)
async def get_current_user() -> Dict[str, Any]:
    """Get current authenticated user - integrate with Clerk JWT validation"""
    # TODO: Implement proper Clerk JWT validation
    return {
        "id": "user_123",
        "email": "admin@sampleclinic.com"
    }

async def verify_organization_access(organization_id: str, user: Dict = Depends(get_current_user)) -> bool:
    """Verify user has admin access to organization"""
    # Check if user is admin/owner of the organization
    membership = db.execute_single("""
        SELECT role FROM organization_members 
        WHERE organization_id = %s AND user_id = %s AND status = 'active'
    """, (organization_id, user["id"]))
    
    if not membership or membership["role"] not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Admin access required for onboarding")
    
    return True

@router.post("/start", response_model=OnboardingResponse)
async def start_onboarding(
    request: OnboardingRequest,
    background_tasks: BackgroundTasks,
    user: Dict = Depends(get_current_user),
    _: bool = Depends(verify_organization_access)
):
    """
    Start the onboarding process for a new organization
    1. Validate API credentials
    2. Store credentials securely
    3. Import initial data
    4. Set up sync schedule
    """
    organization_id = request.organization_id
    steps_completed = []
    
    try:
        # Step 1: Validate Cliniko credentials
        logger.info(f"Starting onboarding for organization {organization_id}")
        
        cliniko_status = await validate_cliniko_credentials(
            request.cliniko_api_key, 
            request.cliniko_region
        )
        steps_completed.append(OnboardingStatus(
            step="cliniko_validation",
            status="completed" if cliniko_status["valid"] else "failed",
            message=cliniko_status["message"],
            progress_percentage=20
        ))
        
        if not cliniko_status["valid"]:
            raise HTTPException(status_code=400, detail=f"Cliniko validation failed: {cliniko_status['message']}")
        
        # Step 2: Validate Chatwoot credentials
        chatwoot_status = await validate_chatwoot_credentials(
            request.chatwoot_api_token,
            request.chatwoot_account_id,
            request.chatwoot_base_url
        )
        steps_completed.append(OnboardingStatus(
            step="chatwoot_validation",
            status="completed" if chatwoot_status["valid"] else "failed",
            message=chatwoot_status["message"],
            progress_percentage=40
        ))
        
        if not chatwoot_status["valid"]:
            raise HTTPException(status_code=400, detail=f"Chatwoot validation failed: {chatwoot_status['message']}")
        
        # Step 3: Store credentials securely
        await store_api_credentials(organization_id, request)
        steps_completed.append(OnboardingStatus(
            step="credential_storage",
            status="completed",
            message="API credentials stored securely",
            progress_percentage=60
        ))
        
        # Step 4: Schedule initial data import in background
        background_tasks.add_task(
            perform_initial_data_import,
            organization_id,
            user["id"]
        )
        
        steps_completed.append(OnboardingStatus(
            step="initial_import_scheduled",
            status="completed",
            message="Initial data import scheduled",
            progress_percentage=80
        ))
        
        # Step 5: Set up sync schedule
        await setup_sync_schedule(organization_id)
        steps_completed.append(OnboardingStatus(
            step="sync_schedule_setup",
            status="completed",
            message="Automatic sync schedule configured",
            progress_percentage=100
        ))
        
        # Log successful onboarding
        await clerk.log_user_action(
            user_id=user["id"],
            organization_id=organization_id,
            action="onboarding_completed",
            resource_type="organization",
            resource_id=organization_id,
            details={"steps": len(steps_completed)},
            success=True
        )
        
        logger.info(f"✅ Onboarding completed for organization {organization_id}")
        
        return OnboardingResponse(
            success=True,
            organization_id=organization_id,
            steps_completed=steps_completed,
            sync_scheduled=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding failed for {organization_id}: {e}")
        
        # Log failed onboarding
        await clerk.log_user_action(
            user_id=user["id"],
            organization_id=organization_id,
            action="onboarding_failed",
            resource_type="organization",
            resource_id=organization_id,
            details={"error": str(e), "steps_completed": len(steps_completed)},
            success=False
        )
        
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

async def validate_cliniko_credentials(api_key: str, region: str) -> Dict[str, Any]:
    """Validate Cliniko API credentials"""
    try:
        # Create temporary client
        client = ClinikoClient()
        client.api_key = api_key
        client.region = region
        
        # Test API call
        test_response = await client.test_connection()
        
        if test_response.get("success"):
            return {
                "valid": True,
                "message": "Cliniko credentials validated successfully",
                "account_info": test_response.get("account_info", {})
            }
        else:
            return {
                "valid": False,
                "message": test_response.get("error", "Failed to validate Cliniko credentials")
            }
            
    except Exception as e:
        logger.error(f"Cliniko validation error: {e}")
        return {
            "valid": False,
            "message": f"Cliniko validation error: {str(e)}"
        }

async def validate_chatwoot_credentials(api_token: str, account_id: str, base_url: str) -> Dict[str, Any]:
    """Validate Chatwoot API credentials"""
    try:
        # Create temporary client
        client = ChatwootClient()
        client.api_token = api_token
        client.account_id = account_id
        client.base_url = base_url
        
        # Test API call
        test_response = await client.test_connection()
        
        if test_response.get("success"):
            return {
                "valid": True,
                "message": "Chatwoot credentials validated successfully",
                "account_info": test_response.get("account_info", {})
            }
        else:
            return {
                "valid": False,
                "message": test_response.get("error", "Failed to validate Chatwoot credentials")
            }
            
    except Exception as e:
        logger.error(f"Chatwoot validation error: {e}")
        return {
            "valid": False,
            "message": f"Chatwoot validation error: {str(e)}"
        }

async def store_api_credentials(organization_id: str, request: OnboardingRequest):
    """Store API credentials securely in database"""
    try:
        # Encrypt credentials (using the existing encryption system)
        from sync_manager_multi_tenant import encrypt_credentials
        
        cliniko_credentials = {
            "api_key": request.cliniko_api_key,
            "region": request.cliniko_region
        }
        
        chatwoot_credentials = {
            "api_token": request.chatwoot_api_token,
            "account_id": request.chatwoot_account_id,
            "base_url": request.chatwoot_base_url
        }
        
        # Store in database
        with db.get_cursor() as cursor:
            # Store Cliniko credentials
            cursor.execute("""
                INSERT INTO api_credentials (organization_id, service_name, credentials, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (organization_id, service_name)
                DO UPDATE SET
                    credentials = EXCLUDED.credentials,
                    updated_at = NOW()
            """, (organization_id, "cliniko", encrypt_credentials(cliniko_credentials)))
            
            # Store Chatwoot credentials
            cursor.execute("""
                INSERT INTO api_credentials (organization_id, service_name, credentials, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (organization_id, service_name)
                DO UPDATE SET
                    credentials = EXCLUDED.credentials,
                    updated_at = NOW()
            """, (organization_id, "chatwoot", encrypt_credentials(chatwoot_credentials)))
            
            db.connection.commit()
            
        logger.info(f"✅ Credentials stored for organization {organization_id}")
        
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        raise

async def perform_initial_data_import(organization_id: str, user_id: str):
    """Perform initial data import in background"""
    try:
        logger.info(f"Starting initial data import for organization {organization_id}")
        
        # Log import start
        await clerk.log_user_action(
            user_id=user_id,
            organization_id=organization_id,
            action="initial_import_started",
            resource_type="sync",
            details={"type": "initial_import"}
        )
        
        # Trigger comprehensive sync using existing sync manager
        result = await multi_tenant_sync.sync_organization(
            organization_id=organization_id,
            force_full_sync=True  # Full initial import
        )
        
        # Log import completion
        await clerk.log_user_action(
            user_id=user_id,
            organization_id=organization_id,
            action="initial_import_completed",
            resource_type="sync",
            details={
                "type": "initial_import",
                "result": result,
                "success": result.get("success", False)
            },
            success=result.get("success", False)
        )
        
        logger.info(f"✅ Initial data import completed for organization {organization_id}")
        
    except Exception as e:
        logger.error(f"Initial data import failed for {organization_id}: {e}")
        
        # Log import failure
        await clerk.log_user_action(
            user_id=user_id,
            organization_id=organization_id,
            action="initial_import_failed",
            resource_type="sync",
            details={"type": "initial_import", "error": str(e)},
            success=False
        )

async def setup_sync_schedule(organization_id: str):
    """Set up automatic sync schedule for the organization"""
    try:
        # Update organization settings to enable auto-sync
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE organizations 
                SET auto_sync_enabled = true,
                    sync_interval_minutes = 30,
                    updated_at = NOW()
                WHERE id = %s
            """, (organization_id,))
            
            db.connection.commit()
            
        logger.info(f"✅ Sync schedule set up for organization {organization_id}")
        
    except Exception as e:
        logger.error(f"Failed to set up sync schedule: {e}")
        raise

@router.get("/status/{organization_id}")
async def get_onboarding_status(
    organization_id: str,
    user: Dict = Depends(get_current_user),
    _: bool = Depends(verify_organization_access)
):
    """Get onboarding status for an organization"""
    try:
        # Check if credentials exist
        credentials_exist = db.execute_single("""
            SELECT COUNT(*) as count FROM api_credentials 
            WHERE organization_id = %s AND service_name IN ('cliniko', 'chatwoot')
        """, (organization_id,))
        
        has_credentials = credentials_exist["count"] >= 2
        
        # Check if initial sync completed
        initial_sync = db.execute_single("""
            SELECT * FROM sync_logs 
            WHERE organization_id = %s 
            ORDER BY started_at DESC 
            LIMIT 1
        """, (organization_id,))
        
        has_initial_sync = initial_sync is not None
        
        # Check if auto-sync is enabled
        org_settings = db.execute_single("""
            SELECT auto_sync_enabled FROM organizations 
            WHERE id = %s
        """, (organization_id,))
        
        auto_sync_enabled = org_settings.get("auto_sync_enabled", False) if org_settings else False
        
        return {
            "organization_id": organization_id,
            "credentials_configured": has_credentials,
            "initial_sync_completed": has_initial_sync,
            "auto_sync_enabled": auto_sync_enabled,
            "onboarding_complete": has_credentials and has_initial_sync and auto_sync_enabled,
            "last_sync": initial_sync.get("completed_at") if initial_sync else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get onboarding status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 