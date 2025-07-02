/*
===========================================
PATIENT REENGAGEMENT MASTER VIEW - v1.4 CLEANER BUSINESS LOGIC
===========================================
Replaces 4 Python services with optimized PostgreSQL:
- reengagement_risk_service.py
- communication_tracking_service.py  
- benchmark_service.py
- predictive_risk_service.py

UPDATES IN v1.4 (CLEANER BUSINESS LOGIC):
✅ Two-dimensional classification: engagement_status + risk_level
✅ Engagement Status: active (engaged) | dormant (inactive) | stale (never engaged)
✅ Risk Level: high | medium | low (independent of engagement)
✅ Simpler, more actionable business categories
✅ Better alignment with staff workflow and priorities
✅ FIXED: Patients with upcoming appointments are ALWAYS low risk
✅ FIXED: Days since last contact can never be negative
✅ ADDED: Lifetime value calculation (total appointments × $140 AUD)

This view calculates:
✅ Engagement status based on recent activity patterns
✅ Risk levels based on appointment adherence and patterns  
✅ Days since last contact (from appointments or conversations)
✅ Missed appointments analysis
✅ Appointment attendance patterns
✅ Action priorities & recommendations
✅ Industry benchmarks comparison
✅ Lifetime value (total appointments × $140 AUD)
*/

-- Drop existing view and dependents to avoid column naming conflicts
DROP VIEW IF EXISTS patient_reengagement_master CASCADE;

CREATE VIEW patient_reengagement_master AS 
WITH patient_contact_analysis AS (
  SELECT 
    p.id as patient_id,
    p.organization_id,
    p.name,
    p.email,
    p.phone,
    p.is_active,
    p.activity_status,
    
    -- === DATE CALCULATIONS ===
    p.last_appointment_date,
    p.next_appointment_time,
    GREATEST(0,
      CASE 
        WHEN p.last_appointment_date IS NULL THEN 
          -- For new patients, use days since creation instead of 999
          COALESCE(EXTRACT(EPOCH FROM (NOW() - p.created_at))/86400, 30)
        ELSE 
          EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400
      END
    ) as days_since_last_appointment,
    
    -- FIXED: Proper NULL handling for days_to_next_appointment
    CASE 
      WHEN p.next_appointment_time IS NULL THEN NULL
      WHEN p.next_appointment_time <= NOW() THEN NULL  -- Past appointments should be NULL
      ELSE EXTRACT(EPOCH FROM (p.next_appointment_time - NOW()))/86400
    END as days_to_next_appointment,
    
    -- === APPOINTMENT METRICS ===
    COALESCE(p.recent_appointment_count, 0) as recent_appointment_count,
    COALESCE(p.upcoming_appointment_count, 0) as upcoming_appointment_count,
    COALESCE(p.total_appointment_count, 0) as total_appointment_count,
    
    -- === TREATMENT NOTES ===
    p.treatment_notes,
    
    -- Get latest conversation date (simplified lookup)
    COALESCE(
      (SELECT MAX(c.updated_at) 
       FROM conversations c 
       WHERE c.organization_id = p.organization_id 
       AND c.cliniko_patient_id = p.cliniko_patient_id
      ),
      (SELECT MAX(c.updated_at) 
       FROM conversations c 
       JOIN contacts_deprecated cd ON c.contact_id = cd.id
       WHERE c.organization_id = p.organization_id 
       AND cd.cliniko_patient_id = p.cliniko_patient_id
      ),
      p.last_appointment_date
    ) as last_communication_date,
    
    -- Calculate days since ANY contact (appointment OR conversation) - ENSURE NON-NEGATIVE
    GREATEST(0, 
      CASE 
        WHEN p.last_appointment_date IS NULL THEN 
          COALESCE(EXTRACT(EPOCH FROM (NOW() - p.created_at))/86400, 30)
        ELSE
          LEAST(
            EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400,
            COALESCE(
              EXTRACT(EPOCH FROM (NOW() - (
                SELECT MAX(c.updated_at) 
                FROM conversations c 
                WHERE c.organization_id = p.organization_id 
                AND (c.cliniko_patient_id = p.cliniko_patient_id 
                     OR c.contact_id IN (
                       SELECT cd.id FROM contacts_deprecated cd 
                       WHERE cd.cliniko_patient_id = p.cliniko_patient_id
                     ))
              )))/86400, 
              EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400
            )
          )
      END
    ) as days_since_last_contact
    
  FROM patients p
  WHERE p.organization_id IS NOT NULL
),

