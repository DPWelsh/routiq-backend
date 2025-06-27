-- =============================================================================
-- DASHBOARD VIEW - All data needed for the sync dashboard
-- =============================================================================

CREATE OR REPLACE VIEW dashboard_summary AS
SELECT 
    p.organization_id,
    
    -- Patient Counts
    COUNT(*) as total_patients,
    COUNT(*) FILTER (WHERE p.is_active = true) as active_patients,
    COUNT(*) FILTER (WHERE p.upcoming_appointment_count > 0) as patients_with_upcoming,
    COUNT(*) FILTER (WHERE p.recent_appointment_count > 0) as patients_with_recent,
    
    -- Appointment Counts
    SUM(p.upcoming_appointment_count) as total_upcoming_appointments,
    SUM(p.recent_appointment_count) as total_recent_appointments,
    SUM(p.total_appointment_count) as total_all_appointments,
    
    -- Averages
    ROUND(AVG(p.upcoming_appointment_count), 2) as avg_upcoming_per_patient,
    ROUND(AVG(p.recent_appointment_count), 2) as avg_recent_per_patient,
    ROUND(AVG(p.total_appointment_count), 2) as avg_total_per_patient,
    
    -- Sync Status
    MAX(p.last_synced_at) as last_sync_time,
    COUNT(*) FILTER (WHERE p.last_synced_at IS NOT NULL) as synced_patients,
    ROUND(
        (COUNT(*) FILTER (WHERE p.last_synced_at IS NOT NULL)::numeric / COUNT(*)::numeric) * 100, 
        1
    ) as sync_percentage,
    
    -- Integration Status
    CASE 
        WHEN COUNT(*) > 0 AND MAX(p.last_synced_at) IS NOT NULL THEN 'Connected'
        WHEN COUNT(*) > 0 THEN 'Partial'
        ELSE 'Not Connected'
    END as integration_status,
    
    -- Activity Status
    CASE 
        WHEN COUNT(*) FILTER (WHERE p.is_active = true) > 0 THEN 'Active'
        ELSE 'Inactive'
    END as activity_status,
    
    -- Timestamp
    NOW() as generated_at
    
FROM patients p
WHERE p.organization_id IS NOT NULL
GROUP BY p.organization_id;

-- =============================================================================
-- RECENT ACTIVITY VIEW - For the Live Activity Log section
-- =============================================================================

CREATE OR REPLACE VIEW recent_sync_activity AS
SELECT 
    sl.id,
    sl.organization_id,
    sl.source_system,
    sl.operation_type,
    sl.status,
    sl.records_processed,
    sl.records_success,
    sl.records_failed,
    sl.started_at,
    sl.completed_at,
    sl.error_details,
    CASE 
        WHEN sl.status = 'completed' AND sl.records_failed = 0 THEN 'success'
        WHEN sl.status = 'completed' AND sl.records_failed > 0 THEN 'partial'
        WHEN sl.status = 'failed' THEN 'error'
        WHEN sl.status = 'running' THEN 'running'
        ELSE 'unknown'
    END as activity_type,
    
    -- Human readable description
    CASE 
        WHEN sl.source_system = 'cliniko' AND sl.operation_type = 'sync' THEN 
            'Cliniko patient sync: ' || COALESCE(sl.records_success::text, '0') || ' patients synced'
        WHEN sl.source_system = 'cliniko' AND sl.operation_type = 'comprehensive_sync' THEN 
            'Comprehensive sync: ' || COALESCE(sl.records_success::text, '0') || ' patients + appointments'
        ELSE 
            sl.source_system || ' ' || sl.operation_type
    END as description,
    
    -- Time ago calculation
    CASE 
        WHEN sl.completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (NOW() - sl.completed_at)) / 60
        ELSE 
            EXTRACT(EPOCH FROM (NOW() - sl.started_at)) / 60
    END as minutes_ago
    
FROM sync_logs sl
WHERE sl.organization_id IS NOT NULL
ORDER BY COALESCE(sl.completed_at, sl.started_at) DESC
LIMIT 50;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Test the dashboard view
-- SELECT * FROM dashboard_summary WHERE organization_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7';

-- Test the activity view  
-- SELECT * FROM recent_sync_activity WHERE organization_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7' LIMIT 10; 