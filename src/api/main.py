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

# SECURITY ENHANCEMENT: Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for API protection"""
    try:
        # Import rate limiter
        from src.services.rate_limiter import rate_limiter, get_rate_limit_identifier
        
        # Determine rate limit tier based on endpoint
        path = str(request.url.path)
        if path.startswith("/api/v1/admin"):
            tier = "admin"
        elif path.startswith("/api/v1/sync"):
            tier = "sync"  
        elif path.startswith("/api/v1/"):
            tier = "api"
        else:
            tier = "public"
        
        # Get identifier for rate limiting
        identifier = get_rate_limit_identifier(request)
        
        # Check rate limit
        allowed, rate_info = rate_limiter.check_limit(tier, identifier)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {identifier} on {tier} endpoint {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Try again in {rate_info.get('retry_after', 60)} seconds.",
                    "rate_limit": {
                        "limit": rate_info.get('limit'),
                        "remaining": rate_info.get('remaining', 0),
                        "reset_time": rate_info.get('reset_time'),
                        "retry_after": rate_info.get('retry_after')
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info.get('limit', 'unknown')),
                    "X-RateLimit-Remaining": str(rate_info.get('remaining', 0)),
                    "X-RateLimit-Reset": str(int(rate_info.get('reset_time', 0))),
                    "Retry-After": str(int(rate_info.get('retry_after', 60)))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info.get('limit', 'unknown'))
            response.headers["X-RateLimit-Remaining"] = str(rate_info.get('remaining', 0))
            response.headers["X-RateLimit-Reset"] = str(int(rate_info.get('reset_time', 0)))
        
        return response
        
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # On error, allow the request to proceed
        return await call_next(request)

# SECURITY ENHANCEMENT: Smart CORS configuration with HTTPS enforcement
# Build allowed origins based on environment
allowed_origins = [
    "https://routiq-admin-dashboard.vercel.app",
    "https://routiq-frontend.vercel.app"
]

# Allow HTTP localhost only in development
if APP_ENV == "development":
    allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        # Also allow HTTPS localhost for development
        "https://localhost:3000",
        "https://localhost:3001"
    ])
    logger.info("🔓 Development mode: HTTP localhost origins allowed")
else:
    logger.info("🔒 Production mode: HTTPS only enforcement active")

# CORS middleware with security hardening
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # SECURITY ENHANCEMENT: More restrictive headers
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "Accept",
        "X-Organization-ID",
        "X-Requested-With",
        "User-Agent"
    ],
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
        # SECURITY ENHANCEMENT: Reduced environment variable exposure
        env_status = {
            "APP_ENV": APP_ENV,
            "PORT": PORT,
            # Only show boolean status, not actual values
            "authentication_configured": bool(os.getenv("CLERK_SECRET_KEY")),
            "database_configured": bool(os.getenv("DATABASE_URL")),
            "encryption_configured": bool(os.getenv("CREDENTIALS_ENCRYPTION_KEY"))
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
    from src.api.appointments import router as appointments_router
    from src.api.sync_manager import router as sync_router
    from src.api.sync_status import router as sync_status_router
    
    # Mount core routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(providers_router, prefix="/api/v1/providers", tags=["Providers"])
    app.include_router(patients_router, prefix="/api/v1/patients", tags=["Patients"])
    app.include_router(appointments_router, prefix="/api/v1/appointments", tags=["Appointments"])
    app.include_router(sync_router, prefix="/api/v1/sync", tags=["Sync Manager"])
    app.include_router(sync_status_router, prefix="/api/v1", tags=["Sync Status & Progress"])
    
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

# Try to include Dashboard endpoints
try:
    from src.api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
    logger.info("✅ Dashboard endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Dashboard endpoints not available: {e}")

# Try to include Reengagement endpoints
try:
    from src.api.reengagement import router as reengagement_router
    app.include_router(reengagement_router, prefix="/api/v1/reengagement", tags=["Reengagement"])
    logger.info("✅ Reengagement endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Reengagement endpoints not available: {e}")

# Future integrations - ready for expansion
# app.include_router(chatwoot_router, prefix="/api/v1/chatwoot", tags=["Chatwoot"])
# app.include_router(manychat_router, prefix="/api/v1/manychat", tags=["ManyChat"])

# All endpoints are now properly organized through routers
# - Admin endpoints: src/api/admin.py (System administration)
# - Cliniko endpoints: src/api/cliniko_admin.py (Cliniko integration)
# - Clerk admin endpoints: src/api/clerk_admin.py (Authentication management)

# SECURITY ENHANCEMENT: Improved global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with security considerations"""
    logger.error(f"Global exception on {request.method} {request.url.path}: {exc}")
    
    # Don't expose internal details in production
    if APP_ENV == "production":
        detail = "An unexpected error occurred"
    else:
        detail = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Routiq Backend API startup complete")
    logger.info("🛡️ Security enhancements: Rate limiting active, auth hardened")
    
    # Start the sync scheduler if enabled
    if os.getenv("ENABLE_SYNC_SCHEDULER", "false").lower() == "true":
        import asyncio
        try:
            from src.services.sync_scheduler import scheduler
            
            # Get sync interval from environment (default to 60 minutes for hourly)
            sync_interval = int(os.getenv("SYNC_INTERVAL_MINUTES", "60"))
            
            logger.info(f"🔄 Starting sync scheduler with {sync_interval} minute intervals")
            
            # Start the scheduler in background
            asyncio.create_task(scheduler.start_scheduler(sync_interval_minutes=sync_interval))
            
            logger.info("✅ Sync scheduler started successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Sync scheduler failed to start: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Routiq Backend API shutdown initiated")
    
    # Cleanup database connections
    try:
        from src.database import db
        db.cleanup_database()
        logger.info("✅ Database connections cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Database cleanup warning: {e}")
    
    # Cleanup rate limiter
    try:
        from src.services.rate_limiter import rate_limiter
        rate_limiter.cleanup_all()
        logger.info("✅ Rate limiter cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Rate limiter cleanup warning: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))

logger.info("Routiq Backend API initialization complete")

# Export the app
__all__ = ["app"] 