appointment_compliance AS (
  SELECT 
    p.organization_id,
    p.id as patient_id,
    
    -- Missed appointments in last 90 days
    COALESCE((
      SELECT COUNT(*) 
      FROM appointments a 
      WHERE a.patient_id = p.id 
      AND a.appointment_date >= NOW() - INTERVAL '90 days'
      AND a.status IN ('no_show', 'cancelled_late', 'missed')
    ), 0) as missed_appointments_90d,
    
    -- Total scheduled appointments in last 90 days  
    COALESCE((
      SELECT COUNT(*) 
      FROM appointments a 
      WHERE a.patient_id = p.id 
      AND a.appointment_date >= NOW() - INTERVAL '90 days'
      AND a.status IN ('scheduled', 'completed', 'no_show', 'cancelled_late', 'missed')
    ), 0) as scheduled_appointments_90d,
    
    -- Attendance rate calculation
    CASE 
      WHEN (
        SELECT COUNT(*) 
        FROM appointments a 
        WHERE a.patient_id = p.id 
        AND a.appointment_date >= NOW() - INTERVAL '90 days'
        AND a.status IN ('scheduled', 'completed', 'no_show', 'cancelled_late', 'missed')
      ) = 0 THEN 1.0
      ELSE 
        COALESCE((
          SELECT COUNT(*) 
          FROM appointments a 
          WHERE a.patient_id = p.id 
          AND a.appointment_date >= NOW() - INTERVAL '90 days'
          AND a.status = 'completed'
        ), 0) * 1.0 / NULLIF((
          SELECT COUNT(*) 
          FROM appointments a 
          WHERE a.patient_id = p.id 
          AND a.appointment_date >= NOW() - INTERVAL '90 days'
          AND a.status IN ('scheduled', 'completed', 'no_show', 'cancelled_late', 'missed')
        ), 0)
    END as attendance_rate_90d
    
  FROM patients p
),

communication_patterns AS (
  SELECT 
    p.organization_id,
    p.id as patient_id,
    
    -- Communication frequency
    COALESCE((
      SELECT COUNT(*) 
      FROM conversations c 
      WHERE c.organization_id = p.organization_id 
      AND c.updated_at >= NOW() - INTERVAL '90 days'
      AND (c.contact_id IN (
        SELECT cd.id FROM contacts_deprecated cd 
        WHERE cd.cliniko_patient_id = p.cliniko_patient_id
      ) OR c.cliniko_patient_id = p.cliniko_patient_id)
    ), 0) as conversations_90d,
    
    -- Last conversation sentiment (if available)
    (
      SELECT c.overall_sentiment
      FROM conversations c 
      WHERE c.organization_id = p.organization_id 
      AND (c.contact_id IN (
        SELECT cd.id FROM contacts_deprecated cd 
        WHERE cd.cliniko_patient_id = p.cliniko_patient_id
      ) OR c.cliniko_patient_id = p.cliniko_patient_id)
      ORDER BY c.updated_at DESC 
      LIMIT 1
    ) as last_conversation_sentiment
    
  FROM patients p
),

