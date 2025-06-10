"""
Routiq Backend v2 - FastAPI Backend
Multi-tenant healthcare SaaS API with Clerk authentication
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("api.startup")
logger.info("Logging configured - Level: INFO, Format: standard")

try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
    import uvicorn
    from pydantic import BaseModel, Field
    
    logger.info("✅ Core FastAPI imports successful")
except Exception as e:
    logger.error(f"❌ FastAPI imports failed: {e}")
    raise

# Environment and configuration
APP_ENV = os.getenv("APP_ENV", "production")
PYTHON_PATH = os.getenv("PYTHONPATH", "not set")
PORT = os.getenv("PORT", "8000")

logger.info(f"App Environment: {APP_ENV}")
logger.info(f"Python Path: {PYTHON_PATH}")
logger.info(f"Port: {PORT}")

# FastAPI app instance
app = FastAPI(
    title="Routiq Backend API",
    description="Multi-tenant healthcare practice management API with Clerk authentication",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "https://*.vercel.app",
        "https://*.netlify.app",
        "https://routiq-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Routiq Backend API",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check environment variables
        env_status = {
            "APP_ENV": APP_ENV,
            "PORT": PORT,
            "PYTHONPATH": PYTHON_PATH,
            "has_clerk_key": bool(os.getenv("CLERK_SECRET_KEY")),
            "has_supabase_url": bool(os.getenv("SUPABASE_URL")),
            "has_database_url": bool(os.getenv("DATABASE_URL")),
            "has_encryption_key": bool(os.getenv("CREDENTIALS_ENCRYPTION_KEY"))
        }
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            environment=env_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# Include routers with error handling
try:
    # Import core API routes
    from src.api.auth import router as auth_router
    from src.api.providers import router as providers_router
    from src.api.patients import router as patients_router
    from src.api.sync_manager import router as sync_router
    from src.api.cliniko_admin import router as cliniko_router
    
    # Mount core routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(providers_router, prefix="/api/v1/providers", tags=["Providers"])
    app.include_router(patients_router, prefix="/api/v1/patients", tags=["Patients"])
    app.include_router(sync_router, prefix="/api/v1/sync", tags=["Sync Manager"])
    app.include_router(cliniko_router, prefix="/api/v1/admin/cliniko", tags=["Cliniko"])
    
    logger.info("✅ Core API routers mounted successfully")
    
except Exception as e:
    logger.warning(f"⚠️ Some core routers failed to load: {e}")

# Try to include admin endpoints
try:
    from src.api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    logger.info("✅ Admin endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Admin endpoints not available: {e}")

# Try to include Clerk admin endpoints
try:
    from src.api.clerk_admin import router as clerk_admin_router
    app.include_router(clerk_admin_router, prefix="/api/v1/admin/clerk", tags=["Clerk Admin"])
    logger.info("✅ Clerk admin endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Clerk admin endpoints not available: {e}")

# Add patient endpoints directly (workaround for router import issues)
@app.get("/api/v1/patients/{organization_id}/active/summary", tags=["Patients"])
async def get_active_patients_summary(organization_id: str):
    """Get active patients summary for an organization"""
    try:
        from database import db
        
        with db.get_cursor() as cursor:
            summary_query = """
            SELECT 
                COUNT(*) as total_active_patients,
                COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                MAX(updated_at) as last_sync_date
            FROM active_patients 
            WHERE organization_id = %s
            """
            
            cursor.execute(summary_query, [organization_id])
            row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "total_active_patients": row['total_active_patients'] or 0,
                "patients_with_recent_appointments": row['patients_with_recent'] or 0,
                "patients_with_upcoming_appointments": row['patients_with_upcoming'] or 0,
                "last_sync_date": row['last_sync_date'].isoformat() if row['last_sync_date'] else None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

@app.get("/api/v1/patients/{organization_id}/active", tags=["Patients"])
async def list_active_patients(organization_id: str):
    """List active patients for an organization"""
    try:
        from database import db
        
        with db.get_cursor() as cursor:
                query = """
                SELECT 
                    ap.*,
                    c.name as contact_name,
                    c.phone as contact_phone
                FROM active_patients ap
                JOIN contacts c ON ap.contact_id = c.id
                WHERE ap.organization_id = %s
                ORDER BY ap.last_appointment_date DESC
                LIMIT 50
                """
                
                cursor.execute(query, [organization_id])
                rows = cursor.fetchall()
                
                patients = []
                for row in rows:
                    patients.append({
                        "id": row['id'],
                        "contact_id": str(row['contact_id']),
                        "contact_name": row['contact_name'],
                        "contact_phone": row['contact_phone'],
                        "recent_appointment_count": row['recent_appointment_count'],
                        "upcoming_appointment_count": row['upcoming_appointment_count'],
                        "total_appointment_count": row['total_appointment_count'],
                        "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                        "recent_appointments": row['recent_appointments'],
                        "upcoming_appointments": row['upcoming_appointments'],
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                        "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                    })
                
                return {
                    "organization_id": organization_id,
                    "patients": patients,
                    "total_count": len(patients),
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Failed to retrieve active patients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active patients: {str(e)}")

@app.get("/api/v1/patients/test", tags=["Patients"])
async def test_patients_endpoints():
    """Test endpoint to verify patients endpoints are working"""
    return {
        "message": "Patients endpoints are working directly in main.py!",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/patients/debug/organizations", tags=["Patients"])
async def debug_patient_organizations():
    """Debug endpoint to see what organization_ids exist in active_patients table"""
    try:
        from database import db
        
        with db.get_cursor() as cursor:
            # Get all distinct organization_ids in active_patients
            cursor.execute("SELECT DISTINCT organization_id, COUNT(*) as count FROM active_patients GROUP BY organization_id")
            org_results = cursor.fetchall()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM active_patients")
            total_result = cursor.fetchone()
            
            return {
                "total_active_patients": total_result['total'] if total_result else 0,
                "organizations_with_patients": [
                    {
                        "organization_id": row['organization_id'],
                        "patient_count": row['count']
                    } for row in org_results
                ],
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to debug organizations: {e}")
        import traceback
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/patients/debug/sample", tags=["Patients"])
async def debug_sample_patients():
    """Debug endpoint to see sample patient data"""
    try:
        from database import db
        
        with db.get_cursor() as cursor:
            # Get first 3 patients with all columns
            cursor.execute("SELECT * FROM active_patients LIMIT 3")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'active_patients' ORDER BY ordinal_position")
            column_info = cursor.fetchall()
            columns = [row['column_name'] for row in column_info]
            
            # Convert rows to list of dictionaries (they should already be dicts from RealDictCursor)
            sample_data = []
            for row in rows:
                # Row is already a dictionary from RealDictCursor
                patient_dict = {key: str(value) if value is not None else None for key, value in row.items()}
                sample_data.append(patient_dict)
            
            return {
                "sample_patients": sample_data,
                "columns": columns,
                "total_samples": len(sample_data),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to debug sample patients: {e}")
        import traceback
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/patients/debug/simple-test", tags=["Patients"])
async def debug_simple_test():
    """Simple test to verify database connectivity"""
    try:
        from database import db
        
        with db.get_cursor() as cursor:
            # Very simple query
            cursor.execute("SELECT 1 as test_value")
            result = cursor.fetchone()
            
            # Try to access the result
            test_val = result['test_value'] if result else None
            
            return {
                "database_connected": True,
                "test_value": test_val,
                "result_type": type(result).__name__ if result else None,
                "result_keys": list(result.keys()) if result else None
            }
            
    except Exception as e:
        import traceback
        return {
            "database_connected": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }



# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if APP_ENV == "development" else "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Routiq Backend API startup complete")
    
    # Optionally start the sync scheduler
    if os.getenv("ENABLE_SYNC_SCHEDULER", "false").lower() == "true":
        import asyncio
        try:
            from src.services.sync_scheduler import scheduler
            
            # Start scheduler in background
            asyncio.create_task(scheduler.start_scheduler(30))  # 30-minute intervals
            logger.info("✅ Sync scheduler started")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start sync scheduler: {e}")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Routiq Backend API shutdown complete")

logger.info("Routiq Backend API initialization complete")

# Export the app
__all__ = ["app"] 