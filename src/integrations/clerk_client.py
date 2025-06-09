"""
Clerk.com Integration for SurfRehab v2
Handle user authentication, organization management, and webhooks
"""

import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import hmac
import hashlib

from database import db

logger = logging.getLogger(__name__)

class ClerkClient:
    """Clerk.com integration for multi-tenant SaaS"""
    
    def __init__(self):
        self.secret_key = os.getenv('CLERK_SECRET_KEY')
        self.webhook_secret = os.getenv('CLERK_WEBHOOK_SECRET')
        
        if not self.secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable required")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Clerk webhook signature for security"""
        if not self.webhook_secret:
            logger.warning("CLERK_WEBHOOK_SECRET not set - webhook signature verification disabled")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_user_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user.created webhook from Clerk"""
        try:
            user_data = payload.get('data', {})
            
            # Extract user information
            user_record = {
                'id': user_data.get('id'),
                'email': user_data.get('email_addresses', [{}])[0].get('email_address'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'image_url': user_data.get('image_url'),
                'clerk_created_at': datetime.fromtimestamp(
                    user_data.get('created_at', 0) / 1000, tz=timezone.utc
                ),
                'clerk_updated_at': datetime.fromtimestamp(
                    user_data.get('updated_at', 0) / 1000, tz=timezone.utc
                )
            }
            
            # Insert or update user
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (id, email, first_name, last_name, image_url, 
                                     clerk_created_at, clerk_updated_at)
                    VALUES (%(id)s, %(email)s, %(first_name)s, %(last_name)s, %(image_url)s,
                           %(clerk_created_at)s, %(clerk_updated_at)s)
                    ON CONFLICT (id) 
                    DO UPDATE SET
                        email = EXCLUDED.email,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        image_url = EXCLUDED.image_url,
                        clerk_updated_at = EXCLUDED.clerk_updated_at,
                        updated_at = NOW()
                    RETURNING id
                """, user_record)
                
                db.connection.commit()
                
            logger.info(f"✅ User created/updated: {user_record['email']}")
            return {"success": True, "user_id": user_record['id']}
            
        except Exception as e:
            logger.error(f"Failed to handle user creation: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_organization_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle organization.created webhook from Clerk"""
        try:
            org_data = payload.get('data', {})
            
            # Extract organization information
            org_record = {
                'id': org_data.get('id'),
                'name': org_data.get('name'),
                'slug': org_data.get('slug'),
                'created_at': datetime.fromtimestamp(
                    org_data.get('created_at', 0) / 1000, tz=timezone.utc
                ),
            }
            
            # Insert organization
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO organizations (id, name, slug, created_at)
                    VALUES (%(id)s, %(name)s, %(slug)s, %(created_at)s)
                    ON CONFLICT (id) 
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        slug = EXCLUDED.slug,
                        updated_at = NOW()
                    RETURNING id
                """, org_record)
                
                db.connection.commit()
                
            logger.info(f"✅ Organization created: {org_record['name']}")
            return {"success": True, "organization_id": org_record['id']}
            
        except Exception as e:
            logger.error(f"Failed to handle organization creation: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_organization_membership_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle organizationMembership.created webhook from Clerk"""
        try:
            membership_data = payload.get('data', {})
            
            # Extract membership information
            membership_record = {
                'organization_id': membership_data.get('organization', {}).get('id'),
                'user_id': membership_data.get('public_user_data', {}).get('user_id'),
                'role': membership_data.get('role', 'member'),
                'status': 'active',
                'joined_at': datetime.fromtimestamp(
                    membership_data.get('created_at', 0) / 1000, tz=timezone.utc
                )
            }
            
            # Insert membership
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO organization_members (organization_id, user_id, role, status, joined_at)
                    VALUES (%(organization_id)s, %(user_id)s, %(role)s, %(status)s, %(joined_at)s)
                    ON CONFLICT (organization_id, user_id)
                    DO UPDATE SET
                        role = EXCLUDED.role,
                        status = EXCLUDED.status,
                        updated_at = NOW()
                    RETURNING id
                """, membership_record)
                
                db.connection.commit()
                
            logger.info(f"✅ Membership created: user {membership_record['user_id']} → org {membership_record['organization_id']}")
            return {"success": True, "membership": membership_record}
            
        except Exception as e:
            logger.error(f"Failed to handle membership creation: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_organizations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all organizations a user belongs to"""
        query = """
            SELECT 
                o.id,
                o.name,
                o.slug,
                om.role,
                om.status,
                om.joined_at
            FROM organizations o
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = %s AND om.status = 'active'
            ORDER BY om.joined_at DESC
        """
        
        return db.execute_query(query, (user_id,))
    
    def get_organization_members(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get all members of an organization"""
        query = """
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.image_url,
                om.role,
                om.status,
                om.joined_at
            FROM users u
            INNER JOIN organization_members om ON u.id = om.user_id
            WHERE om.organization_id = %s AND om.status = 'active'
            ORDER BY om.role, u.first_name
        """
        
        return db.execute_query(query, (organization_id,))
    
    def check_user_permission(self, user_id: str, organization_id: str, required_role: str = 'member') -> bool:
        """Check if user has required permission level in organization"""
        role_hierarchy = {'viewer': 1, 'member': 2, 'admin': 3, 'owner': 4}
        required_level = role_hierarchy.get(required_role, 0)
        
        query = """
            SELECT role FROM organization_members 
            WHERE user_id = %s AND organization_id = %s AND status = 'active'
        """
        
        result = db.execute_single(query, (user_id, organization_id))
        if not result:
            return False
        
        user_level = role_hierarchy.get(result['role'], 0)
        return user_level >= required_level
    
    async def log_user_action(self, user_id: str, organization_id: str, action: str, 
                            resource_type: str = None, resource_id: str = None,
                            details: Dict[str, Any] = None, success: bool = True,
                            ip_address: str = None, user_agent: str = None):
        """Log user action for audit trail"""
        log_data = {
            'organization_id': organization_id,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': json.dumps(details or {}),
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (organization_id, user_id, action, resource_type,
                                      resource_id, details, success, ip_address, user_agent)
                VALUES (%(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s,
                       %(resource_id)s, %(details)s, %(success)s, %(ip_address)s, %(user_agent)s)
            """, log_data)
            
            db.connection.commit()

# Global Clerk client instance
clerk = ClerkClient() 