cleaner_business_logic AS (
  SELECT 
    pca.*,
    ac.missed_appointments_90d,
    ac.scheduled_appointments_90d,
    ac.attendance_rate_90d,
    cp.conversations_90d,
    cp.last_conversation_sentiment,
    
    -- === ENGAGEMENT STATUS (Primary Classification) ===
    CASE 
      -- STALE: Never had any real engagement
      WHEN pca.total_appointment_count = 0 
       AND pca.upcoming_appointment_count = 0 
       AND pca.last_communication_date IS NULL THEN 'stale'
      
      -- ACTIVE: Recent activity or upcoming appointments
      WHEN pca.upcoming_appointment_count > 0 
       OR pca.days_since_last_contact <= 30 THEN 'active'
      
      -- DORMANT: Had engagement but gone quiet  
      ELSE 'dormant'
    END as engagement_status,
    
    -- === RISK LEVEL (Independent Assessment) ===
    CASE 
      -- LOW RISK: Anyone with upcoming appointments should be low risk
      WHEN pca.upcoming_appointment_count > 0 THEN 'low'
      
      -- HIGH RISK: Severe issues - very poor adherence AND long gaps
      WHEN (pca.days_since_last_contact > 90 AND pca.total_appointment_count > 0)  -- Long gap for existing patients
       OR (ac.attendance_rate_90d < 0.5 AND pca.total_appointment_count > 3)      -- Very poor attendance history
       OR (COALESCE(ac.missed_appointments_90d, 0) >= 4) THEN 'high'              -- Frequent no-shows
      
      -- MEDIUM RISK: Some concerns that need monitoring
      WHEN (pca.days_since_last_contact > 60 AND pca.total_appointment_count > 0)  -- Moderate gap for existing patients
       OR (pca.upcoming_appointment_count = 0 AND pca.total_appointment_count > 0 AND pca.days_since_last_contact > 30) -- No upcoming appts + gap
       OR (ac.attendance_rate_90d < 0.7 AND pca.total_appointment_count > 2)      -- Below average attendance
       OR (COALESCE(ac.missed_appointments_90d, 0) >= 2) THEN 'medium'            -- Some missed appointments
      
      -- LOW RISK: Good engagement patterns or new patients
      ELSE 'low'
    END as risk_level,
    
    -- === NUMERIC RISK SCORE (For sorting/prioritization) ===
    CASE 
      -- Base score by engagement status
      WHEN pca.total_appointment_count = 0 
       AND pca.upcoming_appointment_count = 0 
       AND pca.last_communication_date IS NULL THEN 15  -- Stale patients = lower priority
      WHEN pca.upcoming_appointment_count > 0 
       OR pca.days_since_last_contact <= 30 THEN 25      -- Active patients = base priority  
      ELSE 45                                            -- Dormant patients = higher base priority
    END +
    
    -- Risk level modifiers (matching the new thresholds)
    CASE 
      -- Upcoming appointments = no risk bonus (low risk)
      WHEN pca.upcoming_appointment_count > 0 THEN 0
      
      WHEN (pca.days_since_last_contact > 90 AND pca.total_appointment_count > 0)
       OR (ac.attendance_rate_90d < 0.5 AND pca.total_appointment_count > 3)
       OR (COALESCE(ac.missed_appointments_90d, 0) >= 4) THEN 35  -- High risk bonus
      WHEN (pca.days_since_last_contact > 60 AND pca.total_appointment_count > 0)
       OR (pca.upcoming_appointment_count = 0 AND pca.total_appointment_count > 0 AND pca.days_since_last_contact > 30)
       OR (ac.attendance_rate_90d < 0.7 AND pca.total_appointment_count > 2)
       OR (COALESCE(ac.missed_appointments_90d, 0) >= 2) THEN 20  -- Medium risk bonus
      ELSE 0                                                     -- Low risk bonus
    END +
    
    -- Minor adjustments
    (LEAST(5, COALESCE(ac.missed_appointments_90d, 0))) +  -- Missed appointment penalty
    CASE WHEN NOT pca.is_active THEN 5 ELSE 0 END as risk_score  -- Inactive status penalty
    
  FROM patient_contact_analysis pca
  LEFT JOIN appointment_compliance ac ON pca.patient_id = ac.patient_id
  LEFT JOIN communication_patterns cp ON pca.patient_id = cp.patient_id
)

