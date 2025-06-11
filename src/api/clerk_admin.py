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
router = APIRouter()

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

class CredentialsStoreRequest(BaseModel):
    organization_id: str
    service_name: str  # e.g., 'cliniko', 'chatwoot'
    api_key: str
    region: Optional[str] = None
    account_id: Optional[str] = None
    base_url: Optional[str] = None

class CredentialsStoreResponse(BaseModel):
    success: bool
    message: str
    service_name: str
    organization_id: str

class CredentialsRetrieveResponse(BaseModel):
    success: bool
    service_name: str
    organization_id: str
    credentials: Dict[str, Any]  # Decrypted credentials ready for use

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
        db_counts = {
            "users": 0,
            "organizations": 0,
            "organization_members": 0
        }
        
        try:
            users_count = db.execute_single("SELECT COUNT(*) as count FROM users")
            db_counts["users"] = users_count["count"] if users_count else 0
            
            orgs_count = db.execute_single("SELECT COUNT(*) as count FROM organizations")
            db_counts["organizations"] = orgs_count["count"] if orgs_count else 0
            
            members_count = db.execute_single("SELECT COUNT(*) as count FROM organization_members")
            db_counts["organization_members"] = members_count["count"] if members_count else 0
            
        except Exception as e:
            logger.error(f"Error getting database counts: {e}")
            # Keep default counts as 0 instead of returning error message
            # This ensures we always return integers as expected by the frontend
        
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
async def get_sync_logs(limit: int = 10, source: str = "audit"):
    """Get recent Clerk sync logs and results
    
    Args:
        limit: Number of logs to return
        source: 'audit' for audit_logs table, 'sync' for sync_logs table
    """
    try:
        if source == "sync":
            # Get from sync_logs table (new structured format)
            logs_query = """
                SELECT 
                    id,
                    source_system,
                    operation_type,
                    status,
                    records_processed,
                    records_success,
                    records_failed,
                    error_details,
                    started_at,
                    completed_at,
                    metadata
                FROM sync_logs 
                WHERE source_system = 'clerk'
                ORDER BY started_at DESC 
                LIMIT %s
            """
            
            logs = db.execute_query(logs_query, (limit,))
            
            return {
                "sync_logs": logs,
                "total_count": len(logs),
                "source": "sync_logs_table"
            }
        else:
            # Get from audit_logs table (original format)
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
                "total_count": len(logs),
                "source": "audit_logs_table"
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
    """Perform Clerk sync with comprehensive logging to both audit_logs and sync_logs"""
    sync_log_id = None
    
    try:
        # Create sync_logs entry
        sync_log_data = {
            "source_system": "clerk",
            "operation_type": "full_sync",
            "status": "running",
            "metadata": json.dumps({
                "sync_id": sync_id,
                "triggered_by": admin_user_id,
                "api_version": "v1"
            })
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_logs (source_system, operation_type, status, metadata)
                VALUES (%(source_system)s, %(operation_type)s, %(status)s, %(metadata)s)
                RETURNING id
            """, sync_log_data)
            sync_log_id = cursor.fetchone()["id"]
            db.connection.commit()
        
        # Also log to audit_logs for audit trail
        audit_log_data = {
            "organization_id": None,
            "user_id": None,  # Use NULL for system operations
            "action": "clerk_sync_started",
            "resource_type": "clerk_data",
            "resource_id": sync_id,
            "details": json.dumps({"sync_id": sync_id, "triggered_by": admin_user_id, "sync_log_id": str(sync_log_id)}),
            "success": True
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s)
            """, audit_log_data)
            db.connection.commit()
        
        # Perform the actual sync
        sync_result = await clerk_sync.sync_all_data()
        
        # Calculate totals
        total_processed = (
            sync_result.get("users", {}).get("synced", 0) +
            sync_result.get("organizations", {}).get("synced", 0) + 
            sync_result.get("memberships", {}).get("synced", 0)
        )
        
        total_errors = (
            len(sync_result.get("users", {}).get("errors", [])) +
            len(sync_result.get("organizations", {}).get("errors", [])) +
            len(sync_result.get("memberships", {}).get("errors", []))
        )
        
        total_success = total_processed
        
        # Update sync_logs with results
        sync_update_data = {
            "id": sync_log_id,
            "status": "completed" if sync_result["success"] else "failed",
            "records_processed": total_processed + total_errors,
            "records_success": total_success,
            "records_failed": total_errors,
            "error_details": json.dumps({
                "users_errors": sync_result.get("users", {}).get("errors", []),
                "organizations_errors": sync_result.get("organizations", {}).get("errors", []),
                "memberships_errors": sync_result.get("memberships", {}).get("errors", [])
            }) if total_errors > 0 else json.dumps({}),
            "metadata": json.dumps({
                "sync_id": sync_id,
                "triggered_by": admin_user_id,
                "api_version": "v1",
                "users_synced": sync_result.get("users", {}).get("synced", 0),
                "organizations_synced": sync_result.get("organizations", {}).get("synced", 0),
                "memberships_synced": sync_result.get("memberships", {}).get("synced", 0),
                "duration_seconds": sync_result.get("total_duration_seconds", 0)
            })
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE sync_logs 
                SET status = %(status)s,
                    records_processed = %(records_processed)s,
                    records_success = %(records_success)s,
                    records_failed = %(records_failed)s,
                    error_details = %(error_details)s,
                    completed_at = NOW(),
                    metadata = %(metadata)s
                WHERE id = %(id)s
            """, sync_update_data)
            db.connection.commit()
        
        # Also update audit_logs for completion
        audit_log_data.update({
            "action": "clerk_sync_completed" if sync_result["success"] else "clerk_sync_failed",
            "details": json.dumps({
                "sync_id": sync_id, 
                "triggered_by": admin_user_id, 
                "sync_log_id": str(sync_log_id),
                "result": sync_result
            }),
            "success": sync_result["success"],
            "error_message": "; ".join([
                *sync_result.get("users", {}).get("errors", []),
                *sync_result.get("organizations", {}).get("errors", []),
                *sync_result.get("memberships", {}).get("errors", [])
            ][:3]) if not sync_result["success"] else None  # Limit error message length
        })
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success, error_message)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s, %(error_message)s)
            """, audit_log_data)
            db.connection.commit()
        
        logger.info(f"✅ Clerk sync {sync_id} completed: {sync_result['success']}")
        
    except Exception as e:
        logger.error(f"❌ Clerk sync {sync_id} failed: {e}")
        
        # Update sync_logs with failure if ID exists
        if sync_log_id:
            try:
                with db.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE sync_logs 
                        SET status = 'failed',
                            error_details = %s,
                            completed_at = NOW()
                        WHERE id = %s
                    """, (json.dumps({"error": str(e)}), sync_log_id))
                    db.connection.commit()
            except Exception as update_error:
                logger.error(f"Failed to update sync_logs: {update_error}")
        
        # Log sync failure to audit_logs
        try:
            audit_failure_data = {
                "organization_id": None,
                "user_id": None,
                "action": "clerk_sync_failed",
                "resource_type": "clerk_data",
                "resource_id": sync_id,
                "details": json.dumps({
                    "sync_id": sync_id, 
                    "triggered_by": admin_user_id, 
                    "sync_log_id": str(sync_log_id) if sync_log_id else None,
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
                """, audit_failure_data)
                db.connection.commit()
        except Exception as log_error:
            logger.error(f"Failed to log sync failure: {log_error}")

