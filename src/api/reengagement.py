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
            
            # Convert row to dict
            patient_details = dict(row)
            
            return {
                "patient_id": patient_id,
                "organization_id": organization_id,
                "patient_details": patient_details,
                "generated_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching patient reengagement details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{organization_id}/performance")
async def get_reengagement_performance_metrics(
    organization_id: str,
    timeframe: str = "last_30_days"  # last_7_days, last_30_days, last_90_days, last_6_months
):
    """
    Get reengagement performance metrics and trends over time
    
    Query Parameters:
    - timeframe: Time period for metrics ('last_7_days', 'last_30_days', 'last_90_days', 'last_6_months')
    """
    try:
        # Map timeframe to days
        timeframe_days = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90,
            "last_6_months": 180
        }
        
        days = timeframe_days.get(timeframe, 30)  # Default to 30 days
        
        with db.get_cursor() as cursor:
            # Get performance metrics from reengagement view
            performance_query = """
            SELECT 
                COUNT(*) as total_patients,
                COUNT(*) FILTER (WHERE engagement_status = 'active') as currently_active,
                COUNT(*) FILTER (WHERE engagement_status = 'dormant') as currently_dormant,
                COUNT(*) FILTER (WHERE engagement_status = 'stale') as currently_stale,
                COUNT(*) FILTER (WHERE risk_level = 'high') as high_risk,
                COUNT(*) FILTER (WHERE risk_level = 'critical') as critical_risk,
                COUNT(*) FILTER (WHERE action_priority = 1) as urgent_actions,
                COUNT(*) FILTER (WHERE action_priority = 2) as important_actions,
                AVG(CASE contact_success_prediction
                    WHEN 'very_high' THEN 5
                    WHEN 'high' THEN 4
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 2
                    WHEN 'very_low' THEN 1
                    ELSE 3
                END) as avg_contact_success_score,
                AVG(attendance_rate_percent) as avg_attendance_rate,
                AVG(days_since_last_contact) as avg_days_since_contact,
                COUNT(*) FILTER (WHERE days_since_last_contact <= %s) as contacted_in_timeframe,
                COUNT(*) FILTER (WHERE next_appointment_time >= NOW() AND next_appointment_time <= NOW() + make_interval(days => %s)) as upcoming_appointments,
                SUM(lifetime_value_aud) as total_lifetime_value,
                AVG(lifetime_value_aud) as avg_lifetime_value,
                COUNT(*) FILTER (WHERE is_stale = true) as stale_patients,
                COUNT(*) FILTER (WHERE missed_appointments_90d > 0) as patients_with_missed_appts,
                COUNT(*) FILTER (WHERE contact_success_prediction = 'very_high') as very_high_success_prediction,
                COUNT(*) FILTER (WHERE contact_success_prediction = 'high') as high_success_prediction,
                COUNT(*) FILTER (WHERE attendance_rate_percent >= 80) as high_attendance_patients,
                COUNT(*) FILTER (WHERE attendance_rate_percent < 60) as low_attendance_patients
            FROM patient_reengagement_master 
            WHERE organization_id = %s
            """
            
            cursor.execute(performance_query, [days, days, organization_id])
            perf_row = cursor.fetchone()
            
            # Get engagement trend (simulated - you might want to track this over time)
            trend_query = """
            SELECT 
                engagement_status,
                risk_level,
                COUNT(*) as count,
                AVG(lifetime_value_aud) as avg_value
            FROM patient_reengagement_master 
            WHERE organization_id = %s
            GROUP BY engagement_status, risk_level
            ORDER BY engagement_status, risk_level
            """
            
            cursor.execute(trend_query, [organization_id])
            trend_rows = cursor.fetchall()
            
            # Calculate performance metrics
            total_patients = perf_row['total_patients'] or 0
            contacted_in_timeframe = perf_row['contacted_in_timeframe'] or 0
            
            engagement_rate = (contacted_in_timeframe / total_patients * 100) if total_patients > 0 else 0
            reengagement_opportunity = perf_row['currently_dormant'] + perf_row['currently_stale']
            high_priority_count = perf_row['urgent_actions'] + perf_row['important_actions']
            
            # Build trend breakdown
            engagement_trends = {}
            for row in trend_rows:
                status = row['engagement_status']
                if status not in engagement_trends:
                    engagement_trends[status] = {
                        "total_count": 0,
                        "risk_breakdown": {},
                        "avg_value": 0
                    }
                
                engagement_trends[status]["total_count"] += row['count']
                engagement_trends[status]["risk_breakdown"][row['risk_level']] = row['count']
                engagement_trends[status]["avg_value"] = float(row['avg_value']) if row['avg_value'] else 0
            
            return {
                "organization_id": organization_id,
                "timeframe": timeframe,
                "timeframe_days": days,
                "performance_metrics": {
                    "total_patients": total_patients,
                    "engagement_health": {
                        "currently_active": perf_row['currently_active'],
                        "currently_dormant": perf_row['currently_dormant'],
                        "currently_stale": perf_row['currently_stale'],
                        "engagement_rate_percent": round(engagement_rate, 2)
                    },
                    "risk_assessment": {
                        "high_risk": perf_row['high_risk'],
                        "critical_risk": perf_row['critical_risk'],
                        "urgent_actions_needed": perf_row['urgent_actions'],
                        "important_actions_needed": perf_row['important_actions'],
                        "total_high_priority": high_priority_count
                    },
                    "reengagement_opportunities": {
                        "dormant_patients": perf_row['currently_dormant'],
                        "stale_patients": perf_row['currently_stale'],
                        "total_opportunity": reengagement_opportunity,
                        "potential_value_aud": 0  # Could calculate based on avg values
                    },
                    "contact_metrics": {
                        "avg_contact_success_score": round(float(perf_row['avg_contact_success_score']) if perf_row['avg_contact_success_score'] else 0, 2),
                        "avg_days_since_contact": round(float(perf_row['avg_days_since_contact']) if perf_row['avg_days_since_contact'] else 0, 1),
                        "contacted_in_timeframe": contacted_in_timeframe,
                        "contact_rate_percent": round((contacted_in_timeframe / total_patients * 100) if total_patients > 0 else 0, 2),
                        "success_prediction_breakdown": {
                            "very_high": perf_row['very_high_success_prediction'],
                            "high": perf_row['high_success_prediction'],
                            "others": total_patients - (perf_row['very_high_success_prediction'] + perf_row['high_success_prediction'])
                        }
                    },
                    "appointment_metrics": {
                        "upcoming_appointments": perf_row['upcoming_appointments'],
                        "avg_attendance_rate": round(float(perf_row['avg_attendance_rate']) if perf_row['avg_attendance_rate'] else 0, 2),
                        "patients_with_missed_appointments": perf_row['patients_with_missed_appts'],
                        "attendance_breakdown": {
                            "high_attendance": perf_row['high_attendance_patients'],
                            "low_attendance": perf_row['low_attendance_patients'],
                            "medium_attendance": total_patients - (perf_row['high_attendance_patients'] + perf_row['low_attendance_patients'])
                        }
                    },
                    "financial_metrics": {
                        "total_lifetime_value_aud": float(perf_row['total_lifetime_value']) if perf_row['total_lifetime_value'] else 0,
                        "avg_lifetime_value_aud": round(float(perf_row['avg_lifetime_value']) if perf_row['avg_lifetime_value'] else 0, 2)
                    }
                },
                "engagement_trends": engagement_trends,
                "recommendations": {
                    "focus_areas": [],
                    "immediate_actions": high_priority_count,
                    "reengagement_potential": reengagement_opportunity
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance metrics for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}")

# FRONTEND COMPATIBILITY: Alias endpoint for incorrect frontend path
@router.get("/{organization_id}/patients/prioritized")
async def get_prioritized_patients_alias(
    organization_id: str,
    risk_level: str = None,
    engagement_status: str = None,
    action_priority: int = None,
    limit: int = 50,
    include_treatment_notes: bool = True
):
    """
    ALIAS: Frontend compatibility endpoint - redirects to correct /prioritized endpoint
    
    NOTE: Frontend should update to use /{organization_id}/prioritized directly
    This endpoint maintains backward compatibility while frontend is updated
    """
    logger.warning(f"Frontend using deprecated path /patients/prioritized - should use /prioritized")
    
    # Call the correct endpoint function directly
    return await get_prioritized_patients(
        organization_id=organization_id,
        risk_level=risk_level,
        engagement_status=engagement_status,
        action_priority=action_priority,
        limit=limit,
        include_treatment_notes=include_treatment_notes
    )

# Patient Conversation Profile Endpoints
@router.get("/{organization_id}/patient-profiles")
async def get_patient_conversation_profiles(
    organization_id: str, 
    limit: int = 50, 
    offset: int = 0,
    search: str = None,
    engagement_level: str = None,
    churn_risk: str = None,
    action_priority: int = None
):
    """
    Get patient conversation profiles for the conversations page
    Supports filtering by engagement level, churn risk, and action priority
    """
    try:
        with db.get_cursor() as cursor:
            # Build WHERE conditions
            conditions = ["organization_id = %s"]
            params = [organization_id]
            
            # Add search filter
            if search:
                conditions.append("(patient_name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            # Add engagement level filter
            if engagement_level:
                conditions.append("engagement_level = %s")
                params.append(engagement_level)
            
            # Add churn risk filter
            if churn_risk:
                conditions.append("churn_risk = %s")
                params.append(churn_risk)
            
            # Add action priority filter
            if action_priority:
                conditions.append("action_priority = %s")
                params.append(action_priority)
            
            where_clause = " AND ".join(conditions)
            
            # Get patient profiles
            query = f"""
            SELECT 
                patient_id,
                organization_id,
                patient_name,
                email,
                phone,
                is_active,
                activity_status,
                -- Appointment info
                total_appointment_count,
                next_appointment_time,
                next_appointment_type,
                primary_appointment_type,
                days_since_last_appointment,
                days_until_next_appointment,
                -- Conversation metrics
                COALESCE(total_conversations, 0) as total_conversations,
                COALESCE(active_conversations, 0) as active_conversations,
                last_conversation_date,
                days_since_last_conversation,
                overall_sentiment,
                COALESCE(escalation_count, 0) as escalation_count,
                -- Message metrics
                COALESCE(total_messages, 0) as total_messages,
                last_message_date,
                last_message_sentiment,
                days_since_last_message,
                -- Outreach metrics
                COALESCE(total_outreach_attempts, 0) as total_outreach_attempts,
                last_outreach_date,
                last_outreach_method,
                last_outreach_outcome,
                COALESCE(outreach_success_rate, 0) as outreach_success_rate,
                -- Engagement & Risk
                engagement_level,
                churn_risk,
                estimated_lifetime_value,
                contact_success_prediction,
                action_priority,
                -- Treatment info
                treatment_notes,
                treatment_summary,
                last_treatment_note,
                -- Timestamps
                patient_created_at,
                view_generated_at
            FROM patient_conversation_profile
            WHERE {where_clause}
            ORDER BY action_priority ASC, last_conversation_date DESC NULLS LAST
            LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get total count for pagination
            count_query = f"SELECT COUNT(*) FROM patient_conversation_profile WHERE {where_clause}"
            cursor.execute(count_query, params[:-2])  # Exclude limit/offset params
            total_count = cursor.fetchone()[0]
            
            # Convert rows to list of dicts
            profiles = []
            for row in rows:
                profile = dict(row)
                # Format dates
                if profile.get('last_conversation_date'):
                    profile['last_conversation_date'] = profile['last_conversation_date'].isoformat()
                if profile.get('last_message_date'):
                    profile['last_message_date'] = profile['last_message_date'].isoformat()
                if profile.get('last_outreach_date'):
                    profile['last_outreach_date'] = profile['last_outreach_date'].isoformat()
                if profile.get('next_appointment_time'):
                    profile['next_appointment_time'] = profile['next_appointment_time'].isoformat()
                if profile.get('patient_created_at'):
                    profile['patient_created_at'] = profile['patient_created_at'].isoformat()
                if profile.get('view_generated_at'):
                    profile['view_generated_at'] = profile['view_generated_at'].isoformat()
                
                profiles.append(profile)
            
            return {
                "organization_id": organization_id,
                "patient_profiles": profiles,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "filters": {
                    "search": search,
                    "engagement_level": engagement_level,
                    "churn_risk": churn_risk,
                    "action_priority": action_priority
                },
                "generated_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching patient conversation profiles: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{organization_id}/patient-profiles/{patient_id}")
async def get_patient_conversation_profile(organization_id: str, patient_id: str):
    """
    Get detailed conversation profile for a specific patient
    """
    try:
        with db.get_cursor() as cursor:
            # Get full patient profile from the view
            query = """
            SELECT *
            FROM patient_conversation_profile
            WHERE organization_id = %s AND patient_id = %s
            """
            
            cursor.execute(query, [organization_id, patient_id])
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Patient profile not found")
            
            # Convert row to dict
            profile = dict(row)
            
            # Format dates
            date_fields = [
                'first_appointment_date', 'last_appointment_date', 'next_appointment_time',
                'next_appointment_date', 'last_conversation_date', 'last_message_date',
                'last_outreach_date', 'patient_created_at', 'patient_updated_at',
                'last_synced_at', 'view_generated_at'
            ]
            
            for field in date_fields:
                if profile.get(field):
                    profile[field] = profile[field].isoformat()
            
            return {
                "patient_id": patient_id,
                "organization_id": organization_id,
                "profile": profile,
                "generated_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching patient conversation profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{organization_id}/patient-profiles/debug")
async def debug_patient_conversation_profile(organization_id: str):
    """
    Debug endpoint to test patient conversation profile view
    """
    try:
        with db.get_cursor() as cursor:
            # Test basic query
            query = """
            SELECT 
                patient_id,
                organization_id,
                patient_name,
                email,
                phone
            FROM patient_conversation_profile
            WHERE organization_id = %s
            LIMIT 5
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            profiles = []
            for row in rows:
                profiles.append({
                    "patient_id": str(row[0]),
                    "organization_id": row[1],
                    "patient_name": row[2],
                    "email": row[3],
                    "phone": row[4]
                })
            
            return {
                "organization_id": organization_id,
                "debug_profiles": profiles,
                "count": len(profiles),
                "generated_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {
            "error": str(e),
            "organization_id": organization_id,
            "generated_at": datetime.now().isoformat()
        }

@router.get("/{organization_id}/patient-profiles/summary")
async def get_patient_profiles_summary(organization_id: str):
    """
    Get summary statistics for patient conversation profiles
    """
    try:
        with db.get_cursor() as cursor:
            # Get summary statistics
            query = """
            SELECT 
                COUNT(*) as total_patients,
                COUNT(*) FILTER (WHERE engagement_level = 'highly_engaged') as highly_engaged,
                COUNT(*) FILTER (WHERE engagement_level = 'moderately_engaged') as moderately_engaged,
                COUNT(*) FILTER (WHERE engagement_level = 'low_engagement') as low_engagement,
                COUNT(*) FILTER (WHERE engagement_level = 'disengaged') as disengaged,
                COUNT(*) FILTER (WHERE churn_risk = 'critical') as critical_risk,
                COUNT(*) FILTER (WHERE churn_risk = 'high') as high_risk,
                COUNT(*) FILTER (WHERE churn_risk = 'medium') as medium_risk,
                COUNT(*) FILTER (WHERE churn_risk = 'low') as low_risk,
                COUNT(*) FILTER (WHERE action_priority = 1) as priority_1,
                COUNT(*) FILTER (WHERE action_priority = 2) as priority_2,
                COUNT(*) FILTER (WHERE action_priority = 3) as priority_3,
                COUNT(*) FILTER (WHERE action_priority = 4) as priority_4,
                COUNT(*) FILTER (WHERE action_priority = 5) as priority_5,
                ROUND(AVG(estimated_lifetime_value), 2) as avg_lifetime_value,
                COUNT(*) FILTER (WHERE COALESCE(total_conversations, 0) > 0) as patients_with_conversations,
                COUNT(*) FILTER (WHERE COALESCE(escalation_count, 0) > 0) as patients_with_escalations,
                ROUND(AVG(COALESCE(outreach_success_rate, 0)), 2) as avg_outreach_success_rate
            FROM patient_conversation_profile
            WHERE organization_id = %s
            """
            
            cursor.execute(query, [organization_id])
            row = cursor.fetchone()
            
            summary = dict(row) if row else {}
            
            return {
                "organization_id": organization_id,
                "summary": summary,
                "generated_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching patient profiles summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 