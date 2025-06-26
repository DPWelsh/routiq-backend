-- =============================================================================
-- CONSOLIDATED API VIEWS - Optimized for Current Working APIs
-- Based on new 'patients' table structure
-- =============================================================================

-- 1. ORGANIZATION STATUS VIEW
-- Powers: /api/v1/cliniko/status/{org_id}
CREATE OR REPLACE VIEW org_status_summary AS
SELECT 
    organization_id,
    COUNT(*) as total_patients,
    COUNT(*) FILTER (WHERE is_active = true) as active_patients,
    COUNT(*) as synced_patients,  -- All patients in table are synced
    CASE 
        WHEN COUNT(*) > 0 THEN 100.0
        ELSE 0.0 
    END as sync_percentage,
    MAX(last_synced_at) as last_sync_time,
    'connected' as status,
    NOW() as timestamp
FROM patients
GROUP BY organization_id;

-- 2. PATIENT STATS VIEW  
-- Powers: /api/v1/cliniko/patients/{org_id}/stats
CREATE OR REPLACE VIEW patient_stats_summary AS
SELECT 
    organization_id,
    COUNT(*) FILTER (WHERE is_active = true) as total_active_patients,
    ROUND(AVG(recent_appointment_count), 1) as avg_recent_appointments,
    ROUND(AVG(upcoming_appointment_count), 1) as avg_upcoming_appointments, 
    ROUND(AVG(total_appointment_count), 1) as avg_total_appointments,
    
    -- Activity breakdown
    COUNT(*) FILTER (WHERE activity_status = 'active') as active_count,
    COUNT(*) FILTER (WHERE activity_status = 'recently_active') as recently_active_count,
    COUNT(*) FILTER (WHERE activity_status = 'upcoming_only') as upcoming_only_count,
    COUNT(*) FILTER (WHERE activity_status = 'inactive') as inactive_count,
    
    -- Appointment insights
    COUNT(*) FILTER (WHERE upcoming_appointment_count > 0) as patients_with_upcoming,
    COUNT(*) FILTER (WHERE recent_appointment_count > 0) as patients_with_recent,
    COUNT(*) FILTER (WHERE total_appointment_count > 0) as patients_with_any_appointments,
    
    NOW() as timestamp
FROM patients
GROUP BY organization_id;

-- 3. PATIENT DETAILS VIEW
-- Powers: /api/v1/cliniko/patients/{org_id}/stats?include_details=true
CREATE OR REPLACE VIEW patient_details_list AS
SELECT 
    id,
    organization_id,
    name,
    phone,
    email,
    cliniko_patient_id,
    is_active,
    activity_status,
    recent_appointment_count,
    upcoming_appointment_count,
    total_appointment_count,
    last_appointment_date,
    next_appointment_time,
    next_appointment_type,
    primary_appointment_type,
    treatment_notes,
    recent_appointments,
    upcoming_appointments,
    
    -- Calculated fields for API
    CASE 
        WHEN next_appointment_time IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (next_appointment_time - NOW()))/3600
        ELSE NULL
    END as hours_until_next_appointment,
    
    CASE 
        WHEN upcoming_appointment_count > 0 THEN 'scheduled'
        WHEN recent_appointment_count > 0 THEN 'recent'  
        ELSE 'inactive'
    END as appointment_status,
    
    last_synced_at,
    created_at,
    updated_at
    
FROM patients
ORDER BY is_active DESC, last_appointment_date DESC NULLS LAST;

-- 4. SYNC LOGS SUMMARY VIEW
-- Powers: status endpoints with ?include_logs=true
CREATE OR REPLACE VIEW sync_logs_summary AS
SELECT 
    organization_id,
    COUNT(*) as total_syncs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_syncs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_syncs,
    MAX(started_at) as last_sync_started,
    MAX(completed_at) as last_sync_completed,
    SUM(records_processed) as total_records_processed,
    SUM(records_success) as total_records_success,
    SUM(records_failed) as total_records_failed,
    
    -- Recent sync details (JSON for API)
    json_agg(
        json_build_object(
            'id', id,
            'source_system', source_system,
            'operation_type', operation_type,
            'status', status,
            'records_processed', records_processed,
            'records_success', records_success,
            'records_failed', records_failed,
            'started_at', started_at,
            'completed_at', completed_at
        ) ORDER BY started_at DESC
    ) FILTER (WHERE started_at > NOW() - INTERVAL '7 days') as recent_syncs
    
FROM sync_logs
GROUP BY organization_id;

