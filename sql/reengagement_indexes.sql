/*
===========================================
REENGAGEMENT PERFORMANCE INDEXES
===========================================
Optimizes the patient_reengagement_master and reengagement_performance_metrics views
for sub-100ms response times with large datasets.

Based on LEAN-006: Performance Optimization & Indexes

IMPORTANT: Temporal filtering (e.g., "last 90 days") is done in the views and application
layer, not in index predicates, because NOW() is not IMMUTABLE in PostgreSQL.
*/

-- === CORE PATIENT TABLE INDEXES ===
-- These optimize the base patient_reengagement_master view

-- Primary risk-based queries (most common frontend use case)
CREATE INDEX IF NOT EXISTS idx_patients_risk_priority 
ON patients(organization_id, is_active, last_appointment_date DESC, upcoming_appointment_count)
WHERE is_active = true;

-- Organization filtering (every query starts here)
CREATE INDEX IF NOT EXISTS idx_patients_org_active 
ON patients(organization_id, is_active)
WHERE is_active = true;

-- Date range optimization for "days since last contact" calculations
CREATE INDEX IF NOT EXISTS idx_patients_last_appointment 
ON patients(last_appointment_date DESC) 
WHERE last_appointment_date IS NOT NULL;

-- Next appointment lookups
CREATE INDEX IF NOT EXISTS idx_patients_next_appointment 
ON patients(next_appointment_time) 
WHERE next_appointment_time IS NOT NULL;

-- Activity status filtering
CREATE INDEX IF NOT EXISTS idx_patients_activity_status 
ON patients(organization_id, activity_status, last_appointment_date DESC);

-- === APPOINTMENTS TABLE INDEXES ===
-- Optimize appointment compliance calculations

-- Patient appointment history (all appointments, filter in application)
CREATE INDEX IF NOT EXISTS idx_appointments_patient_recent 
ON appointments(patient_id, appointment_date DESC, status);

-- Organization-wide appointment stats
CREATE INDEX IF NOT EXISTS idx_appointments_org_recent 
ON appointments(organization_id, appointment_date DESC, status);

-- Missed appointment tracking
CREATE INDEX IF NOT EXISTS idx_appointments_missed 
ON appointments(patient_id, appointment_date DESC)
WHERE status IN ('no_show', 'cancelled_late', 'missed');

-- === CONVERSATIONS TABLE INDEXES ===
-- Optimize communication tracking

-- Patient conversation lookup (critical for risk calculation)
CREATE INDEX IF NOT EXISTS idx_conversations_patient_recent 
ON conversations(organization_id, updated_at DESC);

-- Contact ID mapping (for deprecated contacts table)
CREATE INDEX IF NOT EXISTS idx_conversations_contact_recent 
ON conversations(contact_id, updated_at DESC);

-- Cliniko patient ID direct lookup
CREATE INDEX IF NOT EXISTS idx_conversations_cliniko_patient 
ON conversations(cliniko_patient_id, updated_at DESC)
WHERE cliniko_patient_id IS NOT NULL;

-- Sentiment analysis optimization
CREATE INDEX IF NOT EXISTS idx_conversations_sentiment 
ON conversations(organization_id, overall_sentiment, updated_at DESC)
WHERE overall_sentiment IS NOT NULL;

-- === OUTREACH LOG INDEXES ===
-- Optimize performance metrics view

-- Core performance queries (30-day and 90-day metrics)
CREATE INDEX IF NOT EXISTS idx_outreach_log_performance 
ON outreach_log(organization_id, created_at DESC, method, outcome);

-- Patient-specific outreach tracking
CREATE INDEX IF NOT EXISTS idx_outreach_log_patient_tracking 
ON outreach_log(patient_id, created_at DESC, outcome);

-- Method-specific success rates
CREATE INDEX IF NOT EXISTS idx_outreach_log_method_success 
ON outreach_log(organization_id, method, outcome, created_at DESC);

-- Success rate calculations
CREATE INDEX IF NOT EXISTS idx_outreach_log_success_tracking 
ON outreach_log(organization_id, created_at DESC)
WHERE outcome = 'success';

-- === CONTACTS_DEPRECATED TABLE INDEXES ===
-- Support legacy contact mapping until migration complete

