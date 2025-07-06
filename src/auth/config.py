"""
Authentication Domain Configuration
Clerk-specific configuration settings using Pydantic BaseSettings
"""

import os
from pydantic import BaseSettings, Field
from typing import Optional


class AuthConfig(BaseSettings):
    """Authentication configuration using BaseSettings"""
    
    # Clerk Configuration
    CLERK_SECRET_KEY: str = Field(
        default="",
        description="Clerk secret key for API access"
    )
    CLERK_PUBLISHABLE_KEY: str = Field(
        default="",
        description="Clerk publishable key for JWT verification"
    )
    
    # JWT Configuration
    JWT_ALGORITHM: str = Field(
        default="RS256", 
        description="JWT signature algorithm"
    )
    JWT_AUDIENCE: Optional[str] = Field(
        default=None,
        description="JWT audience for token validation"
    )
    
    # HTTP Configuration
    HTTP_TIMEOUT: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )
    
    # Security Configuration
    REQUIRE_ORGANIZATION_ACCESS: bool = Field(
        default=True,
        description="Whether to require organization access validation"
    )
    ENABLE_AUTH_LOGGING: bool = Field(
        default=True,
        description="Whether to enable authentication event logging"
    )
    
    # Development Configuration
    DEVELOPMENT_MODE: bool = Field(
        default=False,
        description="Enable development mode (less strict validation)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = ""  # No prefix, use exact env var names


# Global auth configuration instance
auth_config = AuthConfig()


# Export configuration
__all__ = [
    "AuthConfig", 
    "auth_config"
] 