-- 5. HEALTH CHECK VIEW
-- Powers: status endpoints with ?include_health_check=true  
CREATE OR REPLACE VIEW org_health_check AS
SELECT 
    o.id as organization_id,
    o.name as organization_name,
    
    -- Credentials check
    EXISTS(
        SELECT 1 FROM service_credentials sc 
        WHERE sc.organization_id = o.id 
        AND sc.service_name = 'cliniko'
        AND sc.is_active = true
    ) as has_credentials,
    
    EXISTS(
        SELECT 1 FROM service_credentials sc 
        WHERE sc.organization_id = o.id 
        AND sc.service_name = 'cliniko'
        AND sc.is_active = true
        AND sc.last_validated_at > NOW() - INTERVAL '24 hours'
    ) as credentials_active,
    
    -- Sync enabled check
    EXISTS(
        SELECT 1 FROM service_integrations si
        WHERE si.organization_id = o.id
        AND si.service_name = 'cliniko'
        AND si.sync_enabled = true
        AND si.is_active = true
    ) as sync_enabled,
    
    -- Data checks
    EXISTS(SELECT 1 FROM patients p WHERE p.organization_id = o.id) as has_patients,
    EXISTS(
        SELECT 1 FROM patients p 
        WHERE p.organization_id = o.id 
        AND p.last_synced_at > NOW() - INTERVAL '7 days'
    ) as has_synced_data,
    
    -- Recent activity
    (SELECT MAX(last_synced_at) FROM patients WHERE organization_id = o.id) as last_patient_sync,
    (SELECT MAX(started_at) FROM sync_logs WHERE organization_id = o.id) as last_sync_attempt,
    
    NOW() as checked_at
    
FROM organizations o
WHERE o.deleted_at IS NULL;

-- 6. SIMPLIFIED DASHBOARD VIEW
-- Powers: Complete dashboard data in one query
CREATE OR REPLACE VIEW org_dashboard_complete AS
SELECT 
    o.organization_id,
    
    -- Status summary
    o.total_patients,
    o.active_patients, 
    o.synced_patients,
    o.sync_percentage,
    o.last_sync_time,
    o.status,
    
    -- Patient stats  
    s.avg_recent_appointments,
    s.avg_upcoming_appointments,
    s.avg_total_appointments,
    s.active_count,
    s.recently_active_count,
    s.upcoming_only_count,
    s.inactive_count,
    s.patients_with_upcoming,
    s.patients_with_recent,
    
    -- Health check
    h.has_credentials,
    h.credentials_active,
    h.sync_enabled,
    h.has_patients,
    h.has_synced_data,
    h.last_patient_sync,
    h.last_sync_attempt,
    
    -- Sync logs summary
    l.total_syncs,
    l.successful_syncs,
    l.failed_syncs,
    l.last_sync_started,
    l.total_records_processed,
    
    NOW() as generated_at
    
FROM org_status_summary o
LEFT JOIN patient_stats_summary s ON o.organization_id = s.organization_id  
LEFT JOIN org_health_check h ON o.organization_id = h.organization_id
LEFT JOIN sync_logs_summary l ON o.organization_id = l.organization_id;

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Patients table indexes (if not already exist)
CREATE INDEX IF NOT EXISTS idx_patients_org_active ON patients (organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_patients_activity_status ON patients (organization_id, activity_status);
CREATE INDEX IF NOT EXISTS idx_patients_next_appointment ON patients (next_appointment_time) WHERE next_appointment_time IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_patients_last_synced ON patients (organization_id, last_synced_at);

-- Sync logs indexes  
CREATE INDEX IF NOT EXISTS idx_sync_logs_org_recent ON sync_logs (organization_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON sync_logs (organization_id, status, started_at DESC);

-- Service tables indexes
CREATE INDEX IF NOT EXISTS idx_service_credentials_org_active ON service_credentials (organization_id, service_name, is_active);
CREATE INDEX IF NOT EXISTS idx_service_integrations_org_active ON service_integrations (organization_id, service_name, is_active);

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION  
-- =============================================================================

COMMENT ON VIEW org_status_summary IS 'Powers /api/v1/cliniko/status/{org_id} endpoint';
COMMENT ON VIEW patient_stats_summary IS 'Powers /api/v1/cliniko/patients/{org_id}/stats endpoint';
COMMENT ON VIEW patient_details_list IS 'Powers patient details with ?include_details=true';
COMMENT ON VIEW sync_logs_summary IS 'Powers sync history and logs data';
COMMENT ON VIEW org_health_check IS 'Powers health check data for ?include_health_check=true';
COMMENT ON VIEW org_dashboard_complete IS 'Complete dashboard data in single query';

-- =============================================================================
-- DROP OLD VIEWS (Cleanup)
-- =============================================================================

-- Uncomment these after verifying new views work
-- DROP VIEW IF EXISTS patient_overview;
-- DROP VIEW IF EXISTS contact_analytics; 
-- DROP VIEW IF EXISTS organization_dashboard;
-- DROP VIEW IF EXISTS active_patients_view;
-- DROP VIEW IF EXISTS all_patients_view; 