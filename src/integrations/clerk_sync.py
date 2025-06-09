"""
Clerk Data Synchronization Service
Sync existing Clerk users, organizations, and memberships to database
"""

import os
import logging
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from database import db
from integrations.clerk_client import clerk

logger = logging.getLogger(__name__)

class ClerkSyncService:
    """Service to sync Clerk data with local database"""
    
    def __init__(self):
        self.secret_key = os.getenv('CLERK_SECRET_KEY')
        self.base_url = "https://api.clerk.com/v1"
        
        if not self.secret_key:
            logger.warning("CLERK_SECRET_KEY environment variable not found. Clerk sync will be disabled.")
            # Don't raise error immediately - allow service to be imported but fail gracefully when used
            self.available = False
            self.headers = {}
        else:
            self.available = True
            self.headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """
        Comprehensive sync of all Clerk data to database
        Returns sync summary with counts and any errors
        """
        if not self.available:
            return {
                "success": False,
                "error": "Clerk sync service unavailable. CLERK_SECRET_KEY environment variable required."
            }
        
        sync_start = datetime.now(timezone.utc)
        
        logger.info("🔄 Starting comprehensive Clerk data sync...")
        
        summary = {
            "started_at": sync_start.isoformat(),
            "users": {"synced": 0, "errors": []},
            "organizations": {"synced": 0, "errors": []},
            "memberships": {"synced": 0, "errors": []},
            "total_duration_seconds": 0,
            "success": False
        }
        
        try:
            # Step 1: Sync all users
            logger.info("👥 Syncing users from Clerk...")
            users_result = await self.sync_all_users()
            summary["users"] = users_result
            
            # Step 2: Sync all organizations  
            logger.info("🏢 Syncing organizations from Clerk...")
            orgs_result = await self.sync_all_organizations()
            summary["organizations"] = orgs_result
            
            # Step 3: Sync all organization memberships
            logger.info("🔗 Syncing organization memberships from Clerk...")
            memberships_result = await self.sync_all_memberships()
            summary["memberships"] = memberships_result
            
            # Calculate summary
            sync_end = datetime.now(timezone.utc)
            summary["completed_at"] = sync_end.isoformat()
            summary["total_duration_seconds"] = (sync_end - sync_start).total_seconds()
            
            total_errors = (len(summary["users"]["errors"]) + 
                          len(summary["organizations"]["errors"]) + 
                          len(summary["memberships"]["errors"]))
            
            summary["success"] = total_errors == 0
            
            logger.info(f"✅ Clerk sync completed in {summary['total_duration_seconds']:.2f}s")
            logger.info(f"📊 Users: {summary['users']['synced']}, "
                       f"Organizations: {summary['organizations']['synced']}, "
                       f"Memberships: {summary['memberships']['synced']}")
            
            if total_errors > 0:
                logger.warning(f"⚠️ {total_errors} errors occurred during sync")
            
            return summary
            
        except Exception as e:
            sync_end = datetime.now(timezone.utc)
            summary["completed_at"] = sync_end.isoformat()
            summary["total_duration_seconds"] = (sync_end - sync_start).total_seconds()
            summary["error"] = str(e)
            summary["success"] = False
            
            logger.error(f"❌ Clerk sync failed: {e}")
            return summary
    
    async def sync_all_users(self) -> Dict[str, Any]:
        """Fetch and sync all users from Clerk"""
        users_synced = 0
        errors = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch all users with pagination
                offset = 0
                limit = 100
                
                while True:
                    response = await client.get(
                        f"{self.base_url}/users",
                        headers=self.headers,
                        params={"limit": limit, "offset": offset}
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"Failed to fetch users: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        break
                    
                    users_data = response.json()
                    
                    # Process each user
                    for user_data in users_data:
                        try:
                            await self.sync_single_user(user_data)
                            users_synced += 1
                            
                            if users_synced % 10 == 0:
                                logger.info(f"📥 Synced {users_synced} users...")
                                
                        except Exception as e:
                            error_msg = f"Failed to sync user {user_data.get('id', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                    
                    # Check if we have more users to fetch
                    if len(users_data) < limit:
                        break
                    
                    offset += limit
                    
        except Exception as e:
            error_msg = f"Error fetching users from Clerk: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {"synced": users_synced, "errors": errors}
    
    async def sync_all_organizations(self) -> Dict[str, Any]:
        """Fetch and sync all organizations from Clerk"""
        orgs_synced = 0
        errors = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch all organizations with pagination
                offset = 0
                limit = 100
                
                while True:
                    response = await client.get(
                        f"{self.base_url}/organizations",
                        headers=self.headers,
                        params={"limit": limit, "offset": offset}
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"Failed to fetch organizations: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        break
                    
                    response_data = response.json()
                    
                    # Handle different response formats - organizations API returns {"data": [...]} 
                    if isinstance(response_data, dict) and "data" in response_data:
                        orgs_data = response_data["data"]
                        logger.info(f"🔍 Organizations API response: dict format with {len(orgs_data)} organizations")
                    else:
                        orgs_data = response_data
                        logger.info(f"🔍 Organizations API response: direct array format with {len(orgs_data)} organizations")
                    
                    # Process each organization
                    for org_data in orgs_data:
                        try:
                            await self.sync_single_organization(org_data)
                            orgs_synced += 1
                            
                            if orgs_synced % 5 == 0:
                                logger.info(f"🏢 Synced {orgs_synced} organizations...")
                                
                        except Exception as e:
                            error_msg = f"Failed to sync organization {org_data.get('id', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                    
                    # Check if we have more organizations to fetch
                    if len(orgs_data) < limit:
                        break
                    
                    offset += limit
                    
        except Exception as e:
            error_msg = f"Error fetching organizations from Clerk: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {"synced": orgs_synced, "errors": errors}
    
    async def sync_all_memberships(self) -> Dict[str, Any]:
        """Fetch and sync all organization memberships from Clerk"""
        memberships_synced = 0
        errors = []
        
        try:
            # Get all organizations from our database
            orgs_query = "SELECT id FROM organizations"
            organizations = db.execute_query(orgs_query)
            logger.info(f"🔍 Found {len(organizations)} organizations to sync memberships for: {[org['id'] for org in organizations]}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for org in organizations:
                    org_id = org["id"]
                    logger.info(f"🔗 Fetching memberships for organization: {org_id}")
                    
                    try:
                        # Fetch memberships for this organization
                        offset = 0
                        limit = 100
                        
                        while True:
                            response = await client.get(
                                f"{self.base_url}/organizations/{org_id}/memberships",
                                headers=self.headers,
                                params={"limit": limit, "offset": offset}
                            )
                            
                            if response.status_code != 200:
                                if response.status_code == 404:
                                    # Organization doesn't exist in Clerk anymore
                                    logger.warning(f"Organization {org_id} not found in Clerk")
                                    break
                                else:
                                    error_msg = f"Failed to fetch memberships for org {org_id}: {response.status_code}"
                                    logger.error(error_msg)
                                    errors.append(error_msg)
                                    break
                            
                            response_data = response.json()
                            
                            # Handle different response formats - memberships might return {"data": [...]}
                            if isinstance(response_data, dict) and "data" in response_data:
                                memberships_data = response_data["data"]
                                logger.info(f"🔍 Memberships API response: dict format with {len(memberships_data)} memberships for org {org_id}")
                            else:
                                memberships_data = response_data
                                logger.info(f"🔍 Memberships API response: direct array format with {len(memberships_data)} memberships for org {org_id}")
                            
                            # Process each membership
                            for membership_data in memberships_data:
                                try:
                                    await self.sync_single_membership(membership_data)
                                    memberships_synced += 1
                                    
                                    if memberships_synced % 10 == 0:
                                        logger.info(f"🔗 Synced {memberships_synced} memberships...")
                                        
                                except Exception as e:
                                    error_msg = f"Failed to sync membership: {str(e)}"
                                    logger.error(error_msg)
                                    errors.append(error_msg)
                            
                            # Check if we have more memberships to fetch
                            if len(memberships_data) < limit:
                                break
                            
                            offset += limit
                            
                    except Exception as e:
                        error_msg = f"Error fetching memberships for org {org_id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
        except Exception as e:
            error_msg = f"Error during membership sync: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {"synced": memberships_synced, "errors": errors}
    
    async def sync_single_user(self, user_data: Dict[str, Any]):
        """Sync a single user to database using existing ClerkClient logic"""
        
        # Use the existing webhook handler logic
        webhook_payload = {"data": user_data}
        result = await clerk.handle_user_created(webhook_payload)
        
        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error syncing user"))
    
    async def sync_single_organization(self, org_data: Dict[str, Any]):
        """Sync a single organization to database using existing ClerkClient logic"""
        
        # Use the existing webhook handler logic
        webhook_payload = {"data": org_data}
        result = await clerk.handle_organization_created(webhook_payload)
        
        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error syncing organization"))
    
    async def sync_single_membership(self, membership_data: Dict[str, Any]):
        """Sync a single organization membership to database"""
        
        logger.info(f"🔍 Processing membership_data type: {type(membership_data)} | Content: {membership_data}")
        
        # Use the existing webhook handler logic
        webhook_payload = {"data": membership_data}
        result = await clerk.handle_organization_membership_created(webhook_payload)
        
        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error syncing membership"))
    
    async def get_clerk_api_status(self) -> Dict[str, Any]:
        """Check Clerk API connectivity and get basic stats"""
        if not self.available:
            return {
                "connected": False,
                "error": "Clerk sync service unavailable. CLERK_SECRET_KEY environment variable required."
            }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test API connectivity
                response = await client.get(
                    f"{self.base_url}/users",
                    headers=self.headers,
                    params={"limit": 1}
                )
                
                if response.status_code == 200:
                    # Get basic counts
                    users_response = await client.get(
                        f"{self.base_url}/users",
                        headers=self.headers,
                        params={"limit": 1, "offset": 0}
                    )
                    
                    orgs_response = await client.get(
                        f"{self.base_url}/organizations", 
                        headers=self.headers,
                        params={"limit": 1, "offset": 0}
                    )
                    
                    return {
                        "connected": True,
                        "api_accessible": True,
                        "approximate_users": "Available" if users_response.status_code == 200 else "Unavailable",
                        "approximate_organizations": "Available" if orgs_response.status_code == 200 else "Unavailable"
                    }
                else:
                    return {
                        "connected": False,
                        "error": f"API returned {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "connected": False,
                "error": f"Connection failed: {str(e)}"
            }

# Global sync service instance
clerk_sync = ClerkSyncService() 