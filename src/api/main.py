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

# Include routers with proper organization and tagging
# Try to include Admin endpoints
try:
    from src.api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    logger.info("✅ Admin endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Admin endpoints not available: {e}")

# Try to include Cliniko admin endpoints
try:
    from src.api.cliniko_admin import router as cliniko_admin_router
    app.include_router(cliniko_admin_router, prefix="/api/v1/cliniko", tags=["Cliniko"])
    logger.info("✅ Cliniko integration endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Cliniko integration endpoints not available: {e}")

# Try to include Clerk admin endpoints
try:
    from src.api.clerk_admin import router as clerk_admin_router
    app.include_router(clerk_admin_router, prefix="/api/v1/clerk", tags=["Clerk Admin"])
    logger.info("✅ Clerk admin endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Clerk admin endpoints not available: {e}")

# Future integrations - ready for expansion
# app.include_router(chatwoot_router, prefix="/api/v1/chatwoot", tags=["Chatwoot"])
# app.include_router(manychat_router, prefix="/api/v1/manychat", tags=["ManyChat"])

# All endpoints are now properly organized through routers
# - Admin endpoints: src/api/admin.py (System administration)
# - Cliniko endpoints: src/api/cliniko_admin.py (Cliniko integration)
# - Clerk admin endpoints: src/api/clerk_admin.py (Authentication management)

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