"""
Patients API Router - Minimal working version
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from src.database import db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/{organization_id}/active/summary")
async def get_active_patients_summary(organization_id: str):
    """Get active patients summary for an organization"""
    try:
        with db.get_cursor() as cursor:
            summary_query = """
            SELECT 
                COUNT(*) as total_active_patients,
                COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                MAX(updated_at) as last_sync_date
            FROM active_patients 
            WHERE organization_id = %s
            """
            
            cursor.execute(summary_query, [organization_id])
            row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "total_active_patients": row['total_active_patients'] if row else 0,
                "patients_with_recent_appointments": row['patients_with_recent'] if row else 0,
                "patients_with_upcoming_appointments": row['patients_with_upcoming'] if row else 0,
                "last_sync_date": row['last_sync_date'].isoformat() if row and row['last_sync_date'] else None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

@router.get("/{organization_id}/active")
async def list_active_patients(organization_id: str):
    """List active patients for an organization"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                ap.*,
                c.name as contact_name,
                c.phone as contact_phone
            FROM active_patients ap
            JOIN contacts c ON ap.contact_id = c.id
            WHERE ap.organization_id = %s
            ORDER BY ap.last_appointment_date DESC
            LIMIT 50
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": row['id'],
                    "contact_id": str(row['contact_id']),
                    "contact_name": row['contact_name'],
                    "contact_phone": row['contact_phone'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "organization_id": organization_id,
                "patients": patients,
                "total_count": len(patients),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to list active patients for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active patients: {str(e)}")

@router.get("/test")
async def test_patients_router():
    """Test endpoint to verify patients router is loading"""
    return {
        "message": "Patients router is working!",
        "timestamp": datetime.now().isoformat()
    } 