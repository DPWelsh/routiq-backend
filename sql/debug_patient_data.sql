/*
===========================================
DEBUG PATIENT DATA ANALYSIS
===========================================
Simple queries to understand why patient_reengagement_master shows all patients as inactive
with 999 days since last contact.
*/

-- === 1. CHECK BASIC PATIENT DATA ===
SELECT 
  'PATIENT DATA' as check_type,
  COUNT(*) as total_patients,
  COUNT(*) FILTER (WHERE is_active = true) as active_patients,
  COUNT(*) FILTER (WHERE last_appointment_date IS NOT NULL) as patients_with_appointments,
  COUNT(*) FILTER (WHERE activity_status = 'active') as status_active,
  COUNT(*) FILTER (WHERE activity_status = 'inactive') as status_inactive
FROM patients 
WHERE organization_id = 'org_2xwHfNj6eaRUIX10aniXGvx7';

-- === 2. SAMPLE PATIENT RECORDS ===
SELECT 
  'SAMPLE PATIENTS' as check_type,
  name, 
  is_active, 
  activity_status,
  last_appointment_date,
  next_appointment_time,
  recent_appointment_count,
  upcoming_appointment_count,
  total_appointment_count
FROM patients 
WHERE organization_id = 'org_2xwHfNj6eaRUIX10aniXGvx7'
LIMIT 5;

-- === 3. CHECK APPOINTMENTS TABLE ===
SELECT 
  'APPOINTMENTS DATA' as check_type,
  COUNT(*) as total_appointments,
  COUNT(DISTINCT patient_id) as patients_with_appointments,
  MIN(appointment_date) as earliest_appointment,
  MAX(appointment_date) as latest_appointment
FROM appointments a
JOIN patients p ON p.id = a.patient_id
WHERE p.organization_id = 'org_2xwHfNj6eaRUIX10aniXGvx7';

-- === 4. CHECK CONVERSATIONS TABLE ===
SELECT 
  'CONVERSATIONS DATA' as check_type,
  COUNT(*) as total_conversations,
  COUNT(DISTINCT cliniko_patient_id) as patients_with_conversations_direct,
  COUNT(DISTINCT contact_id) as contacts_with_conversations,
  MIN(updated_at) as earliest_conversation,
  MAX(updated_at) as latest_conversation
FROM conversations 
WHERE organization_id = 'org_2xwHfNj6eaRUIX10aniXGvx7';

-- === 5. CHECK CONTACTS_DEPRECATED MAPPING ===
SELECT 
  'CONTACTS MAPPING' as check_type,
  COUNT(*) as total_deprecated_contacts,
  COUNT(DISTINCT cliniko_patient_id) as unique_patient_mappings
FROM contacts_deprecated cd
WHERE EXISTS (
  SELECT 1 FROM patients p 
  WHERE p.cliniko_patient_id = cd.cliniko_patient_id 
  AND p.organization_id = 'org_2xwHfNj6eaRUIX10aniXGvx7'
);

-- === 6. TEST SIMPLE RISK CALCULATION ===
-- This mimics the view logic but simplified
WITH simple_risk AS (
  SELECT 
    p.id,
    p.name,
    p.is_active,
    p.last_appointment_date,
    
    -- Simple days calculation
    CASE 
      WHEN p.last_appointment_date IS NULL THEN 999
      ELSE EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400
    END as days_since_appointment,
    
    -- Check if conversations exist
    (SELECT COUNT(*) 
     FROM conversations c 
     WHERE c.organization_id = p.organization_id 
     AND c.cliniko_patient_id = p.cliniko_patient_id
    ) as direct_conversations,
    
    (SELECT COUNT(*) 
     FROM conversations c 
     JOIN contacts_deprecated cd ON c.contact_id = cd.id
     WHERE c.organization_id = p.organization_id 
     AND cd.cliniko_patient_id = p.cliniko_patient_id
    ) as mapped_conversations
    
  FROM patients p
  WHERE p.organization_id = 'org_2xwHfNj6eaRUIX10aniXGvx7'
  LIMIT 5
)
SELECT 
  'SIMPLE RISK TEST' as check_type,
  sr.*
FROM simple_risk sr; 