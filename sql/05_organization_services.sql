-- Migration: Add organization_services table and configure Surf Rehab with Cliniko
-- This supports multi-tenant practice management system integration

-- Create organization_services table
CREATE TABLE IF NOT EXISTS public.organization_services (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  organization_id text NOT NULL,
  service_name character varying NOT NULL,
  service_config jsonb NULL DEFAULT '{}'::jsonb,
  is_primary boolean NULL DEFAULT false,
  is_active boolean NULL DEFAULT true,
  sync_enabled boolean NULL DEFAULT true,
  last_sync_at timestamp with time zone NULL,
  created_at timestamp with time zone NULL DEFAULT now(),
  CONSTRAINT organization_services_pkey PRIMARY KEY (id),
  CONSTRAINT organization_services_organization_id_service_name_key UNIQUE (organization_id, service_name),
  CONSTRAINT organization_services_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES organizations (id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_organization_services_org_id ON public.organization_services USING btree (organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_services_service_name ON public.organization_services USING btree (service_name);
CREATE INDEX IF NOT EXISTS idx_organization_services_active ON public.organization_services USING btree (is_active) WHERE is_active = true;

-- Insert Surf Rehab's Cliniko configuration
INSERT INTO public.organization_services (
  organization_id,
  service_name,
  service_config,
  is_primary,
  is_active,
  sync_enabled
) VALUES (
  'org_2xwHiNrj68eaRUlX10anlXGvzX7', -- Surf Rehab organization ID
  'cliniko',
  '{
    "region": "au4",
    "api_url": "https://api.au4.cliniko.com/v1",
    "features": ["patients", "appointments", "invoices"],
    "sync_schedule": "*/30 * * * *",
    "description": "Primary practice management system for patient bookings and medical records"
  }'::jsonb,
  true,  -- is_primary (main booking system)
  true,  -- is_active
  true   -- sync_enabled
) ON CONFLICT (organization_id, service_name) 
DO UPDATE SET
  service_config = EXCLUDED.service_config,
  is_primary = EXCLUDED.is_primary,
  is_active = EXCLUDED.is_active,
  sync_enabled = EXCLUDED.sync_enabled;

-- Verify the insert
SELECT 
  os.organization_id,
  o.name as organization_name,
  os.service_name,
  os.is_primary,
  os.is_active,
  os.sync_enabled,
  os.service_config,
  os.created_at
FROM organization_services os
JOIN organizations o ON o.id = os.organization_id
WHERE os.organization_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7';

-- Add comments for documentation
COMMENT ON TABLE public.organization_services IS 'Tracks which practice management systems each organization uses (Cliniko, Nookal, PracSuite, Momence, etc.)';
COMMENT ON COLUMN public.organization_services.service_name IS 'Practice management system name: cliniko, nookal, pracsuite, momence, etc.';
COMMENT ON COLUMN public.organization_services.service_config IS 'Service-specific configuration including API endpoints, features, sync schedules';
COMMENT ON COLUMN public.organization_services.is_primary IS 'Whether this is the primary/main booking system for the organization';
COMMENT ON COLUMN public.organization_services.sync_enabled IS 'Whether automatic syncing is enabled for this service';
COMMENT ON COLUMN public.organization_services.last_sync_at IS 'Timestamp of the last successful sync operation'; 