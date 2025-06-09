"""
Routiq Backend v2 - FastAPI Backend - MINIMAL TEST VERSION
Multi-tenant healthcare SaaS API with Clerk authentication
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

print("🔍 MINIMAL TEST VERSION - Starting basic imports...")

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    from pydantic import BaseModel
    print("✅ Basic FastAPI imports successful")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    raise

print("🔧 Creating minimal FastAPI application...")

# Minimal FastAPI app for testing
app = FastAPI(
    title="Routiq Backend API - TEST",
    description="Minimal test version",
    version="2.0.0-test",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✅ Basic FastAPI app created")

# Simple health check that doesn't require database
@app.get("/")
async def root():
    return {
        "message": "Routiq Backend API - MINIMAL TEST VERSION", 
        "status": "healthy", 
        "version": "2.0.0-test",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Minimal health check without database"""
    return {
        "status": "healthy",
        "environment": {
            "PORT": os.getenv("PORT", "not_set"),
            "PYTHONPATH": os.getenv("PYTHONPATH", "not_set"),
            "APP_ENV": os.getenv("APP_ENV", "not_set"),
            "HAS_CLERK_KEY": "yes" if os.getenv("CLERK_SECRET_KEY") else "no",
            "HAS_SUPABASE_URL": "yes" if os.getenv("SUPABASE_URL") else "no",
            "HAS_DATABASE_URL": "yes" if os.getenv("DATABASE_URL") else "no"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify the API is working"""
    return {
        "message": "Test endpoint working!",
        "railway_env": {
            "region": os.getenv("RAILWAY_REGION", "unknown"),
            "service": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
            "deployment": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
        }
    }

print("✅ All endpoints defined - Minimal app ready to start") 