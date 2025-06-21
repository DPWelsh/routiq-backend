-- TABLE NAMING CLEANUP PLAN
-- Rename tables to be clearer and more consistent

-- =============================================================================
-- PHASE 1: CORE PATIENT DATA CONSOLIDATION
-- =============================================================================

-- 1. Rename patients_new to patients (our new unified table)
ALTER TABLE patients_new RENAME TO patients;

-- 2. Rename old tables to indicate they're deprecated
ALTER TABLE active_patients RENAME TO active_patients_deprecated;
ALTER TABLE contacts RENAME TO contacts_deprecated;

-- Update indexes to match new table name
ALTER INDEX idx_patients_new_org_id RENAME TO idx_patients_org_id;
ALTER INDEX idx_patients_new_is_active RENAME TO idx_patients_is_active;
ALTER INDEX idx_patients_new_activity_status RENAME TO idx_patients_activity_status;
ALTER INDEX idx_patients_new_cliniko_id RENAME TO idx_patients_cliniko_id;
ALTER INDEX idx_patients_new_phone RENAME TO idx_patients_phone;
ALTER INDEX idx_patients_new_next_appt RENAME TO idx_patients_next_appt;
ALTER INDEX idx_patients_new_primary_type RENAME TO idx_patients_primary_type;

-- Update trigger name
DROP TRIGGER patients_updated_at_trigger ON patients;
CREATE TRIGGER patients_updated_at_trigger
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_patients_updated_at();

-- Update views to point to renamed table
DROP VIEW IF EXISTS active_patients_view;
DROP VIEW IF EXISTS all_patients_view;
DROP VIEW IF EXISTS patient_activity_summary;
DROP VIEW IF EXISTS duplicate_phone_analysis;

-- Recreate views with new table name
CREATE VIEW active_patients AS
SELECT 
    id,
    organization_id,
    name,
    email,
    phone,
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
    created_at,
    updated_at
FROM patients 
WHERE is_active = TRUE;

CREATE VIEW patient_activity_summary AS
SELECT 
    organization_id,
    activity_status,
    COUNT(*) as patient_count,
    AVG(total_appointment_count) as avg_appointments,
    COUNT(*) FILTER (WHERE next_appointment_time IS NOT NULL) as with_upcoming
FROM patients
GROUP BY organization_id, activity_status;

-- =============================================================================
-- PHASE 2: CONSISTENT TABLE NAMING
-- =============================================================================

-- Rename other tables for consistency
ALTER TABLE organization_services RENAME TO service_integrations;
ALTER TABLE api_credentials RENAME TO service_credentials;

-- Update foreign key references in renamed tables
-- (Note: This would need to be done carefully in production with dependency checking)

-- =============================================================================
-- PHASE 3: PROPOSED FINAL SCHEMA NAMING
-- =============================================================================

/*
FINAL RECOMMENDED TABLE NAMES:

Core Entities:
- patients (unified patient data with activity status)
- appointments (individual appointment records)
- conversations (chat/communication threads)
- messages (individual messages within conversations)

Organization Management:
- organizations (organization/practice details)
- organization_members (user memberships in organizations)
- users (user accounts)

Integration & Sync:
- service_integrations (which services are enabled per org)
- service_credentials (encrypted API keys and credentials)
- sync_logs (sync operation history)

Audit & Security:
- audit_logs (user action tracking)

Deprecated (to be removed after migration):
- contacts_deprecated (old contact table)
- active_patients_deprecated (old active patients table)
*/

-- =============================================================================
-- PHASE 4: COMMENTS FOR CLARITY
-- =============================================================================

COMMENT ON TABLE patients IS 'Unified patient records with activity status and appointment data';
COMMENT ON TABLE appointments IS 'Individual appointment records linked to patients';
COMMENT ON TABLE conversations IS 'Communication threads (SMS, chat, etc.) with patients';
COMMENT ON TABLE messages IS 'Individual messages within conversation threads';
COMMENT ON TABLE organizations IS 'Healthcare practices/clinics using the system';
COMMENT ON TABLE organization_members IS 'User memberships and roles within organizations';
COMMENT ON TABLE users IS 'User accounts (practitioners, staff, admins)';
COMMENT ON TABLE service_integrations IS 'Enabled third-party service integrations per organization';
COMMENT ON TABLE service_credentials IS 'Encrypted API credentials for third-party services';
COMMENT ON TABLE sync_logs IS 'History of data synchronization operations';
COMMENT ON TABLE audit_logs IS 'User action and system event audit trail';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify new table structure
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN (
    'patients', 
    'appointments', 
    'conversations', 
    'messages',
    'organizations',
    'organization_members', 
    'users',
    'service_integrations',
    'service_credentials',
    'sync_logs',
    'audit_logs'
)
ORDER BY tablename;

-- Check that views are working
SELECT 'active_patients view' as view_name, COUNT(*) as record_count FROM active_patients
UNION ALL
SELECT 'patient_activity_summary view', COUNT(*) FROM patient_activity_summary;

-- =============================================================================
-- ROLLBACK PLAN (if needed)
-- =============================================================================

/*
If rollback is needed:

ALTER TABLE patients RENAME TO patients_new;
ALTER TABLE contacts_deprecated RENAME TO contacts;
ALTER TABLE active_patients_deprecated RENAME TO active_patients;
ALTER TABLE service_integrations RENAME TO organization_services;
ALTER TABLE service_credentials RENAME TO api_credentials;

-- Recreate original views
-- Update application code references
*/ 