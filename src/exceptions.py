"""
Global Exception Classes
Custom exceptions for the FastAPI application
"""

from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class BaseAPIException(HTTPException):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationError(BaseAPIException):
    """Data validation error"""
    
    def __init__(self, detail: str = "Validation error", error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code
        )


class NotFoundError(BaseAPIException):
    """Resource not found error"""
    
    def __init__(self, detail: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code
        )


class AuthenticationError(BaseAPIException):
    """Authentication error"""
    
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTHENTICATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code
        )


class AuthorizationError(BaseAPIException):
    """Authorization error"""
    
    def __init__(self, detail: str = "Access denied", error_code: str = "AUTHORIZATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )


class ConflictError(BaseAPIException):
    """Resource conflict error"""
    
    def __init__(self, detail: str = "Resource conflict", error_code: str = "CONFLICT_ERROR"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code
        )


class RateLimitError(BaseAPIException):
    """Rate limit exceeded error"""
    
    def __init__(self, detail: str = "Rate limit exceeded", error_code: str = "RATE_LIMIT_ERROR"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code
        )


class ServiceUnavailableError(BaseAPIException):
    """Service unavailable error"""
    
    def __init__(self, detail: str = "Service unavailable", error_code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=error_code
        )


class DatabaseError(BaseAPIException):
    """Database operation error"""
    
    def __init__(self, detail: str = "Database error", error_code: str = "DATABASE_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


class ExternalServiceError(BaseAPIException):
    """External service error"""
    
    def __init__(self, detail: str = "External service error", error_code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code=error_code
        )


class BusinessLogicError(BaseAPIException):
    """Business logic error"""
    
    def __init__(self, detail: str = "Business logic error", error_code: str = "BUSINESS_LOGIC_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        ) 