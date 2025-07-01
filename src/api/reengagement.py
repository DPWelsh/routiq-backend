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

@router.get("/{organization_id}/risk-metrics")
async def get_risk_metrics(organization_id: str):
    """Get patient risk metrics and reengagement priorities (dashboard pattern - no auth)"""
    try:
        with db.get_cursor() as cursor:
            # Query the patient_reengagement_master view
            query = """
            SELECT 
                organization_id,
                patient_id,
                patient_name,
                email,
                phone,
                is_active,
                activity_status,
                risk_score,
                risk_level,
                days_since_last_contact,
                days_to_next_appointment,
                last_appointment_date,
                next_appointment_time,
                last_communication_date,
                recent_appointment_count,
                upcoming_appointment_count,
                total_appointment_count,
                missed_appointments_90d,
                scheduled_appointments_90d,
                attendance_rate_percent,
                conversations_90d,
                last_conversation_sentiment,
                action_priority,
                is_stale,
                recommended_action,
                contact_success_prediction,
                attendance_benchmark,
                engagement_benchmark,
                calculated_at,
                view_version
            FROM patient_reengagement_master 
            WHERE organization_id = %s
            ORDER BY risk_score DESC, action_priority ASC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            # Format the results
            patients = []
            for row in rows:
                patients.append({
                    "patient_id": str(row['patient_id']),
                    "patient_name": row['patient_name'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "is_active": row['is_active'],
                    "activity_status": row['activity_status'],
                    "risk_score": row['risk_score'],
                    "risk_level": row['risk_level'],
                    "days_since_last_contact": float(row['days_since_last_contact']) if row['days_since_last_contact'] else None,
                    "days_to_next_appointment": float(row['days_to_next_appointment']) if row['days_to_next_appointment'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "last_communication_date": row['last_communication_date'].isoformat() if row['last_communication_date'] else None,
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "missed_appointments_90d": row['missed_appointments_90d'],
                    "scheduled_appointments_90d": row['scheduled_appointments_90d'],
                    "attendance_rate_percent": float(row['attendance_rate_percent']) if row['attendance_rate_percent'] else None,
                    "conversations_90d": row['conversations_90d'],
                    "last_conversation_sentiment": row['last_conversation_sentiment'],
                    "action_priority": row['action_priority'],
                    "is_stale": row['is_stale'],
                    "recommended_action": row['recommended_action'],
                    "contact_success_prediction": row['contact_success_prediction'],
                    "attendance_benchmark": row['attendance_benchmark'],
                    "engagement_benchmark": row['engagement_benchmark']
                })
            
            # Calculate summary statistics
            total_patients = len(patients)
            critical_patients = len([p for p in patients if p['risk_level'] == 'critical'])
            high_risk_patients = len([p for p in patients if p['risk_level'] == 'high'])
            medium_risk_patients = len([p for p in patients if p['risk_level'] == 'medium'])
            low_risk_patients = len([p for p in patients if p['risk_level'] == 'low'])
            stale_risk_patients = len([p for p in patients if p['risk_level'] == 'stale'])
            stale_patients = len([p for p in patients if p['is_stale']])
            
            return {
                "organization_id": organization_id,
                "summary": {
                    "total_patients": total_patients,
                    "risk_distribution": {
                        "critical": critical_patients,
                        "high": high_risk_patients,
                        "medium": medium_risk_patients,
                        "low": low_risk_patients,
                        "stale": stale_risk_patients
                    },
                    "stale_patients": stale_patients,
                    "avg_risk_score": round(sum(p['risk_score'] for p in patients) / total_patients, 1) if total_patients > 0 else 0
                },
                "patients": patients,
                "view_version": rows[0]['view_version'] if rows else None,
                "calculated_at": rows[0]['calculated_at'].isoformat() if rows else None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get risk metrics for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve risk metrics: {str(e)}") 