-- SurfRehab v2 - Supabase Schema
-- Clean, normalized schema for Cliniko + Chatwoot + ManyChat + Momence integration

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create contacts table (unified contact management)
CREATE TABLE IF NOT EXISTS public.contacts (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    phone character varying(20) NOT NULL,
    email character varying(255) NULL,
    name character varying(255) NULL,
    contact_type character varying(20) NOT NULL DEFAULT 'contact',
    
    -- Cliniko integration
    cliniko_patient_id text NULL,
    
    -- Status and metadata
    status character varying(50) NOT NULL DEFAULT 'active',
    metadata jsonb NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    deleted_at timestamp with time zone NULL,
    
    -- Organization (for multi-tenant support)
    organization_id text NULL,
    
    -- Constraints
    CONSTRAINT contacts_pkey PRIMARY KEY (id),
    CONSTRAINT contacts_phone_key UNIQUE (phone),
    CONSTRAINT contacts_cliniko_patient_id_key UNIQUE (cliniko_patient_id),
    
    -- Check constraints
    CONSTRAINT contacts_phone_format CHECK (phone ~ '^\+[0-9]{7,15}$'),
    CONSTRAINT contacts_contact_type_check CHECK (contact_type IN ('cliniko_patient', 'chatwoot_contact', 'contact')),
    CONSTRAINT contacts_status_check CHECK (status IN ('active', 'inactive', 'deleted'))
);

