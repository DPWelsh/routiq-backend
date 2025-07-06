"""
Authentication Domain Router
FastAPI router for authentication endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from src.auth.dependencies import (
    get_current_user, 
    verify_organization_access, 
    require_organization_access,
    security
)
from src.auth.schemas import (
    AuthResponse, 
    OrganizationAccessResponse,
    UserOrganizationsResponse,
    TokenValidationRequest
)
from src.auth.service import jwt_validator
from src.auth.exceptions import (
    TokenValidationError,
    OrganizationAccessError,
    UserNotFoundError
)
from src.auth.constants import AuthAction, AuthErrorMessages

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        500: {"description": "Internal Server Error"}
    }
)


@router.get("/verify", response_model=AuthResponse)
async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
):
    """
    Verify authentication token and return authentication status
    
    This endpoint validates a JWT token and returns the authentication status.
    It can optionally verify organization access if the x-organization-id header is provided.
    
    Returns:
        AuthResponse: Authentication status and organization information
    """
    try:
        # Get current user from token
        user_data = await get_current_user(credentials, request)
        
        # Try to get organization ID from header (optional for this endpoint)
        from fastapi import Header
        x_organization_id: Optional[str] = request.headers.get("x-organization-id")
        
        organization_id = None
        if x_organization_id:
            try:
                # Verify organization access if organization ID provided
                organization_id = await verify_organization_access(
                    x_organization_id=x_organization_id,
                    user_data=user_data,
                    request=request
                )
            except HTTPException:
                # If organization verification fails, still return success for user auth
                # but indicate organization access failed
                pass
        
        logger.info(f"Authentication verification successful for user: {user_data['user_id']}")
        
        return AuthResponse(
            authenticated=True,
            user_id=user_data["user_id"],
            organization_id=organization_id,
            message="Authentication successful"
        )
        
    except HTTPException as e:
        logger.warning(f"Authentication verification failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Authentication verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail=AuthErrorMessages.TOKEN_INVALID
        )


@router.post("/verify-token", response_model=AuthResponse)
async def verify_token_endpoint(
    token_request: TokenValidationRequest,
    request: Request = None
):
    """
    Verify a JWT token directly (alternative to header-based verification)
    
    Args:
        token_request: Token validation request with JWT token
        request: FastAPI request object
        
    Returns:
        AuthResponse: Token validation result
    """
    try:
        # Verify token using service
        token_payload = await jwt_validator.verify_token(token_request.token)
        user_id = token_payload.get('sub')
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail=AuthErrorMessages.TOKEN_INVALID
            )
        
        logger.info(f"Token verification successful for user: {user_id}")
        
        return AuthResponse(
            authenticated=True,
            user_id=user_id,
            organization_id=None,
            message="Token verification successful"
        )
        
    except TokenValidationError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail=AuthErrorMessages.TOKEN_INVALID
        )


@router.get("/organization/{organization_id}/access", response_model=OrganizationAccessResponse)
async def check_organization_access(
    organization_id: str,
    user_data: dict = Depends(get_current_user),
    request: Request = None
):
    """
    Check if authenticated user has access to specific organization
    
    Args:
        organization_id: Organization ID to check access for
        user_data: Authenticated user data
        request: FastAPI request object
        
    Returns:
        OrganizationAccessResponse: Organization access status
    """
    try:
        # Verify organization access
        has_access = await jwt_validator.verify_organization_access(
            user_data["user_id"], 
            organization_id
        )
        
        if has_access:
            logger.info(f"Organization access granted for user {user_data['user_id']} to org {organization_id}")
            return OrganizationAccessResponse(
                organization_id=organization_id,
                access_granted=True,
                user_id=user_data["user_id"],
                message="Access granted"
            )
        else:
            logger.warning(f"Organization access denied for user {user_data['user_id']} to org {organization_id}")
            return OrganizationAccessResponse(
                organization_id=organization_id,
                access_granted=False,
                user_id=user_data["user_id"],
                message="Access denied"
            )
            
    except OrganizationAccessError as e:
        logger.warning(f"Organization access check failed: {e}")
        return OrganizationAccessResponse(
            organization_id=organization_id,
            access_granted=False,
            user_id=user_data["user_id"],
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Organization access check error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check organization access"
        )


@router.get("/user/organizations", response_model=UserOrganizationsResponse)
async def get_user_organizations(
    user_data: dict = Depends(get_current_user),
    request: Request = None
):
    """
    Get user's organization memberships
    
    Args:
        user_data: Authenticated user data
        request: FastAPI request object
        
    Returns:
        UserOrganizationsResponse: User's organizations
    """
    try:
        # Get user organizations from service
        organizations = await jwt_validator.get_user_organizations(user_data["user_id"])
        
        logger.info(f"Retrieved {len(organizations)} organizations for user {user_data['user_id']}")
        
        return UserOrganizationsResponse(
            user_id=user_data["user_id"],
            organizations=organizations,
            total_count=len(organizations)
        )
        
    except Exception as e:
        logger.error(f"Failed to get user organizations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user organizations"
        )


@router.get("/health")
async def auth_health_check():
    """
    Health check endpoint for authentication service
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0",
        "timestamp": "2025-07-06T00:00:00Z"
    }


# Export router
__all__ = ["router"] 