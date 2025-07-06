"""
Patients Domain Exceptions
Custom exceptions for patient-related operations
"""

from typing import Optional, Dict, Any
from src.exceptions import BaseAPIException


class PatientError(BaseAPIException):
    """Base exception for patient-related errors"""
    pass


class PatientNotFoundError(PatientError):
    """Exception raised when a patient is not found"""
    
    def __init__(self, patient_id: Optional[str] = None, organization_id: Optional[str] = None):
        self.patient_id = patient_id
        self.organization_id = organization_id
        
        if patient_id and organization_id:
            message = f"Patient {patient_id} not found in organization {organization_id}"
        elif patient_id:
            message = f"Patient {patient_id} not found"
        else:
            message = "Patient not found"
            
        super().__init__(message)


class PatientValidationError(PatientError):
    """Exception raised when patient data validation fails"""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, Any]] = None):
        self.field_errors = field_errors or {}
        super().__init__(message)


class PatientServiceError(PatientError):
    """Exception raised when patient service operations fail"""
    pass


class PatientAccessDeniedError(PatientError):
    """Exception raised when user doesn't have access to patient data"""
    
    def __init__(self, organization_id: str, user_id: Optional[str] = None):
        self.organization_id = organization_id
        self.user_id = user_id
        
        message = f"Access denied to patient data for organization {organization_id}"
        if user_id:
            message += f" for user {user_id}"
            
        super().__init__(message)


class PatientSyncError(PatientError):
    """Exception raised when patient sync operations fail"""
    pass


class PatientDatabaseError(PatientError):
    """Exception raised when database operations fail"""
    pass


class PatientBusinessLogicError(PatientError):
    """Exception raised when business logic validation fails"""
    pass


# Export all exceptions
__all__ = [
    "PatientError",
    "PatientNotFoundError",
    "PatientValidationError",
    "PatientServiceError",
    "PatientAccessDeniedError",
    "PatientSyncError",
    "PatientDatabaseError",
    "PatientBusinessLogicError",
] 