"""
Authentication Domain Exceptions
Custom exceptions for authentication-specific errors
"""

from src.exceptions import BaseAPIException, AuthenticationError, AuthorizationError
from src.constants import ErrorCodes


class AuthDomainError(BaseAPIException):
    """Base exception for authentication domain errors"""
    pass


class ClerkConfigurationError(AuthDomainError):
    """Clerk configuration error"""
    
    def __init__(self, detail: str = "Clerk configuration error"):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="CLERK_CONFIG_ERROR"
        )


class TokenValidationError(AuthenticationError):
    """JWT token validation error"""
    
    def __init__(self, detail: str = "Token validation failed"):
        super().__init__(
            detail=detail,
            error_code="TOKEN_VALIDATION_ERROR"
        )


class TokenExpiredError(AuthenticationError):
    """JWT token expired error"""
    
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            detail=detail,
            error_code="TOKEN_EXPIRED"
        )


class InvalidTokenError(AuthenticationError):
    """Invalid JWT token error"""
    
    def __init__(self, detail: str = "Invalid token format"):
        super().__init__(
            detail=detail,
            error_code="INVALID_TOKEN"
        )


class OrganizationAccessError(AuthorizationError):
    """Organization access error"""
    
    def __init__(self, detail: str = "Organization access denied"):
        super().__init__(
            detail=detail,
            error_code="ORGANIZATION_ACCESS_DENIED"
        )


class UserNotFoundError(AuthenticationError):
    """User not found error"""
    
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            detail=detail,
            error_code="USER_NOT_FOUND"
        )


class InvalidOrganizationHeaderError(AuthenticationError):
    """Invalid organization header error"""
    
    def __init__(self, detail: str = "Organization ID required in x-organization-id header"):
        super().__init__(
            detail=detail,
            error_code="INVALID_ORGANIZATION_HEADER"
        )


class MissingCredentialsError(AuthenticationError):
    """Missing authentication credentials error"""
    
    def __init__(self, detail: str = "Authentication token required"):
        super().__init__(
            detail=detail,
            error_code="MISSING_CREDENTIALS"
        )


# Export all auth exceptions
__all__ = [
    "AuthDomainError",
    "ClerkConfigurationError",
    "TokenValidationError",
    "TokenExpiredError", 
    "InvalidTokenError",
    "OrganizationAccessError",
    "UserNotFoundError",
    "InvalidOrganizationHeaderError",
    "MissingCredentialsError",
] 