-- Cliniko patient mapping
CREATE INDEX IF NOT EXISTS idx_contacts_deprecated_cliniko 
ON contacts_deprecated(cliniko_patient_id)
WHERE cliniko_patient_id IS NOT NULL;

-- === PARTIAL INDEXES FOR HIGH-PERFORMANCE FILTERING ===
-- These target the most common dashboard queries

-- Critical risk patients (filter by date in application)
CREATE INDEX IF NOT EXISTS idx_patients_critical_risk 
ON patients(organization_id, last_appointment_date DESC)
WHERE is_active = true 
AND upcoming_appointment_count = 0;

-- High engagement patients (filter by date in application)
CREATE INDEX IF NOT EXISTS idx_patients_high_engagement 
ON patients(organization_id, last_appointment_date DESC)
WHERE is_active = true;

-- Stale patients (filter by date in application)
CREATE INDEX IF NOT EXISTS idx_patients_stale 
ON patients(organization_id, total_appointment_count, upcoming_appointment_count)
WHERE is_active = true;

-- === COMPOSITE INDEXES FOR COMPLEX QUERIES ===

-- Risk calculation optimization (covers most CTE operations)
CREATE INDEX IF NOT EXISTS idx_patients_risk_calculation 
ON patients(organization_id, is_active, last_appointment_date, upcoming_appointment_count, 
           recent_appointment_count, total_appointment_count);

-- Performance dashboard optimization
CREATE INDEX IF NOT EXISTS idx_outreach_log_dashboard 
ON outreach_log(organization_id, created_at DESC, method, outcome, patient_id);

-- === MATERIALIZED VIEW OPTION FOR LARGE DATASETS ===
-- Uncomment if query performance still insufficient with regular view

/*
-- Materialized view for very large datasets (>100k patients)
CREATE MATERIALIZED VIEW IF NOT EXISTS patient_reengagement_master_cache AS
SELECT * FROM patient_reengagement_master;

-- Refresh strategy - run every 30 minutes
CREATE INDEX ON patient_reengagement_master_cache(organization_id, risk_score DESC);
CREATE INDEX ON patient_reengagement_master_cache(organization_id, action_priority, risk_score DESC);

-- Refresh command (add to cron job):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY patient_reengagement_master_cache;
*/

-- === QUERY PLAN ANALYSIS HELPERS ===
-- Use these to analyze performance after deployment

/*
Performance Testing Commands:

-- Test risk dashboard query
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM patient_reengagement_master 
WHERE organization_id = 'org_2SifzKXTBqKgJQMTYD' 
AND risk_level IN ('critical', 'high')
ORDER BY risk_score DESC, action_priority 
LIMIT 20;

-- Test performance metrics query  
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM reengagement_performance_metrics 
WHERE organization_id = 'org_2SifzKXTBqKgJQMTYD';

-- Check index usage
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename IN ('patients', 'appointments', 'conversations', 'outreach_log')
ORDER BY tablename, attname;
*/

-- === MAINTENANCE TASKS ===
-- Add these to regular database maintenance

-- Analyze tables after index creation (run once)
ANALYZE patients;
ANALYZE appointments; 
ANALYZE conversations;
ANALYZE outreach_log;

-- Auto-vacuum optimization for heavily updated tables
ALTER TABLE outreach_log SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE conversations SET (autovacuum_analyze_scale_factor = 0.1);

/*
===========================================
PERFORMANCE TARGETS
===========================================
With these indexes, expect:

✅ Risk dashboard: <100ms for orgs with <10k patients
✅ Performance metrics: <50ms for 90-day aggregations  
✅ Patient list filtering: <200ms for complex risk queries
✅ Individual patient lookup: <10ms

For organizations with >10k patients, consider:
- Materialized view refresh every 30 minutes
- Partitioning by organization_id for very large multi-tenant setups
- Connection pooling (already configured in database.py)

===========================================
DEPLOYMENT NOTES
===========================================
1. Create indexes during low-traffic period
2. Monitor query performance with pg_stat_statements
3. Adjust autovacuum settings based on insert patterns
4. Consider read replicas for analytics queries if needed
*/ 