-- Fix patients table unique constraint for proper conflict resolution
-- This enables the ON CONFLICT clause to work correctly in the sync

-- Add unique constraint on (organization_id, cliniko_patient_id)
-- This allows multiple organizations to have the same cliniko_patient_id
-- but prevents duplicates within the same organization
ALTER TABLE patients 
ADD CONSTRAINT patients_org_cliniko_patient_unique 
UNIQUE (organization_id, cliniko_patient_id);

-- Create index for performance on the composite key
CREATE INDEX IF NOT EXISTS idx_patients_org_cliniko_patient 
ON patients (organization_id, cliniko_patient_id);

-- Add comment
COMMENT ON CONSTRAINT patients_org_cliniko_patient_unique ON patients 
IS 'Ensures unique cliniko_patient_id per organization for proper sync conflict resolution'; 