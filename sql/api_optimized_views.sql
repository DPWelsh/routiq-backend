-- API-Optimized Views for Simplified Endpoint Architecture
-- These views directly support your 4 main API endpoints

-- =============================================================================
-- 1. ORGANIZATION STATUS VIEW (for /api/v1/cliniko/status/{org_id})
-- =============================================================================
CREATE OR REPLACE VIEW v_organization_status AS
SELECT 
    p.organization_id,
    
    -- Patient counts
    COUNT(*) as total_patients,
    COUNT(*) FILTER (WHERE p.is_active = true) as active_patients,
    COUNT(*) as synced_patients,  -- All patients in DB are synced
    
    -- Sync percentage
    CASE 
        WHEN COUNT(*) > 0 THEN 100.0
        ELSE 0.0
    END as sync_percentage,
    
    -- Last sync time
    MAX(p.last_synced_at) as last_sync_time,
    
    -- Connection status
    CASE 
        WHEN COUNT(*) > 0 THEN 'connected'
        ELSE 'disconnected'
    END as status,
    
    -- Current timestamp
    NOW() as timestamp

FROM patients p
GROUP BY p.organization_id;

-- =============================================================================
-- 2. PATIENT STATS VIEW (for /api/v1/cliniko/patients/{org_id}/stats)
-- =============================================================================
CREATE OR REPLACE VIEW v_patient_stats AS
SELECT 
    p.organization_id,
    
    -- Basic counts
    COUNT(*) FILTER (WHERE p.is_active = true) as total_active_patients,
    
    -- Appointment averages
    COALESCE(AVG(p.recent_appointment_count) FILTER (WHERE p.is_active = true), 0.0) as avg_recent_appointments,
    COALESCE(AVG(p.upcoming_appointment_count) FILTER (WHERE p.is_active = true), 0.0) as avg_upcoming_appointments,
    COALESCE(AVG(p.total_appointment_count) FILTER (WHERE p.is_active = true), 0.0) as avg_total_appointments,
    
    -- Timestamp
    NOW() as timestamp

FROM patients p
GROUP BY p.organization_id;

-- =============================================================================
-- 3. PATIENT DETAILS VIEW (for stats with include_details=true)
-- =============================================================================
CREATE OR REPLACE VIEW v_patient_details AS
SELECT 
    p.id,
    p.organization_id,
    p.name,
    p.phone,
    p.email,
    p.cliniko_patient_id,
    p.is_active,
    p.activity_status,
    
    -- Appointment counts
    p.recent_appointment_count,
    p.upcoming_appointment_count, 
    p.total_appointment_count,
    
    -- Appointment dates
    p.first_appointment_date,
    p.last_appointment_date,
    p.next_appointment_time,
    p.next_appointment_type,
    p.primary_appointment_type,
    
    -- Treatment info
    p.treatment_notes,
    
    -- Appointment arrays
    p.recent_appointments,
    p.upcoming_appointments,
    
    -- Metadata
    p.last_synced_at,
    p.created_at,
    p.updated_at

FROM patients p
WHERE p.is_active = true
ORDER BY p.last_appointment_date DESC NULLS LAST;

-- =============================================================================
-- 4. SYNC LOGS VIEW (for status with include_logs=true)
-- =============================================================================
CREATE OR REPLACE VIEW v_recent_sync_logs AS
SELECT 
    sl.id,
    sl.organization_id,
    sl.source_system,
    sl.operation_type,
    sl.status,
    sl.records_processed,
    sl.records_success,
    sl.records_failed,
    sl.error_details,
    sl.started_at,
    sl.completed_at,
    sl.metadata,
    
    -- Duration calculation
    CASE 
        WHEN sl.completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (sl.completed_at - sl.started_at))
        ELSE NULL
    END as duration_seconds,
    
    -- Success rate
    CASE 
        WHEN sl.records_processed > 0 THEN 
            ROUND((sl.records_success::numeric / sl.records_processed) * 100, 2)
        ELSE NULL
    END as success_rate_percent

