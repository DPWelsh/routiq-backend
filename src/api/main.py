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

# FastAPI app instance with enhanced documentation
app = FastAPI(
    title="🏥 Routiq Healthcare API",
    description="""
## Multi-Tenant Healthcare Practice Management API

**Routiq** is a comprehensive healthcare SaaS platform that integrates with multiple practice management systems, 
patient communication tools, and provides intelligent patient analytics.

### 🔑 Authentication
All endpoints require **Clerk JWT authentication** unless otherwise specified.
Include your JWT token in the `Authorization` header: `Bearer <your-jwt-token>`

### 🏢 Multi-Tenant Architecture
Each request must include an `x-organization-id` header to specify which healthcare organization's data to access.

### 🔗 Supported Integrations
- **Cliniko**: Practice management and patient data
- **Chatwoot**: Patient communication and support
- **ManyChat**: Automated patient messaging (coming soon)

### 📊 Key Features
- **Real-time Patient Sync**: Automatic synchronization with practice management systems
- **Smart Patient Analytics**: Active patient identification based on appointment history
- **Multi-Service Integration**: Connect multiple tools in one unified API
- **Secure Multi-Tenancy**: Complete data isolation between organizations

### 🚀 Getting Started
1. **Authenticate**: Get your JWT token from Clerk
2. **Set Organization**: Include `x-organization-id` header in requests
3. **Configure Integrations**: Set up your Cliniko/Chatwoot credentials
4. **Start Syncing**: Use the sync endpoints to import and analyze patient data

### 📈 API Versioning
Current version: **v2.0.0** - All endpoints are prefixed with `/api/v1/`

### 🔧 Support
- **Health Check**: `GET /health` - Check API status and configuration
- **Documentation**: `GET /docs` - Interactive API documentation
- **OpenAPI Spec**: `GET /openapi.json` - Machine-readable API specification
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "🏠 Core",
            "description": "Basic API functionality, health checks, and system status"
        },
        {
            "name": "🔐 Authentication", 
            "description": "Clerk JWT authentication and authorization endpoints"
        },
        {
            "name": "👥 Patients",
            "description": "Patient data management, analytics, and appointment insights"
        },
        {
            "name": "🔄 Sync Manager",
            "description": "Data synchronization with practice management systems"
        },
        {
            "name": "📊 Sync Status & Progress",
            "description": "Real-time sync progress tracking and status monitoring"
        },
        {
            "name": "🏥 Providers",
            "description": "Healthcare provider and practitioner management"
        },
        {
            "name": "⚙️ Admin",
            "description": "System administration, database management, and migrations"
        },
        {
            "name": "🩺 Cliniko",
            "description": "Cliniko practice management system integration"
        },
        {
            "name": "👤 Clerk Admin",
            "description": "User and organization management through Clerk"
        }
    ],
    contact={
        "name": "Routiq Support",
        "email": "support@routiq.com",
    },
    license_info={
        "name": "Private - All Rights Reserved",
    },
    servers=[
        {
            "url": "https://routiq-backend-prod.up.railway.app",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
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

# Enhanced Pydantic models with detailed field descriptions
class HealthResponse(BaseModel):
    """Health check response model with comprehensive system status"""
    status: str = Field(..., description="Overall system health status", example="healthy")
    timestamp: str = Field(..., description="Current server timestamp in ISO format", example="2025-01-15T10:30:00.123456")
    version: str = Field(..., description="API version for compatibility checking", example="2.0.0")
    environment: Dict[str, Any] = Field(..., description="Environment configuration status (no sensitive data)", example={
        "APP_ENV": "production",
        "PORT": "8000",
        "has_clerk_key": True,
        "has_supabase_url": True,
        "has_database_url": True
    })

class ErrorResponse(BaseModel):
    """Standard error response model for consistent error handling"""
    error: str = Field(..., description="Error type or category", example="Authentication failed")
    detail: Optional[str] = Field(None, description="Detailed error message", example="JWT token is expired or invalid")
    timestamp: str = Field(..., description="Error occurrence timestamp", example="2025-01-15T10:30:00.123456")

# Root endpoint
@app.get(
    "/", 
    response_model=Dict[str, Any],
    tags=["🏠 Core"],
    summary="🏠 API Welcome & Information",
    description="""
    **Welcome to the Routiq Healthcare API!**
    
    This endpoint provides basic information about the API and quick links to documentation.
    
    ### Quick Links
    - **Interactive Docs**: [/docs](/docs) - Try out endpoints directly
    - **ReDoc**: [/redoc](/redoc) - Clean, readable documentation
    - **Health Check**: [/health](/health) - System status and configuration
    - **OpenAPI Spec**: [/openapi.json](/openapi.json) - Machine-readable API spec
    
    ### Next Steps
    1. Check the [health endpoint](/health) to verify system status
    2. Visit [/docs](/docs) for interactive API documentation
    3. Get your Clerk JWT token for authentication
    4. Start making authenticated requests with your organization ID
    """
)
async def root():
    """🏠 Welcome endpoint with API information and quick navigation links"""
    return {
        "message": "🏥 Welcome to Routiq Healthcare API",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "quick_links": {
            "health_check": "/health",
            "authentication": "/api/v1/auth/verify",
            "sync_dashboard": "/api/v1/sync/dashboard/{organization_id}",
            "start_sync": "/api/v1/sync/start/{organization_id}"
        },
        "getting_started": "Visit /docs for interactive API documentation"
    }

# Health check endpoint
@app.get(
    "/health", 
    response_model=HealthResponse,
    tags=["🏠 Core"],
    summary="🔍 System Health Check",
    description="""
    **Comprehensive system health and configuration check**
    
    This endpoint provides detailed information about:
    - ✅ API server status and uptime
    - 🔧 Environment configuration
    - 🔑 Required environment variables presence
    - 🗄️ Database connectivity (implicit)
    - 🔐 Authentication service status
    
    ### Use Cases
    - **Monitoring**: Check if the API is running and properly configured
    - **Debugging**: Verify environment variables are set correctly
    - **CI/CD**: Validate deployment health before routing traffic
    - **Support**: Quick diagnostic information for troubleshooting
    
    ### Response Details
    - `status`: Overall system health ("healthy" or "unhealthy")
    - `timestamp`: Current server time (UTC)
    - `version`: API version for compatibility checking
    - `environment`: Configuration status without exposing sensitive values
    
    **Note**: This endpoint does not require authentication and is safe for public monitoring.
    """
)
async def health_check():
    """🔍 Comprehensive health check with environment status"""
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
    from src.api.sync_status import router as sync_status_router
    
    # Mount core routes with enhanced tags
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["🔐 Authentication"])
    app.include_router(providers_router, prefix="/api/v1/providers", tags=["🏥 Providers"])
    app.include_router(patients_router, prefix="/api/v1/patients", tags=["👥 Patients"])
    app.include_router(sync_router, prefix="/api/v1/sync", tags=["🔄 Sync Manager"])
    app.include_router(sync_status_router, prefix="/api/v1", tags=["📊 Sync Status & Progress"])
    
    logger.info("✅ Core API routers mounted successfully")
    
except Exception as e:
    logger.warning(f"⚠️ Some core routers failed to load: {e}")

# Include routers with proper organization and tagging
# Try to include Admin endpoints
try:
    from src.api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["⚙️ Admin"])
    logger.info("✅ Admin endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Admin endpoints not available: {e}")

# Try to include Cliniko admin endpoints
try:
    from src.api.cliniko_admin import router as cliniko_admin_router
    app.include_router(cliniko_admin_router, prefix="/api/v1/cliniko", tags=["🩺 Cliniko"])
    logger.info("✅ Cliniko integration endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Cliniko integration endpoints not available: {e}")

# Try to include Clerk admin endpoints
try:
    from src.api.clerk_admin import router as clerk_admin_router
    app.include_router(clerk_admin_router, prefix="/api/v1/clerk", tags=["👤 Clerk Admin"])
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
    # Cleanup database connections
    try:
        from src.database import cleanup_database
        cleanup_database()
        logger.info("✅ Database connections cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Database cleanup failed: {e}")
    
    logger.info("🛑 Routiq Backend API shutdown complete")

logger.info("Routiq Backend API initialization complete")

# Export the app
__all__ = ["app"] 