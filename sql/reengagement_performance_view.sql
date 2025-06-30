/*
===========================================
REENGAGEMENT PERFORMANCE METRICS VIEW
===========================================
Calculates all performance analytics for reengagement efforts.
Uses the simple outreach_log table for data.

Replaces Python services:
- communication_tracking_service.py
- benchmark_service.py
*/

CREATE OR REPLACE VIEW reengagement_performance_metrics AS
WITH outreach_stats AS (
  SELECT 
    ol.organization_id,
    
    -- === 30-DAY METRICS ===
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days') as total_attempts_30d,
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.outcome = 'success') as successful_contacts_30d,
    
    -- === 90-DAY METRICS ===  
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '90 days') as total_attempts_90d,
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '90 days' AND ol.outcome = 'success') as successful_contacts_90d,
    
    -- === METHOD BREAKDOWN (30 days) ===
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.method = 'phone') as phone_attempts_30d,
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.method = 'phone' AND ol.outcome = 'success') as phone_success_30d,
    
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.method = 'sms') as sms_attempts_30d,
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.method = 'sms' AND ol.outcome = 'success') as sms_success_30d,
    
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.method = 'email') as email_attempts_30d,
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.method = 'email' AND ol.outcome = 'success') as email_success_30d,
    
    -- === PATIENT OUTCOMES ===
    COUNT(DISTINCT ol.patient_id) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days') as patients_contacted_30d,
    COUNT(DISTINCT ol.patient_id) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '30 days' AND ol.outcome = 'success') as patients_reached_30d
    
  FROM outreach_log ol
  GROUP BY ol.organization_id
),

appointment_conversions AS (
  SELECT 
    ol.organization_id,
    
    -- Count patients who had successful contact AND then scheduled an appointment
    COUNT(DISTINCT CASE 
      WHEN ol.outcome = 'success' 
      AND ol.created_at >= NOW() - INTERVAL '30 days'
      AND EXISTS (
        SELECT 1 FROM appointments a 
        WHERE a.patient_id = ol.patient_id 
        AND a.created_at > ol.created_at 
        AND a.created_at <= ol.created_at + INTERVAL '14 days'
        AND a.status IN ('scheduled', 'completed')
      ) THEN ol.patient_id 
    END) as appointments_scheduled_after_contact_30d
    
  FROM outreach_log ol
  GROUP BY ol.organization_id
),

trending_analysis AS (
  SELECT 
    ol.organization_id,
    
    -- Previous 30 days for comparison
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '60 days' AND ol.created_at < NOW() - INTERVAL '30 days') as total_attempts_prev_30d,
    COUNT(*) FILTER (WHERE ol.created_at >= NOW() - INTERVAL '60 days' AND ol.created_at < NOW() - INTERVAL '30 days' AND ol.outcome = 'success') as successful_contacts_prev_30d
    
  FROM outreach_log ol  
  GROUP BY ol.organization_id
),

org_patient_counts AS (
  SELECT 
    p.organization_id,
    COUNT(*) as total_patients,
    COUNT(*) FILTER (WHERE p.is_active = true) as active_patients
  FROM patients p
  GROUP BY p.organization_id
)

