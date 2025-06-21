-- SQL Migration: Enhance Patient Visibility
-- Add fields for appointment type, next appointment time, and treatment notes

-- Add treatment notes field to active_patients table
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS treatment_notes TEXT;
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS next_appointment_type VARCHAR(255);
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS next_appointment_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS primary_appointment_type VARCHAR(255);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_active_patients_next_appointment_time ON active_patients (next_appointment_time);
CREATE INDEX IF NOT EXISTS idx_active_patients_next_appointment_type ON active_patients (next_appointment_type);
CREATE INDEX IF NOT EXISTS idx_active_patients_primary_appointment_type ON active_patients (primary_appointment_type);

-- Add treatment notes to contacts table for additional context
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_treatment_note TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS treatment_summary TEXT;

-- Create index for treatment notes search
CREATE INDEX IF NOT EXISTS idx_contacts_treatment_notes_gin ON contacts USING gin (to_tsvector('english', last_treatment_note));

-- Update the patient_overview view to include new fields
DROP VIEW IF EXISTS patient_overview;
CREATE OR REPLACE VIEW patient_overview AS
SELECT 
    c.id,
    c.name,
    c.phone,
    c.email,
    c.contact_type,
    c.cliniko_patient_id,
    c.status,
    c.created_at,
    c.organization_id,
    c.last_treatment_note,
    c.treatment_summary,
    
    -- Active patient data (if exists)
    ap.recent_appointment_count,
    ap.upcoming_appointment_count,
    ap.total_appointment_count,
    ap.last_appointment_date,
    ap.next_appointment_time,
    ap.next_appointment_type,
    ap.primary_appointment_type,
    ap.treatment_notes,
    
    -- Source information
    c.metadata->>'source' as source,
    
    -- Calculated fields
    CASE 
        WHEN ap.id IS NOT NULL THEN true 
        ELSE false 
    END as is_active_patient,
    
    CASE 
        WHEN ap.upcoming_appointment_count > 0 THEN 'scheduled'
        WHEN ap.recent_appointment_count > 0 THEN 'recent'
        ELSE 'inactive'
    END as appointment_status,
    
    -- Next appointment info
    CASE 
        WHEN ap.next_appointment_time IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (ap.next_appointment_time - NOW()))/3600
        ELSE NULL
    END as hours_until_next_appointment
    
FROM contacts c
LEFT JOIN active_patients ap ON c.id = ap.contact_id
WHERE c.deleted_at IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN active_patients.treatment_notes IS 'Latest treatment notes from most recent appointment';
COMMENT ON COLUMN active_patients.next_appointment_type IS 'Type of the next scheduled appointment';
COMMENT ON COLUMN active_patients.next_appointment_time IS 'Date and time of next scheduled appointment';
COMMENT ON COLUMN active_patients.primary_appointment_type IS 'Most common appointment type for this patient'; 