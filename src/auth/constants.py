"""
Authentication Domain Constants
Authentication-specific constants and enums
"""

from enum import Enum


class AuthAction(str, Enum):
    """Authentication action constants for logging"""
    TOKEN_VALIDATION_SUCCESS = "token_validation_success"
    TOKEN_VALIDATION_FAILED = "token_validation_failed"
    TOKEN_EXPIRED = "token_expired"
    INVALID_TOKEN = "invalid_token"
    ORGANIZATION_ACCESS_GRANTED = "organization_access_granted"
    ORGANIZATION_ACCESS_DENIED = "organization_access_denied"
    USER_NOT_FOUND = "user_not_found"
    CLERK_API_ERROR = "clerk_api_error"
    AUTHENTICATION_ERROR = "authentication_error"
    MISSING_CREDENTIALS = "missing_credentials"
    INVALID_ORGANIZATION_HEADER = "invalid_organization_header"


class TokenType(str, Enum):
    """Token type constants"""
    JWT = "jwt"
    BEARER = "bearer"
    API_KEY = "api_key"


class OrganizationRole(str, Enum):
    """Organization role constants"""
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"
    GUEST = "guest"


class AuthHeaders:
    """Authentication header constants"""
    AUTHORIZATION = "authorization"
    ORGANIZATION_ID = "x-organization-id"
    USER_ID = "x-user-id"
    REQUEST_ID = "x-request-id"


class ClerkEndpoints:
    """Clerk API endpoint constants"""
    BASE_URL = "https://api.clerk.com/v1"
    USER_ORGANIZATIONS = "/users/{user_id}/organization_memberships"
    ORGANIZATION_MEMBERS = "/organizations/{org_id}/memberships"
    USER_PROFILE = "/users/{user_id}"
    JWKS_URL_TEMPLATE = "https://clerk.{instance_id}.com/.well-known/jwks.json"


class AuthErrorMessages:
    """Authentication error message constants"""
    TOKEN_REQUIRED = "Authentication token required"
    TOKEN_INVALID = "Invalid authentication token"
    TOKEN_EXPIRED = "Authentication token has expired"
    ORG_ID_REQUIRED = "Organization ID required in x-organization-id header"
    ORG_ACCESS_DENIED = "Access denied to requested organization"
    USER_NOT_FOUND = "User not found"
    CLERK_CONFIG_ERROR = "Authentication service not properly configured"
    CLERK_API_ERROR = "External authentication service error"


class AuthTimeouts:
    """Authentication timeout constants in seconds"""
    JWT_VERIFICATION = 10
    CLERK_API_REQUEST = 30
    JWKS_FETCH = 15
    DEFAULT_REQUEST = 30


class JWTClaims:
    """JWT claim constants"""
    SUBJECT = "sub"
    AUDIENCE = "aud"
    ISSUER = "iss"
    ISSUED_AT = "iat"
    EXPIRES_AT = "exp"
    NOT_BEFORE = "nbf"
    JWT_ID = "jti"
    SESSION_ID = "sid"
    ORGANIZATION_ID = "org_id"
    USER_ID = "user_id"


class AuthEvents:
    """Authentication event type constants"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    ORGANIZATION_SWITCH = "organization_switch"
    PERMISSION_CHECK = "permission_check"
    API_ACCESS = "api_access"


# Export all constants
__all__ = [
    "AuthAction",
    "TokenType",
    "OrganizationRole",
    "AuthHeaders",
    "ClerkEndpoints",
    "AuthErrorMessages",
    "AuthTimeouts",
    "JWTClaims",
    "AuthEvents",
] 