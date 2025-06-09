-- Fix contacts schema for multi-channel support
-- This addresses the hanging query issue by making phone nullable

-- 1. Make phone field nullable for multi-channel flexibility
ALTER TABLE contacts ALTER COLUMN phone DROP NOT NULL;

-- 2. Drop the existing unique constraint on phone
ALTER TABLE contacts DROP CONSTRAINT contacts_phone_key;

-- 3. Create partial unique index (only for non-null phone numbers)
CREATE UNIQUE INDEX contacts_phone_key ON contacts (phone) WHERE phone IS NOT NULL;

-- 4. Add enhanced schema fields if they don't exist
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS patient_status character varying;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS medical_record_number character varying;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS external_ids jsonb DEFAULT '{}';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS primary_source character varying;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS source_systems character varying[] DEFAULT '{}';

-- 5. Add new constraints for the enhanced fields
DO $$
BEGIN
    -- Add unique constraint for medical record number (partial)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'contacts_medical_record_number_key') THEN
        CREATE UNIQUE INDEX contacts_medical_record_number_key ON contacts (medical_record_number) WHERE medical_record_number IS NOT NULL;
    END IF;

    -- Add check constraint for patient_status
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'contacts_patient_status_check') THEN
        ALTER TABLE contacts ADD CONSTRAINT contacts_patient_status_check 
        CHECK (patient_status IS NULL OR patient_status IN ('active', 'inactive', 'discharged', 'referred'));
    END IF;
END $$;

-- 6. Add channel-specific identifier index
CREATE INDEX IF NOT EXISTS idx_contacts_external_ids_channels 
ON contacts USING GIN ((external_ids->'channels'));

-- 7. Add indexes for the new fields
CREATE INDEX IF NOT EXISTS idx_contacts_patient_status ON contacts (patient_status);
CREATE INDEX IF NOT EXISTS idx_contacts_primary_source ON contacts (primary_source);
CREATE INDEX IF NOT EXISTS idx_contacts_source_systems ON contacts USING GIN (source_systems);

-- 8. Update the phone format check to be less restrictive (allow nulls)
ALTER TABLE contacts DROP CONSTRAINT IF EXISTS contacts_phone_format;
ALTER TABLE contacts ADD CONSTRAINT contacts_phone_format 
CHECK (phone IS NULL OR phone ~ '^\+[0-9]{7,15}$');

COMMENT ON TABLE contacts IS 'Multi-channel unified contacts from all sources (Cliniko, WhatsApp, Instagram, etc.)'; 