FROM sync_logs sl
ORDER BY sl.started_at DESC;

-- =============================================================================
-- 5. HEALTH CHECK VIEW (for status with include_health_check=true)
-- =============================================================================
CREATE OR REPLACE VIEW v_organization_health AS
SELECT 
    o.id as organization_id,
    
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
    
    -- Sync status
    EXISTS(
        SELECT 1 FROM service_integrations si 
        WHERE si.organization_id = o.id 
        AND si.service_name = 'cliniko' 
        AND si.sync_enabled = true
    ) as sync_enabled,
    
    -- Data status
    EXISTS(
        SELECT 1 FROM patients p 
        WHERE p.organization_id = o.id
    ) as has_patients,
    
    EXISTS(
        SELECT 1 FROM patients p 
        WHERE p.organization_id = o.id 
        AND p.last_synced_at > NOW() - INTERVAL '7 days'
    ) as has_synced_data,
    
    -- Last activity
    (
        SELECT MAX(p.last_synced_at) 
        FROM patients p 
        WHERE p.organization_id = o.id
    ) as last_sync_at,
    
    (
        SELECT COUNT(*) 
        FROM patients p 
        WHERE p.organization_id = o.id
    ) as total_patients,
    
    -- Overall health score (0-100)
    (
        CASE WHEN EXISTS(SELECT 1 FROM service_credentials sc WHERE sc.organization_id = o.id AND sc.service_name = 'cliniko' AND sc.is_active = true) THEN 25 ELSE 0 END +
        CASE WHEN EXISTS(SELECT 1 FROM service_credentials sc WHERE sc.organization_id = o.id AND sc.service_name = 'cliniko' AND sc.is_active = true AND sc.last_validated_at > NOW() - INTERVAL '24 hours') THEN 25 ELSE 0 END +
        CASE WHEN EXISTS(SELECT 1 FROM service_integrations si WHERE si.organization_id = o.id AND si.service_name = 'cliniko' AND si.sync_enabled = true) THEN 25 ELSE 0 END +
        CASE WHEN EXISTS(SELECT 1 FROM patients p WHERE p.organization_id = o.id AND p.last_synced_at > NOW() - INTERVAL '7 days') THEN 25 ELSE 0 END
    ) as health_score

FROM organizations o;

-- =============================================================================
-- 6. COMBINED STATUS VIEW (for full status with logs + health)
-- =============================================================================
CREATE OR REPLACE VIEW v_organization_full_status AS
SELECT 
    os.*,
    oh.has_credentials,
    oh.credentials_active,
    oh.sync_enabled,
    oh.has_patients,
    oh.has_synced_data,
    oh.health_score

FROM v_organization_status os
LEFT JOIN v_organization_health oh ON os.organization_id = oh.organization_id;

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Ensure these indexes exist for view performance
CREATE INDEX IF NOT EXISTS idx_patients_org_active ON patients (organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_patients_org_last_sync ON patients (organization_id, last_synced_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_logs_org_started ON sync_logs (organization_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_service_credentials_org_service ON service_credentials (organization_id, service_name, is_active);
CREATE INDEX IF NOT EXISTS idx_service_integrations_org_service ON service_integrations (organization_id, service_name, sync_enabled);

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON VIEW v_organization_status IS 'Organization status summary for /api/v1/cliniko/status endpoint';
COMMENT ON VIEW v_patient_stats IS 'Patient statistics for /api/v1/cliniko/patients/stats endpoint';
COMMENT ON VIEW v_patient_details IS 'Detailed patient data for stats with include_details=true';
COMMENT ON VIEW v_recent_sync_logs IS 'Recent sync logs for status with include_logs=true';
COMMENT ON VIEW v_organization_health IS 'Health check data for status with include_health_check=true';
COMMENT ON VIEW v_organization_full_status IS 'Combined status and health data for full status endpoint'; 