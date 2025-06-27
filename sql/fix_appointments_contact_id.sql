-- =============================================================================
-- FIX APPOINTMENTS TABLE - Make contact_id nullable
-- Since we're using patient_id instead of contact_id for new appointments
-- =============================================================================

-- Make contact_id nullable (it was required before but now we use patient_id)
ALTER TABLE appointments 
ALTER COLUMN contact_id DROP NOT NULL;

-- Verify the change
\d appointments; 