"""
Appointments API Router
Handles appointment-specific endpoints and views
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from src.database import db
from src.api.auth import verify_organization_access

logger = logging.getLogger(__name__)

# FIXED: Router with prefix for Swagger visibility
router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])

@router.get("/{organization_id}/upcoming")
async def get_upcoming_appointments(
    organization_id: str,
    days_ahead: int = Query(7, ge=1, le=30, description="Days ahead to look for appointments"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of appointments to return"),
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Get upcoming appointments for an organization
    
    Returns a list of upcoming appointments sorted by appointment time,
    with patient details and appointment information.
    """
    try:
        with db.get_cursor() as cursor:
            # Calculate date range
            now = datetime.now()
            end_date = now + timedelta(days=days_ahead)
            
            # Query for upcoming appointments with patient details
            query = """
            SELECT 
                p.id as patient_id,
                p.name as patient_name,
                p.phone as patient_phone,
                p.email as patient_email,
                p.next_appointment_time,
                p.next_appointment_type,
                p.upcoming_appointment_count,
                p.upcoming_appointments,
                p.activity_status,
                p.treatment_notes,
                EXTRACT(DAYS FROM (p.next_appointment_time - NOW())) as days_until_appointment,
                EXTRACT(HOURS FROM (p.next_appointment_time - NOW())) as hours_until_appointment
            FROM patients p
            WHERE p.organization_id = %s 
                AND p.is_active = true
                AND p.next_appointment_time IS NOT NULL
                AND p.next_appointment_time BETWEEN NOW() AND %s
            ORDER BY p.next_appointment_time ASC
            LIMIT %s
            """
            
            cursor.execute(query, [organization_id, end_date, limit])
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                # Parse upcoming appointments JSON if available
                upcoming_details = row['upcoming_appointments'] or []
                
                appointment_data = {
                    "id": f"next_{row['patient_id']}", # Unique ID for the appointment
                    "patient_id": str(row['patient_id']),
                    "patient_name": row['patient_name'],
                    "patient_phone": row['patient_phone'],
                    "patient_email": row['patient_email'],
                    "appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "appointment_type": row['next_appointment_type'],
                    "days_until": int(row['days_until_appointment']) if row['days_until_appointment'] is not None else None,
                    "hours_until": round(float(row['hours_until_appointment']), 1) if row['hours_until_appointment'] is not None else None,
                    "total_upcoming_count": row['upcoming_appointment_count'],
                    "activity_status": row['activity_status'],
                    "treatment_notes": row['treatment_notes'],
                    "priority": "high" if (row['days_until_appointment'] or 999) <= 1 else "medium" if (row['days_until_appointment'] or 999) <= 3 else "low"
                }
                
                appointments.append(appointment_data)
            
            # Get summary stats for the response
            summary_query = """
            SELECT 
                COUNT(*) as total_upcoming_in_period,
                COUNT(CASE WHEN p.next_appointment_time <= NOW() + INTERVAL '1 day' THEN 1 END) as due_within_24h,
                COUNT(CASE WHEN p.next_appointment_time <= NOW() + INTERVAL '3 days' THEN 1 END) as due_within_3_days
            FROM patients p
            WHERE p.organization_id = %s 
                AND p.is_active = true
                AND p.next_appointment_time IS NOT NULL
                AND p.next_appointment_time BETWEEN NOW() AND %s
            """
            
            cursor.execute(summary_query, [organization_id, end_date])
            summary_row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "appointments": appointments,
                "summary": {
                    "total_in_period": summary_row['total_upcoming_in_period'] if summary_row else 0,
                    "due_within_24h": summary_row['due_within_24h'] if summary_row else 0,
                    "due_within_3_days": summary_row['due_within_3_days'] if summary_row else 0,
                    "days_ahead": days_ahead
                },
                "filters": {
                    "days_ahead": days_ahead,
                    "limit": limit
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get upcoming appointments for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve upcoming appointments: {str(e)}")

@router.get("/{organization_id}/upcoming/summary")
async def get_upcoming_appointments_summary(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Get summary statistics for upcoming appointments
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                COUNT(CASE WHEN p.next_appointment_time IS NOT NULL AND p.next_appointment_time > NOW() THEN 1 END) as total_upcoming,
                COUNT(CASE WHEN p.next_appointment_time <= NOW() + INTERVAL '1 day' THEN 1 END) as due_today,
                COUNT(CASE WHEN p.next_appointment_time <= NOW() + INTERVAL '7 days' THEN 1 END) as due_this_week,
                COUNT(CASE WHEN p.next_appointment_time <= NOW() + INTERVAL '30 days' THEN 1 END) as due_this_month,
                SUM(p.upcoming_appointment_count) as total_appointment_count,
                MIN(p.next_appointment_time) as earliest_appointment,
                MAX(p.next_appointment_time) as latest_appointment
            FROM patients p
            WHERE p.organization_id = %s 
                AND p.is_active = true
                AND p.upcoming_appointment_count > 0
            """
            
            cursor.execute(query, [organization_id])
            row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "total_upcoming_appointments": row['total_upcoming'] if row else 0,
                "due_today": row['due_today'] if row else 0,
                "due_this_week": row['due_this_week'] if row else 0,
                "due_this_month": row['due_this_month'] if row else 0,
                "total_appointment_count": row['total_appointment_count'] if row else 0,
                "earliest_appointment": row['earliest_appointment'].isoformat() if row and row['earliest_appointment'] else None,
                "latest_appointment": row['latest_appointment'].isoformat() if row and row['latest_appointment'] else None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get upcoming appointments summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve appointments summary: {str(e)}") 