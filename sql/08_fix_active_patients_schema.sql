-- SQL Migration: Fix Active Patients Schema
-- Add contact_id column and migrate existing data

-- Step 1: Add the contact_id column to active_patients table
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS contact_id UUID;

-- Step 2: Create or update contacts for existing active_patients records
-- Use DISTINCT ON to avoid duplicate phone numbers
INSERT INTO contacts (phone, email, name, cliniq_id, status, organization_id, metadata)
SELECT DISTINCT ON (ap.phone)
    ap.phone,
    ap.email,
    ap.name,
    ap.cliniko_patient_id,
    'active',
    ap.organization_id,
    jsonb_build_object('source', 'active_patients_migration', 'migrated_at', NOW())
FROM active_patients ap
WHERE ap.contact_id IS NULL 
AND ap.phone IS NOT NULL
ORDER BY ap.phone, ap.updated_at DESC
ON CONFLICT (phone) DO UPDATE SET
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    cliniq_id = EXCLUDED.cliniq_id,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Handle patients without phone numbers (using cliniko_patient_id)
INSERT INTO contacts (phone, email, name, cliniq_id, status, organization_id, metadata)
SELECT DISTINCT ON (ap.cliniko_patient_id)
    COALESCE(ap.phone, 'temp_' || ap.cliniko_patient_id), -- Temporary phone for patients without phone
    ap.email,
    ap.name,
    ap.cliniko_patient_id,
    'active',
    ap.organization_id,
    jsonb_build_object('source', 'active_patients_migration', 'migrated_at', NOW(), 'temp_phone', true)
FROM active_patients ap
WHERE ap.contact_id IS NULL 
AND ap.phone IS NULL 
AND ap.cliniko_patient_id IS NOT NULL
ORDER BY ap.cliniko_patient_id, ap.updated_at DESC
ON CONFLICT (phone) DO NOTHING;

-- Step 3: Update active_patients with contact_id references
UPDATE active_patients 
SET contact_id = c.id
FROM contacts c
WHERE active_patients.contact_id IS NULL
AND (
    (active_patients.phone IS NOT NULL AND c.phone = active_patients.phone) OR
    (active_patients.cliniko_patient_id IS NOT NULL AND c.cliniq_id = active_patients.cliniko_patient_id)
);

-- Step 4: Add the enhanced fields to active_patients table
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS treatment_notes TEXT;
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS next_appointment_type VARCHAR(255);
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS next_appointment_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE active_patients ADD COLUMN IF NOT EXISTS primary_appointment_type VARCHAR(255);

-- Step 5: Add treatment notes fields to contacts table
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_treatment_note TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS treatment_summary TEXT;

-- Step 6: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_active_patients_contact_id ON active_patients (contact_id);
CREATE INDEX IF NOT EXISTS idx_active_patients_next_appointment_time ON active_patients (next_appointment_time);
CREATE INDEX IF NOT EXISTS idx_active_patients_next_appointment_type ON active_patients (next_appointment_type);
CREATE INDEX IF NOT EXISTS idx_active_patients_primary_appointment_type ON active_patients (primary_appointment_type);
CREATE INDEX IF NOT EXISTS idx_contacts_treatment_notes_gin ON contacts USING gin (to_tsvector('english', last_treatment_note));

-- Step 7: Remove duplicate active_patients records before adding constraints
-- Keep only the most recent record for each contact_id

-- First, show what duplicates exist
DO $$
DECLARE
    duplicate_count INT;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT contact_id, COUNT(*)
        FROM active_patients 
        WHERE contact_id IS NOT NULL
        GROUP BY contact_id
        HAVING COUNT(*) > 1
    ) duplicates;
    
    RAISE NOTICE 'Found % contact_ids with duplicate active_patients records', duplicate_count;
END $$;

-- Remove duplicates, keeping the most recent
DELETE FROM active_patients 
WHERE id NOT IN (
    SELECT DISTINCT ON (contact_id) id
    FROM active_patients 
    WHERE contact_id IS NOT NULL
    ORDER BY contact_id, updated_at DESC, id DESC
);

-- Step 8: Add foreign key constraint (only if all records have contact_id)
DO $$
BEGIN
    -- Check if all active_patients have contact_id
    IF NOT EXISTS (SELECT 1 FROM active_patients WHERE contact_id IS NULL) THEN
        -- Add foreign key constraint
        ALTER TABLE active_patients 
        ADD CONSTRAINT active_patients_contact_id_fkey 
        FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE;
        
        -- Add unique constraint
        ALTER TABLE active_patients 
        ADD CONSTRAINT active_patients_contact_id_key 
        UNIQUE (contact_id);
    ELSE
        RAISE WARNING 'Some active_patients records still have NULL contact_id. Foreign key constraint not added.';
    END IF;
END $$;

-- Step 9: Update the patient_overview view to include new fields
DROP VIEW IF EXISTS patient_overview;
CREATE OR REPLACE VIEW patient_overview AS
SELECT 
    c.id,
    c.name,
    c.phone,
    c.email,
    c.cliniq_id as cliniko_patient_id,
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

-- Step 10: Add helpful comments
COMMENT ON COLUMN active_patients.contact_id IS 'Foreign key reference to contacts table';
COMMENT ON COLUMN active_patients.treatment_notes IS 'Latest treatment notes from most recent appointment';
COMMENT ON COLUMN active_patients.next_appointment_type IS 'Type of the next scheduled appointment';
COMMENT ON COLUMN active_patients.next_appointment_time IS 'Date and time of next scheduled appointment';
COMMENT ON COLUMN active_patients.primary_appointment_type IS 'Most common appointment type for this patient';

-- Step 11: Show migration results
DO $$
DECLARE
    total_active_patients INT;
    patients_with_contact_id INT;
    contacts_created INT;
BEGIN
    SELECT COUNT(*) INTO total_active_patients FROM active_patients;
    SELECT COUNT(*) INTO patients_with_contact_id FROM active_patients WHERE contact_id IS NOT NULL;
    SELECT COUNT(*) INTO contacts_created FROM contacts WHERE metadata->>'source' = 'active_patients_migration';
    
    RAISE NOTICE 'Migration Results:';
    RAISE NOTICE '- Total active patients: %', total_active_patients;
    RAISE NOTICE '- Patients with contact_id: %', patients_with_contact_id;
    RAISE NOTICE '- Contacts created during migration: %', contacts_created;
    
    IF patients_with_contact_id = total_active_patients THEN
        RAISE NOTICE '✅ Migration completed successfully!';
    ELSE
        RAISE WARNING '⚠️  Migration incomplete. % patients still missing contact_id', (total_active_patients - patients_with_contact_id);
    END IF;
END $$; 