-- Create active_patients table (Cliniko appointment data)
CREATE TABLE IF NOT EXISTS public.active_patients (
    id bigserial NOT NULL,
    contact_id uuid NOT NULL,
    
    -- Appointment statistics
    recent_appointment_count integer NOT NULL DEFAULT 0,
    upcoming_appointment_count integer NOT NULL DEFAULT 0,
    total_appointment_count integer NOT NULL DEFAULT 0,
    last_appointment_date timestamp with time zone,
    
    -- Appointment details (JSON arrays)
    recent_appointments jsonb DEFAULT '[]',
    upcoming_appointments jsonb DEFAULT '[]',
    
    -- Search metadata
    search_date_from timestamp with time zone NOT NULL DEFAULT now(),
    search_date_to timestamp with time zone NOT NULL DEFAULT now(),
    
    -- Timestamps
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    
    -- Organization
    organization_id text NULL,
    
    -- Constraints
    CONSTRAINT active_patients_pkey PRIMARY KEY (id),
    CONSTRAINT active_patients_contact_id_key UNIQUE (contact_id),
    CONSTRAINT active_patients_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Create conversations table (Chatwoot + future integrations)
CREATE TABLE IF NOT EXISTS public.conversations (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    contact_id uuid,
    source character varying NOT NULL,
    external_id character varying UNIQUE,
    status character varying DEFAULT 'active',
    
    -- Sentiment analysis
    overall_sentiment character varying CHECK (overall_sentiment IS NULL OR (overall_sentiment IN ('positive', 'negative', 'neutral'))),
    sentiment_score numeric CHECK (sentiment_score IS NULL OR (sentiment_score >= -1.0 AND sentiment_score <= 1.0)),
    
    -- Quality and escalation
    quality_rating integer CHECK (quality_rating >= 1 AND quality_rating <= 5),
    escalation_flag boolean DEFAULT false,
    
    -- User feedback
    user_feedback_rating character varying CHECK (user_feedback_rating IS NULL OR (user_feedback_rating IN ('good', 'bad'))),
    user_feedback_note text,
    user_feedback_timestamp timestamp with time zone,
    
    -- Platform-specific IDs
    chatwoot_conversation_id bigint,
    phone_number character varying,
    cliniko_patient_id text,
    
    -- Metadata and timestamps
    metadata jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    organization_id text,
    
    CONSTRAINT conversations_pkey PRIMARY KEY (id),
    CONSTRAINT conversations_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Create messages table (conversation messages)
CREATE TABLE IF NOT EXISTS public.messages (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    conversation_id uuid NOT NULL,
    sender_type character varying NOT NULL CHECK (sender_type IN ('patient', 'agent', 'system', 'bot', 'user')),
    content text NOT NULL,
    timestamp timestamp with time zone DEFAULT now(),
    external_id character varying UNIQUE,
    
    -- Sentiment analysis
    sentiment_score numeric CHECK (sentiment_score IS NULL OR (sentiment_score >= -1.0 AND sentiment_score <= 1.0)),
    sentiment_label character varying CHECK (sentiment_label IS NULL OR (sentiment_label IN ('positive', 'negative', 'neutral', 'frustrated', 'satisfied', 'confused', 'angry', 'happy', 'upset', 'grateful'))),
    confidence_score numeric CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    analyzed_at timestamp with time zone,
    
    -- User feedback
    user_feedback_rating character varying CHECK (user_feedback_rating IS NULL OR (user_feedback_rating IN ('good', 'bad'))),
    user_feedback_note text,
    user_feedback_timestamp timestamp with time zone,
    
    -- Metadata and flags
    metadata jsonb DEFAULT '{}',
    is_private boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    organization_id text,
    
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Create appointments table (future Google Calendar integration)
CREATE TABLE IF NOT EXISTS public.appointments (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    contact_id uuid NOT NULL,
    appointment_date timestamp with time zone NOT NULL,
    status character varying DEFAULT 'scheduled',
    type character varying,
    notes text,
    
    -- External system IDs
    cliniko_appointment_id text,
    google_calendar_event_id text,
    
    -- Metadata
    metadata jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    organization_id text,
    
    CONSTRAINT appointments_pkey PRIMARY KEY (id),
    CONSTRAINT appointments_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Create organizations table (multi-tenant support)
CREATE TABLE IF NOT EXISTS public.organizations (
    id text NOT NULL DEFAULT uuid_generate_v4()::text,
    name character varying NOT NULL,
    slug character varying UNIQUE,
    display_name character varying,
    description text,
    
    -- Integration settings
    cliniko_instance_id character varying,
    chatwoot_account_id character varying,
    manychat_workspace_id character varying,
    
    -- Billing
    stripe_customer_id character varying UNIQUE,
    subscription_status character varying DEFAULT 'trial' CHECK (subscription_status IN ('trial', 'active', 'past_due', 'canceled', 'suspended')),
    subscription_plan character varying DEFAULT 'basic' CHECK (subscription_plan IN ('basic', 'pro', 'enterprise', 'custom')),
    billing_email character varying,
    
    -- Settings
    settings jsonb DEFAULT '{}',
    timezone character varying DEFAULT 'UTC',
    locale character varying DEFAULT 'en-US',
    
    -- Contact info
    phone character varying,
    website character varying,
    address jsonb DEFAULT '{}',
    
    -- Status and dates
    status character varying DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    onboarded_at timestamp with time zone,
    trial_ends_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    
    CONSTRAINT organizations_pkey PRIMARY KEY (id)
);

-- Create sync_logs table (API sync tracking)
CREATE TABLE IF NOT EXISTS public.sync_logs (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    source_system character varying NOT NULL,
    operation_type character varying NOT NULL,
    status character varying NOT NULL,
    records_processed integer DEFAULT 0,
    records_success integer DEFAULT 0,
    records_failed integer DEFAULT 0,
    error_details jsonb DEFAULT '{}',
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    metadata jsonb DEFAULT '{}',
    organization_id text,
    
    CONSTRAINT sync_logs_pkey PRIMARY KEY (id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON public.contacts (phone);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON public.contacts (email);
CREATE INDEX IF NOT EXISTS idx_contacts_cliniko_patient_id ON public.contacts (cliniko_patient_id);
CREATE INDEX IF NOT EXISTS idx_contacts_contact_type ON public.contacts (contact_type);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON public.contacts (status);
CREATE INDEX IF NOT EXISTS idx_contacts_organization_id ON public.contacts (organization_id);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON public.contacts (created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_metadata_source ON public.contacts ((metadata->>'source'));
CREATE INDEX IF NOT EXISTS idx_contacts_metadata_gin ON public.contacts USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_active_patients_contact_id ON public.active_patients (contact_id);
CREATE INDEX IF NOT EXISTS idx_active_patients_organization_id ON public.active_patients (organization_id);
CREATE INDEX IF NOT EXISTS idx_active_patients_last_appointment_date ON public.active_patients (last_appointment_date);

CREATE INDEX IF NOT EXISTS idx_conversations_contact_id ON public.conversations (contact_id);
CREATE INDEX IF NOT EXISTS idx_conversations_source ON public.conversations (source);
CREATE INDEX IF NOT EXISTS idx_conversations_external_id ON public.conversations (external_id);
CREATE INDEX IF NOT EXISTS idx_conversations_chatwoot_conversation_id ON public.conversations (chatwoot_conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_organization_id ON public.conversations (organization_id);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_type ON public.messages (sender_type);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON public.messages (timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_organization_id ON public.messages (organization_id);

CREATE INDEX IF NOT EXISTS idx_appointments_contact_id ON public.appointments (contact_id);
CREATE INDEX IF NOT EXISTS idx_appointments_appointment_date ON public.appointments (appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON public.appointments (status);
CREATE INDEX IF NOT EXISTS idx_appointments_organization_id ON public.appointments (organization_id);

CREATE INDEX IF NOT EXISTS idx_sync_logs_source_system ON public.sync_logs (source_system);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON public.sync_logs (status);
CREATE INDEX IF NOT EXISTS idx_sync_logs_started_at ON public.sync_logs (started_at);
CREATE INDEX IF NOT EXISTS idx_sync_logs_organization_id ON public.sync_logs (organization_id);

-- Add table comments
COMMENT ON TABLE public.contacts IS 'Unified contacts from all sources (Cliniko, Chatwoot, etc.)';
COMMENT ON TABLE public.active_patients IS 'Contacts with recent/upcoming appointments from Cliniko';
COMMENT ON TABLE public.conversations IS 'Conversations from Chatwoot and other messaging platforms';
COMMENT ON TABLE public.messages IS 'Individual messages within conversations';
COMMENT ON TABLE public.appointments IS 'Appointments from Cliniko and Google Calendar';
COMMENT ON TABLE public.organizations IS 'Multi-tenant organization management';
COMMENT ON TABLE public.sync_logs IS 'API synchronization audit logs'; 