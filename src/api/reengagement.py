"""
Reengagement Platform API Endpoints - Minimal Version
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from src.database import db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/reengagement", tags=["reengagement"])

@router.get("/test")
async def test_reengagement_router():
    """Test endpoint to verify reengagement router is working"""
    return {
        "status": "success",
        "message": "Reengagement API router is working!",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test-db")
async def test_database_connection():
    """Test database connection and basic query"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total_patients FROM patients")
            result = cursor.fetchone()
            
        return {
            "status": "success",
            "message": "Database connection working!",
            "total_patients_in_db": result['total_patients'] if result else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/test-no-depends")
async def test_without_depends_import():
    """Test endpoint to verify router works without Depends import (like dashboard)"""
    return {
        "status": "success", 
        "message": "Router working without Depends import (dashboard pattern)!",
        "fastapi_imports": ["APIRouter", "HTTPException"],
        "pattern": "dashboard_style",
        "timestamp": datetime.now().isoformat()
    } 