@router.post("/store-credentials", response_model=CredentialsStoreResponse)
async def store_api_credentials(request: CredentialsStoreRequest):
    """Store encrypted API credentials for an organization"""
    try:
        from cryptography.fernet import Fernet
        import base64
        
        # Get encryption key from environment
        encryption_key = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
        if not encryption_key:
            raise HTTPException(
                status_code=500,
                detail="CREDENTIALS_ENCRYPTION_KEY environment variable is required"
            )
        
        # Set up encryption
        cipher_suite = Fernet(encryption_key.encode())
        
        # Prepare credentials based on service type
        if request.service_name.lower() == 'cliniko':
            # Compute base64 credentials for Basic Auth (apiKey:)
            import base64 as b64
            base64_creds = b64.b64encode(f"{request.api_key}:".encode()).decode()
            
            credentials = {
                "api_key": request.api_key,
                "region": request.region or "au4",
                "api_url": f"https://api.{request.region or 'au4'}.cliniko.com/v1",
                "base64_credentials": base64_creds
            }
        elif request.service_name.lower() == 'chatwoot':
            credentials = {
                "api_token": request.api_key,
                "account_id": request.account_id,
                "base_url": request.base_url or "https://app.chatwoot.com"
            }
        else:
            # Generic credentials storage
            credentials = {
                "api_key": request.api_key,
                "region": request.region,
                "account_id": request.account_id,
                "base_url": request.base_url
            }
        
        # Remove None values
        credentials = {k: v for k, v in credentials.items() if v is not None}
        
        # Encrypt credentials
        json_data = json.dumps(credentials)
        encrypted_data = cipher_suite.encrypt(json_data.encode())
        encrypted_base64 = base64.b64encode(encrypted_data).decode()
        
        # Store in database as JSON object
        encrypted_json = {"encrypted_data": encrypted_base64}
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO api_credentials (organization_id, service_name, credentials_encrypted, created_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (organization_id, service_name)
                DO UPDATE SET
                    credentials_encrypted = EXCLUDED.credentials_encrypted,
                    created_by = EXCLUDED.created_by,
                    updated_at = NOW()
            """, (request.organization_id, request.service_name.lower(), json.dumps(encrypted_json), None))
            
            db.connection.commit()
        
        # Log the credential storage
        audit_log_data = {
            "organization_id": request.organization_id,
            "user_id": None,  # System operation
            "action": "credentials_stored",
            "resource_type": "api_credentials",
            "resource_id": request.service_name.lower(),
            "details": json.dumps({
                "service_name": request.service_name.lower(),
                "has_api_key": bool(request.api_key),
                "has_region": bool(request.region),
                "has_account_id": bool(request.account_id)
            }),
            "success": True
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s)
            """, audit_log_data)
            db.connection.commit()
        
        logger.info(f"✅ Stored {request.service_name} credentials for organization {request.organization_id}")
        
        return CredentialsStoreResponse(
            success=True,
            message=f"Successfully stored {request.service_name} credentials",
            service_name=request.service_name.lower(),
            organization_id=request.organization_id
        )
        
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credentials/{organization_id}/{service_name}", response_model=CredentialsRetrieveResponse)
async def get_api_credentials(organization_id: str, service_name: str):
    """Retrieve decrypted API credentials for an organization and service"""
    try:
        from cryptography.fernet import Fernet
        import base64
        
        # Get encryption key from environment
        encryption_key = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
        if not encryption_key:
            raise HTTPException(
                status_code=500,
                detail="CREDENTIALS_ENCRYPTION_KEY environment variable is required"
            )
        
        # Set up decryption
        cipher_suite = Fernet(encryption_key.encode())
        
        # Get encrypted credentials from database
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT credentials_encrypted, is_active, last_validated_at
                FROM api_credentials 
                WHERE organization_id = %s AND service_name = %s AND is_active = true
            """, (organization_id, service_name.lower()))
            
            result = cursor.fetchone()
            
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"No active credentials found for {service_name} in organization {organization_id}"
            )
        
        # Decrypt credentials
        credentials_encrypted = result["credentials_encrypted"]
        # Handle both string and dict formats from database
        if isinstance(credentials_encrypted, str):
            encrypted_json = json.loads(credentials_encrypted)
        else:
            encrypted_json = credentials_encrypted
            
        encrypted_data = base64.b64decode(encrypted_json["encrypted_data"].encode())
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        credentials = json.loads(decrypted_data.decode())
        
        # Log the credential access
        audit_log_data = {
            "organization_id": organization_id,
            "user_id": None,  # System operation
            "action": "credentials_accessed",
            "resource_type": "api_credentials",
            "resource_id": service_name.lower(),
            "details": json.dumps({
                "service_name": service_name.lower(),
                "access_time": datetime.now().isoformat(),
                "last_validated": result["last_validated_at"].isoformat() if result["last_validated_at"] else None
            }),
            "success": True
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s)
            """, audit_log_data)
            db.connection.commit()
        
        logger.info(f"✅ Retrieved {service_name} credentials for organization {organization_id}")
        
        return CredentialsRetrieveResponse(
            success=True,
            service_name=service_name.lower(),
            organization_id=organization_id,
            credentials=credentials
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organizations")
async def list_organizations():
    """List all organizations with their IDs and names"""
    try:
        query = """
            SELECT id, name, display_name, slug, status, created_at
            FROM organizations
            ORDER BY created_at DESC
        """
        
        organizations = db.execute_query(query)
        
        return {
            "organizations": organizations,
            "total_count": len(organizations)
        }
        
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_clerk_connection():
    """Test Clerk API connection and permissions"""
    try:
        if not CLERK_SYNC_AVAILABLE:
            return {
                "connected": False,
                "error": "Clerk sync service unavailable. Check CLERK_SECRET_KEY environment variable."
            }
        
        # Test the connection
        status = await clerk_sync.get_clerk_api_status()
        
        return {
            "connected": status.get("connected", False),
            "api_version": status.get("api_version"),
            "permissions": status.get("permissions", []),
            "error": status.get("error") if not status.get("connected") else None,
            "test_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing Clerk connection: {e}")
        return {
            "connected": False,
            "error": str(e),
            "test_timestamp": datetime.now().isoformat()
        }

 