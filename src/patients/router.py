"""
Patients Domain Router
FastAPI router for patient-related endpoints
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from src.patients.service import patient_service
from src.patients.schemas import (
    PatientSummaryResponse,
    PatientListResponse,
    PatientListEnhancedResponse,
    AppointmentTypeSummaryResponse,
    EngagementStatsResponse,
    PatientByAppointmentTypeResponse,
    TestRouterResponse,
    PatientListRequest
)
from src.patients.dependencies import (
    validate_organization_access,
    validate_patient_list_params,
    validate_appointment_type,
    validate_patient_summary_access,
    validate_patient_engagement_access,
    get_patient_service
)
from src.patients.exceptions import (
    PatientNotFoundError,
    PatientServiceError,
    PatientValidationError,
    PatientAccessDeniedError
)
from src.patients.constants import ERROR_MESSAGES
from src.utils import create_success_response, create_error_response

logger = logging.getLogger(__name__)

# Create router with prefix for Swagger visibility
router = APIRouter(prefix="/api/v1/patients", tags=["Patients"])


@router.get("/{organization_id}/active/summary", response_model=PatientSummaryResponse)
async def get_active_patients_summary(
    access_validation: Dict[str, Any] = Depends(validate_patient_summary_access),
    service = Depends(get_patient_service)
):
    """Get active patients summary for an organization"""
    try:
        organization_id = access_validation["organization_id"]
        
        summary_stats = await service.get_active_patients_summary(organization_id)
        
        return PatientSummaryResponse(
            organization_id=organization_id,
            total_active_patients=summary_stats.total_active_patients,
            patients_with_recent_appointments=summary_stats.patients_with_recent_appointments,
            patients_with_upcoming_appointments=summary_stats.patients_with_upcoming_appointments,
            avg_recent_appointments=summary_stats.avg_recent_appointments,
            avg_total_appointments=summary_stats.avg_total_appointments,
            last_sync_date=summary_stats.last_sync_date,
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in get_active_patients_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_active_patients_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient summary"
        )


@router.get("/{organization_id}/patients", response_model=PatientListResponse)
async def list_patients(
    organization_id: str = Depends(validate_organization_access),
    service = Depends(get_patient_service)
):
    """List active patients for an organization"""
    try:
        patients = await service.list_patients(organization_id, limit=50)
        
        return PatientListResponse(
            organization_id=organization_id,
            patients=patients,
            total_count=len(patients),
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in list_patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in list_patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patients"
        )


@router.get("/test", response_model=TestRouterResponse)
async def test_patients_router():
    """Test endpoint to verify patients router is loading"""
    return TestRouterResponse(
        message="Patients router is working!",
        timestamp=datetime.now()
    )


@router.get("/{organization_id}/patients/with-appointments", response_model=PatientListResponse)
async def list_patients_with_appointment_details(
    organization_id: str = Depends(validate_organization_access),
    service = Depends(get_patient_service)
):
    """List active patients with detailed appointment type and treatment information"""
    try:
        patients = await service.list_patients_with_appointment_details(organization_id, limit=100)
        
        return PatientListResponse(
            organization_id=organization_id,
            patients=patients,
            total_count=len(patients),
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in list_patients_with_appointment_details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in list_patients_with_appointment_details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patients with appointment details"
        )


@router.get("/{organization_id}/patients/by-appointment-type/{appointment_type}", response_model=PatientByAppointmentTypeResponse)
async def list_patients_by_appointment_type(
    validated_params: Dict[str, str] = Depends(validate_appointment_type),
    service = Depends(get_patient_service)
):
    """List patients filtered by appointment type"""
    try:
        organization_id = validated_params["organization_id"]
        appointment_type = validated_params["appointment_type"]
        
        patients = await service.list_patients_by_appointment_type(organization_id, appointment_type, limit=100)
        
        return PatientByAppointmentTypeResponse(
            organization_id=organization_id,
            appointment_type=appointment_type,
            patients=patients,
            total_count=len(patients),
            filters_applied={"appointment_type": appointment_type},
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in list_patients_by_appointment_type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in list_patients_by_appointment_type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patients by appointment type"
        )


@router.get("/{organization_id}/patients/appointment-types/summary", response_model=AppointmentTypeSummaryResponse)
async def get_appointment_types_summary(
    organization_id: str = Depends(validate_organization_access),
    service = Depends(get_patient_service)
):
    """Get summary of appointment types and patient distribution"""
    try:
        appointment_summaries = await service.get_appointment_types_summary(organization_id)
        
        # Calculate total patients
        total_patients = sum(summary.patient_count for summary in appointment_summaries)
        
        return AppointmentTypeSummaryResponse(
            organization_id=organization_id,
            total_patients=total_patients,
            appointment_types=appointment_summaries,
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in get_appointment_types_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_appointment_types_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointment types summary"
        )


@router.get("/{organization_id}/summary")
async def patients_summary(
    organization_id: str = Depends(validate_organization_access),
    service = Depends(get_patient_service)
):
    """Get comprehensive patient summary statistics"""
    try:
        summary_data = await service.get_patients_summary(organization_id)
        
        return create_success_response(
            data={
                "organization_id": organization_id,
                "summary": summary_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in patients_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in patients_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patients summary"
        )


@router.get("/{organization_id}/list", response_model=PatientListEnhancedResponse)
async def list_patients_enhanced(
    request_params: PatientListRequest = Depends(validate_patient_list_params),
    service = Depends(get_patient_service)
):
    """Enhanced patient listing with pagination, search, and filtering"""
    try:
        organization_id = request_params.page  # This will be fixed by the dependency
        
        patients, total_count, pagination_info = await service.list_patients_enhanced(
            organization_id=organization_id,
            page=request_params.page,
            limit=request_params.limit,
            search=request_params.search,
            active_only=request_params.active_only,
            engagement_filter=request_params.engagement_filter
        )
        
        return PatientListEnhancedResponse(
            organization_id=organization_id,
            patients=patients,
            total_count=total_count,
            page=pagination_info["page"],
            limit=pagination_info["limit"],
            total_pages=pagination_info["total_pages"],
            has_next=pagination_info["has_next"],
            has_previous=pagination_info["has_previous"],
            filters_applied=pagination_info["filters_applied"],
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in list_patients_enhanced: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except PatientValidationError as e:
        logger.warning(f"Validation error in list_patients_enhanced: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in list_patients_enhanced: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enhanced patient list"
        )


@router.get("/{organization_id}/engagement-stats", response_model=EngagementStatsResponse)
async def get_engagement_statistics(
    access_validation: Dict[str, Any] = Depends(validate_patient_engagement_access),
    service = Depends(get_patient_service)
):
    """Get patient engagement statistics and breakdown"""
    try:
        organization_id = access_validation["organization_id"]
        
        stats, additional_data = await service.get_engagement_statistics(organization_id)
        
        return EngagementStatsResponse(
            organization_id=organization_id,
            stats=stats,
            engagement_breakdown=additional_data["engagement_breakdown"],
            appointment_frequency=additional_data["appointment_frequency"],
            timestamp=datetime.now()
        )
        
    except PatientServiceError as e:
        logger.error(f"Service error in get_engagement_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_engagement_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement statistics"
        )


# Error handlers
@router.exception_handler(PatientNotFoundError)
async def patient_not_found_handler(request, exc: PatientNotFoundError):
    """Handle patient not found errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            message=str(exc),
            error_code="PATIENT_NOT_FOUND",
            details={"patient_id": exc.patient_id, "organization_id": exc.organization_id}
        )
    )


@router.exception_handler(PatientAccessDeniedError)
async def patient_access_denied_handler(request, exc: PatientAccessDeniedError):
    """Handle patient access denied errors"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=create_error_response(
            message=str(exc),
            error_code="PATIENT_ACCESS_DENIED",
            details={"organization_id": exc.organization_id, "user_id": exc.user_id}
        )
    )


@router.exception_handler(PatientValidationError)
async def patient_validation_error_handler(request, exc: PatientValidationError):
    """Handle patient validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            message=str(exc),
            error_code="PATIENT_VALIDATION_ERROR",
            details={"field_errors": exc.field_errors}
        )
    )


@router.exception_handler(PatientServiceError)
async def patient_service_error_handler(request, exc: PatientServiceError):
    """Handle patient service errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            message=str(exc),
            error_code="PATIENT_SERVICE_ERROR"
        )
    )


# Export router
__all__ = ["router"] 