"""
Patients Domain Configuration
Environment-specific settings for patient management
"""

from typing import Optional, List
from pydantic import BaseSettings, Field, validator
from datetime import timedelta

from src.config import Environment


class PatientConfig(BaseSettings):
    """Configuration settings for patient management"""
    
    # Database settings
    PATIENT_DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size for patient operations")
    PATIENT_DB_MAX_OVERFLOW: int = Field(default=10, description="Maximum database connection overflow")
    PATIENT_DB_TIMEOUT: int = Field(default=30, description="Database query timeout in seconds")
    
    # Pagination settings
    PATIENT_DEFAULT_PAGE_SIZE: int = Field(default=50, description="Default number of patients per page")
    PATIENT_MAX_PAGE_SIZE: int = Field(default=500, description="Maximum number of patients per page")
    
    # Search settings
    PATIENT_SEARCH_MIN_LENGTH: int = Field(default=2, description="Minimum search term length")
    PATIENT_SEARCH_MAX_LENGTH: int = Field(default=100, description="Maximum search term length")
    PATIENT_SEARCH_TIMEOUT: int = Field(default=10, description="Search timeout in seconds")
    
    # Cache settings
    PATIENT_CACHE_ENABLED: bool = Field(default=True, description="Enable patient data caching")
    PATIENT_CACHE_TTL: int = Field(default=300, description="Patient cache TTL in seconds")
    PATIENT_SUMMARY_CACHE_TTL: int = Field(default=600, description="Patient summary cache TTL in seconds")
    PATIENT_ENGAGEMENT_CACHE_TTL: int = Field(default=900, description="Patient engagement cache TTL in seconds")
    
    # Sync settings
    PATIENT_SYNC_ENABLED: bool = Field(default=True, description="Enable patient data synchronization")
    PATIENT_SYNC_BATCH_SIZE: int = Field(default=100, description="Batch size for patient sync operations")
    PATIENT_SYNC_TIMEOUT: int = Field(default=300, description="Sync timeout in seconds")
    PATIENT_SYNC_RETRY_COUNT: int = Field(default=3, description="Number of sync retries")
    PATIENT_SYNC_RETRY_DELAY: int = Field(default=60, description="Sync retry delay in seconds")
    
    # Priority calculation settings
    PATIENT_PRIORITY_HIGH_HOURS: int = Field(default=24, description="Hours for high priority classification")
    PATIENT_PRIORITY_MEDIUM_HOURS: int = Field(default=72, description="Hours for medium priority classification")
    
    # Appointment settings
    PATIENT_MAX_APPOINTMENTS: int = Field(default=1000, description="Maximum appointments per patient")
    PATIENT_MAX_RECENT_APPOINTMENTS: int = Field(default=10, description="Maximum recent appointments to track")
    PATIENT_MAX_UPCOMING_APPOINTMENTS: int = Field(default=10, description="Maximum upcoming appointments to track")
    
    # Validation settings
    PATIENT_NAME_MAX_LENGTH: int = Field(default=255, description="Maximum patient name length")
    PATIENT_PHONE_MAX_LENGTH: int = Field(default=20, description="Maximum phone number length")
    PATIENT_EMAIL_MAX_LENGTH: int = Field(default=255, description="Maximum email length")
    PATIENT_NOTES_MAX_LENGTH: int = Field(default=1000, description="Maximum treatment notes length")
    
    # API settings
    PATIENT_API_RATE_LIMIT: int = Field(default=100, description="Patient API rate limit per minute")
    PATIENT_API_BURST_LIMIT: int = Field(default=200, description="Patient API burst limit")
    
    # Export settings
    PATIENT_EXPORT_MAX_RECORDS: int = Field(default=10000, description="Maximum records per export")
    PATIENT_EXPORT_TIMEOUT: int = Field(default=600, description="Export timeout in seconds")
    PATIENT_EXPORT_FORMATS: List[str] = Field(default=["csv", "xlsx", "json"], description="Supported export formats")
    
    # Audit settings
    PATIENT_AUDIT_ENABLED: bool = Field(default=True, description="Enable patient audit logging")
    PATIENT_AUDIT_RETENTION_DAYS: int = Field(default=90, description="Audit log retention in days")
    
    # Performance settings
    PATIENT_QUERY_OPTIMIZATION: bool = Field(default=True, description="Enable query optimization")
    PATIENT_INDEX_HINTS: bool = Field(default=True, description="Enable database index hints")
    PATIENT_PARALLEL_QUERIES: bool = Field(default=False, description="Enable parallel query execution")
    
    # Security settings
    PATIENT_PII_MASKING: bool = Field(default=True, description="Enable PII masking in logs")
    PATIENT_ACCESS_LOGGING: bool = Field(default=True, description="Enable patient access logging")
    PATIENT_DATA_RETENTION_DAYS: int = Field(default=2555, description="Patient data retention in days (7 years)")
    
    # Integration settings
    CLINIKO_SYNC_ENABLED: bool = Field(default=True, description="Enable Cliniko synchronization")
    CLINIKO_SYNC_INTERVAL: int = Field(default=3600, description="Cliniko sync interval in seconds")
    CLINIKO_BATCH_SIZE: int = Field(default=50, description="Cliniko API batch size")
    
    # Feature flags
    PATIENT_ENGAGEMENT_ANALYTICS: bool = Field(default=True, description="Enable engagement analytics")
    PATIENT_PRIORITY_SCORING: bool = Field(default=True, description="Enable priority scoring")
    PATIENT_PREDICTIVE_ANALYTICS: bool = Field(default=False, description="Enable predictive analytics")
    PATIENT_AUTOMATED_WORKFLOWS: bool = Field(default=False, description="Enable automated workflows")
    
    # Notification settings
    PATIENT_NOTIFICATION_ENABLED: bool = Field(default=True, description="Enable patient notifications")
    PATIENT_REMINDER_ENABLED: bool = Field(default=True, description="Enable patient reminders")
    PATIENT_ALERT_ENABLED: bool = Field(default=True, description="Enable patient alerts")
    
    @validator('PATIENT_DEFAULT_PAGE_SIZE')
    def validate_default_page_size(cls, v, values):
        """Validate default page size"""
        max_size = values.get('PATIENT_MAX_PAGE_SIZE', 500)
        if v > max_size:
            raise ValueError(f"Default page size cannot exceed maximum page size ({max_size})")
        return v
    
    @validator('PATIENT_SEARCH_MIN_LENGTH')
    def validate_search_min_length(cls, v):
        """Validate search minimum length"""
        if v < 1:
            raise ValueError("Search minimum length must be at least 1")
        return v
    
    @validator('PATIENT_SEARCH_MAX_LENGTH')
    def validate_search_max_length(cls, v, values):
        """Validate search maximum length"""
        min_length = values.get('PATIENT_SEARCH_MIN_LENGTH', 2)
        if v < min_length:
            raise ValueError(f"Search maximum length must be at least {min_length}")
        return v
    
    @validator('PATIENT_PRIORITY_HIGH_HOURS')
    def validate_priority_hours(cls, v, values):
        """Validate priority hours"""
        if v < 1:
            raise ValueError("Priority hours must be at least 1")
        return v
    
    @validator('PATIENT_PRIORITY_MEDIUM_HOURS')
    def validate_medium_priority_hours(cls, v, values):
        """Validate medium priority hours"""
        high_hours = values.get('PATIENT_PRIORITY_HIGH_HOURS', 24)
        if v <= high_hours:
            raise ValueError(f"Medium priority hours must be greater than high priority hours ({high_hours})")
        return v
    
    @validator('PATIENT_EXPORT_FORMATS')
    def validate_export_formats(cls, v):
        """Validate export formats"""
        supported_formats = ["csv", "xlsx", "json", "xml", "pdf"]
        for fmt in v:
            if fmt not in supported_formats:
                raise ValueError(f"Unsupported export format: {fmt}")
        return v
    
    @validator('PATIENT_DATA_RETENTION_DAYS')
    def validate_retention_days(cls, v):
        """Validate data retention days"""
        if v < 30:
            raise ValueError("Data retention must be at least 30 days")
        return v
    
    class Config:
        """Pydantic configuration"""
        env_prefix = "PATIENT_"
        case_sensitive = True
        validate_assignment = True
        extra = "forbid"


