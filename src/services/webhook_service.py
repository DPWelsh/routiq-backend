"""
Webhook Service for N8N Integration
Handles webhook execution, logging, and retry logic
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

import aiohttp
from src.database import db

logger = logging.getLogger(__name__)

class WebhookService:
    """
    Core service for managing webhook execution and logging
    Integrates with N8N workflows and logs to Supabase
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def trigger_webhook(
        self,
        webhook_type: str,
        organization_id: str,
        patient_id: Optional[str] = None,
        trigger_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        trigger_source: str = 'api'
    ) -> Dict[str, Any]:
        """
        Trigger a webhook workflow with comprehensive logging
        
        Args:
            webhook_type: Type of webhook (patient_followup, appointment_reminder, etc.)
            organization_id: Organization ID for context
            patient_id: Optional patient ID
            trigger_data: Data that triggered the webhook
            user_id: User who triggered the webhook
            trigger_source: Source of trigger (dashboard, bulk_action, automated, api)
            
        Returns:
            Dict with execution results and log ID
        """
        
        # Get webhook template
        template = await self._get_webhook_template(webhook_type, organization_id)
        if not template:
            logger.error(f"No webhook template found for type: {webhook_type}")
            return {
                "success": False,
                "error": f"No webhook template found for type: {webhook_type}",
                "log_id": None
            }
        
        # Generate webhook log ID
        log_id = str(uuid4())
        
        # Build payload from template
        try:
            payload = await self._build_payload(template, organization_id, patient_id, trigger_data)
        except Exception as e:
            logger.error(f"Failed to build webhook payload: {e}")
            return {
                "success": False, 
                "error": f"Failed to build payload: {str(e)}",
                "log_id": None
            }
        
        # Create initial webhook log
        await self._create_webhook_log(
            log_id=log_id,
            organization_id=organization_id,
            patient_id=patient_id,
            webhook_type=webhook_type,
            workflow_name=template['name'],
            n8n_webhook_url=template['n8n_webhook_url'],
            trigger_data=trigger_data,
            request_payload=payload,
            user_id=user_id,
            trigger_source=trigger_source,
            max_retries=template.get('retry_attempts', 3)
        )
        
        # Execute webhook
        result = await self._execute_webhook(log_id, template, payload)
        
        return {
            "success": result["success"],
            "log_id": log_id,
            "status": result["status"],
            "execution_time_ms": result.get("execution_time_ms"),
            "error": result.get("error")
        }
    
    async def _get_webhook_template(self, webhook_type: str, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook template by type and organization"""
        
        try:
            with db.get_cursor() as cursor:
                # Set organization context for RLS
                cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
                
                # Get template (org-specific first, then global)
                query = """
                SELECT id, name, webhook_type, n8n_webhook_url, workflow_id,
                       payload_template, headers, http_method, timeout_seconds,
                       retry_attempts, retry_delay_seconds
                FROM webhook_templates 
                WHERE webhook_type = %s AND is_active = true
                ORDER BY 
                    CASE WHEN organization_id = %s THEN 1 ELSE 2 END,
                    created_at DESC
                LIMIT 1
                """
                
                cursor.execute(query, [webhook_type, organization_id])
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                    
                return None
                
        except Exception as e:
            logger.error(f"Failed to get webhook template: {e}")
            return None
    
    async def _build_payload(
        self, 
        template: Dict[str, Any], 
        organization_id: str,
        patient_id: Optional[str],
        trigger_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build webhook payload from template with variable substitution"""
        
        # Get patient data if patient_id provided
        patient_data = {}
        if patient_id:
            patient_data = await self._get_patient_data(patient_id, organization_id)
        
        # Get organization data
        org_data = await self._get_organization_data(organization_id)
        
        # Prepare substitution variables
        variables = {
            # Patient variables
            "patient_id": patient_id,
            "patient_name": patient_data.get("name", ""),
            "patient_email": patient_data.get("email", ""),
            "patient_phone": patient_data.get("phone", ""),
            "risk_level": patient_data.get("risk_level", ""),
            "engagement_status": patient_data.get("engagement_status", ""),
            "last_appointment_date": patient_data.get("last_appointment_date", ""),
            "total_appointment_count": patient_data.get("total_appointment_count", 0),
            "lifetime_value_aud": patient_data.get("lifetime_value_aud", 0),
            "days_since_last_contact": patient_data.get("days_since_last_contact", 0),
            "action_priority": patient_data.get("action_priority", 4),
            "recommended_action": patient_data.get("recommended_action", ""),
            
            # Organization variables
            "organization_id": organization_id,
            "organization_name": org_data.get("name", ""),
            
            # Context variables
            "timestamp": datetime.now().isoformat(),
            "trigger_source": trigger_data.get("trigger_source", "api") if trigger_data else "api",
            "user_id": trigger_data.get("user_id", "") if trigger_data else ""
        }
        
        # Add any additional trigger data
        if trigger_data:
            variables.update(trigger_data)
        
        # Perform variable substitution in template
        payload_template = template.get('payload_template', {})
        if isinstance(payload_template, str):
            payload_template = json.loads(payload_template)
        
        # Substitute variables in the template
        payload = self._substitute_variables(payload_template, variables)
        
        return payload
    
    def _substitute_variables(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in template object"""
        
        if isinstance(obj, dict):
            return {key: self._substitute_variables(value, variables) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, variables) for item in obj]
        elif isinstance(obj, str):
            # Replace {{variable}} patterns
            result = obj
            for key, value in variables.items():
                result = result.replace(f"{{{{{key}}}}}", str(value) if value is not None else "")
            return result
        else:
            return obj
    
    async def _get_patient_data(self, patient_id: str, organization_id: str) -> Dict[str, Any]:
        """Get patient data from reengagement master view"""
        
        try:
            with db.get_cursor() as cursor:
                # Set context
                cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
                
                query = """
                SELECT patient_name, email, phone, risk_level, engagement_status,
                       last_appointment_date, total_appointment_count, lifetime_value_aud,
                       days_since_last_contact, action_priority, recommended_action
                FROM patient_reengagement_master 
                WHERE patient_id = %s AND organization_id = %s
                """
                
                cursor.execute(query, [patient_id, organization_id])
                row = cursor.fetchone()
                
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"Failed to get patient data: {e}")
            return {}
    
    async def _get_organization_data(self, organization_id: str) -> Dict[str, Any]:
        """Get organization data (placeholder - implement based on your schema)"""
        
        # TODO: Implement based on your organizations table
        return {
            "name": "Healthcare Clinic",  # Replace with actual lookup
            "id": organization_id
        }
    
    async def _create_webhook_log(
        self,
        log_id: str,
        organization_id: str,
        patient_id: Optional[str],
        webhook_type: str,
        workflow_name: str,
        n8n_webhook_url: str,
        trigger_data: Optional[Dict[str, Any]],
        request_payload: Dict[str, Any],
        user_id: Optional[str],
        trigger_source: str,
        max_retries: int = 3
    ):
        """Create initial webhook log entry"""
        
        try:
            with db.get_cursor() as cursor:
                # Set context
                cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
                
                query = """
                INSERT INTO webhook_logs (
                    id, organization_id, patient_id, webhook_type, workflow_name,
                    n8n_webhook_url, trigger_data, request_payload, status,
                    max_retries, triggered_by_user_id, trigger_source
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s
                )
                """
                
                cursor.execute(query, [
                    log_id, organization_id, patient_id, webhook_type, workflow_name,
                    n8n_webhook_url, json.dumps(trigger_data) if trigger_data else None,
                    json.dumps(request_payload), max_retries, user_id, trigger_source
                ])
                
        except Exception as e:
            logger.error(f"Failed to create webhook log: {e}")
            raise
    
    async def _execute_webhook(
        self, 
        log_id: str, 
        template: Dict[str, Any], 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual webhook call to N8N"""
        
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        webhook_url = template['n8n_webhook_url']
        headers = template.get('headers', {"Content-Type": "application/json"})
        if isinstance(headers, str):
            headers = json.loads(headers)
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=template.get('timeout_seconds', 30))
            ) as response:
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                response_data = {}
                
                try:
                    response_data = await response.json()
                except:
                    response_data = {"response_text": await response.text()}
                
                success = response.status < 400
                status = 'success' if success else 'failed'
                
                # Update webhook log
                await self._update_webhook_log(
                    log_id=log_id,
                    status=status,
                    http_status_code=response.status,
                    response_data=response_data,
                    execution_time_ms=execution_time_ms,
                    error_message=None if success else f"HTTP {response.status}: {response.reason}"
                )
                
                return {
                    "success": success,
                    "status": status,
                    "http_status_code": response.status,
                    "execution_time_ms": execution_time_ms,
                    "response_data": response_data
                }
                
        except asyncio.TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._update_webhook_log(
                log_id=log_id,
                status='timeout',
                execution_time_ms=execution_time_ms,
                error_message="Request timeout"
            )
            
            return {
                "success": False,
                "status": "timeout",
                "execution_time_ms": execution_time_ms,
                "error": "Request timeout"
            }
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            await self._update_webhook_log(
                log_id=log_id,
                status='failed',
                execution_time_ms=execution_time_ms,
                error_message=error_message
            )
            
            return {
                "success": False,
                "status": "failed", 
                "execution_time_ms": execution_time_ms,
                "error": error_message
            }
    
    async def _update_webhook_log(
        self,
        log_id: str,
        status: str,
        http_status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update webhook log with execution results"""
        
        try:
            with db.get_cursor() as cursor:
                query = """
                UPDATE webhook_logs 
                SET status = %s,
                    http_status_code = %s,
                    response_data = %s,
                    execution_time_ms = %s,
                    error_message = %s,
                    completed_at = NOW()
                WHERE id = %s
                """
                
                cursor.execute(query, [
                    status,
                    http_status_code,
                    json.dumps(response_data) if response_data else None,
                    execution_time_ms,
                    error_message,
                    log_id
                ])
                
        except Exception as e:
            logger.error(f"Failed to update webhook log: {e}")
    
    async def get_webhook_logs(
        self, 
        organization_id: str, 
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get webhook logs for an organization"""
        
        try:
            with db.get_cursor() as cursor:
                # Set context
                cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
                
                where_clause = ""
                params = [organization_id, limit, offset]
                
                if status_filter:
                    where_clause = " AND status = %s"
                    params.insert(1, status_filter)
                
                query = f"""
                SELECT id, patient_id, webhook_type, workflow_name, status,
                       execution_time_ms, triggered_by_user_id, trigger_source,
                       triggered_at, completed_at, error_message
                FROM webhook_logs 
                WHERE organization_id = %s{where_clause}
                ORDER BY triggered_at DESC
                LIMIT %s OFFSET %s
                """
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            return []
    
    async def retry_webhook(self, log_id: str, organization_id: str) -> Dict[str, Any]:
        """Retry a failed webhook"""
        
        try:
            with db.get_cursor() as cursor:
                # Set context
                cursor.execute("SELECT set_organization_context(%s, 'user')", [organization_id])
                
                # Get webhook log
                query = """
                SELECT webhook_type, request_payload, retry_count, max_retries,
                       patient_id, triggered_by_user_id, trigger_source, trigger_data
                FROM webhook_logs 
                WHERE id = %s AND organization_id = %s
                """
                
                cursor.execute(query, [log_id, organization_id])
                row = cursor.fetchone()
                
                if not row:
                    return {"success": False, "error": "Webhook log not found"}
                
                log_data = dict(row)
                
                # Check retry limit
                if log_data['retry_count'] >= log_data['max_retries']:
                    return {"success": False, "error": "Maximum retry attempts exceeded"}
                
                # Increment retry count
                cursor.execute(
                    "UPDATE webhook_logs SET retry_count = retry_count + 1, status = 'retrying' WHERE id = %s",
                    [log_id]
                )
                
                # Get template and retry
                template = await self._get_webhook_template(log_data['webhook_type'], organization_id)
                if not template:
                    return {"success": False, "error": "Webhook template not found"}
                
                # Execute webhook
                payload = json.loads(log_data['request_payload']) if log_data['request_payload'] else {}
                result = await self._execute_webhook(log_id, template, payload)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to retry webhook: {e}")
            return {"success": False, "error": str(e)}


# Global webhook service instance
webhook_service = WebhookService() 