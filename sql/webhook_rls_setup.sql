/*
===========================================
SUPABASE RLS CONFIGURATION FOR WEBHOOKS
===========================================
Setup and testing for Row Level Security policies
*/

-- ==========================================
-- METHOD 1: SET UP RLS CONTEXT FUNCTIONS
-- ==========================================

-- Function to set organization context (call this from your app)
CREATE OR REPLACE FUNCTION set_organization_context(org_id TEXT, user_role TEXT DEFAULT 'user')
RETURNS void AS $$
BEGIN
    -- Set the organization ID for RLS
    PERFORM set_config('app.current_organization_id', org_id, true);
    
    -- Set the user role for admin access
    PERFORM set_config('app.user_role', user_role, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current organization context
CREATE OR REPLACE FUNCTION get_current_organization()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', true);
END;
$$ LANGUAGE plpgsql;

-- Function to get current user role
CREATE OR REPLACE FUNCTION get_current_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.user_role', true);
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- METHOD 2: AUTH HOOK INTEGRATION (RECOMMENDED)
-- ==========================================

-- Create function to automatically set context from JWT claims
CREATE OR REPLACE FUNCTION auth.set_webhook_context()
RETURNS void AS $$
DECLARE
    organization_id TEXT;
    user_role TEXT;
BEGIN
    -- Extract organization_id from JWT claims
    SELECT COALESCE(
        auth.jwt() ->> 'organization_id',
        auth.jwt() -> 'app_metadata' ->> 'organization_id',
        auth.jwt() -> 'user_metadata' ->> 'organization_id'
    ) INTO organization_id;
    
    -- Extract user role from JWT claims
    SELECT COALESCE(
        auth.jwt() ->> 'role',
        auth.jwt() -> 'app_metadata' ->> 'role',
        auth.jwt() -> 'user_metadata' ->> 'role',
        'user'
    ) INTO user_role;
    
    -- Set the context for RLS
    IF organization_id IS NOT NULL THEN
        PERFORM set_config('app.current_organization_id', organization_id, true);
    END IF;
    
    PERFORM set_config('app.user_role', user_role, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ==========================================
-- METHOD 3: MANUAL TESTING FUNCTIONS
-- ==========================================

-- Test function to simulate different user contexts
CREATE OR REPLACE FUNCTION test_webhook_access(
    test_org_id TEXT,
    test_role TEXT DEFAULT 'user'
)
RETURNS TABLE(
    table_name TEXT,
    can_select BOOLEAN,
    can_insert BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    test_result RECORD;
BEGIN
    -- Set test context
    PERFORM set_organization_context(test_org_id, test_role);
    
    -- Test webhook_logs access
    BEGIN
        PERFORM COUNT(*) FROM webhook_logs;
        RETURN QUERY SELECT 'webhook_logs'::TEXT, true, false, NULL::TEXT;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_logs'::TEXT, false, false, SQLERRM;
    END;
    
    -- Test webhook_logs insert
    BEGIN
        INSERT INTO webhook_logs (organization_id, webhook_type, workflow_name, n8n_webhook_url)
        VALUES (test_org_id, 'test', 'test_workflow', 'https://test.com')
        ON CONFLICT DO NOTHING;
        RETURN QUERY SELECT 'webhook_logs'::TEXT, true, true, 'Insert successful'::TEXT;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_logs'::TEXT, true, false, SQLERRM;
    END;
    
    -- Test webhook_templates access
    BEGIN
        PERFORM COUNT(*) FROM webhook_templates;
        RETURN QUERY SELECT 'webhook_templates'::TEXT, true, false, NULL::TEXT;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_templates'::TEXT, false, false, SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- RLS TESTING SCENARIOS
-- ==========================================

-- Test scenario 1: Regular user access
CREATE OR REPLACE FUNCTION test_regular_user_access()
RETURNS TABLE(
    scenario TEXT,
    organization_id TEXT,
    role TEXT,
    webhook_logs_count INTEGER,
    templates_count INTEGER,
    success BOOLEAN
) AS $$
BEGIN
    -- Test with organization 'org_123'
    PERFORM set_organization_context('org_123', 'user');
    
    RETURN QUERY SELECT 
        'regular_user'::TEXT,
        'org_123'::TEXT,
        'user'::TEXT,
        (SELECT COUNT(*)::INTEGER FROM webhook_logs),
        (SELECT COUNT(*)::INTEGER FROM webhook_templates),
        true;
END;
$$ LANGUAGE plpgsql;

-- Test scenario 2: Admin user access
CREATE OR REPLACE FUNCTION test_admin_user_access()
RETURNS TABLE(
    scenario TEXT,
    organization_id TEXT,
    role TEXT,
    webhook_logs_count INTEGER,
    templates_count INTEGER,
    success BOOLEAN
) AS $$
BEGIN
    -- Test with admin role
    PERFORM set_organization_context('org_123', 'admin');
    
    RETURN QUERY SELECT 
        'admin_user'::TEXT,
        'org_123'::TEXT,
        'admin'::TEXT,
        (SELECT COUNT(*)::INTEGER FROM webhook_logs),
        (SELECT COUNT(*)::INTEGER FROM webhook_templates),
        true;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- WEBHOOK TESTING HELPERS
-- ==========================================

-- Create test webhook log entry
CREATE OR REPLACE FUNCTION create_test_webhook_log(
    org_id TEXT,
    patient_uuid UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    new_log_id UUID;
BEGIN
    -- Set context
    PERFORM set_organization_context(org_id, 'user');
    
    -- Insert test log
    INSERT INTO webhook_logs (
        organization_id,
        patient_id,
        webhook_type,
        workflow_name,
        n8n_webhook_url,
        trigger_data,
        status,
        triggered_by_user_id,
        trigger_source
    ) VALUES (
        org_id,
        patient_uuid,
        'test_webhook',
        'test_workflow',
        'https://test-n8n.com/webhook/test',
        '{"test": "data"}'::jsonb,
        'pending',
        'test_user_123',
        'dashboard'
    ) RETURNING id INTO new_log_id;
    
    RETURN new_log_id;
END;
$$ LANGUAGE plpgsql;

-- Test webhook template access
CREATE OR REPLACE FUNCTION test_webhook_template_access(org_id TEXT)
RETURNS TABLE(
    template_name TEXT,
    webhook_type TEXT,
    is_accessible BOOLEAN
) AS $$
BEGIN
    -- Set context
    PERFORM set_organization_context(org_id, 'user');
    
    -- Return accessible templates
    RETURN QUERY 
    SELECT 
        wt.name,
        wt.webhook_type,
        true
    FROM webhook_templates wt
    WHERE wt.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- CLEANUP FUNCTIONS
-- ==========================================

-- Clean up test data
CREATE OR REPLACE FUNCTION cleanup_test_webhooks()
RETURNS void AS $$
BEGIN
    DELETE FROM webhook_logs WHERE webhook_type = 'test_webhook';
    DELETE FROM webhook_templates WHERE name LIKE 'test_%';
END;
$$ LANGUAGE plpgsql;

/*
===========================================
USAGE INSTRUCTIONS
===========================================

1. SET CONTEXT IN YOUR APPLICATION:
   SELECT set_organization_context('your_org_id', 'user');

2. TEST RLS POLICIES:
   SELECT * FROM test_regular_user_access();
   SELECT * FROM test_admin_user_access();

3. TEST WEBHOOK ACCESS:
   SELECT * FROM test_webhook_access('your_org_id', 'user');

4. CREATE TEST DATA:
   SELECT create_test_webhook_log('your_org_id');

5. VERIFY TEMPLATE ACCESS:
   SELECT * FROM test_webhook_template_access('your_org_id');

6. CLEANUP:
   SELECT cleanup_test_webhooks();
*/ 