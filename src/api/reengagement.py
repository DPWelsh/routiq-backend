"""
Lean Reengagement API - Minimal Test Version
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

# Create router (prefix added in main.py)
router = APIRouter()

@router.get("/test")
def test_reengagement():
    """Test endpoint to verify reengagement router is working"""
    return {
        "message": "Reengagement router is working!",
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }

@router.get("/{organization_id}/dashboard")
def get_reengagement_dashboard(organization_id: str):
    """Get risk-based dashboard data - SIMPLIFIED VERSION"""
    try:
        # Simplified response without database calls for testing
        return {
            "organization_id": organization_id,
            "total_patients": 651,
            "immediate_actions_required": 12,
            "risk_distribution": [
                {"risk_level": "critical", "count": 12, "percentage": 1.8},
                {"risk_level": "high", "count": 23, "percentage": 3.5},
                {"risk_level": "medium", "count": 45, "percentage": 6.9},
                {"risk_level": "low", "count": 89, "percentage": 13.7},
                {"risk_level": "engaged", "count": 482, "percentage": 74.1}
            ],
            "message": "Demo data - database integration pending",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard error for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")

@router.get("/{organization_id}/patients/at-risk")
def get_patients_at_risk(
    organization_id: str,
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get prioritized at-risk patients - SIMPLIFIED VERSION"""
    try:
        # Demo data for testing
        demo_patients = [
            {
                "patient_id": "demo-001",
                "patient_name": "Sarah Chen",
                "email": "sarah.chen@email.com",
                "phone": "+1234567890",
                "risk_score": 95,
                "risk_level": "critical",
                "days_since_last_contact": 62.0,
                "action_priority": 1,
                "recommended_action": "URGENT: Call immediately + schedule appointment",
                "contact_success_prediction": "medium",
                "upcoming_appointments": 0
            },
            {
                "patient_id": "demo-002", 
                "patient_name": "Mike Torres",
                "email": "mike.torres@email.com",
                "phone": "+1234567891",
                "risk_score": 88,
                "risk_level": "high",
                "days_since_last_contact": 45.0,
                "action_priority": 2,
                "recommended_action": "HIGH: Proactive check-in call",
                "contact_success_prediction": "high",
                "upcoming_appointments": 1
            }
        ]
        
        # Filter by risk level if specified
        if risk_level:
            demo_patients = [p for p in demo_patients if p["risk_level"] == risk_level]
        
        return {
            "organization_id": organization_id,
            "patients": demo_patients[:limit],
            "message": "Demo data - database integration pending",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"At-risk patients error for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch patients") 