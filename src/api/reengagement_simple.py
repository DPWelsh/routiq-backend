"""
Simple reengagement API for testing - no auth dependencies
"""

import logging
from fastapi import APIRouter
from src.database import db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/reengagement-test", tags=["reengagement-test"])

@router.get("/health")
async def test_health():
    """Simple health check for reengagement system"""
    return {"status": "healthy", "message": "Reengagement API is working"}

@router.get("/{organization_id}/test-dashboard")
async def test_dashboard(organization_id: str):
    """Test dashboard endpoint without auth"""
    try:
        query = """
        SELECT COUNT(*) as total_patients
        FROM patients 
        WHERE organization_id = $1
        """
        
        result = await db.fetch_one(query, organization_id)
        
        return {
            "organization_id": organization_id,
            "total_patients": result["total_patients"] if result else 0,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        return {"error": str(e), "status": "failed"} 