class PatientDevelopmentConfig(PatientConfig):
    """Development-specific patient configuration"""
    
    # Development overrides
    PATIENT_CACHE_ENABLED: bool = False
    PATIENT_CACHE_TTL: int = 60
    PATIENT_AUDIT_ENABLED: bool = True
    PATIENT_PII_MASKING: bool = False
    PATIENT_PARALLEL_QUERIES: bool = False
    PATIENT_PREDICTIVE_ANALYTICS: bool = True
    PATIENT_AUTOMATED_WORKFLOWS: bool = True


class PatientProductionConfig(PatientConfig):
    """Production-specific patient configuration"""
    
    # Production overrides
    PATIENT_CACHE_ENABLED: bool = True
    PATIENT_CACHE_TTL: int = 600
    PATIENT_AUDIT_ENABLED: bool = True
    PATIENT_PII_MASKING: bool = True
    PATIENT_PARALLEL_QUERIES: bool = True
    PATIENT_PREDICTIVE_ANALYTICS: bool = False
    PATIENT_AUTOMATED_WORKFLOWS: bool = False
    PATIENT_API_RATE_LIMIT: int = 60
    PATIENT_API_BURST_LIMIT: int = 100


class PatientTestingConfig(PatientConfig):
    """Testing-specific patient configuration"""
    
    # Testing overrides
    PATIENT_CACHE_ENABLED: bool = False
    PATIENT_SYNC_ENABLED: bool = False
    PATIENT_AUDIT_ENABLED: bool = False
    PATIENT_NOTIFICATION_ENABLED: bool = False
    PATIENT_REMINDER_ENABLED: bool = False
    PATIENT_ALERT_ENABLED: bool = False
    PATIENT_DEFAULT_PAGE_SIZE: int = 10
    PATIENT_MAX_PAGE_SIZE: int = 50
    PATIENT_EXPORT_MAX_RECORDS: int = 100


def get_patient_config(environment: Environment = Environment.PRODUCTION) -> PatientConfig:
    """
    Get patient configuration based on environment
    
    Args:
        environment: Target environment
        
    Returns:
        PatientConfig: Environment-specific configuration
    """
    config_map = {
        Environment.DEVELOPMENT: PatientDevelopmentConfig,
        Environment.STAGING: PatientConfig,
        Environment.PRODUCTION: PatientProductionConfig,
        Environment.TESTING: PatientTestingConfig,
    }
    
    config_class = config_map.get(environment, PatientConfig)
    return config_class()


# Global configuration instance
patient_config = get_patient_config()


# Export configuration
__all__ = [
    "PatientConfig",
    "PatientDevelopmentConfig",
    "PatientProductionConfig",
    "PatientTestingConfig",
    "get_patient_config",
    "patient_config",
] 