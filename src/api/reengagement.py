"""
===========================================
LEAN REENGAGEMENT API
===========================================
Simple API that queries PostgreSQL views - no complex business logic.
Replaces 4 Python services with thin controllers.

Philosophy: Views do the work. API just serializes JSON.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel
from src.database import db
from src.api.auth import verify_organization_access

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/v1/reengagement", tags=["reengagement"])

# === PYDANTIC MODELS ===

class OutreachLogEntry(BaseModel):
    patient_id: str
    method: str
    outcome: str
    notes: Optional[str] = None
    attempted_by: Optional[str] = None

class RiskSummaryCard(BaseModel):
    risk_level: str
    count: int
    percentage: float

class DashboardSummary(BaseModel):
    organization_id: str
    total_patients: int
    risk_distribution: List[RiskSummaryCard]
    immediate_actions_required: int
    avg_days_since_contact: float
    calculated_at: datetime

# === CORE ENDPOINTS ===

@router.get("/{organization_id}/dashboard")
async def get_reengagement_dashboard(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Get complete reengagement dashboard data.
    Queries patient_reengagement_master view for risk-based metrics.
    
    Replaces: Generic 'Active Patients: 36' with actionable risk data
    """
    try:
        query = """
        SELECT 
            risk_level,
            COUNT(*) as count,
            AVG(days_since_last_contact) as avg_days
        FROM patient_reengagement_master 
        WHERE organization_id = $1
        GROUP BY risk_level
        """
        
        risk_data = await db.fetch_all(query, organization_id)
        
        total = sum(row['count'] for row in risk_data)
        immediate_actions = sum(row['count'] for row in risk_data if row['risk_level'] in ['critical', 'high'])
        
        return {
            "organization_id": organization_id,
            "total_patients": total,
            "immediate_actions_required": immediate_actions,
            "risk_distribution": [
                {
                    "risk_level": row['risk_level'],
                    "count": row['count'],
                    "percentage": round((row['count'] / total * 100) if total > 0 else 0, 1)
                }
                for row in risk_data
            ]
        }
        
    except Exception as e:
        logger.error(f"Dashboard error for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")

