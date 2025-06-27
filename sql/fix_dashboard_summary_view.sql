-- FIX DASHBOARD SUMMARY VIEW
-- Update averages to calculate only for active patients (better metric)
-- ADD: engagement_rate calculation for frontend

-- Drop and recreate the dashboard_summary view
DROP VIEW IF EXISTS dashboard_summary CASCADE;

CREATE VIEW public.dashboard_summary AS
SELECT
  organization_id,
  count(*) as total_patients,
  count(*) FILTER (
    WHERE is_active = true
  ) as active_patients,
  count(*) FILTER (
    WHERE upcoming_appointment_count > 0
  ) as patients_with_upcoming,
  count(*) FILTER (
    WHERE recent_appointment_count > 0
  ) as patients_with_recent,
  sum(upcoming_appointment_count) as total_upcoming_appointments,
  sum(recent_appointment_count) as total_recent_appointments,
  sum(total_appointment_count) as total_all_appointments,
  
  -- FIXED: Calculate averages only for ACTIVE patients (much better metric)
  CASE 
    WHEN count(*) FILTER (WHERE is_active = true) > 0 THEN
      round(
        sum(upcoming_appointment_count) FILTER (WHERE is_active = true)::numeric / 
        count(*) FILTER (WHERE is_active = true)::numeric, 
        2
      )
    ELSE 0
  END as avg_upcoming_per_patient,
  
  CASE 
    WHEN count(*) FILTER (WHERE is_active = true) > 0 THEN
      round(
        sum(recent_appointment_count) FILTER (WHERE is_active = true)::numeric / 
        count(*) FILTER (WHERE is_active = true)::numeric, 
        2
      )
    ELSE 0
  END as avg_recent_per_patient,
  
  CASE 
    WHEN count(*) FILTER (WHERE is_active = true) > 0 THEN
      round(
        sum(total_appointment_count) FILTER (WHERE is_active = true)::numeric / 
        count(*) FILTER (WHERE is_active = true)::numeric, 
        2
      )
    ELSE 0
  END as avg_total_per_patient,
  
  -- NEW: Engagement Rate (percentage of patients with upcoming OR recent appointments)
  CASE
    WHEN count(*) > 0 THEN
      round(
        (count(*) FILTER (WHERE upcoming_appointment_count > 0) + 
         count(*) FILTER (WHERE recent_appointment_count > 0) - 
         count(*) FILTER (WHERE upcoming_appointment_count > 0 AND recent_appointment_count > 0))::numeric / 
        count(*)::numeric * 100::numeric, 
        1
      )
    ELSE 0
  END as engagement_rate,
  
  max(last_synced_at) as last_sync_time,
  count(*) FILTER (
    WHERE last_synced_at IS NOT NULL
  ) as synced_patients,
  round(
    count(*) FILTER (
      WHERE last_synced_at IS NOT NULL
    )::numeric / count(*)::numeric * 100::numeric,
    1
  ) as sync_percentage,
  CASE
    WHEN count(*) > 0 AND max(last_synced_at) IS NOT NULL THEN 'Connected'::text
    WHEN count(*) > 0 THEN 'Partial'::text
    ELSE 'Not Connected'::text
  END as integration_status,
  CASE
    WHEN count(*) FILTER (WHERE is_active = true) > 0 THEN 'Active'::text
    ELSE 'Inactive'::text
  END as activity_status,
  now() as generated_at
FROM patients p
WHERE organization_id IS NOT NULL
GROUP BY organization_id;

-- Add helpful comment
COMMENT ON VIEW dashboard_summary IS 'Dashboard summary with averages calculated for active patients only and engagement rate - Updated for frontend requirements';

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Dashboard summary view updated successfully';
    RAISE NOTICE '✅ Averages now calculated for active patients only';
    RAISE NOTICE '✅ Better metrics: avg appointments per active patient';
    RAISE NOTICE '✅ Added engagement_rate calculation for frontend';
    RAISE NOTICE '✅ Engagement rate = (patients with upcoming OR recent) / total * 100';
END $$; 