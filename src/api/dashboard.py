"""
Dashboard API endpoints
Provides data for the sync dashboard frontend
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from src.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

# Response Models
class DashboardSummary(BaseModel):
    organization_id: str
    total_patients: int
    active_patients: int
    patients_with_upcoming: int
    patients_with_recent: int
    total_upcoming_appointments: int
    total_recent_appointments: int
    total_all_appointments: int
    avg_upcoming_per_patient: float
    avg_recent_per_patient: float
    avg_total_per_patient: float
    engagement_rate: float  # Percentage of patients with upcoming OR recent appointments
    last_sync_time: Optional[datetime]
    synced_patients: int
    sync_percentage: float
    integration_status: str
    activity_status: str
    generated_at: datetime

class BookingMetrics(BaseModel):
    total_bookings: int
    period_comparison: float  # percentage change vs previous period
    bookings_via_ai: int

class PatientMetrics(BaseModel):
    total_patients: int
    active_patients: int
    new_patients: int

class FinancialMetrics(BaseModel):
    total_revenue: float
    avg_revenue_per_patient: float

class AutomationMetrics(BaseModel):
    total_roi: float  # percentage (e.g., 284 for 284%)
    automation_bookings: int
    efficiency_score: float

class DashboardAnalytics(BaseModel):
    booking_metrics: BookingMetrics
    patient_metrics: PatientMetrics
    financial_metrics: FinancialMetrics
    automation_metrics: AutomationMetrics
    timeframe: str
    last_updated: str

class RecentActivity(BaseModel):
    id: str
    source_system: str
    operation_type: str
    status: str
    records_processed: int
    records_success: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime]
    activity_type: str
    description: str
    minutes_ago: float

class DashboardResponse(BaseModel):
    success: bool
    organization_id: str
    summary: DashboardSummary
    recent_activity: List[RecentActivity]
    timestamp: str

@router.get("/{organization_id}/analytics", response_model=DashboardAnalytics)
async def get_dashboard_analytics(
    organization_id: str,
    timeframe: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y")
):
    """
    Get dashboard analytics with exact frontend schema
    
    Frontend integration endpoint - matches Phase 1 requirements exactly
    """
    try:
        # Map timeframe to days
        timeframe_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }
        
        days = timeframe_days.get(timeframe, 30)
        
        with db.get_cursor() as cursor:
            # Get current period data
            current_period_query = """
            SELECT 
                -- Patient metrics
                COUNT(*) as total_patients,
                COUNT(*) FILTER (WHERE is_active = true) as active_patients,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL %s) as new_patients,
                
                -- Booking metrics
                SUM(total_appointment_count) as total_bookings,
                SUM(CASE WHEN upcoming_appointment_count > 0 THEN 1 ELSE 0 END) as patients_with_upcoming,
                
                -- Financial metrics
                SUM(estimated_lifetime_value) as total_revenue,
                AVG(estimated_lifetime_value) as avg_revenue_per_patient,
                
                -- Engagement metrics
                COUNT(*) FILTER (WHERE is_active = true) * 100.0 / COUNT(*) as engagement_rate
            FROM patient_conversation_profile 
            WHERE organization_id = %s
            """
            
            cursor.execute(current_period_query, [f"{days} days", organization_id])
            current_data = cursor.fetchone()
            
            # Get previous period data for comparison
            previous_period_query = """
            SELECT 
                SUM(total_appointment_count) as prev_total_bookings,
                COUNT(*) FILTER (WHERE is_active = true) as prev_active_patients
            FROM patient_conversation_profile 
            WHERE organization_id = %s
            AND created_at < NOW() - INTERVAL %s
            AND created_at >= NOW() - INTERVAL %s
            """
            
            cursor.execute(previous_period_query, [organization_id, f"{days} days", f"{days * 2} days"])
            previous_data = cursor.fetchone()
            
            # Calculate period comparison
            current_bookings = current_data['total_bookings'] or 0
            previous_bookings = previous_data['prev_total_bookings'] or 0
            
            if previous_bookings > 0:
                period_comparison = ((current_bookings - previous_bookings) / previous_bookings) * 100
            else:
                period_comparison = 0.0
            
            # Get automation metrics (placeholder for now)
            automation_query = """
            SELECT 
                COUNT(*) FILTER (WHERE contact_success_prediction = 'very_high') as high_success_predictions,
                AVG(CASE 
                    WHEN contact_success_prediction = 'very_high' THEN 100
                    WHEN contact_success_prediction = 'high' THEN 80
                    WHEN contact_success_prediction = 'medium' THEN 60
                    WHEN contact_success_prediction = 'low' THEN 40
                    ELSE 20
                END) as efficiency_score
            FROM patient_conversation_profile 
            WHERE organization_id = %s
            """
            
            cursor.execute(automation_query, [organization_id])
            automation_data = cursor.fetchone()
            
            # Calculate ROI (simplified - revenue vs engagement cost)
            total_revenue = current_data['total_revenue'] or 0
            total_patients = current_data['total_patients'] or 1
            estimated_cost = total_patients * 50  # Estimated $50 per patient engagement cost
            roi = ((total_revenue - estimated_cost) / estimated_cost) * 100 if estimated_cost > 0 else 0
            
            # Build response
            analytics = DashboardAnalytics(
                booking_metrics=BookingMetrics(
                    total_bookings=current_bookings,
                    period_comparison=round(period_comparison, 2),
                    bookings_via_ai=0  # Placeholder - no AI booking tracking yet
                ),
                patient_metrics=PatientMetrics(
                    total_patients=current_data['total_patients'] or 0,
                    active_patients=current_data['active_patients'] or 0,
                    new_patients=current_data['new_patients'] or 0
                ),
                financial_metrics=FinancialMetrics(
                    total_revenue=total_revenue,
                    avg_revenue_per_patient=current_data['avg_revenue_per_patient'] or 0
                ),
                automation_metrics=AutomationMetrics(
                    total_roi=round(roi, 2),
                    automation_bookings=0,  # Placeholder - no automated booking tracking yet
                    efficiency_score=round(automation_data['efficiency_score'] or 0, 2)
                ),
                timeframe=timeframe,
                last_updated=datetime.now().isoformat()
            )
            
            return analytics
            
    except Exception as e:
        logger.error(f"Failed to get dashboard analytics for {organization_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard analytics: {str(e)}"
        )

@router.get("/{organization_id}/charts")
async def get_dashboard_charts(
    organization_id: str,
    timeframe: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y")
):
    """
    Get dashboard charts data for visualizations
    
    Frontend enhancement endpoint - time-series data for charts
    """
    try:
        # Map timeframe to days and intervals
        timeframe_config = {
            "7d": {"days": 7, "interval": "1 day"},
            "30d": {"days": 30, "interval": "1 day"},
            "90d": {"days": 90, "interval": "3 days"},
            "1y": {"days": 365, "interval": "1 week"}
        }
        
        config = timeframe_config.get(timeframe, {"days": 30, "interval": "1 day"})
        
        with db.get_cursor() as cursor:
            # Get booking trends
            booking_trends_query = """
            SELECT 
                DATE_TRUNC('day', created_at) as date,
                COUNT(*) as bookings,
                SUM(estimated_lifetime_value) as revenue
            FROM patient_conversation_profile 
            WHERE organization_id = %s
            AND created_at >= NOW() - INTERVAL %s
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY date
            """
            
            cursor.execute(booking_trends_query, [organization_id, f"{config['days']} days"])
            booking_trends = cursor.fetchall()
            
            # Get patient satisfaction trend (placeholder)
            satisfaction_trends_query = """
            SELECT 
                DATE_TRUNC('day', created_at) as date,
                3.8 as satisfaction_score,  -- Placeholder average
                COUNT(*) as response_count
            FROM patient_conversation_profile 
            WHERE organization_id = %s
            AND created_at >= NOW() - INTERVAL %s
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY date
            """
            
            cursor.execute(satisfaction_trends_query, [organization_id, f"{config['days']} days"])
            satisfaction_trends = cursor.fetchall()
            
            # Get automation performance
            automation_performance_query = """
            SELECT 
                DATE_TRUNC('day', created_at) as date,
                0 as ai_bookings,  -- Placeholder
                COUNT(*) as total_bookings,
                AVG(CASE 
                    WHEN contact_success_prediction = 'very_high' THEN 100
                    WHEN contact_success_prediction = 'high' THEN 80
                    WHEN contact_success_prediction = 'medium' THEN 60
                    WHEN contact_success_prediction = 'low' THEN 40
                    ELSE 20
                END) as efficiency
            FROM patient_conversation_profile 
            WHERE organization_id = %s
            AND created_at >= NOW() - INTERVAL %s
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY date
            """
            
            cursor.execute(automation_performance_query, [organization_id, f"{config['days']} days"])
            automation_performance = cursor.fetchall()
            
            return {
                "booking_trends": [
                    {
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "bookings": row['bookings'],
                        "revenue": float(row['revenue'] or 0)
                    }
                    for row in booking_trends
                ],
                "patient_satisfaction_trend": [
                    {
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "satisfaction_score": row['satisfaction_score'],
                        "response_count": row['response_count']
                    }
                    for row in satisfaction_trends
                ],
                "automation_performance": [
                    {
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "ai_bookings": row['ai_bookings'],
                        "total_bookings": row['total_bookings'],
                        "efficiency": round(row['efficiency'] or 0, 2)
                    }
                    for row in automation_performance
                ]
            }
            
    except Exception as e:
        logger.error(f"Failed to get dashboard charts for {organization_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard charts: {str(e)}"
        )

@router.get("/{organization_id}", response_model=DashboardResponse)
async def get_dashboard_data(organization_id: str, activity_limit: int = 10):
    """
    Get comprehensive dashboard data for an organization
    
    Returns:
    - Patient counts and statistics
    - Appointment data
    - Sync status
    - Recent activity log
    """
    try:
        with db.get_cursor() as cursor:
            # Get dashboard summary
            summary_query = """
            SELECT * FROM dashboard_summary 
            WHERE organization_id = %s
            """
            cursor.execute(summary_query, [organization_id])
            summary_result = cursor.fetchone()
            
            if not summary_result:
                # Return empty dashboard if no data
                summary_result = {
                    'organization_id': organization_id,
                    'total_patients': 0,
                    'active_patients': 0,
                    'patients_with_upcoming': 0,
                    'patients_with_recent': 0,
                    'total_upcoming_appointments': 0,
                    'total_recent_appointments': 0,
                    'total_all_appointments': 0,
                    'avg_upcoming_per_patient': 0.0,
                    'avg_recent_per_patient': 0.0,
                    'avg_total_per_patient': 0.0,
                    'engagement_rate': 0.0,
                    'last_sync_time': None,
                    'synced_patients': 0,
                    'sync_percentage': 0.0,
                    'integration_status': 'Not Connected',
                    'activity_status': 'Inactive',
                    'generated_at': datetime.now()
                }
            
            # Get recent activity
            activity_query = """
            SELECT * FROM recent_sync_activity 
            WHERE organization_id = %s 
            ORDER BY COALESCE(completed_at, started_at) DESC
            LIMIT %s
            """
            cursor.execute(activity_query, [organization_id, activity_limit])
            activity_results = cursor.fetchall()
            
            # Convert to response models
            summary = DashboardSummary(**summary_result)
            activities = [RecentActivity(**activity) for activity in activity_results]
            
            return DashboardResponse(
                success=True,
                organization_id=organization_id,
                summary=summary,
                recent_activity=activities,
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.error(f"Failed to get dashboard data for {organization_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

@router.get("/{organization_id}/summary", response_model=DashboardSummary)
async def get_dashboard_summary(organization_id: str):
    """
    Get just the summary data (no activity log)
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT * FROM dashboard_summary 
            WHERE organization_id = %s
            """
            cursor.execute(query, [organization_id])
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No dashboard data found for organization {organization_id}"
                )
            
            return DashboardSummary(**result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard summary for {organization_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve dashboard summary: {str(e)}"
        )

@router.get("/{organization_id}/activity", response_model=List[RecentActivity])
async def get_recent_activity(organization_id: str, limit: int = 20):
    """
    Get just the recent activity log
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT * FROM recent_sync_activity 
            WHERE organization_id = %s 
            ORDER BY COALESCE(completed_at, started_at) DESC
            LIMIT %s
            """
            cursor.execute(query, [organization_id, limit])
            results = cursor.fetchall()
            
            return [RecentActivity(**activity) for activity in results]
            
    except Exception as e:
        logger.error(f"Failed to get recent activity for {organization_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve recent activity: {str(e)}"
        ) 