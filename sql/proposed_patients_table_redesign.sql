-- PROPOSED PATIENTS TABLE REDESIGN
-- Consolidate active_patients and contacts into a unified patients table

-- Step 1: Create new unified patients table
CREATE TABLE patients_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL,
    
    -- Core patient information (from contacts)
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    contact_type TEXT DEFAULT 'cliniko_patient',
    cliniko_patient_id TEXT, -- Reference to Cliniko patient ID
    
    -- Activity status
    is_active BOOLEAN DEFAULT FALSE,
    activity_status TEXT, -- 'active', 'recently_active', 'upcoming_only', 'inactive'
    
    -- Appointment statistics
    recent_appointment_count INTEGER DEFAULT 0,
    upcoming_appointment_count INTEGER DEFAULT 0,
    total_appointment_count INTEGER DEFAULT 0,
    
    -- Appointment timing
    first_appointment_date TIMESTAMPTZ,
    last_appointment_date TIMESTAMPTZ,
    next_appointment_time TIMESTAMPTZ,
    
    -- Enhanced patient visibility fields
    next_appointment_type TEXT,
    primary_appointment_type TEXT,
    treatment_notes TEXT,
    
    -- Appointment data (JSON for detailed analysis)
    recent_appointments JSONB DEFAULT '[]'::jsonb,
    upcoming_appointments JSONB DEFAULT '[]'::jsonb,
    
    -- Sync metadata
    search_date_from TIMESTAMPTZ,
    search_date_to TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(organization_id, cliniko_patient_id),
    UNIQUE(organization_id, phone) -- Assuming phone is unique per org
);

-- Indexes for performance
CREATE INDEX idx_patients_new_org_id ON patients_new(organization_id);
CREATE INDEX idx_patients_new_is_active ON patients_new(organization_id, is_active);
CREATE INDEX idx_patients_new_activity_status ON patients_new(organization_id, activity_status);
CREATE INDEX idx_patients_new_cliniko_id ON patients_new(cliniko_patient_id);
CREATE INDEX idx_patients_new_next_appt ON patients_new(organization_id, next_appointment_time) WHERE next_appointment_time IS NOT NULL;
CREATE INDEX idx_patients_new_primary_type ON patients_new(organization_id, primary_appointment_type) WHERE primary_appointment_type IS NOT NULL;

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_patients_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER patients_updated_at_trigger
    BEFORE UPDATE ON patients_new
    FOR EACH ROW
    EXECUTE FUNCTION update_patients_updated_at();

-- Migration script to populate new table
INSERT INTO patients_new (
    organization_id,
    name,
    email,
    phone,
    contact_type,
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
    recent_appointments,
    upcoming_appointments,
    search_date_from,
    search_date_to,
    last_synced_at,
    created_at,
    updated_at
)
SELECT 
    c.organization_id,
    c.name,
    c.email,
    c.phone,
    c.contact_type,
    c.cliniko_patient_id,
    
    -- Determine if patient is active
    CASE 
        WHEN ap.recent_appointment_count > 0 OR ap.upcoming_appointment_count > 0 THEN TRUE
        ELSE FALSE
    END as is_active,
    
    -- Determine activity status
    CASE 
        WHEN ap.recent_appointment_count > 0 AND ap.upcoming_appointment_count > 0 THEN 'active'
        WHEN ap.recent_appointment_count > 0 AND ap.upcoming_appointment_count = 0 THEN 'recently_active'
        WHEN ap.recent_appointment_count = 0 AND ap.upcoming_appointment_count > 0 THEN 'upcoming_only'
        ELSE 'inactive'
    END as activity_status,
    
    COALESCE(ap.recent_appointment_count, 0),
    COALESCE(ap.upcoming_appointment_count, 0),
    COALESCE(ap.total_appointment_count, 0),
    ap.last_appointment_date,
    ap.next_appointment_time,
    ap.next_appointment_type,
    ap.primary_appointment_type,
    ap.treatment_notes,
    COALESCE(ap.recent_appointments, '[]'::jsonb),
    COALESCE(ap.upcoming_appointments, '[]'::jsonb),
    ap.search_date_from,
    ap.search_date_to,
    NOW() as last_synced_at,
    c.created_at,
    GREATEST(c.updated_at, COALESCE(ap.updated_at, c.updated_at))
FROM contacts c
LEFT JOIN active_patients ap ON ap.contact_id = c.id
WHERE c.contact_type = 'cliniko_patient';

-- Views for backward compatibility and easy querying

-- Active patients view (replaces active_patients table)
CREATE VIEW active_patients_view AS
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
FROM patients_new 
WHERE is_active = TRUE;

-- All patients view (replaces contacts for patient queries)
CREATE VIEW all_patients_view AS
SELECT 
    id,
    organization_id,
    name,
    email,
    phone,
    cliniko_patient_id,
    is_active,
    activity_status,
    recent_appointment_count,
    upcoming_appointment_count,
    total_appointment_count,
    first_appointment_date,
    last_appointment_date,
    next_appointment_time,
    next_appointment_type,
    primary_appointment_type,
    treatment_notes,
    last_synced_at,
    created_at,
    updated_at
FROM patients_new;

-- Activity summary view
CREATE VIEW patient_activity_summary AS
SELECT 
    organization_id,
    activity_status,
    COUNT(*) as patient_count,
    AVG(total_appointment_count) as avg_appointments,
    COUNT(*) FILTER (WHERE next_appointment_time IS NOT NULL) as with_upcoming
FROM patients_new
GROUP BY organization_id, activity_status;

COMMENT ON TABLE patients_new IS 'Unified patients table combining contact info and activity data';
COMMENT ON COLUMN patients_new.is_active IS 'TRUE if patient has recent or upcoming appointments';
COMMENT ON COLUMN patients_new.activity_status IS 'Detailed activity classification: active, recently_active, upcoming_only, inactive';
COMMENT ON VIEW active_patients_view IS 'Backward-compatible view showing only active patients';
COMMENT ON VIEW all_patients_view IS 'Complete patient view with activity status';
COMMENT ON VIEW patient_activity_summary IS 'Summary statistics by activity status'; 