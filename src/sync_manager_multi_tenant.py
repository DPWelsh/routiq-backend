"""
Multi-Tenant Sync Manager for SurfRehab v2
Handles API synchronization for multiple organizations with encrypted credentials
"""

import os
import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
import base64

from database import db
from integrations.clerk_client import clerk

logger = logging.getLogger(__name__)

@dataclass
class OrganizationCredentials:
    """Container for organization's API credentials"""
    organization_id: str
    cliniko_api_key: str
    cliniko_subdomain: str
    chatwoot_api_key: str
    chatwoot_account_id: str
    manychat_api_key: str = None
    momence_api_key: str = None

class CredentialsManager:
    """Handles encryption/decryption of API credentials"""
    
    def __init__(self):
        # Get or generate encryption key
        encryption_key = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
        if not encryption_key:
            # In production, this should come from a secure key management service
            raise ValueError("CREDENTIALS_ENCRYPTION_KEY environment variable required")
        
        self.cipher_suite = Fernet(encryption_key.encode())
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for database storage"""
        json_data = json.dumps(credentials)
        encrypted_data = self.cipher_suite.encrypt(json_data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credentials from database"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return {}

class MultiTenantSyncManager:
    """Enhanced sync manager for multi-tenant SaaS"""
    
    def __init__(self):
        self.credentials_manager = CredentialsManager()
    
    def set_organization_context(self, organization_id: str):
        """Set the current organization context for RLS"""
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.current_organization_id', %s, false)",
                (organization_id,)
            )
    
    async def store_api_credentials(self, organization_id: str, service_name: str, 
                                  credentials: Dict[str, Any], created_by: str) -> bool:
        """Store encrypted API credentials for an organization"""
        try:
            # Encrypt the credentials
            encrypted_creds = self.credentials_manager.encrypt_credentials(credentials)
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO service_credentials (organization_id, service_name, credentials_encrypted, created_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (organization_id, service_name)
                    DO UPDATE SET
                        credentials_encrypted = EXCLUDED.credentials_encrypted,
                        updated_at = NOW(),
                        created_by = EXCLUDED.created_by
                """, (organization_id, service_name, encrypted_creds, created_by))
                
                # Log the credential storage
                cursor.execute("""
                    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
                    VALUES (%s, 'store_credentials', 'service_credentials', %s, %s)
                """, (created_by, organization_id, json.dumps({
                    'service_name': service_name,
                    'organization_id': organization_id
                })))
                
            db.connection.commit()
            
            # Log the credential update
            await clerk.log_user_action(
                user_id=created_by,
                organization_id=organization_id,
                action='credentials_updated',
                resource_type='service_credentials',
                resource_id=service_name,
                details={'service': service_name}
            )
            
            logger.info(f"✅ Stored {service_name} credentials for org {organization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials for {service_name}: {e}")
            return False
    
    def get_organization_credentials(self, organization_id: str) -> Optional[OrganizationCredentials]:
        """Retrieve and decrypt all API credentials for an organization"""
        try:
            query = """
                SELECT service_name, credentials_encrypted, is_active
                FROM service_credentials 
                WHERE organization_id = %s AND is_active = true
            """
            
            results = db.execute_query(query, (organization_id,))
            if not results:
                return None
            
            # Decrypt all credentials
            all_creds = {}
            for row in results:
                decrypted = self.credentials_manager.decrypt_credentials(row['credentials_encrypted'])
                all_creds[row['service_name']] = decrypted
            
            # Extract specific service credentials
            cliniko_creds = all_creds.get('cliniko', {})
            chatwoot_creds = all_creds.get('chatwoot', {})
            
            if not cliniko_creds or not chatwoot_creds:
                logger.warning(f"Missing required credentials for org {organization_id}")
                return None
            
            return OrganizationCredentials(
                organization_id=organization_id,
                cliniko_api_key=cliniko_creds.get('api_key'),
                cliniko_subdomain=cliniko_creds.get('subdomain'),
                chatwoot_api_key=chatwoot_creds.get('api_key'),
                chatwoot_account_id=chatwoot_creds.get('account_id'),
                manychat_api_key=all_creds.get('manychat', {}).get('api_key'),
                momence_api_key=all_creds.get('momence', {}).get('api_key')
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for org {organization_id}: {e}")
            return None
    
    async def validate_organization_credentials(self, organization_id: str) -> Dict[str, bool]:
        """Test all API credentials for an organization"""
        creds = self.get_organization_credentials(organization_id)
        if not creds:
            return {"error": "No credentials found"}
        
        validation_results = {}
        
        # Test Cliniko API
        try:
            from integrations.cliniko_client import ClinikoClient
            cliniko = ClinikoClient(creds.cliniko_api_key, creds.cliniko_subdomain)
            test_result = await cliniko.test_connection()
            validation_results['cliniko'] = test_result
        except Exception as e:
            validation_results['cliniko'] = False
            logger.error(f"Cliniko validation failed for org {organization_id}: {e}")
        
        # Test Chatwoot API
        try:
            from integrations.chatwoot_client import ChatwootClient
            chatwoot = ChatwootClient(creds.chatwoot_api_key, creds.chatwoot_account_id)
            test_result = await chatwoot.test_connection()
            validation_results['chatwoot'] = test_result
        except Exception as e:
            validation_results['chatwoot'] = False
            logger.error(f"Chatwoot validation failed for org {organization_id}: {e}")
        
        # Update validation status in database
        for service, is_valid in validation_results.items():
            with db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_credentials 
                    SET last_validated_at = NOW(),
                        validation_error = CASE WHEN %s THEN NULL ELSE 'Connection failed' END
                    WHERE organization_id = %s AND service_name = %s
                """, (is_valid, organization_id, service))
                
        db.connection.commit()
        return validation_results
    
    async def sync_organization_data(self, organization_id: str, force: bool = False) -> Dict[str, Any]:
        """Sync data for a specific organization"""
        start_time = datetime.now(timezone.utc)
        
        # Set organization context for RLS
        self.set_organization_context(organization_id)
        
        # Get credentials
        creds = self.get_organization_credentials(organization_id)
        if not creds:
            return {"success": False, "error": "No valid credentials found"}
        
        sync_results = {
            "organization_id": organization_id,
            "started_at": start_time.isoformat(),
            "cliniko": {"success": False, "synced": 0, "errors": []},
            "chatwoot": {"success": False, "synced": 0, "errors": []}
        }
        
        try:
            # Initialize API clients
            from integrations.cliniko_client import ClinikoClient
            from integrations.chatwoot_client import ChatwootClient
            
            cliniko = ClinikoClient(creds.cliniko_api_key, creds.cliniko_subdomain)
            chatwoot = ChatwootClient(creds.chatwoot_api_key, creds.chatwoot_account_id)
            
            # Sync Cliniko patients
            logger.info(f"🔄 Starting Cliniko sync for org {organization_id}")
            try:
                cliniko_result = await self._sync_cliniko_patients(cliniko, organization_id)
                sync_results["cliniko"] = cliniko_result
            except Exception as e:
                sync_results["cliniko"]["errors"].append(str(e))
                logger.error(f"Cliniko sync failed for org {organization_id}: {e}")
            
            # Sync Chatwoot conversations
            logger.info(f"🔄 Starting Chatwoot sync for org {organization_id}")
            try:
                chatwoot_result = await self._sync_chatwoot_conversations(chatwoot, organization_id)
                sync_results["chatwoot"] = chatwoot_result
            except Exception as e:
                sync_results["chatwoot"]["errors"].append(str(e))
                logger.error(f"Chatwoot sync failed for org {organization_id}: {e}")
            
            # Log sync completion
            sync_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            sync_results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Store sync log
            await self._store_sync_log(organization_id, sync_results)
            
            logger.info(f"✅ Sync completed for org {organization_id}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Sync failed for org {organization_id}: {e}")
            sync_results["error"] = str(e)
            sync_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            await self._store_sync_log(organization_id, sync_results, success=False)
            return sync_results
    
    async def sync_all_organizations(self) -> List[Dict[str, Any]]:
        """Sync data for all active organizations"""
        # Get all organizations with valid credentials
        query = """
            SELECT DISTINCT organization_id 
            FROM service_credentials 
            WHERE is_active = true
        """
        
        organizations = db.execute_query(query)
        all_results = []
        
        for org in organizations:
            org_id = org['organization_id']
            logger.info(f"🔄 Starting sync for organization {org_id}")
            
            result = await self.sync_organization_data(org_id)
            all_results.append(result)
            
            # Small delay between organizations to prevent API rate limiting
            await asyncio.sleep(2)
        
        return all_results
    
    async def _sync_cliniko_patients(self, cliniko, organization_id: str) -> Dict[str, Any]:
        """Sync patients from Cliniko for specific organization"""
        # Implementation similar to existing sync logic, but organization-aware
        return {"success": True, "synced": 0, "errors": []}
    
    async def _sync_chatwoot_conversations(self, chatwoot, organization_id: str) -> Dict[str, Any]:
        """Sync conversations from Chatwoot for specific organization"""
        # Implementation similar to existing sync logic, but organization-aware
        return {"success": True, "synced": 0, "errors": []}
    
    async def _store_sync_log(self, organization_id: str, results: Dict[str, Any], success: bool = True):
        """Store sync log in database"""
        log_data = {
            'organization_id': organization_id,
            'sync_type': 'full',
            'status': 'completed' if success else 'failed',
            'results': json.dumps(results),
            'started_at': results.get('started_at'),
            'completed_at': results.get('completed_at')
        }
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_logs (organization_id, sync_type, status, results, started_at, completed_at)
                VALUES (%(organization_id)s, %(sync_type)s, %(status)s, %(results)s, 
                       %(started_at)s::timestamp, %(completed_at)s::timestamp)
            """, log_data)
            
            db.connection.commit()

# Global sync manager instance
multi_tenant_sync = MultiTenantSyncManager() 