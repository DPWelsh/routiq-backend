"""
HIPAA-Compliant Audit Logging Service
Tracks all PHI access and critical system actions for healthcare compliance
"""

import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request

from src.database import db

logger = logging.getLogger(__name__)

class PHIAuditLogger:
    """HIPAA-compliant audit logger for patient health information access"""
    
    @staticmethod
    async def log_phi_access(
        user_id: str,
        organization_id: str,
        action: str,
        resource_type: str = "patient",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        request: Optional[Request] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Log PHI access for HIPAA compliance
        
        Args:
            user_id: ID of user accessing PHI
            organization_id: Organization context
            action: Action performed (view_patient, export_data, etc.)
            resource_type: Type of resource accessed
            resource_id: ID of specific resource
            details: Additional context
            success: Whether action succeeded
            request: FastAPI request object for IP/user agent
            error_message: Error details if action failed
        """
        try:
            # Extract request information
            ip_address = None
            user_agent = None
            session_id = None
            
            if request:
                # Get client IP (handle proxy headers)
                ip_address = (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                    request.headers.get("X-Real-IP") or
                    getattr(request.client, "host", None) if hasattr(request, "client") else None
                )
                user_agent = request.headers.get("User-Agent")
                # Generate session ID from request if available
                session_id = request.headers.get("X-Session-ID") or f"req_{hash(str(request.url))}"
            
            # Prepare audit log entry
            audit_entry = {
                "organization_id": organization_id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ip_address": ip_address,
                "user_agent": user_agent[:500] if user_agent else None,  # Limit length
                "session_id": session_id,
                "details": json.dumps(details) if details else None,
                "success": success,
                "error_message": error_message,
                "created_at": datetime.now(timezone.utc)
            }
            
            # Insert into audit_logs table
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO audit_logs (
                        organization_id, user_id, action, resource_type, resource_id,
                        ip_address, user_agent, session_id, details, success, error_message,
                        created_at
                    ) VALUES (
                        %(organization_id)s, %(user_id)s, %(action)s, %(resource_type)s, %(resource_id)s,
                        %(ip_address)s, %(user_agent)s, %(session_id)s, %(details)s, %(success)s, %(error_message)s,
                        %(created_at)s
                    )
                """, audit_entry)
                
                db.connection.commit()
            
            # Log critical PHI access to application logs
            if resource_type in ["patient", "appointment", "medical_record"]:
                log_level = logging.WARNING if not success else logging.INFO
                logger.log(
                    log_level,
                    f"PHI_ACCESS: {action} | User: {user_id} | Org: {organization_id} | "
                    f"Resource: {resource_type}:{resource_id} | Success: {success} | IP: {ip_address}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")
            return False
    
    @staticmethod
    async def log_authentication_event(
        user_id: Optional[str],
        organization_id: Optional[str],
        action: str,
        success: bool,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log authentication events (login, logout, failed attempts)"""
        return await PHIAuditLogger.log_phi_access(
            user_id=user_id or "anonymous",
            organization_id=organization_id or "system",
            action=f"auth_{action}",
            resource_type="authentication",
            resource_id=None,
            details=details,
            success=success,
            request=request,
            error_message=error_message
        )
    
    @staticmethod
    async def log_data_export(
        user_id: str,
        organization_id: str,
        export_type: str,
        record_count: int,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """Log data export events for HIPAA compliance"""
        details = {
            "export_type": export_type,
            "record_count": record_count,
            "export_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return await PHIAuditLogger.log_phi_access(
            user_id=user_id,
            organization_id=organization_id,
            action="export_data",
            resource_type="bulk_data",
            resource_id=f"{export_type}_{record_count}_records",
            details=details,
            success=success,
            request=request,
            error_message=error_message
        )
    
    @staticmethod
    async def log_sync_operation(
        organization_id: str,
        sync_type: str,
        records_processed: int,
        success: bool,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log data synchronization operations"""
        sync_details = {
            "sync_type": sync_type,
            "records_processed": records_processed,
            "sync_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if details:
            sync_details.update(details)
        
        return await PHIAuditLogger.log_phi_access(
            user_id="system",
            organization_id=organization_id,
            action="sync_data",
            resource_type="bulk_sync",
            resource_id=f"{sync_type}_{records_processed}_records",
            details=sync_details,
            success=success,
            request=None,
            error_message=error_message
        )
    
    @staticmethod
    async def get_audit_trail(
        organization_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days_back: int = 30,
        limit: int = 100
    ) -> list:
        """Retrieve audit trail for compliance reporting"""
        try:
            query = """
                SELECT 
                    created_at,
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    ip_address,
                    success,
                    error_message,
                    details
                FROM audit_logs 
                WHERE organization_id = %s
                AND created_at >= NOW() - INTERVAL '%s days'
            """
            params = [organization_id, days_back]
            
            # Add optional filters
            if resource_type:
                query += " AND resource_type = %s"
                params.append(resource_type)
            
            if resource_id:
                query += " AND resource_id = %s"
                params.append(resource_id)
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            return db.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []
    
    @staticmethod 
    async def get_phi_access_summary(
        organization_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get summary of PHI access for compliance monitoring"""
        try:
            query = """
                SELECT 
                    action,
                    resource_type,
                    COUNT(*) as access_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(CASE WHEN success = false THEN 1 END) as failed_attempts
                FROM audit_logs 
                WHERE organization_id = %s
                AND created_at >= NOW() - INTERVAL '%s days'
                AND resource_type IN ('patient', 'appointment', 'medical_record')
                GROUP BY action, resource_type
                ORDER BY access_count DESC
            """
            
            results = db.execute_query(query, (organization_id, days_back))
            
            return {
                "organization_id": organization_id,
                "period_days": days_back,
                "phi_access_summary": results,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate PHI access summary: {e}")
            return {"error": str(e)}

# Global audit logger instance
audit_logger = PHIAuditLogger()

# Convenience functions for common audit actions
async def log_patient_view(user_id: str, organization_id: str, patient_id: str, request: Request = None):
    """Quick function to log patient record viewing"""
    return await audit_logger.log_phi_access(
        user_id=user_id,
        organization_id=organization_id,
        action="view_patient",
        resource_type="patient",
        resource_id=patient_id,
        request=request
    )

async def log_patient_export(user_id: str, organization_id: str, patient_count: int, request: Request = None):
    """Quick function to log patient data export"""
    return await audit_logger.log_data_export(
        user_id=user_id,
        organization_id=organization_id,
        export_type="patients",
        record_count=patient_count,
        request=request
    )

async def log_failed_auth(user_id: str, organization_id: str, reason: str, request: Request = None):
    """Quick function to log failed authentication attempts"""
    return await audit_logger.log_authentication_event(
        user_id=user_id,
        organization_id=organization_id,
        action="login_failed",
        success=False,
        request=request,
        error_message=reason
    ) 