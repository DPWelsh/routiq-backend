"""
Authentication Domain Dependencies
FastAPI dependencies for authentication and authorization
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Header, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.auth.service import jwt_validator
from src.auth.exceptions import (
    TokenValidationError,
    OrganizationAccessError,
    MissingCredentialsError,
    InvalidOrganizationHeaderError
)
from src.auth.constants import AuthHeaders, AuthAction, AuthErrorMessages
from src.auth.schemas import AuthenticationEvent

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: Bearer token credentials
        request: FastAPI request object for logging
        
    Returns:
        Dict containing user information from token payload
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    try:
        if not credentials or not credentials.credentials:
            await _log_auth_event(
                request=request,
                action=AuthAction.MISSING_CREDENTIALS,
                success=False,
                error_message=AuthErrorMessages.TOKEN_REQUIRED
            )
            raise HTTPException(
                status_code=401,
                detail=AuthErrorMessages.TOKEN_REQUIRED
            )
        
        # Verify JWT token with Clerk
        token_payload = await jwt_validator.verify_token(credentials.credentials)
        user_id = token_payload.get('sub')
        
        if not user_id:
            await _log_auth_event(
                request=request,
                action=AuthAction.INVALID_TOKEN,
                success=False,
                error_message="Invalid token payload - missing user ID"
            )
            raise HTTPException(
                status_code=401,
                detail=AuthErrorMessages.TOKEN_INVALID
            )
        
        # Log successful authentication
        await _log_auth_event(
            user_id=user_id,
            request=request,
            action=AuthAction.TOKEN_VALIDATION_SUCCESS,
            success=True
        )
        
        logger.debug(f"Successfully authenticated user: {user_id}")
        
        return {
            "user_id": user_id,
            "token_payload": token_payload
        }
        
    except TokenValidationError as e:
        await _log_auth_event(
            request=request,
            action=AuthAction.TOKEN_VALIDATION_FAILED,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await _log_auth_event(
            request=request,
            action=AuthAction.AUTHENTICATION_ERROR,
            success=False,
            error_message=str(e)
        )
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=AuthErrorMessages.TOKEN_INVALID)


async def verify_organization_access(
    x_organization_id: Optional[str] = Header(None, alias=AuthHeaders.ORGANIZATION_ID),
    user_data: Dict[str, Any] = Depends(get_current_user),
    request: Request = None
) -> str:
    """
    Verify organization access and return organization ID
    
    Args:
        x_organization_id: Organization ID from header
        user_data: Authenticated user data from get_current_user
        request: FastAPI request object for logging
        
    Returns:
        Organization ID if access is granted
        
    Raises:
        HTTPException: If organization access is denied or invalid
    """
    user_id = user_data["user_id"]
    
    try:
        # Validate organization ID header
        if not x_organization_id:
            await _log_auth_event(
                user_id=user_id,
                request=request,
                action=AuthAction.INVALID_ORGANIZATION_HEADER,
                success=False,
                error_message=AuthErrorMessages.ORG_ID_REQUIRED
            )
            raise HTTPException(
                status_code=400,
                detail=AuthErrorMessages.ORG_ID_REQUIRED
            )
        
        # Verify user has access to the requested organization
        has_access = await jwt_validator.verify_organization_access(user_id, x_organization_id)
        
        if not has_access:
            await _log_auth_event(
                user_id=user_id,
                organization_id=x_organization_id,
                request=request,
                action=AuthAction.ORGANIZATION_ACCESS_DENIED,
                success=False,
                error_message=f"User {user_id} not member of organization {x_organization_id}"
            )
            raise HTTPException(
                status_code=403,
                detail=AuthErrorMessages.ORG_ACCESS_DENIED
            )
        
        # Log successful organization access
        await _log_auth_event(
            user_id=user_id,
            organization_id=x_organization_id,
            request=request,
            action=AuthAction.ORGANIZATION_ACCESS_GRANTED,
            success=True,
            details={
                "token_type": "JWT",
                "organization_access": "verified"
            }
        )
        
        logger.info(f"Authenticated user {user_id} for organization {x_organization_id}")
        return x_organization_id
        
    except HTTPException:
        raise
    except OrganizationAccessError as e:
        await _log_auth_event(
            user_id=user_id,
            organization_id=x_organization_id,
            request=request,
            action=AuthAction.ORGANIZATION_ACCESS_DENIED,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        await _log_auth_event(
            user_id=user_id,
            organization_id=x_organization_id,
            request=request,
            action=AuthAction.AUTHENTICATION_ERROR,
            success=False,
            error_message=str(e)
        )
        logger.error(f"Organization access verification error: {e}")
        raise HTTPException(status_code=401, detail=AuthErrorMessages.TOKEN_INVALID)


async def require_organization_access(
    organization_id: str,
    user_data: Dict[str, Any] = Depends(get_current_user),
    request: Request = None
) -> str:
    """
    Require access to a specific organization (for path parameters)
    
    Args:
        organization_id: Organization ID from path parameter
        user_data: Authenticated user data from get_current_user
        request: FastAPI request object for logging
        
    Returns:
        Organization ID if access is granted
        
    Raises:
        HTTPException: If organization access is denied
    """
    user_id = user_data["user_id"]
    
    try:
        # Verify user has access to the requested organization
        has_access = await jwt_validator.verify_organization_access(user_id, organization_id)
        
        if not has_access:
            await _log_auth_event(
                user_id=user_id,
                organization_id=organization_id,
                request=request,
                action=AuthAction.ORGANIZATION_ACCESS_DENIED,
                success=False,
                error_message=f"User {user_id} not member of organization {organization_id}"
            )
            raise HTTPException(
                status_code=403,
                detail=AuthErrorMessages.ORG_ACCESS_DENIED
            )
        
        # Log successful organization access
        await _log_auth_event(
            user_id=user_id,
            organization_id=organization_id,
            request=request,
            action=AuthAction.ORGANIZATION_ACCESS_GRANTED,
            success=True,
            details={
                "access_type": "path_parameter",
                "organization_access": "verified"
            }
        )
        
        logger.info(f"Verified user {user_id} access to organization {organization_id}")
        return organization_id
        
    except HTTPException:
        raise
    except Exception as e:
        await _log_auth_event(
            user_id=user_id,
            organization_id=organization_id,
            request=request,
            action=AuthAction.AUTHENTICATION_ERROR,
            success=False,
            error_message=str(e)
        )
        logger.error(f"Organization access verification error: {e}")
        raise HTTPException(status_code=401, detail=AuthErrorMessages.TOKEN_INVALID)


async def _log_auth_event(
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    request: Optional[Request] = None,
    action: AuthAction = AuthAction.AUTHENTICATION_ERROR,
    success: bool = False,
    error_message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log authentication events using the audit logger
    
    Args:
        user_id: User ID (if available)
        organization_id: Organization ID (if available)
        request: FastAPI request object
        action: Authentication action being performed
        success: Whether the action was successful
        error_message: Error message (if any)
        details: Additional details to log
    """
    try:
        # Import here to avoid circular imports
        from src.services.audit_logger import audit_logger
        
        await audit_logger.log_authentication_event(
            user_id=user_id,
            organization_id=organization_id,
            action=action.value,
            success=success,
            request=request,
            error_message=error_message,
            details=details
        )
        
    except Exception as e:
        logger.error(f"Failed to log authentication event: {e}")


# Export dependencies
__all__ = [
    "get_current_user",
    "verify_organization_access", 
    "require_organization_access",
    "security",
] 