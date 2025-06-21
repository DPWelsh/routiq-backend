-- Add Enhanced Patient Visibility Columns
-- Migration to add appointment type, timing, and treatment notes columns

BEGIN;

-- Add enhanced columns to active_patients table
ALTER TABLE public.active_patients 
ADD COLUMN IF NOT EXISTS next_appointment_time timestamp with time zone,
ADD COLUMN IF NOT EXISTS next_appointment_type character varying(100),
ADD COLUMN IF NOT EXISTS primary_appointment_type character varying(100),
ADD COLUMN IF NOT EXISTS treatment_notes text;

-- Add enhanced columns to contacts table for treatment information
ALTER TABLE public.contacts 
ADD COLUMN IF NOT EXISTS last_treatment_note text,
ADD COLUMN IF NOT EXISTS treatment_summary text;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_active_patients_next_appointment_time 
ON public.active_patients (next_appointment_time) 
WHERE next_appointment_time IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_active_patients_next_appointment_type 
ON public.active_patients (next_appointment_type) 
WHERE next_appointment_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_active_patients_primary_appointment_type 
ON public.active_patients (primary_appointment_type) 
WHERE primary_appointment_type IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN active_patients.next_appointment_time IS 'Date and time of next scheduled appointment';
COMMENT ON COLUMN active_patients.next_appointment_type IS 'Type of the next scheduled appointment';
COMMENT ON COLUMN active_patients.primary_appointment_type IS 'Most common appointment type for this patient';
COMMENT ON COLUMN active_patients.treatment_notes IS 'Latest treatment notes and recommendations';
COMMENT ON COLUMN contacts.last_treatment_note IS 'Most recent treatment note for this contact';
COMMENT ON COLUMN contacts.treatment_summary IS 'Summary of treatment history and status';

COMMIT; 