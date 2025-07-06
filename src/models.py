"""
Global Models and Base Classes
Custom Pydantic models with enhanced functionality
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, validator
from fastapi.encoders import jsonable_encoder

from src.utils import datetime_to_gmt_str, utc_now


class CustomModel(BaseModel):
    """
    Custom base model with enhanced functionality
    - Standardized datetime serialization
    - Common validation methods
    - Serialization helpers
    """
    
    model_config = ConfigDict(
        # Serialize datetime objects to ISO format with timezone
        json_encoders={datetime: datetime_to_gmt_str},
        # Allow population by field names or aliases
        populate_by_name=True,
        # Validate assignments after model creation
        validate_assignment=True,
        # Use enum values instead of enum names
        use_enum_values=True,
        # Include extra fields in serialization
        extra="forbid",
        # Validate default values
        validate_default=True,
        # String constraints
        str_strip_whitespace=True,
    )
    
    def serializable_dict(self, **kwargs) -> Dict[str, Any]:
        """
        Return a dictionary containing only serializable fields
        Safe for JSON serialization
        """
        default_dict = self.model_dump(**kwargs)
        return jsonable_encoder(default_dict)
    
    def dict_without_none(self, **kwargs) -> Dict[str, Any]:
        """Return dictionary excluding None values"""
        data = self.model_dump(**kwargs)
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomModel":
        """Create model instance from dictionary"""
        return cls(**data)


class TimestampedModel(CustomModel):
    """
    Base model with automatic timestamp fields
    """
    
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    @validator('created_at', 'updated_at', pre=True)
    def ensure_utc_timezone(cls, v):
        """Ensure timestamps have UTC timezone"""
        if v and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=None)  # Will be handled by datetime_to_gmt_str
        return v


class BaseResponse(CustomModel):
    """
    Base response model for API endpoints
    """
    
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(default="Operation completed successfully", description="Response message")
    timestamp: datetime = Field(default_factory=utc_now, description="Response timestamp")


class BaseListResponse(BaseResponse):
    """
    Base response model for list endpoints
    """
    
    total_count: int = Field(default=0, description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of items per page")
    
    @validator('page', 'page_size')
    def validate_pagination(cls, v):
        """Validate pagination parameters"""
        if v < 1:
            raise ValueError("Page and page_size must be greater than 0")
        return v


class ErrorResponse(CustomModel):
    """
    Standard error response model
    """
    
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(description="Error type or code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=utc_now, description="Error timestamp")


class ValidationErrorResponse(ErrorResponse):
    """
    Validation error response model
    """
    
    errors: list = Field(default_factory=list, description="List of validation errors")


class PaginationParams(CustomModel):
    """
    Common pagination parameters
    """
    
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries"""
        return self.page_size


class SortParams(CustomModel):
    """
    Common sorting parameters
    """
    
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order"""
        if v and v.lower() not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower() if v else v


class FilterParams(CustomModel):
    """
    Common filtering parameters
    """
    
    search: Optional[str] = Field(default=None, description="Search query")
    status: Optional[str] = Field(default=None, description="Filter by status")
    created_after: Optional[datetime] = Field(default=None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(default=None, description="Filter by creation date")
    
    @validator('created_after', 'created_before', pre=True)
    def parse_datetime_strings(cls, v):
        """Parse datetime strings to datetime objects"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid datetime format: {v}")
        return v


class OrganizationScopedModel(CustomModel):
    """
    Base model for organization-scoped resources
    """
    
    organization_id: str = Field(description="Organization identifier")
    
    @validator('organization_id')
    def validate_organization_id(cls, v):
        """Validate organization ID format"""
        if not v or not v.startswith('org_'):
            raise ValueError("Organization ID must start with 'org_'")
        return v


class UserScopedModel(CustomModel):
    """
    Base model for user-scoped resources
    """
    
    user_id: str = Field(description="User identifier")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format"""
        if not v:
            raise ValueError("User ID is required")
        return v


class AuditModel(TimestampedModel):
    """
    Base model with audit fields
    """
    
    created_by: Optional[str] = Field(default=None, description="User who created the record")
    updated_by: Optional[str] = Field(default=None, description="User who last updated the record")
    version: int = Field(default=1, description="Record version for optimistic locking")
    
    def increment_version(self):
        """Increment version number"""
        self.version += 1
        self.updated_at = utc_now()


class SoftDeleteModel(AuditModel):
    """
    Base model with soft delete functionality
    """
    
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")
    deleted_by: Optional[str] = Field(default=None, description="User who deleted the record")
    
    def soft_delete(self, deleted_by: Optional[str] = None):
        """Mark record as soft deleted"""
        self.is_deleted = True
        self.deleted_at = utc_now()
        self.deleted_by = deleted_by
        self.increment_version()
    
    def restore(self, updated_by: Optional[str] = None):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.updated_by = updated_by
        self.increment_version()


# Export commonly used models
__all__ = [
    "CustomModel",
    "TimestampedModel", 
    "BaseResponse",
    "BaseListResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    "PaginationParams",
    "SortParams",
    "FilterParams",
    "OrganizationScopedModel",
    "UserScopedModel",
    "AuditModel",
    "SoftDeleteModel",
] 