"""
Admin API endpoints for system administration and database management
Pure system administration - NOT integration-specific
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import json
from datetime import datetime

from src.database import db

router = APIRouter(tags=["Admin"])
logger = logging.getLogger(__name__)

@router.post("/migrate/organization-services")
async def migrate_organization_services() -> Dict[str, Any]:
    """
    Create organization_services table for multi-integration support
    System-level migration for service configuration management
    """
    try:
        migration_results = []
        
        # Step 1: Create the table
        logger.info("Creating organization_services table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.organization_services (
          id uuid NOT NULL DEFAULT uuid_generate_v4(),
          organization_id text NOT NULL,
          service_name character varying NOT NULL,
          service_config jsonb NULL DEFAULT '{}'::jsonb,
          is_primary boolean NULL DEFAULT false,
          is_active boolean NULL DEFAULT true,
          sync_enabled boolean NULL DEFAULT true,
          last_sync_at timestamp with time zone NULL,
          created_at timestamp with time zone NULL DEFAULT now(),
          CONSTRAINT organization_services_pkey PRIMARY KEY (id),
          CONSTRAINT organization_services_organization_id_service_name_key UNIQUE (organization_id, service_name),
          CONSTRAINT organization_services_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES organizations (id)
        );
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(create_table_sql)
            db.connection.commit()
            migration_results.append("✅ organization_services table created")
        
        # Step 2: Create indexes
        logger.info("Creating indexes...")
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_organization_services_org_id ON public.organization_services USING btree (organization_id);",
            "CREATE INDEX IF NOT EXISTS idx_organization_services_service_name ON public.organization_services USING btree (service_name);",
            "CREATE INDEX IF NOT EXISTS idx_organization_services_active ON public.organization_services USING btree (is_active) WHERE is_active = true;"
        ]
        
        with db.get_cursor() as cursor:
            for idx_sql in indexes_sql:
                cursor.execute(idx_sql)
            db.connection.commit()
            migration_results.append("✅ Indexes created")
        
        return {
            "success": True,
            "migration_completed_at": datetime.now().isoformat(),
            "results": migration_results,
            "message": "Organization services table created for multi-integration support"
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/organization-services/{organization_id}")
async def get_organization_services(organization_id: str) -> Dict[str, Any]:
    """
    Get all services configured for an organization
    Returns: Cliniko, Chatwoot, ManyChat, etc. configurations
    """
    try:
        query = """
        SELECT 
          os.*,
          o.name as organization_name
        FROM organization_services os
        JOIN organizations o ON o.id = os.organization_id
        WHERE os.organization_id = %s
        ORDER BY os.is_primary DESC, os.service_name;
        """
        
        services = db.execute_query(query, (organization_id,))
        
        return {
            "organization_id": organization_id,
            "services": services,
            "total_services": len(services),
            "active_services": len([s for s in services if s['is_active']]),
            "primary_service": next((s for s in services if s['is_primary']), None),
            "available_integrations": [s['service_name'] for s in services]
        }
        
    except Exception as e:
        logger.error(f"Failed to get organization services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/system-health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get overall system health across all integrations
    System-wide monitoring endpoint
    """
    try:
        health_data = {}
        
        # Database connectivity
        try:
            db_health = db.health_check()
            health_data["database"] = {"status": "healthy" if db_health else "unhealthy", "connected": db_health}
        except Exception as e:
            health_data["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Get total counts across all organizations
        try:
            with db.get_cursor() as cursor:
                # Total organizations
                cursor.execute("SELECT COUNT(*) as total FROM organizations")
                org_result = cursor.fetchone()
                total_organizations = org_result['total'] if org_result else 0
                
                # Total contacts
                cursor.execute("SELECT COUNT(*) as total FROM contacts")
                contact_result = cursor.fetchone()
                total_contacts = contact_result['total'] if contact_result else 0
                
                # Total active patients 
                cursor.execute("SELECT COUNT(*) as total FROM active_patients")
                patient_result = cursor.fetchone()
                total_active_patients = patient_result['total'] if patient_result else 0
                
                # Service configurations
                cursor.execute("SELECT service_name, COUNT(*) as count FROM organization_services GROUP BY service_name")
                service_results = cursor.fetchall()
                
                health_data["metrics"] = {
                    "total_organizations": total_organizations,
                    "total_contacts": total_contacts,
                    "total_active_patients": total_active_patients,
                    "configured_services": {row['service_name']: row['count'] for row in service_results}
                }
                
        except Exception as e:
            health_data["metrics"] = {"error": str(e)}
        
        # Overall health status
        overall_status = "healthy" if health_data.get("database", {}).get("status") == "healthy" else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "system_health": health_data,
            "message": f"System is {overall_status}"
        }
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/sync-logs/all")
async def get_all_sync_logs(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent sync logs across ALL integrations
    System-wide sync monitoring
    """
    try:
        query = """
        SELECT 
            sl.*,
            o.name as organization_name
        FROM sync_logs sl
        LEFT JOIN organizations o ON sl.organization_id = o.id
        ORDER BY sl.created_at DESC
        LIMIT %s;
        """
        
        logs = db.execute_query(query, (limit,))
        
        # Group by source system for better overview
        by_source = {}
        for log in logs:
            source = log.get('source_system', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(log)
        
        return {
            "logs": logs,
            "total_logs": len(logs),
            "by_source_system": by_source,
            "available_sources": list(by_source.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/cleanup")
async def cleanup_old_data(days_old: int = 90) -> Dict[str, Any]:
    """
    Clean up old data across all integrations
    System maintenance endpoint
    """
    try:
        cleanup_results = []
        
        # Clean old sync logs
        with db.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM sync_logs 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """, (days_old,))
            deleted_logs = cursor.rowcount
            db.connection.commit()
            cleanup_results.append(f"Deleted {deleted_logs} old sync logs")
        
        # Clean old audit logs
        with db.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_logs 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """, (days_old,))
            deleted_audits = cursor.rowcount
            db.connection.commit()
            cleanup_results.append(f"Deleted {deleted_audits} old audit logs")
        
        return {
            "success": True,
            "days_cleaned": days_old,
            "cleanup_results": cleanup_results,
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}") 