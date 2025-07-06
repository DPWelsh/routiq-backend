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

# 🚨 FAILSAFE DEPLOYMENT VERIFICATION - IMPOSSIBLE TO MISS
print("🚨🚨🚨 FAILSAFE: Enhanced debug version is ACTIVE - main.py loaded 🚨🚨🚨")
logger.critical("🚨🚨🚨 FAILSAFE: Enhanced debug version is ACTIVE - main.py loaded 🚨🚨🚨")
logger.error("🚨🚨🚨 FAILSAFE: Enhanced debug version is ACTIVE - main.py loaded 🚨🚨🚨")
logger.warning("🚨🚨🚨 FAILSAFE: Enhanced debug version is ACTIVE - main.py loaded 🚨🚨🚨")
logger.info("🚨🚨🚨 FAILSAFE: Enhanced debug version is ACTIVE - main.py loaded 🚨🚨🚨")

# 🚨 DEPLOYMENT VERIFICATION CHECKPOINT
logger.info("🚨 DEPLOYMENT CHECKPOINT: Enhanced debugging version deployed successfully")
logger.info("🚨 DEPLOYMENT CHECKPOINT: This confirms our changes are active")

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
    "https://routiq-frontend.vercel.app",
    # Production and development frontend domains
    "https://app.routiq.ai",
    "https://dev.app.routiq.ai"
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

logger.info("🚨 FLOW CHECKPOINT: Passed global exception handler setup")

# 🚨 EXECUTION FLOW CHECKPOINT
logger.critical("🚨 FLOW CHECKPOINT: Reached router loading section in main.py")
logger.error("🚨 FLOW CHECKPOINT: About to start core router imports")
print("🚨 PRINT: Reached router loading section")

# WRAP ENTIRE ROUTER SECTION IN EXCEPTION HANDLING
try:
    logger.critical("🚨 INSIDE TRY BLOCK: Starting router loading")
    
    # FIXED: Include routers individually to prevent all-or-nothing failures  
    # Each router now has its own prefix defined, no need for additional prefixes here

    logger.info("🚨 CRITICAL CHECKPOINT: Starting enhanced router loading section")
    logger.info("🚨 CRITICAL CHECKPOINT: This message confirms the section is being reached")

    # ENHANCED LOGGING: Debug router loading issues
    logger.info("🔍 Starting individual router loading with detailed error tracking...")
    logger.info(f"🔍 Current working directory: {os.getcwd()}")
    logger.info(f"🔍 Python path: {os.getenv('PYTHONPATH', 'Not set')}")

    # Test basic import capability
    try:
        import src
        logger.info("🔍 Basic 'src' package import: SUCCESS")
    except Exception as e:
        logger.error(f"🔍 Basic 'src' package import: FAILED - {e}")

    try:
        import src.api
        logger.info("🔍 'src.api' package import: SUCCESS")
    except Exception as e:
        logger.error(f"🔍 'src.api' package import: FAILED - {e}")

    # Authentication endpoints
    logger.info("🔍 CHECKPOINT 1: About to attempt auth router import")
    try:
        logger.info("🔍 Attempting to import auth router...")
        from src.api.auth import router as auth_router
        logger.info("🔍 Auth router imported successfully, mounting...")
        app.include_router(auth_router)
        logger.info("✅ Authentication endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Authentication router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Authentication endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        
    logger.info("🔍 CHECKPOINT 2: Auth router attempt complete")

    # Providers endpoints  
    try:
        logger.info("🔍 Attempting to import providers router...")
        from src.api.providers import router as providers_router
        logger.info("🔍 Providers router imported successfully, mounting...")
        app.include_router(providers_router)
        logger.info("✅ Providers endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Providers router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Providers endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")

    # Patients endpoints
    try:
        logger.info("🔍 Attempting to import patients router...")
        from src.api.patients import router as patients_router
        logger.info("🔍 Patients router imported successfully, mounting...")
        app.include_router(patients_router)
        logger.info("✅ Patients endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Patients router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Patients endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")

    # Appointments endpoints
    try:
        logger.info("🔍 Attempting to import appointments router...")
        from src.api.appointments import router as appointments_router
        logger.info("🔍 Appointments router imported successfully, mounting...")
        app.include_router(appointments_router)
        logger.info("✅ Appointments endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Appointments router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Appointments endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")

    # Sync Manager endpoints
    try:
        logger.info("🔍 Attempting to import sync_manager router...")
        from src.api.sync_manager import router as sync_manager_router
        logger.info("🔍 Sync Manager router imported successfully, mounting...")
        app.include_router(sync_manager_router)
        logger.info("✅ Sync Manager endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Sync Manager router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Sync Manager endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")

    # Sync Status endpoints
    try:
        logger.info("🔍 Attempting to import sync_status router...")
        from src.api.sync_status import router as sync_status_router
        logger.info("🔍 Sync Status router imported successfully, mounting...")
        app.include_router(sync_status_router)
        logger.info("✅ Sync Status endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Sync Status router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Sync Status endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")

    # Webhooks endpoints
    try:
        logger.info("🔍 Attempting to import webhooks router...")
        from src.api.webhooks import router as webhooks_router
        logger.info("🔍 Webhooks router imported successfully, mounting...")
        app.include_router(webhooks_router)
        logger.info("✅ Webhooks endpoints enabled")
    except ImportError as e:
        logger.error(f"❌ Webhooks router import failed: {e}")
        logger.error(f"❌ Import error details: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Webhooks endpoints failed to load: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")

    logger.info("🔍 Router loading complete. Check logs above for any failures.")

    # CRITICAL: Report final router count to verify what actually loaded
    try:
        router_count = len(app.routes)
        logger.info(f"🚨 FINAL ROUTER COUNT: {router_count} total routes registered")
        
        # List all registered route prefixes for debugging
        prefixes = set()
        for route in app.routes:
            if hasattr(route, 'path'):
                path_parts = route.path.split('/')
                if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'v1':
                    prefixes.add(f"/{'/'.join(path_parts[:4])}")
        
        logger.info(f"🚨 REGISTERED PREFIXES: {sorted(list(prefixes))}")
        
    except Exception as e:
        logger.error(f"🚨 ERROR COUNTING ROUTES: {e}")

except Exception as router_section_error:
    logger.critical(f"🚨🚨🚨 ROUTER SECTION EXCEPTION: {router_section_error}")
    logger.critical(f"🚨🚨🚨 ERROR TYPE: {type(router_section_error).__name__}")
    print(f"🚨🚨🚨 ROUTER SECTION FAILED: {router_section_error}")
    
    # Continue with fallback behavior
    logger.critical("🚨 CONTINUING WITH FALLBACK ROUTER LOADING")

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
    app.include_router(reengagement_router)
    logger.info("✅ Reengagement endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Reengagement endpoints not available: {e}")

# Webhooks moved to core section above

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