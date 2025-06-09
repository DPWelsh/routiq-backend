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
            # Fallback for development
            return None
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Clerk JWT token"""
        try:
            # For development, skip verification if no proper keys
            if not self.clerk_secret_key.startswith('sk_'):
                # Development mode - return mock user
                return {
                    "sub": "user_sample_123",  # Clerk user ID
                    "email": "admin@sampleclinic.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "org_id": "org_sample_123",
                    "org_role": "admin"
                }
            
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
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")
    
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
            # Fallback to database
            from integrations.clerk_client import clerk
            return clerk.get_user_organizations(user_id)

# Global validator instance
clerk_jwt = ClerkJWTValidator() 