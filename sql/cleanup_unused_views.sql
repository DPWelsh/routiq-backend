-- CLEANUP UNUSED DATABASE VIEWS AND TABLES
-- Remove views/tables that are no longer used in the codebase
-- Keep only: dashboard_summary and recent_sync_activity (views)

-- ANALYSIS RESULTS:
-- ✅ KEEP: dashboard_summary (used in src/api/dashboard.py)
-- ✅ KEEP: recent_sync_activity (used in src/api/dashboard.py)
-- ❌ REMOVE: All other views (unused)
-- ❌ REMOVE: contacts_deprecated (unused table)
-- ❌ REMOVE: active_patients (replaced by unified patients table)

-- 1. Remove unused views (safe to delete)
DROP VIEW IF EXISTS appointment_summary CASCADE;
DROP VIEW IF EXISTS patient_activity_summary CASCADE;
DROP VIEW IF EXISTS patient_details_list CASCADE;
DROP VIEW IF EXISTS patient_stats_summary CASCADE;
DROP VIEW IF EXISTS org_dashboard_complete CASCADE;
DROP VIEW IF EXISTS org_health_check CASCADE;
DROP VIEW IF EXISTS org_status_summary CASCADE;
DROP VIEW IF EXISTS conversation_insights CASCADE;
DROP VIEW IF EXISTS messages_by_contact CASCADE;
DROP VIEW IF EXISTS phi_access_log CASCADE;

-- 2. Remove unused tables (safe to delete)
DROP TABLE IF EXISTS contacts_deprecated CASCADE;
DROP TABLE IF EXISTS active_patients CASCADE;  -- Should be dead, replaced by unified patients table

-- 3. Add comments to the views we're keeping
COMMENT ON VIEW dashboard_summary IS 'Main dashboard summary data - ACTIVE (used by dashboard API)';
COMMENT ON VIEW recent_sync_activity IS 'Recent sync activity log - ACTIVE (used by dashboard API)';

-- Log cleanup completion
DO $$
BEGIN
    RAISE NOTICE 'Database cleanup completed successfully';
    RAISE NOTICE '✅ Kept: dashboard_summary, recent_sync_activity (views)';
    RAISE NOTICE '❌ Removed: 10 unused views';
    RAISE NOTICE '❌ Removed: contacts_deprecated, active_patients (tables)';
    RAISE NOTICE '';
    RAISE NOTICE 'NOTE: If any code still references active_patients table,';
    RAISE NOTICE 'it should be updated to use the unified patients table.';
END $$; 