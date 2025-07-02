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
                engagement_status,
                risk_level,
                risk_score,
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
                treatment_notes,
                lifetime_value_aud,
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
            ORDER BY action_priority ASC, risk_score DESC
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
                    "engagement_status": row['engagement_status'],
                    "risk_level": row['risk_level'],
                    "risk_score": row['risk_score'],
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
                    "treatment_notes": row['treatment_notes'],
                    "lifetime_value_aud": row['lifetime_value_aud'],
                    "action_priority": row['action_priority'],
                    "is_stale": row['is_stale'],
                    "recommended_action": row['recommended_action'],
                    "contact_success_prediction": row['contact_success_prediction'],
                    "attendance_benchmark": row['attendance_benchmark'],
                    "engagement_benchmark": row['engagement_benchmark'],
                    "calculated_at": row['calculated_at'].isoformat() if row['calculated_at'] else None,
                    "view_version": row['view_version']
                })
            
            # Calculate summary statistics
            total_patients = len(patients)
            high_risk_count = len([p for p in patients if p['risk_level'] == 'high'])
            medium_risk_count = len([p for p in patients if p['risk_level'] == 'medium'])
            low_risk_count = len([p for p in patients if p['risk_level'] == 'low'])
            
            dormant_patients = len([p for p in patients if p['engagement_status'] == 'dormant'])
            active_patients = len([p for p in patients if p['engagement_status'] == 'active'])
            stale_patients = len([p for p in patients if p['engagement_status'] == 'stale'])
            
            priority_1_count = len([p for p in patients if p['action_priority'] == 1])
            priority_2_count = len([p for p in patients if p['action_priority'] == 2])
            
            return {
                "organization_id": organization_id,
                "summary": {
                    "total_patients": total_patients,
                    "risk_distribution": {
                        "high": high_risk_count,
                        "medium": medium_risk_count,
                        "low": low_risk_count
                    },
                    "engagement_distribution": {
                        "active": active_patients,
                        "dormant": dormant_patients,
                        "stale": stale_patients
                    },
                    "action_priorities": {
                        "urgent": priority_1_count,
                        "important": priority_2_count,
                        "medium": len([p for p in patients if p['action_priority'] == 3]),
                        "low": len([p for p in patients if p['action_priority'] == 4])
                    }
                },
                "patients": patients,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get risk metrics for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve risk metrics: {str(e)}")

@router.get("/{organization_id}/prioritized")
async def get_prioritized_patients(
    organization_id: str,
    risk_level: str = None,  # 'high', 'medium', 'low'
    engagement_status: str = None,  # 'active', 'dormant', 'stale'
    action_priority: int = None,  # 1, 2, 3, 4
    limit: int = 50,
    include_treatment_notes: bool = True
):
    """
    Get prioritized patient list for reengagement with filtering options
    
    Query Parameters:
    - risk_level: Filter by risk level ('high', 'medium', 'low')
    - engagement_status: Filter by engagement ('active', 'dormant', 'stale')  
    - action_priority: Filter by priority (1=urgent, 2=important, 3=medium, 4=low)
    - limit: Number of results (default: 50, max: 200)
    - include_treatment_notes: Include treatment notes in response (default: true)
    """
    try:
        # Validate limit
        if limit > 200:
            limit = 200
        if limit < 1:
            limit = 50
            
        with db.get_cursor() as cursor:
            # Build WHERE conditions
            where_conditions = ["organization_id = %s"]
            params = [organization_id]
            
            if risk_level:
                where_conditions.append("risk_level = %s")
                params.append(risk_level)
            
            if engagement_status:
                where_conditions.append("engagement_status = %s")
                params.append(engagement_status)
                
            if action_priority is not None:
                where_conditions.append("action_priority = %s")
                params.append(action_priority)
            
            where_clause = " AND ".join(where_conditions)
            
            # Build SELECT fields based on include_treatment_notes
            select_fields = """
                patient_id,
                patient_name,
                email,
                phone,
                is_active,
                engagement_status,
                risk_level,
                risk_score,
                days_since_last_contact,
                days_to_next_appointment,
                last_appointment_date,
                next_appointment_time,
                recent_appointment_count,
                upcoming_appointment_count,
                total_appointment_count,
                missed_appointments_90d,
                attendance_rate_percent,
                lifetime_value_aud,
                action_priority,
                recommended_action,
                contact_success_prediction
            """
            
            if include_treatment_notes:
                select_fields += ",\ntreatment_notes"
            
            # Get prioritized results
            query = f"""
            SELECT {select_fields}
            FROM patient_reengagement_master 
            WHERE {where_clause}
            ORDER BY action_priority ASC, risk_score DESC, days_since_last_contact DESC
            LIMIT %s
            """
            
            cursor.execute(query, params + [limit])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patient_data = {
                    "patient_id": str(row['patient_id']),
                    "patient_name": row['patient_name'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "is_active": row['is_active'],
                    "engagement_status": row['engagement_status'],
                    "risk_level": row['risk_level'],
                    "risk_score": row['risk_score'],
                    "days_since_last_contact": float(row['days_since_last_contact']) if row['days_since_last_contact'] else None,
                    "days_to_next_appointment": float(row['days_to_next_appointment']) if row['days_to_next_appointment'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "missed_appointments_90d": row['missed_appointments_90d'],
                    "attendance_rate_percent": float(row['attendance_rate_percent']) if row['attendance_rate_percent'] else None,
                    "lifetime_value_aud": row['lifetime_value_aud'],
                    "action_priority": row['action_priority'],
                    "recommended_action": row['recommended_action'],
                    "contact_success_prediction": row['contact_success_prediction']
                }
                
                # Add treatment notes if requested
                if include_treatment_notes:
                    patient_data["treatment_notes"] = row['treatment_notes']
                
                patients.append(patient_data)
            
            return {
                "organization_id": organization_id,
                "filters": {
                    "risk_level": risk_level,
                    "engagement_status": engagement_status,
                    "action_priority": action_priority,
                    "limit": limit,
                    "include_treatment_notes": include_treatment_notes
                },
                "patients": patients,
                "result_count": len(patients),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get prioritized patients for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prioritized patients: {str(e)}")

@router.get("/{organization_id}/dashboard-summary")
async def get_reengagement_dashboard_summary(organization_id: str):
    """
    Get summary metrics for the reengagement dashboard
    """
    try:
        with db.get_cursor() as cursor:
            # Get comprehensive summary from the view
            summary_query = """
            SELECT 
                COUNT(*) as total_patients,
                COUNT(*) FILTER (WHERE engagement_status = 'active') as active_patients,
                COUNT(*) FILTER (WHERE engagement_status = 'dormant') as dormant_patients,
                COUNT(*) FILTER (WHERE engagement_status = 'stale') as stale_patients,
                COUNT(*) FILTER (WHERE risk_level = 'high') as high_risk_patients,
                COUNT(*) FILTER (WHERE risk_level = 'medium') as medium_risk_patients,
                COUNT(*) FILTER (WHERE risk_level = 'low') as low_risk_patients,
                COUNT(*) FILTER (WHERE action_priority = 1) as urgent_priority,
                COUNT(*) FILTER (WHERE action_priority = 2) as important_priority,
                AVG(lifetime_value_aud) as avg_lifetime_value,
                AVG(days_since_last_contact) as avg_days_since_contact,
                AVG(attendance_rate_percent) as avg_attendance_rate,
                SUM(lifetime_value_aud) as total_lifetime_value
            FROM patient_reengagement_master 
            WHERE organization_id = %s
            """
            
            cursor.execute(summary_query, [organization_id])
            summary_row = cursor.fetchone()
            
            # Get top priority patients for quick action
            priority_query = """
            SELECT 
                patient_id,
                patient_name,
                email,
                phone,
                engagement_status,
                risk_level,
                action_priority,
                recommended_action,
                days_since_last_contact,
                lifetime_value_aud
            FROM patient_reengagement_master 
            WHERE organization_id = %s
            AND action_priority <= 2
            ORDER BY action_priority ASC, risk_score DESC
            LIMIT 10
            """
            
            cursor.execute(priority_query, [organization_id])
            priority_rows = cursor.fetchall()
            
            priority_patients = []
            for row in priority_rows:
                priority_patients.append({
                    "patient_id": str(row['patient_id']),
                    "patient_name": row['patient_name'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "engagement_status": row['engagement_status'],
                    "risk_level": row['risk_level'],
                    "action_priority": row['action_priority'],
                    "recommended_action": row['recommended_action'],
                    "days_since_last_contact": float(row['days_since_last_contact']) if row['days_since_last_contact'] else None,
                    "lifetime_value_aud": row['lifetime_value_aud']
                })
            
            return {
                "organization_id": organization_id,
                "summary_metrics": {
                    "total_patients": summary_row['total_patients'],
                    "engagement_breakdown": {
                        "active": summary_row['active_patients'],
                        "dormant": summary_row['dormant_patients'],
                        "stale": summary_row['stale_patients']
                    },
                    "risk_breakdown": {
                        "high": summary_row['high_risk_patients'],
                        "medium": summary_row['medium_risk_patients'],
                        "low": summary_row['low_risk_patients']
                    },
                    "action_priorities": {
                        "urgent": summary_row['urgent_priority'],
                        "important": summary_row['important_priority']
                    },
                    "financial_metrics": {
                        "total_lifetime_value_aud": float(summary_row['total_lifetime_value']) if summary_row['total_lifetime_value'] else 0,
                        "avg_lifetime_value_aud": float(summary_row['avg_lifetime_value']) if summary_row['avg_lifetime_value'] else 0
                    },
                    "engagement_metrics": {
                        "avg_days_since_contact": float(summary_row['avg_days_since_contact']) if summary_row['avg_days_since_contact'] else 0,
                        "avg_attendance_rate_percent": float(summary_row['avg_attendance_rate']) if summary_row['avg_attendance_rate'] else 0
                    }
                },
                "priority_patients": priority_patients,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get dashboard summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard summary: {str(e)}")

@router.get("/{organization_id}/patient/{patient_id}/details")
async def get_patient_reengagement_details(organization_id: str, patient_id: str):
    """
    Get detailed reengagement information for a specific patient
    """
    try:
        with db.get_cursor() as cursor:
            # Get full patient details from the reengagement view
            query = """
            SELECT *
            FROM patient_reengagement_master 
            WHERE organization_id = %s AND patient_id = %s
            """
            
            cursor.execute(query, [organization_id, patient_id])
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Patient not found")
            
            patient_details = {
                "patient_id": str(row['patient_id']),
                "patient_name": row['patient_name'],
                "email": row['email'],
                "phone": row['phone'],
                "is_active": row['is_active'],
                "activity_status": row['activity_status'],
                
                # Engagement Analysis
                "engagement_analysis": {
                    "status": row['engagement_status'],
                    "risk_level": row['risk_level'],
                    "risk_score": row['risk_score'],
                    "action_priority": row['action_priority'],
                    "recommended_action": row['recommended_action'],
                    "contact_success_prediction": row['contact_success_prediction']
                },
                
                # Time Metrics
                "time_metrics": {
                    "days_since_last_contact": float(row['days_since_last_contact']) if row['days_since_last_contact'] else None,
                    "days_to_next_appointment": float(row['days_to_next_appointment']) if row['days_to_next_appointment'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "last_communication_date": row['last_communication_date'].isoformat() if row['last_communication_date'] else None
                },
                
                # Appointment History
                "appointment_metrics": {
                    "recent_count": row['recent_appointment_count'],
                    "upcoming_count": row['upcoming_appointment_count'],
                    "total_count": row['total_appointment_count'],
                    "missed_90d": row['missed_appointments_90d'],
                    "scheduled_90d": row['scheduled_appointments_90d'],
                    "attendance_rate_percent": float(row['attendance_rate_percent']) if row['attendance_rate_percent'] else None
                },
                
                # Communication History
                "communication_metrics": {
                    "conversations_90d": row['conversations_90d'],
                    "last_conversation_sentiment": row['last_conversation_sentiment']
                },
                
                # Treatment Information
                "treatment_info": {
                    "notes": row['treatment_notes']
                },
                
                # Financial Metrics
                "financial_metrics": {
                    "lifetime_value_aud": row['lifetime_value_aud']
                },
                
                # Benchmarks
                "benchmarks": {
                    "attendance_benchmark": row['attendance_benchmark'],
                    "engagement_benchmark": row['engagement_benchmark']
                },
                
                # Metadata
                "metadata": {
                    "is_stale": row['is_stale'],
                    "calculated_at": row['calculated_at'].isoformat() if row['calculated_at'] else None,
                    "view_version": row['view_version']
                }
            }
            
            return {
                "organization_id": organization_id,
                "patient": patient_details,
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient details for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient details: {str(e)}") 