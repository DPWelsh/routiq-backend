-- FIXED PATIENTS TABLE MIGRATION
-- Handles duplicate phone numbers and other edge cases

-- Step 1: Create unified patients table (without strict phone uniqueness)
CREATE TABLE patients_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL,
    
    -- Core patient information
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
    
    -- Constraints (relaxed to handle duplicates)
    UNIQUE(organization_id, cliniko_patient_id)
    -- Note: Removed phone uniqueness constraint due to shared family phones
);

-- Indexes for performance
CREATE INDEX idx_patients_new_org_id ON patients_new(organization_id);
CREATE INDEX idx_patients_new_is_active ON patients_new(organization_id, is_active);
CREATE INDEX idx_patients_new_activity_status ON patients_new(organization_id, activity_status);
CREATE INDEX idx_patients_new_cliniko_id ON patients_new(cliniko_patient_id);
CREATE INDEX idx_patients_new_phone ON patients_new(organization_id, phone) WHERE phone IS NOT NULL;
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

-- Step 2: Migration with duplicate handling
-- Use DISTINCT ON to handle duplicates by keeping the most recent record
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
SELECT DISTINCT ON (c.organization_id, COALESCE(c.cliniko_patient_id, c.id::text))
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
WHERE c.contact_type = 'cliniko_patient'
ORDER BY 
    c.organization_id, 
    COALESCE(c.cliniko_patient_id, c.id::text),
    c.updated_at DESC; -- Keep most recently updated record for duplicates

-- Step 3: Create views for backward compatibility

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

-- Duplicate phone analysis view (for monitoring)
CREATE VIEW duplicate_phone_analysis AS
SELECT 
    organization_id,
    phone,
    COUNT(*) as patient_count,
    STRING_AGG(name, ', ' ORDER BY name) as patient_names,
    STRING_AGG(id::text, ', ' ORDER BY name) as patient_ids
FROM patients_new
WHERE phone IS NOT NULL
GROUP BY organization_id, phone
HAVING COUNT(*) > 1;

-- Migration verification queries
DO $$
DECLARE
    contacts_count INTEGER;
    patients_count INTEGER;
    active_patients_count INTEGER;
    active_view_count INTEGER;
BEGIN
    -- Count original records
    SELECT COUNT(*) INTO contacts_count 
    FROM contacts 
    WHERE contact_type = 'cliniko_patient';
    
    SELECT COUNT(*) INTO active_patients_count 
    FROM active_patients;
    
    -- Count new records
    SELECT COUNT(*) INTO patients_count 
    FROM patients_new;
    
    SELECT COUNT(*) INTO active_view_count 
    FROM active_patients_view;
    
    -- Report migration results
    RAISE NOTICE '📊 MIGRATION RESULTS:';
    RAISE NOTICE '   Original contacts (patients): %', contacts_count;
    RAISE NOTICE '   Original active_patients: %', active_patients_count;
    RAISE NOTICE '   New patients table: %', patients_count;
    RAISE NOTICE '   Active patients view: %', active_view_count;
    
    IF patients_count < contacts_count THEN
        RAISE NOTICE '⚠️  Some duplicate records were consolidated';
    END IF;
    
    RAISE NOTICE '✅ Migration completed successfully!';
END $$;

-- Comments for documentation
COMMENT ON TABLE patients_new IS 'Unified patients table combining contact info and activity data';
COMMENT ON COLUMN patients_new.is_active IS 'TRUE if patient has recent or upcoming appointments';
COMMENT ON COLUMN patients_new.activity_status IS 'Detailed activity classification: active, recently_active, upcoming_only, inactive';
COMMENT ON VIEW active_patients_view IS 'Backward-compatible view showing only active patients';
COMMENT ON VIEW all_patients_view IS 'Complete patient view with activity status';
COMMENT ON VIEW patient_activity_summary IS 'Summary statistics by activity status';
COMMENT ON VIEW duplicate_phone_analysis IS 'Analysis of patients sharing phone numbers (families, etc.)'; 