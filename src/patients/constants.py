"""
Patients Domain Constants
Constants and configuration values for patient management
"""

from enum import Enum
from typing import Dict, Any

# Pagination constants
PATIENTS_PER_PAGE_DEFAULT = 50
PATIENTS_PER_PAGE_MAX = 500

# Priority calculation constants (in hours)
PRIORITY_HOURS_HIGH = 24
PRIORITY_HOURS_MEDIUM = 72

# Search constants
SEARCH_MIN_LENGTH = 2
SEARCH_MAX_LENGTH = 100

# Appointment constants
MAX_APPOINTMENTS_PER_PATIENT = 1000
MAX_RECENT_APPOINTMENTS = 10
MAX_UPCOMING_APPOINTMENTS = 10

# Sync constants
SYNC_BATCH_SIZE = 100
SYNC_TIMEOUT_SECONDS = 300

# Patient status constants
class PatientStatus(str, Enum):
    """Patient status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class PatientEngagementLevel(str, Enum):
    """Patient engagement level enumeration"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class PatientPriority(str, Enum):
    """Patient priority enumeration"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AppointmentStatus(str, Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


# Database field limits
FIELD_LIMITS = {
    "name": 255,
    "phone": 20,
    "email": 255,
    "cliniko_patient_id": 50,
    "treatment_notes": 1000,
    "appointment_type": 100,
    "activity_status": 50,
}

# Error messages
ERROR_MESSAGES = {
    "PATIENT_NOT_FOUND": "Patient not found",
    "INVALID_ORGANIZATION": "Invalid organization ID",
    "ACCESS_DENIED": "Access denied to patient data",
    "VALIDATION_ERROR": "Patient data validation failed",
    "DATABASE_ERROR": "Database operation failed",
    "SYNC_ERROR": "Patient sync operation failed",
    "SEARCH_TOO_SHORT": f"Search term must be at least {SEARCH_MIN_LENGTH} characters",
    "SEARCH_TOO_LONG": f"Search term cannot exceed {SEARCH_MAX_LENGTH} characters",
    "INVALID_PAGE": "Invalid page number",
    "INVALID_LIMIT": f"Limit must be between 1 and {PATIENTS_PER_PAGE_MAX}",
}

# Default values
DEFAULT_VALUES = {
    "is_active": True,
    "activity_status": PatientStatus.ACTIVE.value,
    "recent_appointment_count": 0,
    "upcoming_appointment_count": 0,
    "total_appointment_count": 0,
    "engagement_level": PatientEngagementLevel.NONE.value,
    "priority": PatientPriority.LOW.value,
}

# Validation rules
VALIDATION_RULES = {
    "name": {
        "required": True,
        "min_length": 1,
        "max_length": FIELD_LIMITS["name"],
        "pattern": r"^[a-zA-Z\s\-\.\'\,]+$",
    },
    "phone": {
        "required": False,
        "min_length": 10,
        "max_length": FIELD_LIMITS["phone"],
        "pattern": r"^[\+]?[1-9][\d\s\-\(\)]{8,}$",
    },
    "email": {
        "required": False,
        "min_length": 5,
        "max_length": FIELD_LIMITS["email"],
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    },
    "cliniko_patient_id": {
        "required": False,
        "min_length": 1,
        "max_length": FIELD_LIMITS["cliniko_patient_id"],
        "pattern": r"^[0-9]+$",
    },
}

# API response templates
API_RESPONSES = {
    "SUCCESS": {
        "status": "success",
        "message": "Operation completed successfully",
    },
    "ERROR": {
        "status": "error",
        "message": "Operation failed",
    },
    "VALIDATION_ERROR": {
        "status": "error",
        "message": "Validation failed",
        "errors": {},
    },
}

# Cache settings
CACHE_SETTINGS = {
    "patient_summary_ttl": 300,  # 5 minutes
    "patient_list_ttl": 180,     # 3 minutes
    "engagement_stats_ttl": 600, # 10 minutes
    "appointment_types_ttl": 900, # 15 minutes
}

# Export all constants
__all__ = [
    # Pagination
    "PATIENTS_PER_PAGE_DEFAULT",
    "PATIENTS_PER_PAGE_MAX",
    
    # Priority
    "PRIORITY_HOURS_HIGH",
    "PRIORITY_HOURS_MEDIUM",
    
    # Search
    "SEARCH_MIN_LENGTH",
    "SEARCH_MAX_LENGTH",
    
    # Appointments
    "MAX_APPOINTMENTS_PER_PATIENT",
    "MAX_RECENT_APPOINTMENTS",
    "MAX_UPCOMING_APPOINTMENTS",
    
    # Sync
    "SYNC_BATCH_SIZE",
    "SYNC_TIMEOUT_SECONDS",
    
    # Enums
    "PatientStatus",
    "PatientEngagementLevel",
    "PatientPriority",
    "AppointmentStatus",
    
    # Data structures
    "FIELD_LIMITS",
    "ERROR_MESSAGES",
    "DEFAULT_VALUES",
    "VALIDATION_RULES",
    "API_RESPONSES",
    "CACHE_SETTINGS",
] 