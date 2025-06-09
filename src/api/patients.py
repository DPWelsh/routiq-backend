"""
Patients API Router
Active patients endpoints with organization-specific access control
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.database import Database
from src.api.auth import verify_organization_access

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models
class ActivePatientResponse(BaseModel):
    id: int
    contact_id: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    recent_appointment_count: int
    upcoming_appointment_count: int
    total_appointment_count: int
    last_appointment_date: Optional[datetime] = None
    recent_appointments: Optional[List[Dict[str, Any]]] = None
    upcoming_appointments: Optional[List[Dict[str, Any]]] = None
    search_date_from: Optional[datetime] = None
    search_date_to: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ActivePatientsListResponse(BaseModel):
    patients: List[ActivePatientResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

class ActivePatientsSummaryResponse(BaseModel):
    total_active_patients: int
    patients_with_recent_appointments: int
    patients_with_upcoming_appointments: int
    last_sync_date: Optional[datetime] = None
    organization_id: str

@router.get("/active", response_model=ActivePatientsListResponse)
async def list_active_patients(
    organization_id: str = Depends(verify_organization_access),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    min_recent_appointments: Optional[int] = Query(None, ge=0, description="Filter by minimum recent appointments"),
    has_upcoming: Optional[bool] = Query(None, description="Filter by upcoming appointments"),
    search_name: Optional[str] = Query(None, description="Search by contact name")
):
    """
    List active patients for an organization with filtering and pagination
    """
    try:
        db = Database()
        
        # Build the query
        query = """
        SELECT 
            ap.*,
            c.name as contact_name,
            c.phone as contact_phone
        FROM active_patients ap
        JOIN contacts c ON ap.contact_id = c.id
        WHERE ap.organization_id = %s
        """
        params = [organization_id]
        
        # Add filters
        if min_recent_appointments is not None:
            query += " AND ap.recent_appointment_count >= %s"
            params.append(min_recent_appointments)
            
        if has_upcoming is not None:
            if has_upcoming:
                query += " AND ap.upcoming_appointment_count > 0"
            else:
                query += " AND ap.upcoming_appointment_count = 0"
                
        if search_name:
            query += " AND c.name ILIKE %s"
            params.append(f"%{search_name}%")
        
        # Add ordering
        query += " ORDER BY ap.last_appointment_date DESC, ap.recent_appointment_count DESC"
        
        # Get total count
        count_query = query.replace(
            "SELECT ap.*, c.name as contact_name, c.phone as contact_phone",
            "SELECT COUNT(*)"
        )
        
        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                # Get total count
                await cursor.execute(count_query, params)
                total_count = (await cursor.fetchone())[0]
                
                # Get paginated results
                offset = (page - 1) * page_size
                paginated_query = query + " LIMIT %s OFFSET %s"
                paginated_params = params + [page_size, offset]
                
                await cursor.execute(paginated_query, paginated_params)
                rows = await cursor.fetchall()
                
                # Convert to response models
                patients = []
                for row in rows:
                    patient = ActivePatientResponse(
                        id=row[0],
                        contact_id=str(row[1]),
                        contact_name=row[12],  # contact_name from JOIN
                        contact_phone=row[13],  # contact_phone from JOIN
                        recent_appointment_count=row[2],
                        upcoming_appointment_count=row[3],
                        total_appointment_count=row[4],
                        last_appointment_date=row[5],
                        recent_appointments=row[6],
                        upcoming_appointments=row[7],
                        search_date_from=row[8],
                        search_date_to=row[9],
                        created_at=row[10],
                        updated_at=row[11]
                    )
                    patients.append(patient)
                
                return ActivePatientsListResponse(
                    patients=patients,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    has_next=(page * page_size) < total_count,
                    has_previous=page > 1
                )
                
    except Exception as e:
        logger.error(f"Failed to list active patients: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active patients")

@router.get("/active/summary", response_model=ActivePatientsSummaryResponse)
async def get_active_patients_summary(
    organization_id: str = Depends(verify_organization_access)
):
    """
    Get summary statistics for active patients
    """
    try:
        db = Database()
        
        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                # Get summary statistics
                summary_query = """
                SELECT 
                    COUNT(*) as total_active_patients,
                    COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                    COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                    MAX(updated_at) as last_sync_date
                FROM active_patients 
                WHERE organization_id = %s
                """
                
                await cursor.execute(summary_query, [organization_id])
                row = await cursor.fetchone()
                
                return ActivePatientsSummaryResponse(
                    total_active_patients=row[0] or 0,
                    patients_with_recent_appointments=row[1] or 0,
                    patients_with_upcoming_appointments=row[2] or 0,
                    last_sync_date=row[3],
                    organization_id=organization_id
                )
                
    except Exception as e:
        logger.error(f"Failed to get active patients summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")

@router.get("/active/{patient_id}", response_model=ActivePatientResponse)
async def get_active_patient(
    patient_id: int,
    organization_id: str = Depends(verify_organization_access)
):
    """
    Get detailed information for a specific active patient
    """
    try:
        db = Database()
        
        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                query = """
                SELECT 
                    ap.*,
                    c.name as contact_name,
                    c.phone as contact_phone
                FROM active_patients ap
                JOIN contacts c ON ap.contact_id = c.id
                WHERE ap.id = %s AND ap.organization_id = %s
                """
                
                await cursor.execute(query, [patient_id, organization_id])
                row = await cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Active patient not found")
                
                return ActivePatientResponse(
                    id=row[0],
                    contact_id=str(row[1]),
                    contact_name=row[12],
                    contact_phone=row[13],
                    recent_appointment_count=row[2],
                    upcoming_appointment_count=row[3],
                    total_appointment_count=row[4],
                    last_appointment_date=row[5],
                    recent_appointments=row[6],
                    upcoming_appointments=row[7],
                    search_date_from=row[8],
                    search_date_to=row[9],
                    created_at=row[10],
                    updated_at=row[11]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active patient") 