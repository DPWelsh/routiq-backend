-- Patients View for Frontend
-- Provides comprehensive patient information with appointment statistics and activity status
-- Optimized for patient listing, searching, and management interfaces

CREATE OR REPLACE VIEW patients_summary AS
SELECT 
    p.id,
    p.organization_id,
    p.name,
    p.email,
    p.phone,
    p.contact_type,
    p.cliniko_patient_id,
    p.is_active,
    p.activity_status,
    
    -- Appointment counts
    p.recent_appointment_count,
    p.upcoming_appointment_count,
    p.total_appointment_count,
    
    -- Date information
    p.first_appointment_date,
    p.last_appointment_date,
    p.next_appointment_time,
    p.next_appointment_type,
    p.primary_appointment_type,
    
    -- Treatment information
    p.treatment_notes,
    
    -- JSON appointment arrays (for detailed views)
    p.recent_appointments,
    p.upcoming_appointments,
    
    -- Engagement metrics
    CASE 
        WHEN p.upcoming_appointment_count > 0 OR p.recent_appointment_count > 0 THEN 'engaged'
        WHEN p.total_appointment_count > 0 THEN 'inactive'
        ELSE 'never_engaged'
    END as engagement_status,
    
    -- Activity calculations
    CASE 
        WHEN p.next_appointment_time IS NOT NULL THEN 
            EXTRACT(DAYS FROM (p.next_appointment_time - NOW()))
        ELSE NULL
    END as days_until_next_appointment,
    
    CASE 
        WHEN p.last_appointment_date IS NOT NULL THEN 
            EXTRACT(DAYS FROM (NOW() - p.last_appointment_date))
        ELSE NULL
    END as days_since_last_appointment,
    
    -- Patient status indicators
    CASE 
        WHEN p.next_appointment_time IS NOT NULL AND p.next_appointment_time > NOW() THEN true
        ELSE false
    END as has_upcoming_appointment,
    
    CASE 
        WHEN p.last_appointment_date IS NOT NULL AND p.last_appointment_date >= NOW() - INTERVAL '30 days' THEN true
        ELSE false
    END as has_recent_appointment,
    
    -- Search and sync metadata
    p.search_date_from,
    p.search_date_to,
    p.last_synced_at,
    p.created_at,
    p.updated_at,
    
    -- Calculated fields for UI
    COALESCE(p.name, 'Unknown Patient') as display_name,
    COALESCE(p.email, p.phone, 'No contact info') as primary_contact,
    
    -- Status priority for sorting (lower number = higher priority)
    CASE 
        WHEN p.upcoming_appointment_count > 0 THEN 1
        WHEN p.recent_appointment_count > 0 THEN 2
        WHEN p.total_appointment_count > 0 THEN 3
        ELSE 4
    END as status_priority

FROM patients p
WHERE p.organization_id IS NOT NULL
ORDER BY 
    status_priority ASC,
    p.next_appointment_time ASC NULLS LAST,
    p.last_appointment_date DESC NULLS LAST,
    p.name ASC;

-- Grant access to the view
GRANT SELECT ON patients_summary TO PUBLIC;

-- Create indexes on the underlying table for better performance
-- (Only create if they don't already exist)
CREATE INDEX IF NOT EXISTS idx_patients_organization_id ON patients(organization_id);
CREATE INDEX IF NOT EXISTS idx_patients_is_active ON patients(is_active);
CREATE INDEX IF NOT EXISTS idx_patients_next_appointment ON patients(next_appointment_time);
CREATE INDEX IF NOT EXISTS idx_patients_last_appointment ON patients(last_appointment_date);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);
CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_cliniko_id ON patients(cliniko_patient_id); 