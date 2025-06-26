-- =============================================================================
-- SIMPLIFIED API FUNCTIONS - Just Query Views
-- Replace complex Python logic with simple SQL functions
-- =============================================================================

-- 1. GET ORGANIZATION STATUS
-- Powers: /api/v1/cliniko/status/{org_id}
CREATE OR REPLACE FUNCTION get_org_status(
    p_org_id TEXT,
    p_include_logs BOOLEAN DEFAULT FALSE,
    p_include_health_check BOOLEAN DEFAULT FALSE,
    p_logs_limit INTEGER DEFAULT 5
) RETURNS JSON AS $$
DECLARE
    result JSON;
    status_data JSON;
    logs_data JSON := NULL;
    health_data JSON := NULL;
BEGIN
    -- Get basic status
    SELECT row_to_json(t) INTO status_data
    FROM (
        SELECT 
            organization_id,
            total_patients,
            active_patients, 
            synced_patients,
            sync_percentage,
            last_sync_time,
            status,
            timestamp
        FROM org_status_summary 
        WHERE organization_id = p_org_id
    ) t;
    
    -- Add logs if requested
    IF p_include_logs THEN
        SELECT json_build_object(
            'sync_logs', 
            (SELECT json_agg(log_entry) 
             FROM (
                 SELECT * FROM jsonb_array_elements(recent_syncs::jsonb) AS log_entry
                 LIMIT p_logs_limit
             ) limited_logs),
            'sync_logs_count', total_syncs
        ) INTO logs_data
        FROM sync_logs_summary 
        WHERE organization_id = p_org_id;
    END IF;
    
    -- Add health check if requested  
    IF p_include_health_check THEN
        SELECT row_to_json(t) INTO health_data
        FROM (
            SELECT 
                has_credentials,
                credentials_active,
                sync_enabled,
                has_patients,
                has_synced_data,
                last_patient_sync,
                last_sync_attempt,
                checked_at
            FROM org_health_check 
            WHERE organization_id = p_org_id
        ) t;
    END IF;
    
    -- Combine results
    result := json_build_object(
        'organization_id', p_org_id,
        'total_patients', (status_data->>'total_patients')::INTEGER,
        'active_patients', (status_data->>'active_patients')::INTEGER,
        'synced_patients', (status_data->>'synced_patients')::INTEGER,
        'sync_percentage', (status_data->>'sync_percentage')::NUMERIC,
        'last_sync_time', status_data->>'last_sync_time',
        'status', status_data->>'status',
        'timestamp', status_data->>'timestamp',
        'sync_logs', CASE WHEN logs_data IS NOT NULL THEN logs_data->'sync_logs' ELSE NULL END,
        'sync_logs_count', CASE WHEN logs_data IS NOT NULL THEN logs_data->>'sync_logs_count' ELSE NULL END,
        'health_check', health_data
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 2. GET PATIENT STATS
-- Powers: /api/v1/cliniko/patients/{org_id}/stats
CREATE OR REPLACE FUNCTION get_patient_stats(
    p_org_id TEXT,
    p_include_details BOOLEAN DEFAULT FALSE,
    p_with_appointments_only BOOLEAN DEFAULT FALSE,
    p_limit INTEGER DEFAULT 10
) RETURNS JSON AS $$
DECLARE
    result JSON;
    stats_data JSON;
    details_data JSON := NULL;
BEGIN
    -- Get basic stats
    SELECT row_to_json(t) INTO stats_data
    FROM (
        SELECT 
            total_active_patients,
            avg_recent_appointments,
            avg_upcoming_appointments,
            avg_total_appointments,
            active_count,
            recently_active_count,
            upcoming_only_count,
            inactive_count,
            patients_with_upcoming,
            patients_with_recent,
            patients_with_any_appointments,
            timestamp
        FROM patient_stats_summary 
        WHERE organization_id = p_org_id
    ) t;
    
    -- Add patient details if requested
    IF p_include_details THEN
        SELECT json_agg(patient_detail) INTO details_data
        FROM (
            SELECT 
                id,
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
                appointment_status,
                hours_until_next_appointment
            FROM patient_details_list 
            WHERE organization_id = p_org_id
            AND (
                CASE 
                    WHEN p_with_appointments_only THEN total_appointment_count > 0
                    ELSE TRUE
                END
            )
            LIMIT p_limit
        ) patient_detail;
    END IF;
    
    -- Combine results
    result := json_build_object(
        'total_active_patients', (stats_data->>'total_active_patients')::INTEGER,
        'avg_recent_appointments', (stats_data->>'avg_recent_appointments')::NUMERIC,
        'avg_upcoming_appointments', (stats_data->>'avg_upcoming_appointments')::NUMERIC,
        'avg_total_appointments', (stats_data->>'avg_total_appointments')::NUMERIC,
        'organization_id', p_org_id,
        'filters', json_build_object(
            'with_appointments_only', p_with_appointments_only,
            'include_details', p_include_details
        ),
        'timestamp', stats_data->>'timestamp',
        'patient_details', details_data,
        'patient_details_count', CASE WHEN details_data IS NOT NULL THEN json_array_length(details_data) ELSE NULL END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 3. GET COMPLETE DASHBOARD
-- Powers: Single query for complete dashboard
CREATE OR REPLACE FUNCTION get_org_dashboard(p_org_id TEXT) RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT row_to_json(t) INTO result
    FROM (
        SELECT 
            organization_id,
            total_patients,
            active_patients,
            synced_patients,
            sync_percentage,
            last_sync_time,
            status,
            avg_recent_appointments,
            avg_upcoming_appointments,
            avg_total_appointments,
            active_count,
            recently_active_count,
            upcoming_only_count,
            inactive_count,
            patients_with_upcoming,
            patients_with_recent,
            has_credentials,
            credentials_active,
            sync_enabled,
            has_patients,
            has_synced_data,
            last_patient_sync,
            last_sync_attempt,
            total_syncs,
            successful_syncs,
            failed_syncs,
            last_sync_started,
            total_records_processed,
            generated_at
        FROM org_dashboard_complete 
        WHERE organization_id = p_org_id
    ) t;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 4. GET SYNC LOGS
-- Powers: Sync history endpoints
CREATE OR REPLACE FUNCTION get_sync_logs(
    p_org_id TEXT,
    p_limit INTEGER DEFAULT 10
) RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'organization_id', p_org_id,
        'total_syncs', total_syncs,
        'successful_syncs', successful_syncs, 
        'failed_syncs', failed_syncs,
        'last_sync_started', last_sync_started,
        'last_sync_completed', last_sync_completed,
        'total_records_processed', total_records_processed,
        'total_records_success', total_records_success,
        'total_records_failed', total_records_failed,
        'recent_syncs', (
            SELECT json_agg(log_entry)
            FROM (
                SELECT * FROM jsonb_array_elements(recent_syncs::jsonb) AS log_entry
                LIMIT p_limit  
            ) limited_logs
        )
    ) INTO result
    FROM sync_logs_summary
    WHERE organization_id = p_org_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SIMPLE WRAPPER VIEWS FOR DIRECT API ACCESS
-- =============================================================================

-- For APIs that just need simple SELECT statements
CREATE OR REPLACE VIEW api_org_status AS
SELECT 
    organization_id,
    get_org_status(organization_id, false, false) as status_data
FROM org_status_summary;

CREATE OR REPLACE VIEW api_patient_stats AS  
SELECT 
    organization_id,
    get_patient_stats(organization_id, false, false) as stats_data
FROM patient_stats_summary;

-- =============================================================================
-- USAGE EXAMPLES
-- =============================================================================

/*
-- Basic status (replaces complex Python logic):
SELECT get_org_status('org_2xwHiNrj68eaRUlX10anlXGvzX7');

-- Status with logs:
SELECT get_org_status('org_2xwHiNrj68eaRUlX10anlXGvzX7', true, false, 3);

-- Status with health check:
SELECT get_org_status('org_2xwHiNrj68eaRUlX10anlXGvzX7', false, true);

-- Status with everything:
SELECT get_org_status('org_2xwHiNrj68eaRUlX10anlXGvzX7', true, true, 5);

-- Patient stats basic:
SELECT get_patient_stats('org_2xwHiNrj68eaRUlX10anlXGvzX7');

-- Patient stats with details:
SELECT get_patient_stats('org_2xwHiNrj68eaRUlX10anlXGvzX7', true, false, 5);

-- Patient stats with appointments only:
SELECT get_patient_stats('org_2xwHiNrj68eaRUlX10anlXGvzX7', true, true, 3);

-- Complete dashboard:
SELECT get_org_dashboard('org_2xwHiNrj68eaRUlX10anlXGvzX7');

-- Sync logs:
SELECT get_sync_logs('org_2xwHiNrj68eaRUlX10anlXGvzX7', 5);
*/

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON FUNCTION get_org_status(TEXT, BOOLEAN, BOOLEAN, INTEGER) IS 'Returns organization status with optional logs and health check';
COMMENT ON FUNCTION get_patient_stats(TEXT, BOOLEAN, BOOLEAN, INTEGER) IS 'Returns patient statistics with optional details filtering';
COMMENT ON FUNCTION get_org_dashboard(TEXT) IS 'Returns complete dashboard data in single query';
COMMENT ON FUNCTION get_sync_logs(TEXT, INTEGER) IS 'Returns sync logs and statistics for organization'; 