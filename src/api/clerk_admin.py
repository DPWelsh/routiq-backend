"""
Clerk Administration Endpoints
Manage Clerk data synchronization and administration tasks
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from database import db

# Conditional import for clerk_sync (requires CLERK_SECRET_KEY)
try:
    from integrations.clerk_sync import clerk_sync
    CLERK_SYNC_AVAILABLE = True
except Exception as e:
    logger.warning(f"Clerk sync unavailable: {e}")
    CLERK_SYNC_AVAILABLE = False
    clerk_sync = None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["clerk-admin"])

# Pydantic models
class SyncStatusResponse(BaseModel):
    clerk_api_connected: bool
    database_counts: Dict[str, int]
    last_sync: Optional[datetime] = None
    sync_in_progress: bool = False

class SyncTriggerResponse(BaseModel):
    success: bool
    message: str
    sync_id: Optional[str] = None
    estimated_duration: Optional[str] = None

class SyncResultResponse(BaseModel):
    sync_summary: Dict[str, Any]
    success: bool
    duration_seconds: float
    counts: Dict[str, int]

# Auth dependency (disabled for testing)
async def get_admin_user() -> Dict[str, Any]:
    """Get current authenticated admin user - disabled for testing"""
    return {
        "id": "system",
        "email": "system@routiq.com", 
        "role": "system"
    }

@router.get("/status", response_model=SyncStatusResponse)
async def get_clerk_sync_status():
    """Get current Clerk synchronization status and database counts"""
    try:
        # Check if Clerk sync is available
        if not CLERK_SYNC_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Clerk sync service unavailable. Check CLERK_SECRET_KEY environment variable."
            )
        
        # Check Clerk API connectivity
        clerk_status = await clerk_sync.get_clerk_api_status()
        
        # Get current database counts
        db_counts = {}
        
        try:
            users_count = db.execute_single("SELECT COUNT(*) as count FROM users")
            db_counts["users"] = users_count["count"] if users_count else 0
            
            orgs_count = db.execute_single("SELECT COUNT(*) as count FROM organizations")
            db_counts["organizations"] = orgs_count["count"] if orgs_count else 0
            
            members_count = db.execute_single("SELECT COUNT(*) as count FROM organization_members")
            db_counts["organization_members"] = members_count["count"] if members_count else 0
            
        except Exception as e:
            logger.error(f"Error getting database counts: {e}")
            db_counts = {"error": str(e)}
        
        # Check for recent sync logs (if you have them)
        try:
            last_sync_query = """
                SELECT created_at FROM audit_logs 
                WHERE action = 'clerk_sync_completed' 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            last_sync_result = db.execute_single(last_sync_query)
            last_sync = last_sync_result["created_at"] if last_sync_result else None
        except Exception:
            last_sync = None
        
        return SyncStatusResponse(
            clerk_api_connected=clerk_status.get("connected", False),
            database_counts=db_counts,
            last_sync=last_sync,
            sync_in_progress=False  # TODO: Implement sync status tracking
        )
        
    except Exception as e:
        logger.error(f"Error getting Clerk sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync", response_model=SyncTriggerResponse)
