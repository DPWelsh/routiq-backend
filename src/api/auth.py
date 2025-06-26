"""
Clerk Authentication Utilities for FastAPI
"""

import os
import jwt
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
import json
from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ClerkJWTValidator:
    """Validates Clerk JWT tokens"""
    
    def __init__(self):
        self.clerk_secret_key = os.getenv('CLERK_SECRET_KEY')
        self.clerk_publishable_key = os.getenv('CLERK_PUBLISHABLE_KEY')
        
        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable required")
    
    async def get_clerk_public_key(self) -> str:
        """Fetch Clerk's public key for JWT verification"""
        try:
            # Extract instance ID from publishable key
            instance_id = self.clerk_publishable_key.split('_')[1] if self.clerk_publishable_key else 'test'
            
            # Fetch JWKS from Clerk
            jwks_url = f"https://clerk.{instance_id}.com/.well-known/jwks.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()
                
            # Return the first key (in production, you'd match by kid)
            if jwks.get('keys'):
                return jwks['keys'][0]
            
            raise ValueError("No public keys found in JWKS")
            
        except Exception as e:
            logger.error(f"Failed to get Clerk public key: {e}")
            return None
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Clerk JWT token"""
        try:
            # SECURITY FIX: Remove development mode bypass
            # Always require proper JWT validation
            if not self.clerk_secret_key or not self.clerk_secret_key.startswith('sk_'):
                logger.error("Invalid or missing CLERK_SECRET_KEY - must start with 'sk_'")
                raise HTTPException(
                    status_code=401, 
                    detail="Authentication service not properly configured"
                )
            
            # Production JWT verification
            # Decode without verification first to get header
            unverified_header = jwt.get_unverified_header(token)
            
            # Get public key from Clerk
            public_key = await self.get_clerk_public_key()
            
            if not public_key:
                raise HTTPException(status_code=401, detail="Could not verify token")
            
            # Verify token
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                audience=self.clerk_publishable_key
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Token verification failed")
    
    async def get_user_organizations(self, user_id: str) -> list:
        """Get user organizations from Clerk API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.clerk_secret_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.clerk.com/v1/users/{user_id}/organization_memberships",
                    headers=headers
                )
                
                if response.status_code == 200:
                    memberships = response.json()
                    return [
                        {
                            "id": membership["organization"]["id"],
                            "name": membership["organization"]["name"],
                            "role": membership["role"]
                        }
                        for membership in memberships
                    ]
                else:
                    # Fallback to database
                    from integrations.clerk_client import clerk
                    return clerk.get_user_organizations(user_id)
                    
        except Exception as e:
            logger.error(f"Failed to get user organizations: {e}")
            # Fallback to database
            from integrations.clerk_client import clerk
            return clerk.get_user_organizations(user_id)

# Global validator instance
clerk_jwt = ClerkJWTValidator()

# Create router
router = APIRouter()

# Security
security = HTTPBearer()

# Pydantic models
class AuthResponse(BaseModel):
    authenticated: bool
    organization_id: Optional[str] = None
    message: str

class OrganizationAccessResponse(BaseModel):
    organization_id: str
    access_granted: bool
    message: str

async def verify_organization_access(
    x_organization_id: Optional[str] = Header(None, alias="x-organization-id"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> str:
    """
    Verify organization access and return organization ID
    SECURITY ENHANCEMENT: Proper JWT validation required with audit logging
    """
    user_id = None
    try:
        if not x_organization_id:
            raise HTTPException(
                status_code=400, 
                detail="Organization ID required in x-organization-id header"
            )
        
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=401,
                detail="Authentication token required"
            )
        
        # SECURITY ENHANCEMENT: Validate JWT token
        try:
            # Verify the JWT token with Clerk
            token_payload = await clerk_jwt.verify_token(credentials.credentials)
            user_id = token_payload.get('sub')
            
            if not user_id:
                # Log failed authentication attempt
                from src.services.audit_logger import audit_logger
                await audit_logger.log_authentication_event(
                    user_id=None,
                    organization_id=x_organization_id,
                    action="token_validation_failed",
                    success=False,
                    request=request,
                    error_message="Invalid token payload - missing user ID"
                )
                raise HTTPException(status_code=401, detail="Invalid token payload")
            
            # Verify user has access to the requested organization
            user_orgs = await clerk_jwt.get_user_organizations(user_id)
            org_ids = [org['id'] for org in user_orgs]
            
            if x_organization_id not in org_ids:
                # Log unauthorized organization access attempt
                from src.services.audit_logger import audit_logger
                await audit_logger.log_authentication_event(
                    user_id=user_id,
                    organization_id=x_organization_id,
                    action="organization_access_denied",
                    success=False,
                    request=request,
                    error_message=f"User {user_id} not member of organization {x_organization_id}",
                    details={"available_organizations": org_ids}
                )
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied to requested organization"
                )
            
            # Log successful authentication
            from src.services.audit_logger import audit_logger
            await audit_logger.log_authentication_event(
                user_id=user_id,
                organization_id=x_organization_id,
                action="organization_access_granted",
                success=True,
                request=request,
                details={
                    "token_type": "JWT",
                    "organization_access": "verified"
                }
            )
            
            logger.info(f"Authenticated user {user_id} for organization {x_organization_id}")
            return x_organization_id
            
        except HTTPException:
            raise
        except Exception as e:
            # Log authentication system error
            from src.services.audit_logger import audit_logger
            await audit_logger.log_authentication_event(
                user_id=user_id,
                organization_id=x_organization_id,
                action="token_validation_error",
                success=False,
                request=request,
                error_message=str(e)
            )
            logger.error(f"Token validation error: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
    except HTTPException:
        raise
    except Exception as e:
        # Log general authentication error
        from src.services.audit_logger import audit_logger
        await audit_logger.log_authentication_event(
            user_id=user_id,
            organization_id=x_organization_id,
            action="authentication_error", 
            success=False,
            request=request,
            error_message=str(e)
        )
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")

@router.get("/verify", response_model=AuthResponse)
async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_organization_id: Optional[str] = Header(None, alias="x-organization-id")
):
    """
    Verify authentication token and organization access
    """
    try:
        organization_id = await verify_organization_access(x_organization_id, credentials)
        
        return AuthResponse(
            authenticated=True,
            organization_id=organization_id,
            message="Authentication successful"
        )
        
    except HTTPException as e:
        return AuthResponse(
            authenticated=False,
            organization_id=None,
            message=e.detail
        )

@router.get("/organization/{organization_id}/access", response_model=OrganizationAccessResponse)
async def check_organization_access(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """
    Check if authenticated user has access to specific organization
    """
    access_granted = (organization_id == verified_org_id)
    
    return OrganizationAccessResponse(
        organization_id=organization_id,
        access_granted=access_granted,
        message="Access granted" if access_granted else "Access denied"
    ) 