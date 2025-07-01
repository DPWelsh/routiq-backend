"""
Reengagement Platform API Endpoints - Minimal Version
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from src.database import db
from src.api.auth import verify_organization_access

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

@router.get("/{organization_id}/risk-metrics")
async def get_risk_metrics(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """Get patient risk assessment metrics"""
    try:
        with db.get_cursor() as cursor:
            # Get risk summary from master view
            risk_query = """
            SELECT 
                risk_level,
                COUNT(*) as patient_count
            FROM patient_reengagement_master_view 
            WHERE organization_id = %s
            GROUP BY risk_level
            """
            
            cursor.execute(risk_query, [organization_id])
            risk_rows = cursor.fetchall()
            
            # Initialize risk counts
            risk_summary = {
                "critical": 0,
                "high": 0, 
                "medium": 0,
                "low": 0,
                "engaged": 0
            }
            
            # Populate actual counts
            for row in risk_rows:
                risk_level = row['risk_level']
                if risk_level in risk_summary:
                    risk_summary[risk_level] = row['patient_count']
            
            # Get alert metrics
            alerts_query = """
            SELECT 
                COUNT(*) FILTER (WHERE missed_appointments_90d > 0) as missed_appointments,
                COUNT(*) FILTER (WHERE days_since_last_contact > 30) as failed_communications,
                COUNT(*) FILTER (WHERE days_to_next_appointment IS NULL) as no_future_appointments,
                COUNT(*) FILTER (WHERE action_priority <= 2) as immediate_actions_required
            FROM patient_reengagement_master_view 
            WHERE organization_id = %s
            """
            
            cursor.execute(alerts_query, [organization_id])
            alerts_row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "risk_summary": risk_summary,
                "alerts": {
                    "missed_appointments_14d": alerts_row['missed_appointments'] or 0,
                    "failed_communications": alerts_row['failed_communications'] or 0,
                    "no_future_appointments": alerts_row['no_future_appointments'] or 0
                },
                "immediate_actions_required": alerts_row['immediate_actions_required'] or 0,
                "last_updated": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 