SELECT 
  COALESCE(os.organization_id, ac.organization_id, ta.organization_id, opc.organization_id) as organization_id,
  
  -- === CORE PERFORMANCE METRICS ===
  COALESCE(os.total_attempts_30d, 0) as total_outreach_attempts_30d,
  COALESCE(os.successful_contacts_30d, 0) as successful_contacts_30d,
  COALESCE(os.patients_contacted_30d, 0) as unique_patients_contacted_30d,
  COALESCE(os.patients_reached_30d, 0) as unique_patients_reached_30d,
  
  -- === SUCCESS RATES ===
  CASE 
    WHEN COALESCE(os.total_attempts_30d, 0) = 0 THEN 0
    ELSE ROUND((COALESCE(os.successful_contacts_30d, 0) * 100.0 / os.total_attempts_30d), 1)
  END as contact_success_rate_30d,
  
  CASE 
    WHEN COALESCE(os.patients_contacted_30d, 0) = 0 THEN 0  
    ELSE ROUND((COALESCE(os.patients_reached_30d, 0) * 100.0 / os.patients_contacted_30d), 1)
  END as patient_reach_rate_30d,
  
  -- === APPOINTMENT CONVERSION ===
  COALESCE(ac.appointments_scheduled_after_contact_30d, 0) as appointments_scheduled_after_contact_30d,
  CASE 
    WHEN COALESCE(os.successful_contacts_30d, 0) = 0 THEN 0
    ELSE ROUND((COALESCE(ac.appointments_scheduled_after_contact_30d, 0) * 100.0 / os.successful_contacts_30d), 1)
  END as appointment_conversion_rate_30d,
  
  -- === CHANNEL PERFORMANCE ===
  json_build_object(
    'phone', json_build_object(
      'attempts', COALESCE(os.phone_attempts_30d, 0),
      'successes', COALESCE(os.phone_success_30d, 0),
      'success_rate', CASE 
        WHEN COALESCE(os.phone_attempts_30d, 0) = 0 THEN 0
        ELSE ROUND((COALESCE(os.phone_success_30d, 0) * 100.0 / os.phone_attempts_30d), 1)
      END
    ),
    'sms', json_build_object(
      'attempts', COALESCE(os.sms_attempts_30d, 0),
      'successes', COALESCE(os.sms_success_30d, 0),
      'success_rate', CASE 
        WHEN COALESCE(os.sms_attempts_30d, 0) = 0 THEN 0
        ELSE ROUND((COALESCE(os.sms_success_30d, 0) * 100.0 / os.sms_attempts_30d), 1)
      END
    ),
    'email', json_build_object(
      'attempts', COALESCE(os.email_attempts_30d, 0),
      'successes', COALESCE(os.email_success_30d, 0),
      'success_rate', CASE 
        WHEN COALESCE(os.email_attempts_30d, 0) = 0 THEN 0
        ELSE ROUND((COALESCE(os.email_success_30d, 0) * 100.0 / os.email_attempts_30d), 1)
      END
    )
  ) as channel_performance_30d,
  
  -- === TRENDING (vs previous 30 days) ===
  CASE 
    WHEN COALESCE(ta.total_attempts_prev_30d, 0) = 0 AND COALESCE(os.total_attempts_30d, 0) = 0 THEN 0
    WHEN COALESCE(ta.total_attempts_prev_30d, 0) = 0 THEN 100  -- New activity
    ELSE ROUND(((COALESCE(os.total_attempts_30d, 0) - COALESCE(ta.total_attempts_prev_30d, 0)) * 100.0 / ta.total_attempts_prev_30d), 1)
  END as attempts_trend_percent,
  
  CASE 
    WHEN COALESCE(ta.successful_contacts_prev_30d, 0) = 0 AND COALESCE(os.successful_contacts_30d, 0) = 0 THEN 0
    WHEN COALESCE(ta.successful_contacts_prev_30d, 0) = 0 THEN 100  -- New success
    ELSE ROUND(((COALESCE(os.successful_contacts_30d, 0) - COALESCE(ta.successful_contacts_prev_30d, 0)) * 100.0 / ta.successful_contacts_prev_30d), 1)
  END as success_trend_percent,
  
  -- === INDUSTRY BENCHMARKS ===
  CASE 
    WHEN COALESCE(os.total_attempts_30d, 0) = 0 THEN 'no_data'
    WHEN (COALESCE(os.successful_contacts_30d, 0) * 100.0 / os.total_attempts_30d) >= 60 THEN 'excellent'    -- Top 25%
    WHEN (COALESCE(os.successful_contacts_30d, 0) * 100.0 / os.total_attempts_30d) >= 45 THEN 'above_average' -- Industry avg ~45%
    WHEN (COALESCE(os.successful_contacts_30d, 0) * 100.0 / os.total_attempts_30d) >= 30 THEN 'average'
    ELSE 'below_average'
  END as performance_vs_benchmark,
  
  -- === EFFICIENCY METRICS ===
  CASE 
    WHEN COALESCE(opc.active_patients, 0) = 0 THEN 0
    ELSE ROUND((COALESCE(os.patients_reached_30d, 0) * 100.0 / opc.active_patients), 1)
  END as patient_base_engagement_rate_30d,
  
  -- Calculate average days to successful contact
  COALESCE((
    SELECT ROUND(AVG(
      EXTRACT(EPOCH FROM (ol_success.created_at - (
        SELECT MAX(prm.last_communication_date) 
        FROM patient_reengagement_master prm 
        WHERE prm.patient_id = ol_success.patient_id
      ))) / 86400
    )::numeric, 1)
    FROM outreach_log ol_success
    WHERE ol_success.organization_id = COALESCE(os.organization_id, ac.organization_id, ta.organization_id, opc.organization_id)
    AND ol_success.created_at >= NOW() - INTERVAL '30 days'
    AND ol_success.outcome = 'success'
  ), 0) as avg_days_to_successful_contact,
  
  -- === METADATA ===
  opc.total_patients,
  opc.active_patients,
  NOW() as calculated_at,
  '1.0' as view_version

FROM outreach_stats os
FULL OUTER JOIN appointment_conversions ac ON os.organization_id = ac.organization_id  
FULL OUTER JOIN trending_analysis ta ON COALESCE(os.organization_id, ac.organization_id) = ta.organization_id
FULL OUTER JOIN org_patient_counts opc ON COALESCE(os.organization_id, ac.organization_id, ta.organization_id) = opc.organization_id

ORDER BY COALESCE(os.organization_id, ac.organization_id, ta.organization_id, opc.organization_id);

/*
Performance Notes:
- Uses filtered aggregation for efficient metric calculation
- JSON objects for complex channel performance data
- Trending analysis compares current vs previous periods
- Industry benchmarks built-in (45% average contact success rate)
- Optimized with proper indexing on outreach_log table
*/ 