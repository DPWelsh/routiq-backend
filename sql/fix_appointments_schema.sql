 -- =============================================================================
-- FIX APPOINTMENTS TABLE SCHEMA
-- Update to work with new patients table instead of contacts_deprecated
-- =============================================================================

-- Step 1: Add patient_id column to appointments table
ALTER TABLE appointments 
ADD COLUMN IF NOT EXISTS patient_id UUID;

-- Step 2: Create index for the new patient_id column
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id 
ON appointments (patient_id);

-- Step 3: Populate patient_id from existing contact_id where possible
-- This links appointments to patients via the old contacts_deprecated table
UPDATE appointments 
SET patient_id = p.id
FROM patients p
JOIN contacts_deprecated c ON c.cliniko_patient_id = p.cliniko_patient_id
WHERE appointments.contact_id = c.id 
AND appointments.patient_id IS NULL
AND p.organization_id = appointments.organization_id;

-- Step 4: Add foreign key constraint to patients table
ALTER TABLE appointments 
ADD CONSTRAINT appointments_patient_id_fkey 
FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE;

-- Step 5: Update indexes for better performance
CREATE INDEX IF NOT EXISTS idx_appointments_patient_org 
ON appointments (patient_id, organization_id, appointment_date);

CREATE INDEX IF NOT EXISTS idx_appointments_date_range 
ON appointments (organization_id, appointment_date DESC) 
WHERE deleted_at IS NULL;

-- Step 6: Add constraint to ensure appointments have either contact_id OR patient_id
ALTER TABLE appointments 
ADD CONSTRAINT appointments_must_have_contact_or_patient 
CHECK (contact_id IS NOT NULL OR patient_id IS NOT NULL);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON COLUMN appointments.patient_id IS 'Links to patients table (new schema)';
COMMENT ON COLUMN appointments.contact_id IS 'Links to contacts_deprecated table (legacy)';
COMMENT ON CONSTRAINT appointments_must_have_contact_or_patient ON appointments 
IS 'Ensures appointments are linked to either legacy contacts or new patients';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check how many appointments are linked to patients vs contacts
SELECT 
    COUNT(*) as total_appointments,
    COUNT(patient_id) as linked_to_patients,
    COUNT(contact_id) as linked_to_contacts,
    COUNT(*) FILTER (WHERE patient_id IS NOT NULL AND contact_id IS NOT NULL) as linked_to_both,
    COUNT(*) FILTER (WHERE patient_id IS NULL AND contact_id IS NULL) as orphaned
FROM appointments;