-- SurfRehab v2 - Multi-Tenant SaaS Enhancements
-- Additional tables and constraints for Clerk.com integration

-- Create users table (synced from Clerk)
CREATE TABLE IF NOT EXISTS public.users (
    id text NOT NULL,  -- Clerk user ID
    email character varying NOT NULL,
    first_name character varying,
    last_name character varying,
    image_url character varying,
    
    -- Clerk metadata
    clerk_created_at timestamp with time zone,
    clerk_updated_at timestamp with time zone,
    
    -- App-specific fields
    role character varying DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    timezone character varying DEFAULT 'UTC',
    preferences jsonb DEFAULT '{}',
    last_login_at timestamp with time zone,
    
    -- Standard timestamps
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email)
);

-- Create organization_members table (many-to-many: users ↔ organizations)
CREATE TABLE IF NOT EXISTS public.organization_members (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    organization_id text NOT NULL,
    user_id text NOT NULL,
    
    -- Role within this specific organization
    role character varying DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    
    -- Permissions
    permissions jsonb DEFAULT '{}',
    
    -- Status
    status character varying DEFAULT 'active' CHECK (status IN ('active', 'invited', 'suspended')),
    
    -- Metadata
    invited_by text,
    invited_at timestamp with time zone,
    joined_at timestamp with time zone,
    
    -- Timestamps
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    
    CONSTRAINT organization_members_pkey PRIMARY KEY (id),
    CONSTRAINT organization_members_org_user_unique UNIQUE (organization_id, user_id),
    CONSTRAINT organization_members_organization_fkey FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT organization_members_user_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT organization_members_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES users(id)
);

-- Create api_credentials table (encrypted storage for org-specific API keys)
CREATE TABLE IF NOT EXISTS public.api_credentials (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    organization_id text NOT NULL,
    
    -- Service identification
    service_name character varying NOT NULL,  -- 'cliniko', 'chatwoot', 'manychat', etc.
    service_instance character varying,       -- 'au4', 'account_123', etc.
    
    -- Encrypted credentials (use pgcrypto or app-level encryption)
    credentials_encrypted jsonb NOT NULL,    -- Encrypted API keys, tokens, etc.
    
    -- Configuration
    is_active boolean DEFAULT true,
    last_validated_at timestamp with time zone,
    validation_error text,
    
    -- Metadata
    created_by text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    
    CONSTRAINT api_credentials_pkey PRIMARY KEY (id),
    CONSTRAINT api_credentials_org_service_unique UNIQUE (organization_id, service_name),
    CONSTRAINT api_credentials_organization_fkey FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT api_credentials_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Create audit_logs table (track all user actions across organizations)
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    organization_id text,
    user_id text,
    
    -- Action details
    action character varying NOT NULL,        -- 'sync_data', 'view_patients', 'export_data', etc.
    resource_type character varying,          -- 'contact', 'message', 'organization', etc.
    resource_id character varying,            -- ID of the affected resource
    
    -- Context
    ip_address inet,
    user_agent text,
    session_id character varying,
    
    -- Details
    details jsonb DEFAULT '{}',
    success boolean DEFAULT true,
    error_message text,
    
    -- Timestamp
    created_at timestamp with time zone DEFAULT now(),
    
    CONSTRAINT audit_logs_pkey PRIMARY KEY (id),
    CONSTRAINT audit_logs_organization_fkey FOREIGN KEY (organization_id) REFERENCES organizations(id),
    CONSTRAINT audit_logs_user_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Add Row Level Security (RLS) for data isolation
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for contacts table
CREATE POLICY contacts_organization_isolation ON contacts
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id', true));

-- RLS Policies for active_patients table  
CREATE POLICY active_patients_organization_isolation ON active_patients
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id', true));

-- RLS Policies for conversations table
CREATE POLICY conversations_organization_isolation ON conversations
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id', true));

-- RLS Policies for messages table
CREATE POLICY messages_organization_isolation ON messages
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id', true));

-- RLS Policies for appointments table
CREATE POLICY appointments_organization_isolation ON appointments
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id', true));

-- Add indexes for multi-tenant performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users (created_at);

CREATE INDEX IF NOT EXISTS idx_organization_members_organization_id ON public.organization_members (organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON public.organization_members (user_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_role ON public.organization_members (role);
CREATE INDEX IF NOT EXISTS idx_organization_members_status ON public.organization_members (status);

CREATE INDEX IF NOT EXISTS idx_api_credentials_organization_id ON public.api_credentials (organization_id);
CREATE INDEX IF NOT EXISTS idx_api_credentials_service_name ON public.api_credentials (service_name);
CREATE INDEX IF NOT EXISTS idx_api_credentials_is_active ON public.api_credentials (is_active);

CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON public.audit_logs (organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs (created_at);

-- Add table comments
COMMENT ON TABLE public.users IS 'Users synced from Clerk.com authentication';
COMMENT ON TABLE public.organization_members IS 'Many-to-many relationship between users and organizations';
COMMENT ON TABLE public.api_credentials IS 'Encrypted API credentials for each organization';
COMMENT ON TABLE public.audit_logs IS 'Audit trail of all user actions across the platform'; 