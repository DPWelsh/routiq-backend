"""
Patients Domain Schemas
Pydantic models for patient-related API requests and responses
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from src.models import CustomModel


class ActivityStatus(str, Enum):
    """Patient activity status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class Priority(str, Enum):
    """Patient priority levels based on upcoming appointments"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EngagementFilter(str, Enum):
    """Patient engagement filter options"""
    ENGAGED = "engaged"
    INACTIVE = "inactive"
    NEVER_ENGAGED = "never_engaged"


class PatientBase(CustomModel):
    """Base patient model with common fields"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    cliniko_patient_id: Optional[str] = None
    is_active: bool = True
    activity_status: Optional[ActivityStatus] = None


class Patient(PatientBase):
    """Full patient model with all fields"""
    id: str
    recent_appointment_count: int = 0
    upcoming_appointment_count: int = 0
    total_appointment_count: int = 0
    first_appointment_date: Optional[datetime] = None
    last_appointment_date: Optional[datetime] = None
    next_appointment_time: Optional[datetime] = None
    next_appointment_type: Optional[str] = None
    primary_appointment_type: Optional[str] = None
    treatment_notes: Optional[str] = None
    recent_appointments: Optional[List[Dict[str, Any]]] = None
    upcoming_appointments: Optional[List[Dict[str, Any]]] = None
    last_synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PatientWithPriority(Patient):
    """Patient model with calculated priority field"""
    priority: Priority


class PatientSummaryStats(CustomModel):
    """Patient summary statistics"""
    total_active_patients: int
    patients_with_recent_appointments: int
    patients_with_upcoming_appointments: int
    avg_recent_appointments: float
    avg_total_appointments: float
    last_sync_date: Optional[datetime] = None


class PatientSummaryResponse(CustomModel):
    """Response model for patient summary endpoint"""
    organization_id: str
    total_active_patients: int
    patients_with_recent_appointments: int
    patients_with_upcoming_appointments: int
    avg_recent_appointments: float
    avg_total_appointments: float
    last_sync_date: Optional[datetime] = None
    timestamp: datetime


class PatientListResponse(CustomModel):
    """Response model for patient list endpoints"""
    organization_id: str
    patients: List[Union[Patient, PatientWithPriority]]
    total_count: int
    timestamp: datetime


class PatientListEnhancedResponse(CustomModel):
    """Enhanced response model for paginated patient list"""
    organization_id: str
    patients: List[Patient]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_previous: bool
    filters_applied: Dict[str, Any]
    timestamp: datetime


class AppointmentType(CustomModel):
    """Appointment type model"""
    name: str
    count: int
    percentage: float


class AppointmentTypeSummary(CustomModel):
    """Appointment type summary statistics"""
    appointment_type: str
    patient_count: int
    percentage_of_total: float
    avg_appointments_per_patient: float
    most_recent_appointment: Optional[datetime] = None


class AppointmentTypeSummaryResponse(CustomModel):
    """Response model for appointment type summary"""
    organization_id: str
    total_patients: int
    appointment_types: List[AppointmentTypeSummary]
    timestamp: datetime


class EngagementStats(CustomModel):
    """Patient engagement statistics"""
    total_patients: int
    engaged_patients: int
    inactive_patients: int
    never_engaged_patients: int
    engagement_rate: float
    avg_appointments_per_patient: float
    patients_with_upcoming: int
    patients_with_recent: int


class EngagementStatsResponse(CustomModel):
    """Response model for engagement statistics"""
    organization_id: str
    stats: EngagementStats
    engagement_breakdown: Dict[str, int]
    appointment_frequency: Dict[str, int]
    timestamp: datetime


class PatientByAppointmentTypeResponse(CustomModel):
    """Response model for patients filtered by appointment type"""
    organization_id: str
    appointment_type: str
    patients: List[Patient]
    total_count: int
    filters_applied: Dict[str, str]
    timestamp: datetime


class TestRouterResponse(CustomModel):
    """Response model for test endpoint"""
    message: str
    timestamp: datetime


# Request models
class PatientListRequest(CustomModel):
    """Request model for enhanced patient list"""
    page: int = 1
    limit: int = 50
    search: Optional[str] = None
    active_only: bool = True
    engagement_filter: Optional[EngagementFilter] = None


class PatientCreateRequest(PatientBase):
    """Request model for creating a new patient"""
    organization_id: str


class PatientUpdateRequest(CustomModel):
    """Request model for updating a patient"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    activity_status: Optional[ActivityStatus] = None
    treatment_notes: Optional[str] = None


# Error response models
class PatientNotFoundError(CustomModel):
    """Error response when patient is not found"""
    error: str = "Patient not found"
    detail: str
    patient_id: Optional[str] = None
    organization_id: str
    timestamp: datetime


class PatientValidationError(CustomModel):
    """Error response for patient validation errors"""
    error: str = "Validation error"
    detail: str
    field_errors: Dict[str, List[str]]
    timestamp: datetime


# Export all schemas
__all__ = [
    # Enums
    "ActivityStatus",
    "Priority", 
    "EngagementFilter",
    
    # Base models
    "PatientBase",
    "Patient",
    "PatientWithPriority",
    
    # Response models
    "PatientSummaryResponse",
    "PatientListResponse",
    "PatientListEnhancedResponse",
    "AppointmentTypeSummaryResponse",
    "EngagementStatsResponse",
    "PatientByAppointmentTypeResponse",
    "TestRouterResponse",
    
    # Supporting models
    "PatientSummaryStats",
    "AppointmentType",
    "AppointmentTypeSummary",
    "EngagementStats",
    
    # Request models
    "PatientListRequest",
    "PatientCreateRequest",
    "PatientUpdateRequest",
    
    # Error models
    "PatientNotFoundError",
    "PatientValidationError",
] 