@router.get("/{organization_id}/patients/at-risk")
async def get_patients_at_risk(
    organization_id: str,
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Get prioritized list of at-risk patients with action recommendations.
    Queries patient_reengagement_master view with filters.
    
    Frontend gets: Actionable patient list instead of random 651 patients
    """
    try:
        where_clause = "organization_id = $1"
        params = [organization_id]
        
        if risk_level:
            where_clause += " AND risk_level = $2"
            params.append(risk_level)
            
        query = f"""
        SELECT 
            patient_id, patient_name, email, phone, risk_score, risk_level,
            days_since_last_contact, action_priority, recommended_action,
            contact_success_prediction, upcoming_appointment_count
        FROM patient_reengagement_master 
        WHERE {where_clause}
        ORDER BY action_priority ASC, risk_score DESC
        LIMIT ${len(params) + 1}
        """
        params.append(limit)
        
        patients = await db.fetch_all(query, *params)
        
        return {
            "patients": [
                {
                    "patient_id": str(p["patient_id"]),
                    "patient_name": p["patient_name"],
                    "email": p["email"],
                    "phone": p["phone"],
                    "risk_score": p["risk_score"],
                    "risk_level": p["risk_level"],
                    "days_since_last_contact": float(p["days_since_last_contact"]),
                    "action_priority": p["action_priority"],
                    "recommended_action": p["recommended_action"],
                    "contact_success_prediction": p["contact_success_prediction"],
                    "upcoming_appointments": p["upcoming_appointment_count"]
                }
                for p in patients
            ]
        }
        
    except Exception as e:
        logger.error(f"At-risk patients error for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch patients")

@router.get("/{organization_id}/performance")
async def get_reengagement_performance(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Get reengagement performance metrics and analytics.
    Queries reengagement_performance_metrics view.
    
    Shows: Contact success rates, channel performance, trending, benchmarks
    """
    try:
        performance_query = """
        SELECT 
            organization_id,
            total_outreach_attempts_30d,
            successful_contacts_30d,
            unique_patients_contacted_30d,
            unique_patients_reached_30d,
            contact_success_rate_30d,
            patient_reach_rate_30d,
            appointments_scheduled_after_contact_30d,
            appointment_conversion_rate_30d,
            channel_performance_30d,
            attempts_trend_percent,
            success_trend_percent,
            performance_vs_benchmark,
            patient_base_engagement_rate_30d,
            avg_days_to_successful_contact,
            total_patients,
            active_patients,
            calculated_at
        FROM reengagement_performance_metrics 
        WHERE organization_id = $1
        """
        
        performance = await db.fetch_one(performance_query, organization_id)
        
        if not performance:
            # Return empty state for organizations with no outreach data yet
            return {
                "organization_id": organization_id,
                "summary": {
                    "total_attempts_30d": 0,
                    "successful_contacts_30d": 0,
                    "contact_success_rate_30d": 0.0,
                    "appointment_conversion_rate_30d": 0.0
                },
                "trending": {
                    "attempts_trend_percent": 0.0,
                    "success_trend_percent": 0.0
                },
                "benchmarks": {
                    "performance_vs_industry": "no_data",
                    "patient_engagement_rate": 0.0
                },
                "channel_performance": {
                    "phone": {"attempts": 0, "successes": 0, "success_rate": 0.0},
                    "sms": {"attempts": 0, "successes": 0, "success_rate": 0.0},
                    "email": {"attempts": 0, "successes": 0, "success_rate": 0.0}
                },
                "metadata": {
                    "total_patients": 0,
                    "active_patients": 0,
                    "has_data": False,
                    "calculated_at": datetime.utcnow()
                }
            }
        
        return {
            "organization_id": performance["organization_id"],
            "summary": {
                "total_attempts_30d": performance["total_outreach_attempts_30d"],
                "successful_contacts_30d": performance["successful_contacts_30d"],
                "unique_patients_contacted_30d": performance["unique_patients_contacted_30d"],
                "unique_patients_reached_30d": performance["unique_patients_reached_30d"],
                "contact_success_rate_30d": float(performance["contact_success_rate_30d"]),
                "patient_reach_rate_30d": float(performance["patient_reach_rate_30d"]),
                "appointments_scheduled_after_contact_30d": performance["appointments_scheduled_after_contact_30d"],
                "appointment_conversion_rate_30d": float(performance["appointment_conversion_rate_30d"]),
                "avg_days_to_successful_contact": float(performance["avg_days_to_successful_contact"])
            },
            "trending": {
                "attempts_trend_percent": float(performance["attempts_trend_percent"]),
                "success_trend_percent": float(performance["success_trend_percent"])
            },
            "benchmarks": {
                "performance_vs_industry": performance["performance_vs_benchmark"],
                "patient_engagement_rate": float(performance["patient_base_engagement_rate_30d"])
            },
            "channel_performance": performance["channel_performance_30d"],
            "metadata": {
                "total_patients": performance["total_patients"],
                "active_patients": performance["active_patients"],
                "has_data": True,
                "calculated_at": performance["calculated_at"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching performance metrics for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance data")

@router.post("/{organization_id}/log-outreach")
async def log_outreach_attempt(
    organization_id: str,
    outreach: OutreachLogEntry,
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Log a manual outreach attempt.
    Simple INSERT into outreach_log table.
    
    Start manual before building complex SMS/email integrations.
    """
    try:
        query = """
        INSERT INTO outreach_log 
        (patient_id, organization_id, method, outcome, notes, attempted_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, created_at
        """
        
        result = await db.fetch_one(
            query,
            UUID(outreach.patient_id),
            organization_id,
            outreach.method,
            outreach.outcome,
            outreach.notes,
            outreach.attempted_by
        )
        
        return {
            "success": True,
            "outreach_id": str(result["id"]),
            "logged_at": result["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Outreach logging error: {e}")
        raise HTTPException(status_code=500, detail="Failed to log outreach")

@router.get("/{organization_id}/patients/{patient_id}/outreach-history")
async def get_patient_outreach_history(
    organization_id: str,
    patient_id: str,
    limit: int = Query(20, ge=1, le=100),
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Get outreach history for a specific patient.
    Simple query of outreach_log table.
    """
    try:
        history_query = """
        SELECT 
            id,
            method,
            outcome,
            notes,
            attempted_by,
            created_at
        FROM outreach_log 
        WHERE patient_id = $1 AND organization_id = $2
        ORDER BY created_at DESC
        LIMIT $3
        """
        
        history = await db.fetch_all(
            history_query, 
            UUID(patient_id), 
            organization_id, 
            limit
        )
        
        return {
            "patient_id": patient_id,
            "outreach_history": [
                {
                    "id": str(record["id"]),
                    "method": record["method"],
                    "outcome": record["outcome"],
                    "notes": record["notes"],
                    "attempted_by": record["attempted_by"],
                    "created_at": record["created_at"]
                }
                for record in history
            ],
            "total_returned": len(history)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient_id format")
    except Exception as e:
        logger.error(f"Error fetching outreach history for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch outreach history")

# === HEALTH CHECK ===
@router.get("/{organization_id}/health")
async def reengagement_health_check(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Health check for reengagement system.
    Validates views and data availability.
    """
    try:
        # Test master view
        view_test = await db.fetch_one(
            "SELECT COUNT(*) as patient_count FROM patient_reengagement_master WHERE organization_id = $1",
            organization_id
        )
        
        return {
            "status": "healthy",
            "organization_id": organization_id,
            "patients_in_system": view_test["patient_count"],
            "views_accessible": True,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Health check failed for {organization_id}: {e}")
        return {
            "status": "unhealthy",
            "organization_id": organization_id,
            "error": str(e),
            "timestamp": datetime.utcnow()
        } 