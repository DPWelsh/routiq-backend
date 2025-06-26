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

@router.get("/{organization_id}/patients")
async def list_patients(organization_id: str):
    """List active patients for an organization"""
    try:
        with db.get_cursor() as cursor:
            # Use the unified patients table
            query = """
            SELECT 
                id,
                name,
                phone,
                email,
                cliniko_patient_id,
                is_active,
                activity_status,
                recent_appointment_count,
                upcoming_appointment_count,
                total_appointment_count,
                first_appointment_date,
                last_appointment_date,
                next_appointment_time,
                next_appointment_type,
                primary_appointment_type,
                treatment_notes,
                recent_appointments,
                upcoming_appointments,
                last_synced_at,
                created_at,
                updated_at
            FROM patients
            WHERE organization_id = %s AND is_active = true
            ORDER BY 
                CASE 
                    WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                    ELSE last_appointment_date 
                END DESC
            LIMIT 50
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "is_active": row['is_active'],
                    "activity_status": row['activity_status'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "first_appointment_date": row['first_appointment_date'].isoformat() if row['first_appointment_date'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row['next_appointment_time'] else None,
                    "next_appointment_type": row['next_appointment_type'],
                    "primary_appointment_type": row['primary_appointment_type'],
                    "treatment_notes": row['treatment_notes'],
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    "last_synced_at": row['last_synced_at'].isoformat() if row['last_synced_at'] else None,
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

@router.get("/{organization_id}/patients/with-appointments")
async def list_patients_with_appointment_details(organization_id: str):
    """List active patients with detailed appointment type and treatment information"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                id,
                name,
                phone,
                email,
                cliniko_patient_id,
                is_active,
                activity_status,
                recent_appointment_count,
                upcoming_appointment_count,
                total_appointment_count,
                first_appointment_date,
                last_appointment_date,
                next_appointment_time,
                next_appointment_type,
                primary_appointment_type,
                treatment_notes,
                recent_appointments,
                upcoming_appointments,
                last_synced_at,
                created_at,
                updated_at,
                -- Calculate priority based on next appointment
                CASE 
                    WHEN next_appointment_time IS NOT NULL AND 
                         next_appointment_time <= NOW() + INTERVAL '24 hours' THEN 'high'
                    WHEN next_appointment_time IS NOT NULL AND 
                         next_appointment_time <= NOW() + INTERVAL '72 hours' THEN 'medium'
                    ELSE 'low'
                END as priority
            FROM patients
            WHERE organization_id = %s AND is_active = true
            ORDER BY 
                CASE 
                    WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                    ELSE last_appointment_date 
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
                    "id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "is_active": row['is_active'],
                    "activity_status": row['activity_status'],
                    "priority": row['priority'],
                    
                    # Appointment counts
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    
                    # Appointment details
                    "first_appointment_date": row['first_appointment_date'].isoformat() if row['first_appointment_date'] else None,
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "next_appointment_time": next_appointment_formatted,
                    "next_appointment_type": row.get('next_appointment_type'),
                    "primary_appointment_type": row.get('primary_appointment_type'),
                    
                    # Treatment information
                    "treatment_notes": row.get('treatment_notes'),
                    
                    # Calculated fields
                    "hours_until_next_appointment": round(hours_until_next, 1) if hours_until_next is not None else None,
                    "days_until_next_appointment": round(days_until_next, 1) if days_until_next is not None else None,
                    
                    # Raw appointment data
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    
                    # Sync and timestamps
                    "last_synced_at": row['last_synced_at'].isoformat() if row['last_synced_at'] else None,
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

@router.get("/{organization_id}/patients/by-appointment-type/{appointment_type}")
async def list_patients_by_appointment_type(organization_id: str, appointment_type: str):
    """List patients filtered by appointment type"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                id,
                name,
                phone,
                email,
                cliniko_patient_id,
                is_active,
                activity_status,
                recent_appointment_count,
                upcoming_appointment_count,
                total_appointment_count,
                last_appointment_date,
                next_appointment_time,
                next_appointment_type,
                primary_appointment_type,
                treatment_notes,
                recent_appointments,
                upcoming_appointments
            FROM patients
            WHERE organization_id = %s 
            AND is_active = true
            AND (next_appointment_type = %s OR primary_appointment_type = %s)
            ORDER BY next_appointment_time ASC, last_appointment_date DESC
            """
            
            cursor.execute(query, [organization_id, appointment_type, appointment_type])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "is_active": row['is_active'],
                    "activity_status": row['activity_status'],
                    "next_appointment_type": row.get('next_appointment_type'),
                    "primary_appointment_type": row.get('primary_appointment_type'),
                    "next_appointment_time": row['next_appointment_time'].isoformat() if row.get('next_appointment_time') else None,
                    "treatment_notes": row.get('treatment_notes'),
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments']
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

@router.get("/{organization_id}/patients/appointment-types/summary")
async def get_appointment_types_summary(organization_id: str):
    """Get summary of appointment types for the organization"""
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                next_appointment_type,
                primary_appointment_type,
                COUNT(*) as patient_count,
                COUNT(CASE WHEN next_appointment_time IS NOT NULL THEN 1 END) as with_upcoming,
                MIN(next_appointment_time) as earliest_upcoming,
                MAX(next_appointment_time) as latest_upcoming
            FROM patients
            WHERE organization_id = %s
            AND is_active = true
            AND (next_appointment_type IS NOT NULL OR primary_appointment_type IS NOT NULL)
            GROUP BY next_appointment_type, primary_appointment_type
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

@router.get("/{organization_id}/summary")
async def patients_summary(organization_id: str):
    """Get patient summary statistics"""
    try:
        with db.get_cursor() as cursor:
            # Get total patients count
            cursor.execute(
                "SELECT COUNT(*) as total FROM patients WHERE organization_id = %s",
                [organization_id]
            )
            total_result = cursor.fetchone()
            total_patients = total_result['total'] if total_result else 0
            
            # Get active patients count
            cursor.execute(
                "SELECT COUNT(*) as active FROM patients WHERE organization_id = %s AND is_active = true",
                [organization_id]
            )
            active_result = cursor.fetchone()
            active_patients = active_result['active'] if active_result else 0
            
            # Get patients with upcoming appointments
            cursor.execute(
                "SELECT COUNT(*) as upcoming FROM patients WHERE organization_id = %s AND upcoming_appointment_count > 0",
                [organization_id]
            )
            upcoming_result = cursor.fetchone()
            patients_with_upcoming = upcoming_result['upcoming'] if upcoming_result else 0
            
            # Get recent activity
            cursor.execute(
                "SELECT COUNT(*) as recent FROM patients WHERE organization_id = %s AND recent_appointment_count > 0",
                [organization_id]
            )
            recent_result = cursor.fetchone()
            patients_with_recent = recent_result['recent'] if recent_result else 0
            
            return {
                "total_patients": total_patients,
                "active_patients": active_patients,
                "patients_with_upcoming_appointments": patients_with_upcoming,
                "patients_with_recent_activity": patients_with_recent,
                "last_updated": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get patient summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}") 