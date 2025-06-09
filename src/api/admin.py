"""
Admin API endpoints for database migrations and management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import json
from datetime import datetime

from src.database import db

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)

@router.post("/migrate/organization-services")
async def migrate_organization_services() -> Dict[str, Any]:
    """
    Create organization_services table and configure Surf Rehab with Cliniko
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
        
        # Step 3: Insert Surf Rehab configuration
        logger.info("Configuring Surf Rehab with Cliniko...")
        
        insert_sql = """
        INSERT INTO public.organization_services (
          organization_id,
          service_name,
          service_config,
          is_primary,
          is_active,
          sync_enabled
        ) VALUES (
          %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (organization_id, service_name) 
        DO UPDATE SET
          service_config = EXCLUDED.service_config,
          is_primary = EXCLUDED.is_primary,
          is_active = EXCLUDED.is_active,
          sync_enabled = EXCLUDED.sync_enabled
        RETURNING id;
        """
        
        surf_rehab_config = {
            "region": "au4",
            "api_url": "https://api.au4.cliniko.com/v1",
            "features": ["patients", "appointments", "invoices"],
            "sync_schedule": "*/30 * * * *",
            "description": "Primary practice management system for patient bookings and medical records"
        }
        
        with db.get_cursor() as cursor:
            cursor.execute(insert_sql, (
                'org_2xwHiNrj68eaRUlX10anlXGvzX7',  # Surf Rehab org ID
                'cliniko',
                json.dumps(surf_rehab_config),
                True,   # is_primary
                True,   # is_active  
                True    # sync_enabled
            ))
            result = cursor.fetchone()
            db.connection.commit()
            migration_results.append(f"✅ Surf Rehab configured with Cliniko (ID: {result['id']})")
        
        # Step 4: Verify the configuration
        logger.info("Verifying configuration...")
        
        verify_sql = """
        SELECT 
          os.organization_id,
          o.name as organization_name,
          os.service_name,
          os.is_primary,
          os.is_active,
          os.sync_enabled,
          os.service_config,
          os.created_at
        FROM organization_services os
        JOIN organizations o ON o.id = os.organization_id
        WHERE os.organization_id = %s AND os.service_name = %s;
        """
        
        verification = db.execute_query(verify_sql, (
            'org_2xwHiNrj68eaRUlX10anlXGvzX7',
            'cliniko'
        ))
        
        return {
            "success": True,
            "migration_completed_at": datetime.now().isoformat(),
            "results": migration_results,
            "surf_rehab_config": verification[0] if verification else None,
            "message": "Organization services table created and Surf Rehab configured with Cliniko"
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/organization-services/{organization_id}")
async def get_organization_services(organization_id: str) -> Dict[str, Any]:
    """
    Get all services configured for an organization
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
            "primary_service": next((s for s in services if s['is_primary']), None)
        }
        
    except Exception as e:
        logger.error(f"Failed to get organization services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-sync/{organization_id}")
async def test_cliniko_sync(organization_id: str) -> Dict[str, Any]:
    """
    Test Cliniko sync for a specific organization - step by step validation
    """
    try:
        from src.services.cliniko_sync_service import cliniko_sync_service
        
        # Run the actual sync
        result = cliniko_sync_service.sync_organization_active_patients(organization_id)
        
        return {
            "test_type": "cliniko_sync_test",
            "organization_id": organization_id,
            "sync_result": result,
            "test_completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Test sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test sync failed: {str(e)}")

@router.get("/sync-logs/{organization_id}")
async def get_sync_logs(organization_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get recent sync logs for an organization
    """
    try:
        query = """
        SELECT *
        FROM sync_logs
        WHERE organization_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """
        
        logs = db.execute_query(query, (organization_id, limit))
        
        return {
            "organization_id": organization_id,
            "logs": logs,
            "total_logs": len(logs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 