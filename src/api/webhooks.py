"""
Webhook API Endpoints
Frontend interface for triggering N8N workflows with Clerk authentication
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from src.services.webhook_service import webhook_service
from src.database import db
from src.api.auth import verify_organization_access

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class TriggerWebhookRequest(BaseModel):
    webhook_type: str
    patient_id: Optional[str] = None
    trigger_data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    trigger_source: str = "api"

class WebhookResponse(BaseModel):
    success: bool
    log_id: Optional[str] = None
    status: Optional[str] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None
    message: str

class WebhookLogResponse(BaseModel):
    id: str
    patient_id: Optional[str]
    webhook_type: str
    workflow_name: str
    status: str
    execution_time_ms: Optional[int]
    triggered_by_user_id: Optional[str]
    trigger_source: str
    triggered_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

# ==========================================
# WEBHOOK ENDPOINTS
# ==========================================

@router.post("/{organization_id}/trigger")
async def trigger_webhook(
    request_obj: Request,
    request: TriggerWebhookRequest,
    organization_id: str = Depends(verify_organization_access)
) -> WebhookResponse:
    """
    Trigger a webhook workflow with Clerk authentication
    
    This endpoint:
    1. Verifies user has access to the organization (via Clerk)
    2. Gets the webhook template
    3. Builds the payload with patient data
    4. Calls the N8N webhook
    5. Logs everything to Supabase
    
    Requires:
    - Valid Clerk JWT token in Authorization header
    - User must be member of the organization
    """
    
    try:
        # Extract user context from Clerk token (already verified by dependency)
        user_id = getattr(request_obj.state, 'user_id', request.user_id)
        
        # Set organization context for RLS (Clerk already verified access)
        with db.get_cursor() as cursor:
            cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
        
        # Use webhook service to trigger the webhook
        async with webhook_service as ws:
            result = await ws.trigger_webhook(
                webhook_type=request.webhook_type,
                organization_id=organization_id,
                patient_id=request.patient_id,
                trigger_data=request.trigger_data,
                user_id=user_id,
                trigger_source=request.trigger_source
            )
        
        # Build response
        if result["success"]:
            message = f"Webhook {request.webhook_type} triggered successfully"
        else:
            message = f"Webhook {request.webhook_type} failed: {result.get('error', 'Unknown error')}"
        
        return WebhookResponse(
            success=result["success"],
            log_id=result["log_id"],
            status=result.get("status"),
            execution_time_ms=result.get("execution_time_ms"),
            error=result.get("error"),
            message=message
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger webhook: {str(e)}"
        )

@router.get("/{organization_id}/logs")
async def get_webhook_logs(
    organization_id: str = Depends(verify_organization_access),
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get webhook execution logs for an organization (Clerk authenticated)
    
    Requires:
    - Valid Clerk JWT token in Authorization header
    - User must be member of the organization
    """
    
    try:
        # Set organization context (Clerk already verified access)
        with db.get_cursor() as cursor:
            cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
        
        # Get logs using webhook service
        async with webhook_service as ws:
            logs = await ws.get_webhook_logs(
                organization_id=organization_id,
                limit=limit,
                offset=offset,
                status_filter=status_filter
            )
        
        # Convert to response models
        log_responses = []
        for log in logs:
            log_responses.append(WebhookLogResponse(
                id=log["id"],
                patient_id=log["patient_id"],
                webhook_type=log["webhook_type"],
                workflow_name=log["workflow_name"],
                status=log["status"],
                execution_time_ms=log["execution_time_ms"],
                triggered_by_user_id=log["triggered_by_user_id"],
                trigger_source=log["trigger_source"],
                triggered_at=log["triggered_at"],
                completed_at=log["completed_at"],
                error_message=log["error_message"]
            ))
        
        return {
            "organization_id": organization_id,
            "logs": log_responses,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(log_responses)
            },
            "filters": {
                "status_filter": status_filter
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook logs: {str(e)}"
        )

