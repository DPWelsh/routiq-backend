"""
Admin API endpoints for database migrations and management
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

@router.post("/import-cliniko-patients/{organization_id}")
async def import_cliniko_patients(organization_id: str) -> Dict[str, Any]:
    """
    Import all Cliniko patients into the contacts table for unified contact management
    """
    try:
        from src.services.cliniko_patient_import_service import ClinikoPatientImportService
        
        # Initialize the import service
        import_service = ClinikoPatientImportService(organization_id)
        
        # Run the import
        result = await import_service.import_all_patients()
        
        return {
            "operation": "cliniko_patient_import",
            "organization_id": organization_id,
            "import_result": result,
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Patient import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Patient import failed: {str(e)}")

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

@router.get("/debug-contacts/{organization_id}")
async def debug_contacts(organization_id: str) -> Dict[str, Any]:
    """
    Debug contacts for an organization to understand sync issues
    """
    try:
        # Check total contacts for organization
        total_query = """
        SELECT COUNT(*) as total_contacts
        FROM contacts 
        WHERE organization_id = %s;
        """
        
        total_result = db.execute_query(total_query, (organization_id,))
        total_contacts = total_result[0]['total_contacts'] if total_result else 0
        
        # Get sample contacts
        sample_query = """
        SELECT id, name, email, cliniko_patient_id, created_at
        FROM contacts 
        WHERE organization_id = %s
        ORDER BY created_at DESC
        LIMIT 5;
        """
        
        sample_contacts = db.execute_query(sample_query, (organization_id,))
        
        # Check contacts with cliniko_patient_id
        cliniko_query = """
        SELECT COUNT(*) as cliniko_linked_contacts
        FROM contacts 
        WHERE organization_id = %s AND cliniko_patient_id IS NOT NULL;
        """
        
        cliniko_result = db.execute_query(cliniko_query, (organization_id,))
        cliniko_linked = cliniko_result[0]['cliniko_linked_contacts'] if cliniko_result else 0
        
        return {
            "organization_id": organization_id,
            "total_contacts": total_contacts,
            "cliniko_linked_contacts": cliniko_linked,
            "sample_contacts": sample_contacts,
            "debug_info": {
                "has_contacts": total_contacts > 0,
                "has_cliniko_links": cliniko_linked > 0,
                "contact_structure": "id, name, email, cliniko_patient_id"
            }
        }
        
    except Exception as e:
        logger.error(f"Debug contacts failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug-cliniko-patient-raw/{organization_id}")
async def debug_cliniko_patient_raw(organization_id: str) -> Dict[str, Any]:
    """
    Get raw Cliniko patient data to see all available fields including phone numbers
    """
    try:
        from src.services.cliniko_sync_service import cliniko_sync_service
        
        # Get credentials and set up API
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        if not credentials:
            return {"error": "No credentials found"}
            
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = cliniko_sync_service._create_auth_headers(credentials["api_key"])
        
        # Get first patient with full raw data
        url = f"{api_url}/patients"
        params = {'page': 1, 'per_page': 1}
        
        data = cliniko_sync_service._make_cliniko_request(url, headers, params)
        
        if not data or not data.get('patients'):
            return {"error": "No patients found"}
        
        raw_patient = data['patients'][0]
        
        return {
            "organization_id": organization_id,
            "raw_cliniko_patient": raw_patient,
            "available_fields": list(raw_patient.keys()),
            "phone_fields_check": {
                "phone_mobile": raw_patient.get('phone_mobile'),
                "phone_home": raw_patient.get('phone_home'),
                "phone": raw_patient.get('phone'),
                "mobile": raw_patient.get('mobile'),
                "home_phone": raw_patient.get('home_phone'),
                "mobile_phone": raw_patient.get('mobile_phone')
            }
        }
        
    except Exception as e:
        logger.error(f"Raw patient debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug-contacts-full/{organization_id}")
async def debug_contacts_full(organization_id: str, limit: int = 3) -> Dict[str, Any]:
    """
    Debug full contact records including phone numbers and external_ids
    """
    try:
        # Get full contact records
        query = """
        SELECT id, name, email, phone, cliniko_patient_id, 
               external_ids, primary_source, source_systems, 
               metadata, created_at
        FROM contacts 
        WHERE organization_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """
        
        contacts = db.execute_query(query, (organization_id, limit))
        
        # Check phone number statistics
        phone_stats_query = """
        SELECT 
            COUNT(*) as total_contacts,
            COUNT(phone) as contacts_with_phone,
            COUNT(CASE WHEN phone IS NULL THEN 1 END) as contacts_without_phone
        FROM contacts 
        WHERE organization_id = %s;
        """
        
        phone_stats = db.execute_query(phone_stats_query, (organization_id,))
        
        return {
            "organization_id": organization_id,
            "phone_statistics": phone_stats[0] if phone_stats else {},
            "sample_full_contacts": contacts,
            "analysis": {
                "total_sampled": len(contacts),
                "phone_extraction_issue": "Check if phone numbers exist in external_ids vs phone field"
            }
        }
        
    except Exception as e:
        logger.error(f"Full debug contacts failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug-sync-detailed/{organization_id}")
async def debug_sync_detailed(organization_id: str) -> Dict[str, Any]:
    """
    Detailed sync debug - show matching attempts
    """
    try:
        from src.services.cliniko_sync_service import cliniko_sync_service
        
        # Get credentials and set up API
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(organization_id)
        if not credentials:
            return {"error": "No credentials found"}
            
        api_url = credentials.get("api_url", "https://api.au4.cliniko.com/v1")
        headers = cliniko_sync_service._create_auth_headers(credentials["api_key"])
        
        # Get first 5 patients and 5 appointments for testing
        print("Getting sample patients...")
        all_patients = cliniko_sync_service.get_cliniko_patients(api_url, headers)
        patients = all_patients[:5] if len(all_patients) > 5 else all_patients
        
        print("Getting sample appointments...")
        appointments = cliniko_sync_service.get_cliniko_appointments(
            api_url, 
            headers, 
            cliniko_sync_service.forty_five_days_ago, 
            cliniko_sync_service.current_date
        )
        sample_appointments = appointments[:5] if len(appointments) > 5 else appointments
        
        # Test contact matching for each patient
        matching_results = []
        for patient in patients:
            contact_id = cliniko_sync_service._find_contact_id(patient, organization_id)
            
            matching_results.append({
                "cliniko_patient": {
                    "id": patient.get('id'),
                    "name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                    "email": patient.get('email')
                },
                "contact_found": contact_id is not None,
                "contact_id": contact_id
            })
        
        return {
            "organization_id": organization_id,
            "debug_results": {
                "total_patients_available": len(all_patients),
                "total_appointments_45_days": len(appointments),
                "sample_patients_tested": len(patients),
                "sample_appointments": len(sample_appointments),
                "matching_attempts": matching_results
            },
            "sample_cliniko_data": {
                "patients": [
                    {
                        "id": p.get('id'),
                        "name": f"{p.get('first_name', '')} {p.get('last_name', '')}",
                        "email": p.get('email'),
                        "created_at": p.get('created_at')
                    } for p in patients
                ],
                "appointments": [
                    {
                        "id": a.get('id'),
                        "date": a.get('starts_at'),
                        "patient_id": a.get('patient', {}).get('id') if isinstance(a.get('patient'), dict) else a.get('patient')
                    } for a in sample_appointments
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-patients/{organization_id}")
async def get_active_patients(organization_id: str):
    """
    Get active patients for an organization
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                ap.*,
                c.name as contact_name,
                c.phone as contact_phone
            FROM active_patients ap
            JOIN contacts c ON ap.contact_id = c.id
            WHERE ap.organization_id = %s
            ORDER BY ap.last_appointment_date DESC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "id": row['id'],
                    "contact_id": str(row['contact_id']),
                    "contact_name": row['contact_name'],
                    "contact_phone": row['contact_phone'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "total_appointment_count": row['total_appointment_count'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "recent_appointments": row['recent_appointments'],
                    "upcoming_appointments": row['upcoming_appointments'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "organization_id": organization_id,
                "active_patients": patients,
                "total_count": len(patients),
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to get active patients for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active patients: {str(e)}")

@router.get("/active-patients/{organization_id}/summary")
async def get_active_patients_summary(organization_id: str):
    """
    Get active patients summary for an organization
    """
    try:
        with db.get_cursor() as cursor:
            summary_query = """
            SELECT 
                COUNT(*) as total_active_patients,
                COUNT(CASE WHEN recent_appointment_count > 0 THEN 1 END) as patients_with_recent,
                COUNT(CASE WHEN upcoming_appointment_count > 0 THEN 1 END) as patients_with_upcoming,
                MAX(updated_at) as last_sync_date,
                AVG(recent_appointment_count) as avg_recent_appointments,
                AVG(total_appointment_count) as avg_total_appointments
            FROM active_patients 
            WHERE organization_id = %s
            """
            
            cursor.execute(summary_query, [organization_id])
            row = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "total_active_patients": row['total_active_patients'] if row else 0,
                "patients_with_recent_appointments": row['patients_with_recent'] if row else 0,
                "patients_with_upcoming_appointments": row['patients_with_upcoming'] if row else 0,
                "last_sync_date": row['last_sync_date'].isoformat() if row and row['last_sync_date'] else None,
                "avg_recent_appointments": float(row['avg_recent_appointments']) if row and row['avg_recent_appointments'] else 0.0,
                "avg_total_appointments": float(row['avg_total_appointments']) if row and row['avg_total_appointments'] else 0.0,
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to get active patients summary for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

@router.get("/contacts/{organization_id}/with-appointments")
async def get_contacts_with_appointments(organization_id: str):
    """
    Get contacts that have appointments (active patients with contact details)
    """
    try:
        with db.get_cursor() as cursor:
            query = """
            SELECT 
                c.id,
                c.name,
                c.phone,
                c.email,
                c.cliniko_patient_id,
                ap.recent_appointment_count,
                ap.upcoming_appointment_count,
                ap.last_appointment_date,
                ap.recent_appointments
            FROM contacts c
            JOIN active_patients ap ON c.id = ap.contact_id
            WHERE c.organization_id = %s
            ORDER BY ap.last_appointment_date DESC
            """
            
            cursor.execute(query, [organization_id])
            rows = cursor.fetchall()
            
            contacts = []
            for row in rows:
                contacts.append({
                    "contact_id": str(row['id']),
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row['email'],
                    "cliniko_patient_id": row['cliniko_patient_id'],
                    "recent_appointment_count": row['recent_appointment_count'],
                    "upcoming_appointment_count": row['upcoming_appointment_count'],
                    "last_appointment_date": row['last_appointment_date'].isoformat() if row['last_appointment_date'] else None,
                    "recent_appointments": row['recent_appointments']
                })
            
            return {
                "organization_id": organization_id,
                "contacts_with_appointments": contacts,
                "total_count": len(contacts),
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"Failed to get contacts with appointments for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contacts: {str(e)}")

@router.post("/sync/schedule/{organization_id}")
async def schedule_sync(organization_id: str):
    """
    Schedule or trigger a sync for an organization
    """
    try:
        from src.services.sync_scheduler import scheduler
        
        # Use the scheduler's safe sync method
        success = await scheduler.sync_organization_safe(organization_id)
        
        return {
            "organization_id": organization_id,
            "sync_scheduled": success,
            "message": "Sync started successfully" if success else "Sync already running or failed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule sync for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule sync: {str(e)}")

@router.get("/sync/dashboard/{organization_id}")
async def get_sync_dashboard(organization_id: str):
    """
    Comprehensive sync status dashboard with metrics and recent activity
    """
    try:
        with db.get_cursor() as cursor:
            # Get overall sync metrics
            metrics_query = """
            SELECT 
                COUNT(*) as total_contacts,
                COUNT(CASE WHEN cliniko_patient_id IS NOT NULL THEN 1 END) as cliniko_linked,
                COUNT(*) - COUNT(CASE WHEN cliniko_patient_id IS NOT NULL THEN 1 END) as unlinked
            FROM contacts 
            WHERE organization_id = %s
            """
            cursor.execute(metrics_query, [organization_id])
            contact_metrics = cursor.fetchone()
            
            # Get active patients metrics
            active_query = """
            SELECT 
                COUNT(*) as total_active,
                AVG(recent_appointment_count) as avg_recent,
                AVG(total_appointment_count) as avg_total,
                MAX(last_appointment_date) as most_recent_appointment,
                MAX(updated_at) as last_sync
            FROM active_patients 
            WHERE organization_id = %s
            """
            cursor.execute(active_query, [organization_id])
            active_metrics = cursor.fetchone()
            
            # Get recent sync history (if sync_logs table exists)
            try:
                history_query = """
                SELECT 
                    status, started_at, completed_at, 
                    duration_seconds, patients_processed, 
                    active_patients_found, errors_count
                FROM sync_logs 
                WHERE organization_id = %s 
                ORDER BY started_at DESC 
                LIMIT 10
                """
                cursor.execute(history_query, [organization_id])
                sync_history = cursor.fetchall()
            except:
                # Table doesn't exist yet
                sync_history = []
            
            # Get organization service config
            service_query = """
            SELECT service_config, is_active, sync_enabled, last_sync_at
            FROM organization_services 
            WHERE organization_id = %s AND service_name = 'cliniko'
            """
            cursor.execute(service_query, [organization_id])
            service_config = cursor.fetchone()
            
            return {
                "organization_id": organization_id,
                "dashboard_generated_at": datetime.now().isoformat(),
                "contact_metrics": {
                    "total_contacts": contact_metrics['total_contacts'] if contact_metrics else 0,
                    "cliniko_linked": contact_metrics['cliniko_linked'] if contact_metrics else 0,
                    "unlinked": contact_metrics['unlinked'] if contact_metrics else 0,
                    "link_percentage": (contact_metrics['cliniko_linked'] / contact_metrics['total_contacts'] * 100) if contact_metrics and contact_metrics['total_contacts'] else 0
                },
                "active_patient_metrics": {
                    "total_active": active_metrics['total_active'] if active_metrics else 0,
                    "avg_recent_appointments": float(active_metrics['avg_recent']) if active_metrics and active_metrics['avg_recent'] else 0,
                    "avg_total_appointments": float(active_metrics['avg_total']) if active_metrics and active_metrics['avg_total'] else 0,
                    "most_recent_appointment": active_metrics['most_recent_appointment'].isoformat() if active_metrics and active_metrics['most_recent_appointment'] else None,
                    "last_sync": active_metrics['last_sync'].isoformat() if active_metrics and active_metrics['last_sync'] else None
                },
                "service_status": {
                    "cliniko_configured": service_config is not None,
                    "sync_enabled": service_config['sync_enabled'] if service_config else False,
                    "is_active": service_config['is_active'] if service_config else False,
                    "last_service_sync": service_config['last_sync_at'].isoformat() if service_config and service_config['last_sync_at'] else None
                },
                "sync_history": [
                    {
                        "status": row['status'],
                        "started_at": row['started_at'].isoformat() if row['started_at'] else None,
                        "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None,
                        "duration_seconds": row['duration_seconds'],
                        "patients_processed": row['patients_processed'],
                        "active_patients_found": row['active_patients_found'],
                        "errors_count": row['errors_count']
                    } for row in sync_history
                ],
                "health_indicators": {
                    "has_contacts": (contact_metrics['total_contacts'] if contact_metrics else 0) > 0,
                    "has_active_patients": (active_metrics['total_active'] if active_metrics else 0) > 0,
                    "recent_sync": active_metrics and active_metrics['last_sync'] and (datetime.now() - active_metrics['last_sync']).days < 1 if active_metrics and active_metrics['last_sync'] else False,
                    "high_link_rate": (contact_metrics['cliniko_linked'] / contact_metrics['total_contacts'] * 100) > 90 if contact_metrics and contact_metrics['total_contacts'] else False
                }
            }
                
    except Exception as e:
        logger.error(f"Failed to generate sync dashboard for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

@router.get("/monitoring/system-health")
async def get_system_health():
    """
    System-wide health monitoring for all organizations
    """
    try:
        with db.get_cursor() as cursor:
            # Get system-wide metrics
            system_query = """
            SELECT 
                COUNT(DISTINCT organization_id) as total_organizations,
                COUNT(*) as total_contacts,
                COUNT(CASE WHEN cliniko_patient_id IS NOT NULL THEN 1 END) as total_linked
            FROM contacts
            """
            cursor.execute(system_query)
            system_metrics = cursor.fetchone()
            
            # Get active patients system metrics
            active_system_query = """
            SELECT 
                COUNT(DISTINCT organization_id) as orgs_with_active,
                COUNT(*) as total_active_patients,
                AVG(recent_appointment_count) as avg_recent_appointments
            FROM active_patients
            """
            cursor.execute(active_system_query)
            active_system = cursor.fetchone()
            
            # Get recent sync activity (last 24 hours)
            try:
                recent_activity_query = """
                SELECT 
                    COUNT(*) as syncs_24h,
                    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful_syncs,
                    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_syncs
                FROM sync_logs 
                WHERE started_at > NOW() - INTERVAL '24 hours'
                """
                cursor.execute(recent_activity_query)
                recent_activity = cursor.fetchone()
            except:
                # Table doesn't exist
                recent_activity = {'syncs_24h': 0, 'successful_syncs': 0, 'failed_syncs': 0}
            
            return {
                "system_health_check": datetime.now().isoformat(),
                "overall_metrics": {
                    "total_organizations": system_metrics['total_organizations'] if system_metrics else 0,
                    "total_contacts": system_metrics['total_contacts'] if system_metrics else 0,
                    "total_linked_contacts": system_metrics['total_linked'] if system_metrics else 0,
                    "total_active_patients": active_system['total_active_patients'] if active_system else 0,
                    "organizations_with_active_patients": active_system['orgs_with_active'] if active_system else 0
                },
                "sync_activity_24h": {
                    "total_syncs": recent_activity['syncs_24h'] if recent_activity else 0,
                    "successful_syncs": recent_activity['successful_syncs'] if recent_activity else 0,
                    "failed_syncs": recent_activity['failed_syncs'] if recent_activity else 0,
                    "success_rate": (recent_activity['successful_syncs'] / recent_activity['syncs_24h'] * 100) if recent_activity and recent_activity['syncs_24h'] else 100
                },
                "health_status": {
                    "status": "healthy" if not recent_activity or recent_activity['failed_syncs'] == 0 else "degraded" if recent_activity['failed_syncs'] < recent_activity['successful_syncs'] else "unhealthy",
                    "has_data": (system_metrics['total_contacts'] if system_metrics else 0) > 0,
                    "recent_activity": (recent_activity['syncs_24h'] if recent_activity else 0) > 0,
                    "all_systems_operational": (not recent_activity or recent_activity['failed_syncs'] == 0) and (system_metrics['total_contacts'] if system_metrics else 0) > 0
                }
            }
                
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}") 