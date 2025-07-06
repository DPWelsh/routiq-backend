"""
Patients Domain Service
Business logic for patient management operations
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from math import ceil

from src.database import db
from src.patients.schemas import (
    Patient,
    PatientWithPriority,
    PatientSummaryStats,
    EngagementStats,
    AppointmentTypeSummary,
    ActivityStatus,
    Priority,
    EngagementFilter
)
from src.patients.exceptions import (
    PatientNotFoundError,
    PatientServiceError,
    PatientValidationError
)
from src.patients.constants import (
    PATIENTS_PER_PAGE_DEFAULT,
    PATIENTS_PER_PAGE_MAX,
    PRIORITY_HOURS_HIGH,
    PRIORITY_HOURS_MEDIUM
)

logger = logging.getLogger(__name__)


class PatientService:
    """Service class for patient management operations"""
    
    def __init__(self):
        """Initialize the patient service"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_active_patients_summary(self, organization_id: str) -> PatientSummaryStats:
        """
        Get summary statistics for active patients in an organization
        
        Args:
            organization_id: Organization to get summary for
            
        Returns:
            PatientSummaryStats: Summary statistics
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                summary_query = """
                SELECT 
                    COUNT(*) as total_active_patients,
                    COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                    COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                    AVG(CASE WHEN recent_appointment_count > 0 THEN recent_appointment_count END) as avg_recent_appointments,
                    AVG(CASE WHEN total_appointment_count > 0 THEN total_appointment_count END) as avg_total_appointments,
                    MAX(last_synced_at) as last_sync_date
                FROM patients 
                WHERE organization_id = %s AND is_active = true
                """
                
                cursor.execute(summary_query, [organization_id])
                row = cursor.fetchone()
                
                if not row:
                    return PatientSummaryStats(
                        total_active_patients=0,
                        patients_with_recent_appointments=0,
                        patients_with_upcoming_appointments=0,
                        avg_recent_appointments=0.0,
                        avg_total_appointments=0.0,
                        last_sync_date=None
                    )
                
                return PatientSummaryStats(
                    total_active_patients=row['total_active_patients'] or 0,
                    patients_with_recent_appointments=row['patients_with_recent'] or 0,
                    patients_with_upcoming_appointments=row['patients_with_upcoming'] or 0,
                    avg_recent_appointments=float(row['avg_recent_appointments']) if row['avg_recent_appointments'] else 0.0,
                    avg_total_appointments=float(row['avg_total_appointments']) if row['avg_total_appointments'] else 0.0,
                    last_sync_date=row['last_sync_date']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve patient summary: {str(e)}")
    
    async def list_patients(self, organization_id: str, limit: int = 50) -> List[Patient]:
        """
        List active patients for an organization
        
        Args:
            organization_id: Organization to get patients for
            limit: Maximum number of patients to return
            
        Returns:
            List[Patient]: List of patient objects
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                query = """
                SELECT 
                    id, name, phone, email, cliniko_patient_id, is_active, activity_status,
                    recent_appointment_count, upcoming_appointment_count, total_appointment_count,
                    first_appointment_date, last_appointment_date, next_appointment_time,
                    next_appointment_type, primary_appointment_type, treatment_notes,
                    recent_appointments, upcoming_appointments, last_synced_at,
                    created_at, updated_at
                FROM patients
                WHERE organization_id = %s AND is_active = true
                ORDER BY 
                    CASE 
                        WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                        ELSE last_appointment_date 
                    END DESC
                LIMIT %s
                """
                
                cursor.execute(query, [organization_id, limit])
                rows = cursor.fetchall()
                
                patients = []
                for row in rows:
                    patients.append(self._row_to_patient(row))
                
                return patients
                
        except Exception as e:
            self.logger.error(f"Failed to list patients for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve patients: {str(e)}")
    
    async def list_patients_with_appointment_details(self, organization_id: str, limit: int = 100) -> List[PatientWithPriority]:
        """
        List active patients with detailed appointment information and priority calculation
        
        Args:
            organization_id: Organization to get patients for
            limit: Maximum number of patients to return
            
        Returns:
            List[PatientWithPriority]: List of patients with priority
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                query = """
                SELECT 
                    id, name, phone, email, cliniko_patient_id, is_active, activity_status,
                    recent_appointment_count, upcoming_appointment_count, total_appointment_count,
                    first_appointment_date, last_appointment_date, next_appointment_time,
                    next_appointment_type, primary_appointment_type, treatment_notes,
                    recent_appointments, upcoming_appointments, last_synced_at,
                    created_at, updated_at,
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
                LIMIT %s
                """
                
                cursor.execute(query, [organization_id, limit])
                rows = cursor.fetchall()
                
                patients = []
                for row in rows:
                    patient_data = self._row_to_patient_dict(row)
                    patient_data["priority"] = Priority(row["priority"])
                    patients.append(PatientWithPriority(**patient_data))
                
                return patients
                
        except Exception as e:
            self.logger.error(f"Failed to list patients with details for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve patients with appointment details: {str(e)}")
    
    async def list_patients_by_appointment_type(self, organization_id: str, appointment_type: str, limit: int = 100) -> List[Patient]:
        """
        List patients filtered by primary appointment type
        
        Args:
            organization_id: Organization to get patients for
            appointment_type: Appointment type to filter by
            limit: Maximum number of patients to return
            
        Returns:
            List[Patient]: List of filtered patients
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                query = """
                SELECT 
                    id, name, phone, email, cliniko_patient_id, is_active, activity_status,
                    recent_appointment_count, upcoming_appointment_count, total_appointment_count,
                    first_appointment_date, last_appointment_date, next_appointment_time,
                    next_appointment_type, primary_appointment_type, treatment_notes,
                    recent_appointments, upcoming_appointments, last_synced_at,
                    created_at, updated_at
                FROM patients
                WHERE organization_id = %s 
                  AND is_active = true 
                  AND primary_appointment_type = %s
                ORDER BY last_appointment_date DESC
                LIMIT %s
                """
                
                cursor.execute(query, [organization_id, appointment_type, limit])
                rows = cursor.fetchall()
                
                patients = []
                for row in rows:
                    patients.append(self._row_to_patient(row))
                
                return patients
                
        except Exception as e:
            self.logger.error(f"Failed to list patients by appointment type {appointment_type} for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve patients by appointment type: {str(e)}")
    
    async def get_appointment_types_summary(self, organization_id: str) -> List[AppointmentTypeSummary]:
        """
        Get summary of appointment types and patient distribution
        
        Args:
            organization_id: Organization to get summary for
            
        Returns:
            List[AppointmentTypeSummary]: List of appointment type summaries
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                query = """
                SELECT 
                    primary_appointment_type as appointment_type,
                    COUNT(*) as patient_count,
                    AVG(total_appointment_count) as avg_appointments_per_patient,
                    MAX(last_appointment_date) as most_recent_appointment
                FROM patients
                WHERE organization_id = %s 
                  AND is_active = true 
                  AND primary_appointment_type IS NOT NULL
                GROUP BY primary_appointment_type
                ORDER BY patient_count DESC
                """
                
                cursor.execute(query, [organization_id])
                rows = cursor.fetchall()
                
                # Calculate total patients for percentage calculation
                total_patients = sum(row['patient_count'] for row in rows)
                
                summaries = []
                for row in rows:
                    percentage = (row['patient_count'] / total_patients * 100) if total_patients > 0 else 0
                    
                    summaries.append(AppointmentTypeSummary(
                        appointment_type=row['appointment_type'],
                        patient_count=row['patient_count'],
                        percentage_of_total=round(percentage, 2),
                        avg_appointments_per_patient=float(row['avg_appointments_per_patient']) if row['avg_appointments_per_patient'] else 0.0,
                        most_recent_appointment=row['most_recent_appointment']
                    ))
                
                return summaries
                
        except Exception as e:
            self.logger.error(f"Failed to get appointment types summary for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve appointment types summary: {str(e)}")
    
    async def get_patients_summary(self, organization_id: str) -> Dict[str, Any]:
        """
        Get comprehensive patient summary statistics
        
        Args:
            organization_id: Organization to get summary for
            
        Returns:
            Dict[str, Any]: Comprehensive summary data
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                query = """
                SELECT 
                    COUNT(*) as total_patients,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_patients,
                    COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                    COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                    AVG(total_appointment_count) as avg_total_appointments,
                    MAX(last_synced_at) as last_sync_time
                FROM patients
                WHERE organization_id = %s
                """
                
                cursor.execute(query, [organization_id])
                row = cursor.fetchone()
                
                if not row:
                    return {
                        "total_patients": 0,
                        "active_patients": 0,
                        "patients_with_upcoming": 0,
                        "patients_with_recent": 0,
                        "avg_total_appointments": 0.0,
                        "last_sync_time": None
                    }
                
                return {
                    "total_patients": row['total_patients'] or 0,
                    "active_patients": row['active_patients'] or 0,
                    "patients_with_upcoming": row['patients_with_upcoming'] or 0,
                    "patients_with_recent": row['patients_with_recent'] or 0,
                    "avg_total_appointments": float(row['avg_total_appointments']) if row['avg_total_appointments'] else 0.0,
                    "last_sync_time": row['last_sync_time']
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get patients summary for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve patients summary: {str(e)}")
    
    async def list_patients_enhanced(
        self, 
        organization_id: str,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        active_only: bool = True,
        engagement_filter: Optional[EngagementFilter] = None
    ) -> Tuple[List[Patient], int, Dict[str, Any]]:
        """
        Enhanced patient listing with pagination, search, and filtering
        
        Args:
            organization_id: Organization to get patients for
            page: Page number (1-based)
            limit: Number of patients per page
            search: Search term for name, phone, or email
            active_only: Whether to include only active patients
            engagement_filter: Filter by engagement level
            
        Returns:
            Tuple[List[Patient], int, Dict[str, Any]]: (patients, total_count, pagination_info)
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            # Validate and sanitize inputs
            limit = min(limit, PATIENTS_PER_PAGE_MAX)
            offset = (page - 1) * limit
            
            # Build query conditions
            conditions = ["organization_id = %s"]
            params = [organization_id]
            
            if active_only:
                conditions.append("is_active = true")
            
            if search:
                conditions.append("(name ILIKE %s OR phone ILIKE %s OR email ILIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if engagement_filter:
                if engagement_filter == EngagementFilter.ENGAGED:
                    conditions.append("recent_appointment_count > 0")
                elif engagement_filter == EngagementFilter.INACTIVE:
                    conditions.append("recent_appointment_count = 0 AND total_appointment_count > 0")
                elif engagement_filter == EngagementFilter.NEVER_ENGAGED:
                    conditions.append("total_appointment_count = 0")
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            with db.get_cursor() as cursor:
                count_query = f"""
                SELECT COUNT(*) as total
                FROM patients
                WHERE {where_clause}
                """
                
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()['total']
                
                # Get patients
                query = f"""
                SELECT 
                    id, name, phone, email, cliniko_patient_id, is_active, activity_status,
                    recent_appointment_count, upcoming_appointment_count, total_appointment_count,
                    first_appointment_date, last_appointment_date, next_appointment_time,
                    next_appointment_type, primary_appointment_type, treatment_notes,
                    recent_appointments, upcoming_appointments, last_synced_at,
                    created_at, updated_at
                FROM patients
                WHERE {where_clause}
                ORDER BY 
                    CASE 
                        WHEN next_appointment_time IS NOT NULL THEN next_appointment_time 
                        ELSE last_appointment_date 
                    END DESC
                LIMIT %s OFFSET %s
                """
                
                cursor.execute(query, params + [limit, offset])
                rows = cursor.fetchall()
                
                patients = [self._row_to_patient(row) for row in rows]
                
                # Calculate pagination info
                total_pages = ceil(total_count / limit) if limit > 0 else 1
                has_next = page < total_pages
                has_previous = page > 1
                
                pagination_info = {
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_previous": has_previous,
                    "filters_applied": {
                        "search": search,
                        "active_only": active_only,
                        "engagement_filter": engagement_filter.value if engagement_filter else None
                    }
                }
                
                return patients, total_count, pagination_info
                
        except Exception as e:
            self.logger.error(f"Failed to list patients enhanced for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve enhanced patient list: {str(e)}")
    
    async def get_engagement_statistics(self, organization_id: str) -> Tuple[EngagementStats, Dict[str, Any]]:
        """
        Get patient engagement statistics and breakdown
        
        Args:
            organization_id: Organization to get statistics for
            
        Returns:
            Tuple[EngagementStats, Dict[str, Any]]: (stats, additional_data)
            
        Raises:
            PatientServiceError: If database operation fails
        """
        try:
            with db.get_cursor() as cursor:
                # Main engagement stats
                stats_query = """
                SELECT 
                    COUNT(*) as total_patients,
                    COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as engaged_patients,
                    COUNT(CASE WHEN recent_appointment_count = 0 AND total_appointment_count > 0 THEN 1 END) as inactive_patients,
                    COUNT(CASE WHEN total_appointment_count = 0 THEN 1 END) as never_engaged_patients,
                    AVG(total_appointment_count) as avg_appointments_per_patient,
                    COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                    COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent
                FROM patients
                WHERE organization_id = %s AND is_active = true
                """
                
                cursor.execute(stats_query, [organization_id])
                row = cursor.fetchone()
                
                if not row or row['total_patients'] == 0:
                    empty_stats = EngagementStats(
                        total_patients=0,
                        engaged_patients=0,
                        inactive_patients=0,
                        never_engaged_patients=0,
                        engagement_rate=0.0,
                        avg_appointments_per_patient=0.0,
                        patients_with_upcoming=0,
                        patients_with_recent=0
                    )
                    return empty_stats, {"engagement_breakdown": {}, "appointment_frequency": {}}
                
                total_patients = row['total_patients']
                engaged_patients = row['engaged_patients'] or 0
                engagement_rate = (engaged_patients / total_patients * 100) if total_patients > 0 else 0
                
                stats = EngagementStats(
                    total_patients=total_patients,
                    engaged_patients=engaged_patients,
                    inactive_patients=row['inactive_patients'] or 0,
                    never_engaged_patients=row['never_engaged_patients'] or 0,
                    engagement_rate=round(engagement_rate, 2),
                    avg_appointments_per_patient=float(row['avg_appointments_per_patient']) if row['avg_appointments_per_patient'] else 0.0,
                    patients_with_upcoming=row['patients_with_upcoming'] or 0,
                    patients_with_recent=row['patients_with_recent'] or 0
                )
                
                # Additional breakdown data
                breakdown_query = """
                SELECT 
                    CASE 
                        WHEN recent_appointment_count > 0 THEN 'engaged'
                        WHEN recent_appointment_count = 0 AND total_appointment_count > 0 THEN 'inactive'
                        ELSE 'never_engaged'
                    END as engagement_status,
                    COUNT(*) as count
                FROM patients
                WHERE organization_id = %s AND is_active = true
                GROUP BY engagement_status
                """
                
                cursor.execute(breakdown_query, [organization_id])
                breakdown_rows = cursor.fetchall()
                
                engagement_breakdown = {row['engagement_status']: row['count'] for row in breakdown_rows}
                
                # Appointment frequency breakdown
                frequency_query = """
                SELECT 
                    CASE 
                        WHEN total_appointment_count = 0 THEN '0'
                        WHEN total_appointment_count = 1 THEN '1'
                        WHEN total_appointment_count BETWEEN 2 AND 5 THEN '2-5'
                        WHEN total_appointment_count BETWEEN 6 AND 10 THEN '6-10'
                        ELSE '10+'
                    END as frequency_range,
                    COUNT(*) as count
                FROM patients
                WHERE organization_id = %s AND is_active = true
                GROUP BY frequency_range
                """
                
                cursor.execute(frequency_query, [organization_id])
                frequency_rows = cursor.fetchall()
                
                appointment_frequency = {row['frequency_range']: row['count'] for row in frequency_rows}
                
                additional_data = {
                    "engagement_breakdown": engagement_breakdown,
                    "appointment_frequency": appointment_frequency
                }
                
                return stats, additional_data
                
        except Exception as e:
            self.logger.error(f"Failed to get engagement statistics for {organization_id}: {e}")
            raise PatientServiceError(f"Failed to retrieve engagement statistics: {str(e)}")
    
    def _row_to_patient(self, row: Dict[str, Any]) -> Patient:
        """Convert database row to Patient object"""
        return Patient(
            id=str(row['id']),
            name=row['name'],
            phone=row['phone'],
            email=row['email'],
            cliniko_patient_id=row['cliniko_patient_id'],
            is_active=row['is_active'],
            activity_status=ActivityStatus(row['activity_status']) if row['activity_status'] else None,
            recent_appointment_count=row['recent_appointment_count'] or 0,
            upcoming_appointment_count=row['upcoming_appointment_count'] or 0,
            total_appointment_count=row['total_appointment_count'] or 0,
            first_appointment_date=row['first_appointment_date'],
            last_appointment_date=row['last_appointment_date'],
            next_appointment_time=row['next_appointment_time'],
            next_appointment_type=row['next_appointment_type'],
            primary_appointment_type=row['primary_appointment_type'],
            treatment_notes=row['treatment_notes'],
            recent_appointments=row['recent_appointments'],
            upcoming_appointments=row['upcoming_appointments'],
            last_synced_at=row['last_synced_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_patient_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database row to patient dictionary"""
        return {
            "id": str(row['id']),
            "name": row['name'],
            "phone": row['phone'],
            "email": row['email'],
            "cliniko_patient_id": row['cliniko_patient_id'],
            "is_active": row['is_active'],
            "activity_status": row['activity_status'],
            "recent_appointment_count": row['recent_appointment_count'] or 0,
            "upcoming_appointment_count": row['upcoming_appointment_count'] or 0,
            "total_appointment_count": row['total_appointment_count'] or 0,
            "first_appointment_date": row['first_appointment_date'],
            "last_appointment_date": row['last_appointment_date'],
            "next_appointment_time": row['next_appointment_time'],
            "next_appointment_type": row['next_appointment_type'],
            "primary_appointment_type": row['primary_appointment_type'],
            "treatment_notes": row['treatment_notes'],
            "recent_appointments": row['recent_appointments'],
            "upcoming_appointments": row['upcoming_appointments'],
            "last_synced_at": row['last_synced_at'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }


# Global service instance
patient_service = PatientService()


# Export service
__all__ = [
    "PatientService",
    "patient_service",
] 