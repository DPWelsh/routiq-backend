"""
Global Constants
Application-wide constants and enums
"""

from enum import Enum
from typing import Dict, Any


class APIStatus(str, Enum):
    """API response status constants"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncStatus(str, Enum):
    """Sync operation status constants"""
    IDLE = "idle"
    STARTING = "starting"
    FETCHING_PATIENTS = "fetching_patients"
    FETCHING_APPOINTMENTS = "fetching_appointments"
    ANALYZING = "analyzing"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    """User role constants"""
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class IntegrationStatus(str, Enum):
    """Integration status constants"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"
    TESTING = "testing"


class PatientStatus(str, Enum):
    """Patient status constants"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AppointmentStatus(str, Enum):
    """Appointment status constants"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class WebhookType(str, Enum):
    """Webhook type constants"""
    PATIENT_CREATED = "patient_created"
    PATIENT_UPDATED = "patient_updated"
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"


class CacheKeys:
    """Cache key constants"""
    PATIENT_PROFILE = "patient_profile:{patient_id}"
    ORGANIZATION_PATIENTS = "org_patients:{org_id}"
    SYNC_STATUS = "sync_status:{org_id}"
    DASHBOARD_SUMMARY = "dashboard_summary:{org_id}"
    INTEGRATION_CONFIG = "integration_config:{org_id}:{service}"


class Timeouts:
    """Timeout constants in seconds"""
    HTTP_REQUEST = 30
    DATABASE_QUERY = 60
    SYNC_OPERATION = 3600  # 1 hour
    CACHE_DEFAULT = 300    # 5 minutes
    CACHE_LONG = 1800      # 30 minutes


class Limits:
    """Application limits"""
    MAX_PATIENTS_PER_SYNC = 10000
    MAX_APPOINTMENTS_PER_SYNC = 50000
    MAX_CONCURRENT_SYNCS = 3
    MAX_RETRY_ATTEMPTS = 3
    MAX_WEBHOOK_RETRIES = 5
    MAX_FILE_SIZE_MB = 10
    MAX_EXPORT_RECORDS = 100000


class DateFormats:
    """Date format constants"""
    ISO_DATETIME = "%Y-%m-%dT%H:%M:%S.%fZ"
    ISO_DATE = "%Y-%m-%d"
    DISPLAY_DATETIME = "%Y-%m-%d %H:%M:%S"
    DISPLAY_DATE = "%B %d, %Y"


class Headers:
    """HTTP header constants"""
    ORGANIZATION_ID = "x-organization-id"
    REQUEST_ID = "x-request-id"
    API_VERSION = "x-api-version"
    CONTENT_TYPE = "content-type"
    AUTHORIZATION = "authorization"


class ErrorCodes:
    """Error code constants"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMIT = "RATE_LIMIT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    BUSINESS_LOGIC_ERROR = "BUSINESS_LOGIC_ERROR"


# API Response Templates
RESPONSE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "success": {
        "success": True,
        "message": "Operation completed successfully",
        "data": None,
        "timestamp": None
    },
    "error": {
        "success": False,
        "message": "An error occurred",
        "error": None,
        "timestamp": None
    },
    "validation_error": {
        "success": False,
        "message": "Validation failed",
        "errors": [],
        "timestamp": None
    }
} 