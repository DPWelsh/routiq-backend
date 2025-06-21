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
            # Check if contact_id column exists in active_patients table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'active_patients' 
                AND column_name = 'contact_id'
            """)
            has_contact_id = cursor.fetchone() is not None
            
            if has_contact_id:
                # New schema with contact_id foreign key
                query = """
                SELECT 
                    ap.*,
                    c.name as contact_name,
                    c.phone as contact_phone,
                    c.email as contact_email,
                    c.last_treatment_note,
                    c.treatment_summary
                FROM active_patients ap
                LEFT JOIN contacts c ON ap.contact_id = c.id
                WHERE ap.organization_id = %s
                ORDER BY 
                    CASE 
                        WHEN ap.next_appointment_time IS NOT NULL THEN ap.next_appointment_time 
                        ELSE ap.last_appointment_date 
                    END DESC
                LIMIT 50
                """
            else:
                # Legacy schema - active_patients has direct patient info
                query = """
                SELECT 
                    ap.*,
                    ap.name as contact_name,
                    ap.phone as contact_phone,
                    ap.email as contact_email,
                    NULL as last_treatment_note,
                    NULL as treatment_summary
                FROM active_patients ap
                WHERE ap.organization_id = %s
                ORDER BY ap.last_appointment_date DESC
                LIMIT 50
                """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                # Parse next appointment time if available
                next_appointment_time = row.get('next_appointment_time')
                next_appointment_formatted = None
                hours_until_next = None
                
                if next_appointment_time:
                    next_appointment_formatted = next_appointment_time.isoformat()
                    # Calculate hours until next appointment
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    hours_until_next = (next_appointment_time - now).total_seconds() / 3600
                
                patients.append({
                    "id": row['id'],
                    "contact_id": str(row['contact_id']),
                    "contact_name": row['contact_name'],
                    "contact_phone": row['contact_phone'],
                    "contact_email": row['contact_email'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    
                    # Enhanced fields
                    "next_appointment_time": next_appointment_formatted,
                    "next_appointment_type": row.get('next_appointment_type'),
                    "primary_appointment_type": row.get('primary_appointment_type'),
                    "treatment_notes": row.get('treatment_notes'),
                    "last_treatment_note": row.get('last_treatment_note'),
                    "treatment_summary": row.get('treatment_summary'),
                    "hours_until_next_appointment": round(hours_until_next, 1) if hours_until_next is not None else None,
                    
                    # Timestamps
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

@router.get("/{organization_id}/active/with-appointments")
async def list_patients_with_appointment_details(organization_id: str):
    """List active patients with detailed appointment type and treatment information"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                ap.*,
                c.name as contact_name,
                c.phone as contact_phone,
                c.email as contact_email,
                c.last_treatment_note,
                c.treatment_summary,
                -- Calculate priority based on next appointment
                CASE 
                    WHEN ap.next_appointment_time IS NOT NULL AND 
                         ap.next_appointment_time <= NOW() + INTERVAL '24 hours' THEN 'high'
                    WHEN ap.next_appointment_time IS NOT NULL AND 
                         ap.next_appointment_time <= NOW() + INTERVAL '72 hours' THEN 'medium'
                    ELSE 'low'
                END as priority
            FROM active_patients ap
            JOIN contacts c ON ap.contact_id = c.id
            WHERE ap.organization_id = %s
            ORDER BY 
                CASE 
                    WHEN ap.next_appointment_time IS NOT NULL THEN ap.next_appointment_time 
                    ELSE ap.last_appointment_date 
                END ASC
            LIMIT 100
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                # Parse next appointment time
                next_appointment_time = row.get('next_appointment_time')
                next_appointment_formatted = None
                hours_until_next = None
                days_until_next = None
                
                if next_appointment_time:
                    next_appointment_formatted = next_appointment_time.isoformat()
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    hours_until_next = (next_appointment_time - now).total_seconds() / 3600
                    days_until_next = hours_until_next / 24
                
                patients.append({
                    "id": row['id'],
                    "contact_id": str(row['contact_id']),
                    "contact_name": row['contact_name'],
                    "contact_phone": row['contact_phone'],
                    "contact_email": row['contact_email'],
                    "priority": row['priority'],
                    
                    # Appointment counts
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    
                    # Appointment details
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": next_appointment_formatted,
                    "next_appointment_type": row.get('next_appointment_type'),
                    "primary_appointment_type": row.get('primary_appointment_type'),
                    
                    # Treatment information
                    "treatment_notes": row.get('treatment_notes'),
                    "last_treatment_note": row.get('last_treatment_note'),
                    "treatment_summary": row.get('treatment_summary'),
                    
                    # Calculated fields
                    "hours_until_next_appointment": round(hours_until_next, 1) if hours_until_next is not None else None,
                    "days_until_next_appointment": round(days_until_next, 1) if days_until_next is not None else None,
                    
                    # Raw appointment data
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    
                    # Timestamps
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
        logger.error(f"Failed to list patients with appointment details for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patients: {str(e)}")

@router.get("/{organization_id}/by-appointment-type/{appointment_type}")
async def list_patients_by_appointment_type(organization_id: str, appointment_type: str):
    """List patients filtered by appointment type"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                ap.*,
                c.name as contact_name,
                c.phone as contact_phone,
                c.email as contact_email
            FROM active_patients ap
            JOIN contacts c ON ap.contact_id = c.id
            WHERE ap.organization_id = %s 
            AND (ap.next_appointment_type = %s OR ap.primary_appointment_type = %s)
            ORDER BY ap.next_appointment_time ASC, ap.last_appointment_date DESC
            """
            
            cursor.execute(query, [organization_id, appointment_type, appointment_type])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": row['id'],
                    "contact_id": str(row['contact_id']),
                    "contact_name": row['contact_name'],
                    "contact_phone": row['contact_phone'],
                    "contact_email": row['contact_email'],
                    "next_appointment_type": row.get('next_appointment_type'),
                    "primary_appointment_type": row.get('primary_appointment_type'),
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row.get('next_appointment_time') else None,
                    "treatment_notes": row.get('treatment_notes'),
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count']
                })
            
            return {
                "organization_id": organization_id,
                "appointment_type": appointment_type,
                "patients": patients,
                "total_count": len(patients),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to list patients by appointment type for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patients: {str(e)}")

@router.get("/{organization_id}/appointment-types/summary")
async def get_appointment_types_summary(organization_id: str):
    """Get summary of appointment types for the organization"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                ap.next_appointment_type,
                ap.primary_appointment_type,
                COUNT(*) as patient_count,
                COUNT(CASE WHEN ap.next_appointment_time IS NOT NULL THEN 1 END) as with_upcoming,
                MIN(ap.next_appointment_time) as earliest_upcoming,
                MAX(ap.next_appointment_time) as latest_upcoming
            FROM active_patients ap
            WHERE ap.organization_id = %s
            AND (ap.next_appointment_type IS NOT NULL OR ap.primary_appointment_type IS NOT NULL)
            GROUP BY ap.next_appointment_type, ap.primary_appointment_type
            ORDER BY patient_count DESC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            appointment_types = []
            for row in rows:
                appointment_types.append({
                    "next_appointment_type": row['next_appointment_type'],
                    "primary_appointment_type": row['primary_appointment_type'],
                    "patient_count": row['patient_count'],
                    "patients_with_upcoming": row['with_upcoming'],
                    "earliest_upcoming": row['earliest_upcoming'].isoformat() if row['earliest_upcoming'] else None,
                    "latest_upcoming": row['latest_upcoming'].isoformat() if row['latest_upcoming'] else None
                })
            
            return {
                "organization_id": organization_id,
                "appointment_types": appointment_types,
                "total_types": len(appointment_types),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get appointment types summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}") 