SELECT 
  cbl.organization_id,
  cbl.patient_id,
  cbl.name as patient_name,
  cbl.email,
  cbl.phone,
  cbl.is_active,
  cbl.activity_status,
  
  -- === CLEANER BUSINESS CLASSIFICATIONS ===
  cbl.engagement_status,                                    -- active | dormant | stale
  cbl.risk_level,                                          -- high | medium | low
  LEAST(100, GREATEST(0, cbl.risk_score)) as risk_score,   -- 0-100 for sorting
  
  -- === TIME METRICS ===
  ROUND(cbl.days_since_last_contact::numeric, 1) as days_since_last_contact,
  CASE 
    WHEN cbl.days_to_next_appointment IS NULL THEN NULL
    ELSE ROUND(cbl.days_to_next_appointment::numeric, 1)
  END as days_to_next_appointment,
  cbl.last_appointment_date,
  cbl.next_appointment_time,
  cbl.last_communication_date,
  
  -- === ENGAGEMENT METRICS ===
  cbl.recent_appointment_count,
  cbl.upcoming_appointment_count,
  cbl.total_appointment_count,
  cbl.missed_appointments_90d,
  cbl.scheduled_appointments_90d,
  ROUND((cbl.attendance_rate_90d * 100)::numeric, 1) as attendance_rate_percent,
  cbl.conversations_90d,
  cbl.last_conversation_sentiment,
  
  -- === TREATMENT NOTES ===
  cbl.treatment_notes,
  
  -- === LIFETIME VALUE ===
  (cbl.total_appointment_count * 140) as lifetime_value_aud,
  
  -- === ACTION PRIORITY (1-4, 1=most urgent) ===
  CASE 
    WHEN cbl.engagement_status = 'dormant' AND cbl.risk_level = 'high' THEN 1      -- Urgent: Lost high-risk patients
    WHEN cbl.engagement_status = 'active' AND cbl.risk_level = 'high' THEN 2       -- Important: Active but high-risk
    WHEN cbl.engagement_status = 'dormant' AND cbl.risk_level = 'medium' THEN 2    -- Important: Dormant medium-risk
    WHEN cbl.risk_level = 'medium' THEN 3                                          -- Medium: All other medium-risk
    ELSE 4                                                                          -- Low: Active low-risk & stale
  END as action_priority,
  
  -- === STALE PATIENT FLAG ===
  CASE WHEN cbl.engagement_status = 'stale' THEN true ELSE false END as is_stale,
  
  -- === RECOMMENDED ACTION (Business-focused) ===
  CASE 
    WHEN cbl.engagement_status = 'stale' THEN 'NEW: Schedule initial consultation'
    WHEN cbl.engagement_status = 'dormant' AND cbl.risk_level = 'high' THEN 'URGENT: Call immediately - high-risk dormant patient'
    WHEN cbl.engagement_status = 'active' AND cbl.risk_level = 'high' THEN 'PRIORITY: Address adherence issues while engaged'
    WHEN cbl.engagement_status = 'dormant' THEN 'FOLLOW-UP: Re-engage dormant patient'
    WHEN cbl.risk_level = 'medium' THEN 'MONITOR: Check in and prevent issues'
    ELSE 'MAINTAIN: Continue current care plan'
  END as recommended_action,
  
  -- === CONTACT SUCCESS PREDICTION ===
  CASE 
    WHEN cbl.attendance_rate_90d >= 0.9 AND cbl.upcoming_appointment_count > 0 THEN 'very_high'
    WHEN cbl.engagement_status = 'active' AND cbl.attendance_rate_90d >= 0.8 THEN 'high'
    WHEN cbl.engagement_status = 'active' OR cbl.attendance_rate_90d >= 0.7 THEN 'high'
    WHEN cbl.attendance_rate_90d >= 0.6 OR cbl.total_appointment_count > 0 THEN 'medium'
    WHEN cbl.engagement_status = 'dormant' AND cbl.days_since_last_contact <= 60 THEN 'low'
    ELSE 'very_low'
  END as contact_success_prediction,
  
  -- === BENCHMARK COMPARISON ===
  CASE 
    WHEN cbl.attendance_rate_90d >= 0.75 THEN 'above_industry_avg'  -- Industry avg ~75%
    WHEN cbl.attendance_rate_90d >= 0.60 THEN 'at_industry_avg'
    ELSE 'below_industry_avg'
  END as attendance_benchmark,
  
  CASE 
    WHEN cbl.engagement_status = 'active' THEN 'good_engagement'     
    WHEN cbl.engagement_status = 'dormant' THEN 'poor_engagement'
    ELSE 'no_engagement'  -- stale
  END as engagement_benchmark,
  
  -- === METADATA ===
  NOW() as calculated_at,
  'v1.4.2-added-lifetime-value' as view_version

FROM cleaner_business_logic cbl
ORDER BY 
  CASE 
    WHEN cbl.engagement_status = 'dormant' AND cbl.risk_level = 'high' THEN 1
    WHEN cbl.engagement_status = 'active' AND cbl.risk_level = 'high' THEN 2
    WHEN cbl.engagement_status = 'dormant' AND cbl.risk_level = 'medium' THEN 3
    WHEN cbl.risk_level = 'medium' THEN 4
    ELSE 5
  END,
  cbl.days_since_last_contact DESC;

-- === PERFORMANCE INDEXES ===
-- These will be created separately for optimal performance

/*
===========================================
CLEANER BUSINESS LOGIC SUMMARY
===========================================

ENGAGEMENT STATUS (Primary):
✅ ACTIVE: Recent activity (≤30 days) OR upcoming appointments
✅ DORMANT: Had engagement but gone quiet (>30 days, no upcoming)  
✅ STALE: Never had any real engagement (0 appointments, no communication)

RISK LEVELS (Independent):
✅ LOW: PRIORITY - Anyone with upcoming appointments (overrides all other factors)
✅ HIGH: Poor adherence (<60% attendance, 3+ missed) OR long gaps (>60 days)
✅ MEDIUM: Some concerns (>30 days gap, no upcoming, <80% attendance)
✅ LOW: Good engagement and adherence patterns OR upcoming appointments

ACTION PRIORITIES:
1. Dormant + High Risk = URGENT: Call immediately - high-risk dormant patient
2. Active + High Risk = PRIORITY: Address adherence issues while engaged  
2. Dormant + Medium Risk = IMPORTANT: Re-engage dormant patient
3. Any Medium Risk = MONITOR: Check in and prevent issues
4. Active + Low Risk, Stale = MAINTAIN: Continue current care plan

This logic is:
- Simple to understand: 2 clear dimensions
- Actionable for staff: Clear priority order
- Business-focused: Matches workflow patterns
- Scalable: Works for any patient volume
===========================================
*/ 