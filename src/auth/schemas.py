"""
Authentication Domain Schemas
Pydantic models for authentication requests and responses
"""

from typing import Optional, List, Dict, Any
from pydantic import Field

from src.models import CustomModel, BaseResponse


class AuthResponse(CustomModel):
    """Response model for authentication verification"""
    
    authenticated: bool = Field(description="Whether authentication was successful")
    organization_id: Optional[str] = Field(default=None, description="Organization ID if authenticated")
    message: str = Field(description="Authentication status message")


class OrganizationAccessResponse(CustomModel):
    """Response model for organization access verification"""
    
    organization_id: str = Field(description="Organization ID being checked")
    access_granted: bool = Field(description="Whether access is granted")
    message: str = Field(description="Access status message")


class TokenValidationRequest(CustomModel):
    """Request model for token validation"""
    
    token: str = Field(description="JWT token to validate")
    organization_id: Optional[str] = Field(default=None, description="Organization ID to verify access")


class UserOrganization(CustomModel):
    """Model representing a user's organization membership"""
    
    id: str = Field(description="Organization ID")
    name: str = Field(description="Organization name")
    role: str = Field(description="User's role in the organization")


class UserOrganizationsResponse(BaseResponse):
    """Response model for user organizations"""
    
    organizations: List[UserOrganization] = Field(default_factory=list, description="List of user organizations")
    user_id: str = Field(description="User ID")


class AuthenticationEvent(CustomModel):
    """Model for authentication event logging"""
    
    user_id: Optional[str] = Field(default=None, description="User ID")
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    action: str = Field(description="Authentication action")
    success: bool = Field(description="Whether the action was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


# Export all schemas
__all__ = [
    "AuthResponse",
    "OrganizationAccessResponse", 
    "TokenValidationRequest",
    "UserOrganization",
    "UserOrganizationsResponse",
    "AuthenticationEvent",
] 