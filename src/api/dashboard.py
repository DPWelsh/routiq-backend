"""
Dashboard API endpoints
Provides data for the sync dashboard frontend
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
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
    last_sync_time: Optional[datetime]
    synced_patients: int
    sync_percentage: float
    integration_status: str
    activity_status: str
    generated_at: datetime

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