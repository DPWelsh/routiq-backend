"""
Authentication Domain Service
Business logic for authentication, JWT validation, and organization access
"""

import os
import jwt
import httpx
import logging
from typing import Dict, Any, List, Optional

from src.auth.config import auth_config
from src.auth.exceptions import (
    ClerkConfigurationError,
    TokenValidationError, 
    OrganizationAccessError
)
from src.auth.schemas import UserOrganization
from src.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class ClerkJWTValidator:
    """
    Validates Clerk JWT tokens and manages organization access
    
    This service handles:
    - JWT token verification with Clerk's public keys
    - Organization membership validation
    - User organization retrieval
    """
    
    def __init__(self):
        """Initialize the JWT validator with Clerk configuration"""
        self.clerk_secret_key = auth_config.CLERK_SECRET_KEY
        self.clerk_publishable_key = auth_config.CLERK_PUBLISHABLE_KEY
        
        if not self.clerk_secret_key:
            raise ClerkConfigurationError("CLERK_SECRET_KEY environment variable required")
        
        if not self.clerk_secret_key.startswith('sk_'):
            raise ClerkConfigurationError("CLERK_SECRET_KEY must start with 'sk_'")
    
    async def get_clerk_public_key(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Clerk's public key for JWT verification from JWKS endpoint
        
        Returns:
            Dict containing the public key information or None if failed
            
        Raises:
            ClerkConfigurationError: If unable to retrieve public key
        """
        try:
            # Extract instance ID from publishable key
            instance_id = self.clerk_publishable_key.split('_')[1] if self.clerk_publishable_key else 'test'
            
            # Construct JWKS URL
            jwks_url = f"https://clerk.{instance_id}.com/.well-known/jwks.json"
            
            async with httpx.AsyncClient(timeout=auth_config.HTTP_TIMEOUT) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()
                
            # Return the first key (in production, you'd match by kid)
            if jwks.get('keys'):
                return jwks['keys'][0]
            
            raise ClerkConfigurationError("No public keys found in JWKS")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Clerk public key: {e}")
            raise ClerkConfigurationError(f"Failed to fetch JWKS: {e}")
        except Exception as e:
            logger.error(f"Failed to get Clerk public key: {e}")
            raise ClerkConfigurationError(f"JWKS retrieval failed: {e}")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Clerk JWT token and extract payload
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Dict containing the token payload
            
        Raises:
            TokenValidationError: If token is invalid or expired
            AuthenticationError: For general authentication failures
        """
        try:
            # Decode without verification first to get header
            unverified_header = jwt.get_unverified_header(token)
            
            # Get public key from Clerk
            public_key = await self.get_clerk_public_key()
            
            if not public_key:
                raise TokenValidationError("Could not retrieve public key for token verification")
            
            # Verify token with public key
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                audience=self.clerk_publishable_key
            )
            
            logger.debug(f"Successfully verified token for user: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token has expired")
            raise TokenValidationError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: Invalid token - {e}")
            raise TokenValidationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification failed with unexpected error: {e}")
            raise AuthenticationError("Token verification failed")
    
    async def get_user_organizations(self, user_id: str) -> List[UserOrganization]:
        """
        Get user's organization memberships from Clerk API
        
        Args:
            user_id: The user ID to get organizations for
            
        Returns:
            List of UserOrganization objects
            
        Raises:
            OrganizationAccessError: If unable to retrieve organizations
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.clerk_secret_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=auth_config.HTTP_TIMEOUT) as client:
                response = await client.get(
                    f"https://api.clerk.com/v1/users/{user_id}/organization_memberships",
                    headers=headers
                )
                
                if response.status_code == 200:
                    memberships = response.json()
                    organizations = [
                        UserOrganization(
                            id=membership["organization"]["id"],
                            name=membership["organization"]["name"],
                            role=membership["role"]
                        )
                        for membership in memberships
                    ]
                    
                    logger.debug(f"Retrieved {len(organizations)} organizations for user {user_id}")
                    return organizations
                    
                elif response.status_code == 404:
                    logger.warning(f"User {user_id} not found in Clerk")
                    return []
                else:
                    logger.error(f"Clerk API error: {response.status_code} - {response.text}")
                    # Fallback to database if available
                    return await self._fallback_get_user_organizations(user_id)
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user organizations: {e}")
            return await self._fallback_get_user_organizations(user_id)
        except Exception as e:
            logger.error(f"Failed to get user organizations: {e}")
            return await self._fallback_get_user_organizations(user_id)
    
    async def _fallback_get_user_organizations(self, user_id: str) -> List[UserOrganization]:
        """
        Fallback method to get organizations from database when Clerk API fails
        
        Args:
            user_id: The user ID to get organizations for
            
        Returns:
            List of UserOrganization objects from database
        """
        try:
            # Import here to avoid circular imports
            from src.integrations.clerk_client import clerk
            
            logger.info(f"Using database fallback for user {user_id} organizations")
            db_orgs = clerk.get_user_organizations(user_id)
            
            # Convert to UserOrganization objects
            organizations = [
                UserOrganization(
                    id=org.get("id", ""),
                    name=org.get("name", ""),
                    role=org.get("role", "member")
                )
                for org in db_orgs
            ]
            
            return organizations
            
        except Exception as e:
            logger.error(f"Database fallback failed for user {user_id}: {e}")
            raise OrganizationAccessError(f"Unable to retrieve organizations for user {user_id}")
    
    async def verify_organization_access(self, user_id: str, organization_id: str) -> bool:
        """
        Verify if user has access to the specified organization
        
        Args:
            user_id: The user ID
            organization_id: The organization ID to check access for
            
        Returns:
            True if user has access, False otherwise
            
        Raises:
            OrganizationAccessError: If unable to verify access
        """
        try:
            user_orgs = await self.get_user_organizations(user_id)
            org_ids = [org.id for org in user_orgs]
            
            has_access = organization_id in org_ids
            
            logger.debug(f"Organization access check for user {user_id}, org {organization_id}: {has_access}")
            
            return has_access
            
        except Exception as e:
            logger.error(f"Failed to verify organization access: {e}")
            raise OrganizationAccessError(f"Unable to verify organization access: {e}")


# Global service instance
jwt_validator = ClerkJWTValidator()


# Export service classes and instance
__all__ = [
    "ClerkJWTValidator",
    "jwt_validator",
] 