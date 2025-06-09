"""
Routiq Backend v2 - FastAPI Backend
Multi-tenant healthcare SaaS API with Clerk authentication
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

# Import our existing components
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Initialize startup configuration
from api.startup import initialize
initialize()

from database import db
from integrations.clerk_client import clerk
from sync_manager_multi_tenant import multi_tenant_sync

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Routiq Backend API",
    description="Multi-tenant healthcare practice management API with integrated conversation sync",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Routiq Dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.vercel.app",
        "https://routiq-hub-dashboard.vercel.app",
        "http://localhost:3000",  # Development
        "http://localhost:3001",  # Development alternate
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.railway.app", "localhost", "127.0.0.1"]
)

# Pydantic models
class UserInfo(BaseModel):
    id: str
    email: str
    organizations: List[Dict[str, Any]]

class SyncStatus(BaseModel):
    organization_id: str
    status: str
    last_sync: Optional[datetime]
    cliniko_status: str
    chatwoot_status: str

class CredentialsRequest(BaseModel):
    service_name: str
    credentials: Dict[str, Any]

# Auth dependency
async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """Extract and validate Clerk JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Remove 'Bearer ' prefix
        token = authorization.replace("Bearer ", "")
        
        # In production, use Clerk's JWT verification
        # For now, we'll simulate user data
        # TODO: Implement proper Clerk JWT validation
        
        return {
            "id": "user_123",
            "email": "admin@sampleclinic.com",
            "organizations": ["org_sample_123"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def verify_org_access(organization_id: str, user: Dict = Depends(get_current_user)):
    """Verify user has access to organization"""
    if organization_id not in user.get("organizations", []):
        raise HTTPException(status_code=403, detail="Access denied to organization")
    return True

# Health check
@app.get("/")
async def root():
    return {"message": "Routiq Backend API", "status": "healthy", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

# Authentication endpoints
@app.get("/api/v1/auth/me", response_model=UserInfo)
async def get_current_user_info(user: Dict = Depends(get_current_user)):
    """Get current user information and organizations"""
    organizations = clerk.get_user_organizations(user["id"])
    
    return UserInfo(
        id=user["id"],
        email=user["email"],
        organizations=organizations
    )

# Organization endpoints
@app.get("/api/v1/organizations")
async def list_organizations(user: Dict = Depends(get_current_user)):
    """List organizations user has access to"""
    return clerk.get_user_organizations(user["id"])

@app.get("/api/v1/organizations/{organization_id}/members")
async def get_organization_members(
    organization_id: str,
    _: bool = Depends(verify_org_access)
):
    """Get organization members"""
    return clerk.get_organization_members(organization_id)

# Sync management endpoints
@app.get("/api/v1/organizations/{organization_id}/sync/status")
async def get_sync_status(
    organization_id: str,
    _: bool = Depends(verify_org_access)
):
    """Get sync status for organization"""
    
    # Get latest sync log
    query = """
        SELECT status, started_at, completed_at, results
        FROM sync_logs 
        WHERE organization_id = %s 
        ORDER BY started_at DESC 
        LIMIT 1
    """
    
    latest_sync = db.execute_single(query, (organization_id,))
    
    if not latest_sync:
        return {
            "organization_id": organization_id,
            "status": "never_synced",
            "last_sync": None,
            "cliniko_status": "unknown",
            "chatwoot_status": "unknown"
        }
    
    results = latest_sync.get("results", {})
    if isinstance(results, str):
        import json
        results = json.loads(results)
    
    return {
        "organization_id": organization_id,
        "status": latest_sync["status"],
        "last_sync": latest_sync["completed_at"],
        "cliniko_status": results.get("cliniko", {}).get("success", False),
        "chatwoot_status": results.get("chatwoot", {}).get("success", False),
        "details": results
    }

@app.post("/api/v1/organizations/{organization_id}/sync/trigger")
async def trigger_sync(
    organization_id: str,
    background_tasks: BackgroundTasks,
    user: Dict = Depends(get_current_user),
    _: bool = Depends(verify_org_access)
):
    """Trigger manual sync for organization"""
    
    # Add sync task to background
    background_tasks.add_task(
        multi_tenant_sync.sync_organization_data,
        organization_id
    )
    
    # Log the action
    await clerk.log_user_action(
        user_id=user["id"],
        organization_id=organization_id,
        action="manual_sync_triggered",
        resource_type="organization",
        resource_id=organization_id
    )
    
    return {"message": "Sync triggered", "organization_id": organization_id}

# Credentials management
@app.post("/api/v1/organizations/{organization_id}/credentials")
async def store_credentials(
    organization_id: str,
    request: CredentialsRequest,
    user: Dict = Depends(get_current_user),
    _: bool = Depends(verify_org_access)
):
    """Store API credentials for organization"""
    
    success = await multi_tenant_sync.store_api_credentials(
        organization_id=organization_id,
        service_name=request.service_name,
        credentials=request.credentials,
        created_by=user["id"]
    )
    
    if success:
        return {"message": "Credentials stored successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to store credentials")

@app.get("/api/v1/organizations/{organization_id}/credentials/validate")
async def validate_credentials(
    organization_id: str,
    _: bool = Depends(verify_org_access)
):
    """Validate API credentials for organization"""
    
    results = await multi_tenant_sync.validate_organization_credentials(organization_id)
    return results

# Data endpoints
@app.get("/api/v1/organizations/{organization_id}/contacts")
async def get_contacts(
    organization_id: str,
    limit: int = 100,
    offset: int = 0,
    _: bool = Depends(verify_org_access)
):
    """Get contacts for organization"""
    
    # Set organization context for RLS
    multi_tenant_sync.set_organization_context(organization_id)
    
    query = """
        SELECT id, phone_number, name, contact_type, source, 
               created_at, updated_at
        FROM contacts 
        WHERE organization_id = %s
        ORDER BY updated_at DESC
        LIMIT %s OFFSET %s
    """
    
    contacts = db.execute_query(query, (organization_id, limit, offset))
    
    # Get total count
    count_query = "SELECT COUNT(*) as total FROM contacts WHERE organization_id = %s"
    total = db.execute_single(count_query, (organization_id,))
    
    return {
        "contacts": contacts,
        "total": total["total"],
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/organizations/{organization_id}/active-patients")
async def get_active_patients(
    organization_id: str,
    limit: int = 100,
    offset: int = 0,
    _: bool = Depends(verify_org_access)
):
    """Get active patients for organization"""
    
    multi_tenant_sync.set_organization_context(organization_id)
    
    query = """
        SELECT 
            ap.id,
            ap.cliniko_patient_id,
            ap.status,
            ap.last_appointment_date,
            ap.next_appointment_date,
            c.name,
            c.phone_number,
            c.contact_type
        FROM active_patients ap
        JOIN contacts c ON ap.contact_id = c.id
        WHERE ap.organization_id = %s
        ORDER BY ap.last_appointment_date DESC
        LIMIT %s OFFSET %s
    """
    
    patients = db.execute_query(query, (organization_id, limit, offset))
    
    return {
        "patients": patients,
        "total": len(patients),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/organizations/{organization_id}/analytics/summary")
async def get_analytics_summary(
    organization_id: str,
    _: bool = Depends(verify_org_access)
):
    """Get analytics summary for organization"""
    
    multi_tenant_sync.set_organization_context(organization_id)
    
    # Get various counts
    queries = {
        "total_contacts": "SELECT COUNT(*) as count FROM contacts WHERE organization_id = %s",
        "active_patients": "SELECT COUNT(*) as count FROM active_patients WHERE organization_id = %s",
        "total_messages": "SELECT COUNT(*) as count FROM messages WHERE organization_id = %s",
        "conversations": "SELECT COUNT(*) as count FROM conversations WHERE organization_id = %s"
    }
    
    summary = {}
    for key, query in queries.items():
        result = db.execute_single(query, (organization_id,))
        summary[key] = result["count"] if result else 0
    
    return summary

# Webhook endpoints (for Clerk)
@app.post("/webhooks/clerk")
async def clerk_webhook(request: dict):
    """Handle Clerk webhooks"""
    
    event_type = request.get("type")
    
    if event_type == "user.created":
        result = await clerk.handle_user_created(request)
    elif event_type == "organization.created":
        result = await clerk.handle_organization_created(request)
    elif event_type == "organizationMembership.created":
        result = await clerk.handle_organization_membership_created(request)
    else:
        return {"message": f"Unhandled event type: {event_type}"}
    
    return result

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("APP_ENV") == "development"
    ) 