async def trigger_clerk_sync(background_tasks: BackgroundTasks):
    """Trigger a comprehensive Clerk data synchronization"""
    try:
        # Check if Clerk sync is available
        if not CLERK_SYNC_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Clerk sync service unavailable. Check CLERK_SECRET_KEY environment variable."
            )
        
        # Check if Clerk API is accessible
        clerk_status = await clerk_sync.get_clerk_api_status()
        
        if not clerk_status.get("connected"):
            raise HTTPException(
                status_code=503, 
                detail=f"Clerk API not accessible: {clerk_status.get('error', 'Unknown error')}"
            )
        
        # Schedule sync in background
        sync_id = f"sync_{datetime.now().isoformat()}"
        
        background_tasks.add_task(
            perform_clerk_sync_with_logging,
            sync_id,
            "system"  # Use system identifier instead of admin user
        )
        
        logger.info(f"🔄 Clerk sync triggered (ID: {sync_id})")
        
        return SyncTriggerResponse(
            success=True,
            message="Clerk data synchronization started in background",
            sync_id=sync_id,
            estimated_duration="1-5 minutes depending on data volume"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering Clerk sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync-logs")
async def get_sync_logs(limit: int = 10):
    """Get recent Clerk sync logs and results"""
    try:
        # Get recent sync logs from audit_logs
        logs_query = """
            SELECT created_at, details, success, error_message
            FROM audit_logs 
            WHERE action IN ('clerk_sync_started', 'clerk_sync_completed', 'clerk_sync_failed')
            ORDER BY created_at DESC 
            LIMIT %s
        """
        
        logs = db.execute_query(logs_query, (limit,))
        
        return {
            "sync_logs": logs,
            "total_count": len(logs)
        }
        
    except Exception as e:
        logger.error(f"Error getting sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database-summary")
async def get_database_summary():
    """Get detailed summary of Clerk data in database"""
    try:
        summary = {}
        
        # Users summary
        users_query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as users_last_7_days,
                COUNT(CASE WHEN last_login_at IS NOT NULL THEN 1 END) as users_with_login
            FROM users
        """
        users_stats = db.execute_single(users_query)
        summary["users"] = users_stats
        
        # Organizations summary  
        orgs_query = """
            SELECT 
                COUNT(*) as total_organizations,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as orgs_last_7_days,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_organizations
            FROM organizations
        """
        orgs_stats = db.execute_single(orgs_query)
        summary["organizations"] = orgs_stats
        
        # Memberships summary
        memberships_query = """
            SELECT 
                COUNT(*) as total_memberships,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_memberships,
                COUNT(DISTINCT organization_id) as orgs_with_members,
                COUNT(DISTINCT user_id) as users_with_orgs
            FROM organization_members
        """
        memberships_stats = db.execute_single(memberships_query)
        summary["memberships"] = memberships_stats
        
        # Role distribution
        role_query = """
            SELECT role, COUNT(*) as count
            FROM organization_members 
            WHERE status = 'active'
            GROUP BY role
            ORDER BY count DESC
        """
        role_distribution = db.execute_query(role_query)
        summary["role_distribution"] = role_distribution
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting database summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_clerk_sync_with_logging(sync_id: str, admin_user_id: str):
    """Perform Clerk sync with comprehensive logging"""
    try:
        # Log sync start (use NULL for system operations to avoid FK constraint)
        log_data = {
            "organization_id": None,
            "user_id": None,  # Use NULL for system operations
            "action": "clerk_sync_started",
            "resource_type": "clerk_data",
            "resource_id": sync_id,
            "details": json.dumps({"sync_id": sync_id, "triggered_by": admin_user_id}),
            "success": True
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s)
            """, log_data)
            db.connection.commit()
        
        # Perform the actual sync
        sync_result = await clerk_sync.sync_all_data()
        
        # Log sync completion
        log_data.update({
            "action": "clerk_sync_completed" if sync_result["success"] else "clerk_sync_failed",
            "details": json.dumps({
                "sync_id": sync_id, 
                "triggered_by": admin_user_id, 
                "result": sync_result
            }),
            "success": sync_result["success"],
            "error_message": sync_result.get("error") if not sync_result["success"] else None
        })
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success, error_message)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s, %(error_message)s)
            """, log_data)
            db.connection.commit()
        
        logger.info(f"✅ Clerk sync {sync_id} completed: {sync_result['success']}")
        
    except Exception as e:
        logger.error(f"❌ Clerk sync {sync_id} failed: {e}")
        
        # Log sync failure
        try:
            log_data = {
                "organization_id": None,
                "user_id": None,  # Use NULL for system operations
                "action": "clerk_sync_failed",
                "resource_type": "clerk_data",
                "resource_id": sync_id,
                "details": json.dumps({
                    "sync_id": sync_id, 
                    "triggered_by": admin_user_id, 
                    "error": str(e)
                }),
                "success": False,
                "error_message": str(e)
            }
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                          resource_id, details, success, error_message)
                    VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                           %(resource_id)s, %(details)s, %(success)s, %(error_message)s)
                """, log_data)
                db.connection.commit()
        except Exception as log_error:
            logger.error(f"Failed to log sync failure: {log_error}")

@router.post("/test-connection")
async def test_clerk_connection():
    """Test Clerk API connection and authentication"""
    try:
        # Check if Clerk sync is available
        if not CLERK_SYNC_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Clerk sync service unavailable. Check CLERK_SECRET_KEY environment variable."
            )
        
        status = await clerk_sync.get_clerk_api_status()
        
        return {
            "clerk_api_status": status,
            "timestamp": datetime.now().isoformat(),
            "tested_by": "system"
        }
        
    except Exception as e:
        logger.error(f"Error testing Clerk connection: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 