"""
SurfRehab v2 - API Sync Manager
Direct integration with Cliniko, Chatwoot APIs → Supabase
"""

import os
import asyncio
import logging
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from database import db
from integrations.cliniko_client import ClinikoClient
from integrations.chatwoot_client import ChatwootClient

logger = logging.getLogger(__name__)

class SyncManager:
    """Main sync manager for all API integrations"""
    
    def __init__(self, organization_id: str = None):
        self.organization_id = organization_id or os.getenv('ORGANIZATION_ID', 'default')
        self.cliniko_client = ClinikoClient()
        self.chatwoot_client = ChatwootClient()
    
    def normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number to international format"""
        if not phone:
            return None
        
        # Remove all non-digits
        digits = re.sub(r'[^\d]', '', str(phone))
        
        # Skip if too short or too long
        if len(digits) < 7 or len(digits) > 15:
            return None
        
        # Add + prefix if not present
        if not digits.startswith('+'):
            # Assume Australian number if 10 digits starting with 0
            if len(digits) == 10 and digits.startswith('0'):
                digits = '61' + digits[1:]  # Australia country code
            # Add + prefix
            digits = '+' + digits
        
        return digits
    
    async def sync_cliniko_patients(self) -> Dict[str, Any]:
        """Sync active patients from Cliniko API"""
        start_time = datetime.now(timezone.utc)
        logger.info("🏥 Starting Cliniko patient sync...")
        
        sync_data = {
            'source_system': 'cliniko',
            'operation_type': 'sync_patients',
            'organization_id': self.organization_id,
            'started_at': start_time,
            'records_processed': 0,
            'records_success': 0,
            'records_failed': 0,
            'error_details': {},
            'metadata': {}
        }
        
        try:
            # Get active patients from Cliniko
            patients = await self.cliniko_client.get_active_patients()
            
            if not patients:
                logger.warning("No active patients found in Cliniko")
                sync_data.update({
                    'status': 'warning',
                    'completed_at': datetime.now(timezone.utc),
                    'error_details': {'message': 'No patients found'}
                })
                db.log_sync_operation(sync_data)
                return {"success": False, "error": "No patients found"}
            
            sync_data['records_processed'] = len(patients)
            contacts_created = 0
            active_patients_created = 0
            
            for patient in patients:
                try:
                    # Normalize phone number
                    phone = self.normalize_phone(patient.get('phone'))
                    if not phone:
                        logger.warning(f"Skipping patient {patient.get('name')} - invalid phone")
                        sync_data['records_failed'] += 1
                        continue
                    
                    # Create or update contact
                    contact_data = {
                        'phone': phone,
                        'email': patient.get('email'),
                        'name': patient.get('name'),
                        'contact_type': 'cliniko_patient',
                        'cliniko_patient_id': str(patient.get('id')),
                        'status': 'active',
                        'organization_id': self.organization_id,
                        'metadata': json.dumps({
                            'source': 'cliniko_active_patients',
                            'synced_at': datetime.now(timezone.utc).isoformat(),
                            'original_data': patient
                        })
                    }
                    
                    contact_id = db.insert_contact(contact_data)
                    contacts_created += 1
                    
                    # Create or update active patient record
                    active_patient_data = {
                        'contact_id': contact_id,
                        'recent_appointment_count': patient.get('recent_appointment_count', 0),
                        'upcoming_appointment_count': patient.get('upcoming_appointment_count', 0),
                        'total_appointment_count': patient.get('total_appointment_count', 0),
                        'last_appointment_date': patient.get('last_appointment_date'),
                        'recent_appointments': json.dumps(patient.get('recent_appointments', [])),
                        'upcoming_appointments': json.dumps(patient.get('upcoming_appointments', [])),
                        'search_date_from': patient.get('search_date_from'),
                        'search_date_to': patient.get('search_date_to'),
                        'organization_id': self.organization_id
                    }
                    
                    db.insert_active_patient(active_patient_data)
                    active_patients_created += 1
                    sync_data['records_success'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing patient {patient.get('name')}: {e}")
                    sync_data['records_failed'] += 1
                    continue
            
            # Log successful sync
            sync_data.update({
                'status': 'success',
                'completed_at': datetime.now(timezone.utc),
                'metadata': {
                    'contacts_created': contacts_created,
                    'active_patients_created': active_patients_created
                }
            })
            db.log_sync_operation(sync_data)
            
            logger.info(f"✅ Cliniko sync complete: {contacts_created} contacts, {active_patients_created} active patients")
            return {
                "success": True,
                "contacts_created": contacts_created,
                "active_patients_created": active_patients_created
            }
            
        except Exception as e:
            logger.error(f"Cliniko sync failed: {e}")
            sync_data.update({
                'status': 'error',
                'completed_at': datetime.now(timezone.utc),
                'error_details': {'message': str(e)}
            })
            db.log_sync_operation(sync_data)
            return {"success": False, "error": str(e)}
    
    async def sync_chatwoot_conversations(self) -> Dict[str, Any]:
        """Sync conversations and contacts from Chatwoot API"""
        start_time = datetime.now(timezone.utc)
        logger.info("💬 Starting Chatwoot conversation sync...")
        
        sync_data = {
            'source_system': 'chatwoot',
            'operation_type': 'sync_conversations',
            'organization_id': self.organization_id,
            'started_at': start_time,
            'records_processed': 0,
            'records_success': 0,
            'records_failed': 0,
            'error_details': {},
            'metadata': {}
        }
        
        try:
            # Get conversations from Chatwoot
            conversations = await self.chatwoot_client.get_conversations()
            
            if not conversations:
                logger.warning("No conversations found in Chatwoot")
                sync_data.update({
                    'status': 'warning',
                    'completed_at': datetime.now(timezone.utc),
                    'error_details': {'message': 'No conversations found'}
                })
                db.log_sync_operation(sync_data)
                return {"success": False, "error": "No conversations found"}
            
            sync_data['records_processed'] = len(conversations)
            contacts_created = 0
            conversations_created = 0
            
            for conversation in conversations:
                try:
                    # Extract phone number from conversation
                    phone = self.normalize_phone(
                        conversation.get('meta', {}).get('sender', {}).get('phone_number')
                    )
                    
                    if not phone:
                        logger.warning(f"Skipping conversation {conversation.get('id')} - no valid phone")
                        sync_data['records_failed'] += 1
                        continue
                    
                    # Create or update contact
                    contact_data = {
                        'phone': phone,
                        'email': conversation.get('meta', {}).get('sender', {}).get('email'),
                        'name': conversation.get('meta', {}).get('sender', {}).get('name') or f"WhatsApp {phone}",
                        'contact_type': 'chatwoot_contact',
                        'status': 'active',
                        'organization_id': self.organization_id,
                        'metadata': json.dumps({
                            'source': 'chatwoot_conversations',
                            'chatwoot_conversation_id': conversation.get('id'),
                            'synced_at': datetime.now(timezone.utc).isoformat(),
                            'conversation_status': conversation.get('status'),
                            'last_activity': conversation.get('last_activity_at')
                        })
                    }
                    
                    contact_id = db.insert_contact(contact_data)
                    contacts_created += 1
                    
                    # Create conversation record
                    conversation_data = {
                        'contact_id': contact_id,
                        'source': 'chatwoot',
                        'external_id': str(conversation.get('id')),
                        'chatwoot_conversation_id': conversation.get('id'),
                        'phone_number': phone,
                        'status': conversation.get('status', 'active'),
                        'organization_id': self.organization_id,
                        'metadata': json.dumps({
                            'chatwoot_data': conversation,
                            'synced_at': datetime.now(timezone.utc).isoformat()
                        })
                    }
                    
                    db.insert_conversation(conversation_data)
                    conversations_created += 1
                    sync_data['records_success'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing conversation {conversation.get('id')}: {e}")
                    sync_data['records_failed'] += 1
                    continue
            
            # Log successful sync
            sync_data.update({
                'status': 'success',
                'completed_at': datetime.now(timezone.utc),
                'metadata': {
                    'contacts_created': contacts_created,
                    'conversations_created': conversations_created
                }
            })
            db.log_sync_operation(sync_data)
            
            logger.info(f"✅ Chatwoot sync complete: {contacts_created} contacts, {conversations_created} conversations")
            return {
                "success": True,
                "contacts_created": contacts_created,
                "conversations_created": conversations_created
            }
            
        except Exception as e:
            logger.error(f"Chatwoot sync failed: {e}")
            sync_data.update({
                'status': 'error',
                'completed_at': datetime.now(timezone.utc),
                'error_details': {'message': str(e)}
            })
            db.log_sync_operation(sync_data)
            return {"success": False, "error": str(e)}
    
    async def full_sync(self) -> Dict[str, Any]:
        """Run complete sync from all APIs"""
        logger.info("🔄 Starting full API sync...")
        
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": self.organization_id,
            "cliniko": await self.sync_cliniko_patients(),
            "chatwoot": await self.sync_chatwoot_conversations(),
        }
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["success"] = all(r.get("success", False) for r in [results["cliniko"], results["chatwoot"]])
        
        logger.info(f"🎉 Full sync complete: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")
        return results
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and data counts"""
        try:
            # Get contact statistics
            contact_stats = db.get_contact_stats(self.organization_id)
            
            # Get active patients count
            active_patients = db.execute_query(
                "SELECT COUNT(*) as count FROM patients WHERE organization_id = %s AND is_active = true",
                (self.organization_id,)
            )
            active_patients_count = active_patients[0]['count'] if active_patients else 0
            
            # Get conversations count
            conversations = db.execute_query(
                "SELECT COUNT(*) as count FROM conversations WHERE deleted_at IS NULL AND organization_id = %s",
                (self.organization_id,)
            )
            conversations_count = conversations[0]['count'] if conversations else 0
            
            # Get recent sync logs
            recent_syncs = db.get_recent_sync_logs(self.organization_id, limit=5)
            
            return {
                "success": True,
                "organization_id": self.organization_id,
                "contact_stats": contact_stats,
                "active_patients_count": active_patients_count,
                "conversations_count": conversations_count,
                "recent_syncs": recent_syncs,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {"success": False, "error": str(e)} 