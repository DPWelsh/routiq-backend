/*
===========================================
SIMPLE COMMUNICATION TRACKING
===========================================
Minimal table to track reengagement outreach attempts.
Start with manual data entry. Prove value before automation.

Replaces complex integration services:
- sms_tracking.py
- email_tracking.py  
- phone_tracking.py
*/

-- === OUTREACH LOG TABLE ===
CREATE TABLE IF NOT EXISTS outreach_log (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  patient_id uuid NOT NULL,
  organization_id text NOT NULL,
  
  -- === OUTREACH DETAILS ===
  method varchar(20) NOT NULL CHECK (method IN ('sms', 'email', 'phone', 'in_person', 'postal')),
  outcome varchar(20) NOT NULL CHECK (outcome IN ('success', 'no_response', 'failed', 'busy', 'voicemail', 'bounced', 'opted_out')),
  
  -- === METADATA ===
  notes text,
  attempted_by text, -- user_id who made the attempt
  
  -- === TIMESTAMPS ===
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  
  -- === CONSTRAINTS ===
  CONSTRAINT outreach_log_pkey PRIMARY KEY (id),
  CONSTRAINT outreach_log_patient_fkey FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
  CONSTRAINT outreach_log_organization_fkey FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

-- === PERFORMANCE INDEXES ===
-- Optimize for common queries
CREATE INDEX IF NOT EXISTS idx_outreach_log_patient_id ON outreach_log(patient_id);
CREATE INDEX IF NOT EXISTS idx_outreach_log_organization_id ON outreach_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_outreach_log_created_at ON outreach_log(created_at);
CREATE INDEX IF NOT EXISTS idx_outreach_log_method_outcome ON outreach_log(method, outcome);

-- Composite index for performance queries (removed temporal predicate - use application filtering)
CREATE INDEX IF NOT EXISTS idx_outreach_log_patient_recent ON outreach_log(patient_id, created_at DESC);

/*
===========================================
USAGE EXAMPLES
===========================================

-- Log a successful phone call:
INSERT INTO outreach_log (patient_id, organization_id, method, outcome, notes, attempted_by)
VALUES ('patient-uuid', 'org_id', 'phone', 'success', 'Scheduled follow-up appointment', 'user_id');

-- Log failed SMS attempt:
INSERT INTO outreach_log (patient_id, organization_id, method, outcome, notes, attempted_by)
VALUES ('patient-uuid', 'org_id', 'sms', 'no_response', 'No reply after 48 hours', 'user_id');

-- Query recent outreach for a patient:
SELECT method, outcome, notes, created_at 
FROM outreach_log 
WHERE patient_id = 'patient-uuid' 
ORDER BY created_at DESC 
LIMIT 10;
*/ 