@router.post("/{organization_id}/retry/{log_id}")
async def retry_webhook(
    organization_id: str,
    log_id: str
) -> WebhookResponse:
    """
    Retry a failed webhook
    """
    
    try:
        # Set organization context
        with db.get_cursor() as cursor:
            cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
        
        # Retry using webhook service
        async with webhook_service as ws:
            result = await ws.retry_webhook(log_id, organization_id)
        
        if result["success"]:
            message = f"Webhook retry successful"
        else:
            message = f"Webhook retry failed: {result.get('error', 'Unknown error')}"
        
        return WebhookResponse(
            success=result["success"],
            log_id=log_id,
            status=result.get("status"),
            execution_time_ms=result.get("execution_time_ms"),
            error=result.get("error"),
            message=message
        )
        
    except Exception as e:
        logger.error(f"Failed to retry webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry webhook: {str(e)}"
        )

@router.get("/{organization_id}/templates")
async def get_webhook_templates(organization_id: str) -> Dict[str, Any]:
    """
    Get available webhook templates for an organization
    """
    
    try:
        # Set organization context
        with db.get_cursor() as cursor:
            cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
            
            # Get templates (org-specific + global)
            query = """
            SELECT id, name, description, webhook_type, workflow_id, is_active,
                   timeout_seconds, retry_attempts
            FROM webhook_templates 
            WHERE is_active = true
            ORDER BY 
                CASE WHEN organization_id = %s THEN 1 ELSE 2 END,
                name
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            templates = [dict(row) for row in rows]
            
        return {
            "organization_id": organization_id,
            "templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook templates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook templates: {str(e)}"
        )

@router.get("/{organization_id}/status/{log_id}")
async def get_webhook_status(
    organization_id: str,
    log_id: str
) -> Dict[str, Any]:
    """
    Get status of a specific webhook execution
    """
    
    try:
        # Set organization context
        with db.get_cursor() as cursor:
            cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
            
            # Get specific webhook log
            query = """
            SELECT id, webhook_type, workflow_name, status, execution_time_ms,
                   retry_count, max_retries, triggered_at, completed_at, 
                   error_message, response_data
            FROM webhook_logs 
            WHERE id = %s AND organization_id = %s
            """
            
            cursor.execute(query, [log_id, organization_id])
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Webhook log not found")
            
            log_data = dict(row)
            
        return {
            "log_id": log_id,
            "organization_id": organization_id,
            "webhook_type": log_data["webhook_type"],
            "workflow_name": log_data["workflow_name"],
            "status": log_data["status"],
            "execution_time_ms": log_data["execution_time_ms"],
            "retry_count": log_data["retry_count"],
            "max_retries": log_data["max_retries"],
            "triggered_at": log_data["triggered_at"],
            "completed_at": log_data["completed_at"],
            "error_message": log_data["error_message"],
            "can_retry": (
                log_data["status"] in ["failed", "timeout"] and 
                log_data["retry_count"] < log_data["max_retries"]
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook status: {str(e)}"
        )

# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

@router.get("/{organization_id}/analytics")
async def get_webhook_analytics(organization_id: str) -> Dict[str, Any]:
    """
    Get webhook performance analytics
    """
    
    try:
        # Set organization context
        with db.get_cursor() as cursor:
            cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
            
            # Get analytics from view
            query = """
            SELECT webhook_type, workflow_name,
                   total_executions, successful_executions, failed_executions,
                   success_rate_percent, avg_execution_time_ms,
                   avg_retry_count
            FROM webhook_analytics 
            WHERE organization_id = %s
            AND execution_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY total_executions DESC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            analytics = [dict(row) for row in rows]
            
            # Calculate overall stats
            total_executions = sum(a["total_executions"] for a in analytics)
            total_successful = sum(a["successful_executions"] for a in analytics)
            overall_success_rate = (total_successful / total_executions * 100) if total_executions > 0 else 0
            
        return {
            "organization_id": organization_id,
            "period": "last_30_days",
            "overall_stats": {
                "total_executions": total_executions,
                "total_successful": total_successful,
                "overall_success_rate": round(overall_success_rate, 2)
            },
            "by_workflow": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook analytics: {str(e)}"
        )

# ==========================================
# HEALTH CHECK
# ==========================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "webhook_api",
        "timestamp": datetime.now().isoformat()
    } 