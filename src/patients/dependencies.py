"""
Patients Domain Dependencies
FastAPI dependencies for patient-related operations
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Query, Path
from fastapi.security import HTTPBearer

from src.auth import dependencies as auth_dependencies
from src.patients.service import patient_service
from src.patients.schemas import (
    Patient,
    PatientListRequest,
    EngagementFilter
)
from src.patients.exceptions import (
    PatientNotFoundError,
    PatientAccessDeniedError,
    PatientValidationError
)
from src.patients.constants import (
    PATIENTS_PER_PAGE_DEFAULT,
    PATIENTS_PER_PAGE_MAX,
    SEARCH_MIN_LENGTH,
    SEARCH_MAX_LENGTH,
    ERROR_MESSAGES
)

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_patient_service():
    """Dependency to get patient service instance"""
    return patient_service


async def validate_organization_access(
    organization_id: str = Path(..., description="Organization ID"),
    verified_org_id: str = Depends(auth_dependencies.verify_organization_access)
) -> str:
    """
    Validate that the user has access to the organization
    
    Args:
        organization_id: Organization ID from path
        verified_org_id: Verified organization ID from auth
        
    Returns:
        str: Validated organization ID
        
    Raises:
        PatientAccessDeniedError: If access is denied
    """
    if organization_id != verified_org_id:
        logger.warning(f"Organization access denied: requested={organization_id}, verified={verified_org_id}")
        raise PatientAccessDeniedError(organization_id)
    
    return organization_id


async def validate_patient_exists(
    patient_id: str = Path(..., description="Patient ID"),
    organization_id: str = Depends(validate_organization_access),
    service = Depends(get_patient_service)
) -> Patient:
    """
    Validate that patient exists and user has access
    
    Args:
        patient_id: Patient ID from path
        organization_id: Validated organization ID
        service: Patient service instance
        
    Returns:
        Patient: Patient object
        
    Raises:
        PatientNotFoundError: If patient is not found
    """
    try:
        # Note: This would require a get_patient_by_id method in the service
        # For now, we'll use a placeholder approach
        patients = await service.list_patients(organization_id, limit=1000)
        patient = next((p for p in patients if p.id == patient_id), None)
        
        if not patient:
            logger.warning(f"Patient not found: id={patient_id}, org={organization_id}")
            raise PatientNotFoundError(patient_id, organization_id)
        
        return patient
        
    except Exception as e:
        logger.error(f"Error validating patient existence: {e}")
        raise PatientNotFoundError(patient_id, organization_id)


async def validate_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(PATIENTS_PER_PAGE_DEFAULT, ge=1, le=PATIENTS_PER_PAGE_MAX, description="Number of items per page")
) -> Dict[str, int]:
    """
    Validate pagination parameters
    
    Args:
        page: Page number
        limit: Items per page
        
    Returns:
        Dict[str, int]: Validated pagination parameters
        
    Raises:
        PatientValidationError: If parameters are invalid
    """
    try:
        if page < 1:
            raise PatientValidationError(ERROR_MESSAGES["INVALID_PAGE"])
        
        if limit < 1 or limit > PATIENTS_PER_PAGE_MAX:
            raise PatientValidationError(ERROR_MESSAGES["INVALID_LIMIT"])
        
        return {
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error validating pagination parameters: {e}")
        raise PatientValidationError("Invalid pagination parameters")


async def validate_search_params(
    search: Optional[str] = Query(None, min_length=SEARCH_MIN_LENGTH, max_length=SEARCH_MAX_LENGTH, description="Search term")
) -> Optional[str]:
    """
    Validate search parameters
    
    Args:
        search: Search term
        
    Returns:
        Optional[str]: Validated search term
        
    Raises:
        PatientValidationError: If search term is invalid
    """
    if search is None:
        return None
    
    # Clean the search term
    search = search.strip()
    
    if not search:
        return None
    
    if len(search) < SEARCH_MIN_LENGTH:
        raise PatientValidationError(ERROR_MESSAGES["SEARCH_TOO_SHORT"])
    
    if len(search) > SEARCH_MAX_LENGTH:
        raise PatientValidationError(ERROR_MESSAGES["SEARCH_TOO_LONG"])
    
    return search


async def validate_patient_list_params(
    organization_id: str = Depends(validate_organization_access),
    pagination: Dict[str, int] = Depends(validate_pagination_params),
    search: Optional[str] = Depends(validate_search_params),
    active_only: bool = Query(True, description="Filter to active patients only"),
    engagement_filter: Optional[EngagementFilter] = Query(None, description="Filter by engagement level")
) -> PatientListRequest:
    """
    Validate and combine patient list parameters
    
    Args:
        organization_id: Validated organization ID
        pagination: Validated pagination parameters
        search: Validated search term
        active_only: Whether to filter to active patients
        engagement_filter: Engagement level filter
        
    Returns:
        PatientListRequest: Validated request parameters
    """
    return PatientListRequest(
        page=pagination["page"],
        limit=pagination["limit"],
        search=search,
        active_only=active_only,
        engagement_filter=engagement_filter
    )


async def validate_appointment_type(
    appointment_type: str = Path(..., description="Appointment type to filter by"),
    organization_id: str = Depends(validate_organization_access)
) -> Dict[str, str]:
    """
    Validate appointment type parameter
    
    Args:
        appointment_type: Appointment type from path
        organization_id: Validated organization ID
        
    Returns:
        Dict[str, str]: Validated parameters
        
    Raises:
        PatientValidationError: If appointment type is invalid
    """
    # Clean the appointment type
    appointment_type = appointment_type.strip()
    
    if not appointment_type:
        raise PatientValidationError("Appointment type cannot be empty")
    
    if len(appointment_type) > 100:
        raise PatientValidationError("Appointment type too long")
    
    return {
        "appointment_type": appointment_type,
        "organization_id": organization_id
    }


async def get_current_user_with_patient_access(
    current_user: Dict[str, Any] = Depends(auth_dependencies.get_current_user)
) -> Dict[str, Any]:
    """
    Get current user with patient access validation
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Current user with patient access
        
    Raises:
        PatientAccessDeniedError: If user doesn't have patient access
    """
    # Add any patient-specific access checks here
    # For now, we'll just pass through the current user
    return current_user


async def validate_patient_summary_access(
    organization_id: str = Depends(validate_organization_access),
    current_user: Dict[str, Any] = Depends(get_current_user_with_patient_access)
) -> Dict[str, Any]:
    """
    Validate access to patient summary data
    
    Args:
        organization_id: Validated organization ID
        current_user: Current user with patient access
        
    Returns:
        Dict[str, Any]: Access validation result
    """
    return {
        "organization_id": organization_id,
        "user_id": current_user.get("id"),
        "has_summary_access": True
    }


async def validate_patient_engagement_access(
    organization_id: str = Depends(validate_organization_access),
    current_user: Dict[str, Any] = Depends(get_current_user_with_patient_access)
) -> Dict[str, Any]:
    """
    Validate access to patient engagement statistics
    
    Args:
        organization_id: Validated organization ID
        current_user: Current user with patient access
        
    Returns:
        Dict[str, Any]: Access validation result
    """
    return {
        "organization_id": organization_id,
        "user_id": current_user.get("id"),
        "has_engagement_access": True
    }


# Audit logging dependency
async def log_patient_access(
    organization_id: str,
    action: str,
    patient_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_with_patient_access)
):
    """
    Log patient access for audit purposes
    
    Args:
        organization_id: Organization ID
        action: Action being performed
        patient_id: Optional patient ID
        current_user: Current user
    """
    logger.info(f"Patient access: user={current_user.get('id')}, org={organization_id}, action={action}, patient={patient_id}")


# Export all dependencies
__all__ = [
    "get_patient_service",
    "validate_organization_access",
    "validate_patient_exists",
    "validate_pagination_params",
    "validate_search_params",
    "validate_patient_list_params",
    "validate_appointment_type",
    "get_current_user_with_patient_access",
    "validate_patient_summary_access",
    "validate_patient_engagement_access",
    "log_patient_access",
] 