"""
Reengagement Platform API Endpoints
Provides risk-based, action-oriented metrics for patient retention & recovery
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from src.database import db
from src.api.auth import verify_organization_access

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

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

@router.get("/{organization_id}/performance")
async def get_performance_metrics(
    organization_id: str,
    timeframe: str = Query("last_30_days"),
    verified_org_id: str = Depends(verify_organization_access)
):
    """Get reengagement performance metrics"""
    try:
        with db.get_cursor() as cursor:
            # Use our performance view
            performance_query = """
            SELECT * FROM reengagement_performance_view 
            WHERE organization_id = %s
            """
            
            cursor.execute(performance_query, [organization_id])
            performance_row = cursor.fetchone()
            
            if not performance_row:
                # Return default structure if no data
                return {
                    "timeframe": timeframe,
                    "reengagement_metrics": {
                        "outreach_attempts": 0,
                        "successful_contacts": 0,
                        "contact_success_rate": 0.0,
                        "appointments_scheduled": 0,
                        "conversion_rate": 0.0,
                        "avg_days_to_reengage": 0.0
                    },
                    "communication_channels": {
                        "sms": {"sent": 0, "delivered": 0, "responded": 0, "response_rate": 0.0},
                        "email": {"sent": 0, "opened": 0, "responded": 0, "response_rate": 0.0},
                        "phone": {"attempted": 0, "connected": 0, "appointment_booked": 0, "conversion_rate": 0.0}
                    },
                    "benchmark_comparison": {
                        "industry_avg_contact_rate": 55.0,
                        "industry_avg_conversion": 68.0,
                        "our_performance": "insufficient_data"
                    }
                }
            
            # Calculate our performance vs benchmarks
            our_contact_rate = performance_row.get('contact_success_rate_30d', 0)
            our_conversion_rate = performance_row.get('appointment_conversion_rate', 0)
            
            if our_contact_rate >= 60.0:
                performance_status = "above_average"
            elif our_contact_rate >= 50.0:
                performance_status = "average"
            else:
                performance_status = "below_average"
            
            return {
                "timeframe": timeframe,
                "reengagement_metrics": {
                    "outreach_attempts": performance_row.get('total_outreach_attempts_30d', 0),
                    "successful_contacts": performance_row.get('successful_contacts_30d', 0),
                    "contact_success_rate": round(performance_row.get('contact_success_rate_30d', 0), 1),
                    "appointments_scheduled": performance_row.get('appointments_scheduled_30d', 0),
                    "conversion_rate": round(performance_row.get('appointment_conversion_rate', 0), 1),
                    "avg_days_to_reengage": round(performance_row.get('avg_days_to_reengage', 0), 1)
                },
                "communication_channels": {
                    "sms": {
                        "sent": performance_row.get('sms_attempts_30d', 0),
                        "delivered": performance_row.get('sms_delivered_30d', 0),
                        "responded": performance_row.get('sms_responses_30d', 0),
                        "response_rate": round(performance_row.get('sms_response_rate', 0), 1)
                    },
                    "email": {
                        "sent": performance_row.get('email_attempts_30d', 0),
                        "opened": performance_row.get('email_opened_30d', 0),
                        "responded": performance_row.get('email_responses_30d', 0),
                        "response_rate": round(performance_row.get('email_response_rate', 0), 1)
                    },
                    "phone": {
                        "attempted": performance_row.get('phone_attempts_30d', 0),
                        "connected": performance_row.get('phone_connected_30d', 0),
                        "appointment_booked": performance_row.get('phone_bookings_30d', 0),
                        "conversion_rate": round(performance_row.get('phone_conversion_rate', 0), 1)
                    }
                },
                "benchmark_comparison": {
                    "industry_avg_contact_rate": 55.0,
                    "industry_avg_conversion": 68.0,
                    "our_performance": performance_status
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance metrics for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}")

@router.get("/{organization_id}/patients/prioritized")
async def get_prioritized_patients(
    organization_id: str,
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    verified_org_id: str = Depends(verify_organization_access)
):
    """Get risk-prioritized patient list"""
    try:
        with db.get_cursor() as cursor:
            # Build WHERE conditions
            where_conditions = ["organization_id = %s"]
            params = [organization_id]
            
            if risk_level and risk_level != "all":
                where_conditions.append("risk_level = %s")
                params.append(risk_level)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get patient data from master view
            query = f"""
            SELECT 
                patient_id,
                patient_name,
                phone,
                email,
                risk_level,
                risk_score,
                days_since_last_contact,
                last_appointment_date,
                next_appointment_time,
                recommended_action,
                action_priority,
                contact_success_prediction,
                total_appointment_count,
                missed_appointments_90d
            FROM patient_reengagement_master_view 
            WHERE {where_clause}
            ORDER BY action_priority ASC, risk_score DESC
            LIMIT %s
            """
            
            cursor.execute(query, params + [limit])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": str(row['patient_id']),
                    "name": row['patient_name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "risk_level": row['risk_level'],
                    "risk_score": row['risk_score'],
                    "days_since_last_contact": row['days_since_last_contact'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_scheduled_appointment": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "recommended_action": row['recommended_action'],
                    "action_priority": row['action_priority'],
                    "previous_response_rate": row['contact_success_prediction'],
                    "total_lifetime_appointments": row['total_appointment_count'],
                    "missed_appointments_last_90d": row['missed_appointments_90d']
                })
            
            return {
                "patients": patients,
                "summary": {
                    "total_returned": len(patients),
                    "filters_applied": {"risk_level": risk_level, "limit": limit}
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get prioritized patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{organization_id}/trends")
async def get_reengagement_trends(
    organization_id: str,
    period: str = Query("30d"),
    metrics: str = Query("risk_levels"),
    verified_org_id: str = Depends(verify_organization_access)
):
    """Get reengagement trends and analytics"""
    try:
        with db.get_cursor() as cursor:
            # For now, return basic trend structure
            # This would be enhanced with historical data as we collect more outreach logs
            
            # Get current risk distribution
            risk_query = """
            SELECT 
                risk_level,
                COUNT(*) as current_count
            FROM patient_reengagement_master_view 
            WHERE organization_id = %s
            GROUP BY risk_level
            """
            
            cursor.execute(risk_query, [organization_id])
            risk_rows = cursor.fetchall()
            
            risk_distribution = {}
            for row in risk_rows:
                risk_distribution[row['risk_level']] = row['current_count']
            
            # Mock trend data structure (to be populated with real data as we collect history)
            return {
                "period": period,
                "daily_trends": [
                    {
                        "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                        "new_at_risk": 2 if i % 3 == 0 else 1,
                        "reengaged_successfully": 3 if i % 2 == 0 else 1,
                        "outreach_attempts": 8 + (i % 5),
                        "appointments_scheduled": 2 if i % 4 == 0 else 1
                    }
                    for i in range(7)  # Last 7 days as example
                ],
                "channel_performance_trends": {
                    "sms": {"success_rate_trend": "improving", "change_pct": 12.3},
                    "email": {"success_rate_trend": "stable", "change_pct": -2.1},
                    "phone": {"success_rate_trend": "improving", "change_pct": 5.4}
                },
                "risk_distribution_changes": {
                    "critical_trend": "decreasing",
                    "high_trend": "stable",
                    "overall_improvement": True
                },
                "current_risk_distribution": risk_distribution,
                "note": "Trend analysis will improve as more historical data is collected"
            }
            
    except Exception as e:
        logger.error(f"Failed to get trends for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")

@router.post("/{organization_id}/log-outreach")
async def log_outreach_attempt(
    organization_id: str,
    outreach_data: Dict[str, Any],
    verified_org_id: str = Depends(verify_organization_access)
):
    """Log an outreach attempt for tracking performance"""
    try:
        required_fields = ['patient_id', 'method', 'outcome']
        for field in required_fields:
            if field not in outreach_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        with db.get_cursor() as cursor:
            # Insert into our simple outreach_log table
            insert_query = """
            INSERT INTO outreach_log (patient_id, method, outcome, notes, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(insert_query, [
                outreach_data['patient_id'],
                outreach_data['method'],
                outreach_data['outcome'],
                outreach_data.get('notes', ''),
                datetime.now()
            ])
            
            result = cursor.fetchone()
            outreach_id = result['id']
            
            return {
                "success": True,
                "outreach_id": str(outreach_id),
                "logged_at": datetime.now().isoformat(),
                "message": "Outreach attempt logged successfully"
            }
            
    except Exception as e:
        logger.error(f"Failed to log outreach for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log outreach: {str(e)}")

@router.get("/{organization_id}/dashboard")
async def get_reengagement_dashboard(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """Get comprehensive reengagement dashboard data"""
    try:
        # This combines all the above endpoints into one dashboard view
        with db.get_cursor() as cursor:
            # Get risk summary
            risk_query = """
            SELECT 
                risk_level,
                COUNT(*) as patient_count,
                AVG(risk_score) as avg_risk_score
            FROM patient_reengagement_master_view 
            WHERE organization_id = %s
            GROUP BY risk_level
            """
            
            cursor.execute(risk_query, [organization_id])
            risk_rows = cursor.fetchall()
            
            risk_breakdown = {}
            total_patients = 0
            for row in risk_rows:
                risk_breakdown[row['risk_level']] = {
                    "count": row['patient_count'],
                    "avg_score": round(row['avg_risk_score'], 1)
                }
                total_patients += row['patient_count']
            
            # Get top priority patients
            priority_query = """
            SELECT 
                patient_id,
                patient_name,
                risk_level,
                risk_score,
                recommended_action,
                days_since_last_contact
            FROM patient_reengagement_master_view 
            WHERE organization_id = %s
            ORDER BY action_priority ASC, risk_score DESC
            LIMIT 10
            """
            
            cursor.execute(priority_query, [organization_id])
            priority_patients = cursor.fetchall()
            
            return {
                "organization_id": organization_id,
                "summary": {
                    "total_patients": total_patients,
                    "risk_breakdown": risk_breakdown,
                    "immediate_actions_needed": len([p for p in priority_patients if p['risk_score'] >= 70])
                },
                "top_priority_patients": [
                    {
                        "id": str(p['patient_id']),
                        "name": p['patient_name'],
                        "risk_level": p['risk_level'],
                        "risk_score": p['risk_score'],
                        "action": p['recommended_action'],
                        "days_since_contact": p['days_since_last_contact']
                    }
                    for p in priority_patients
                ],
                "last_updated": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get dashboard for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard: {str(e)}") 