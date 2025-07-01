/*
===========================================
SIMPLIFIED SUPABASE RLS CONFIGURATION
===========================================
This version works without auth schema permissions
*/

-- ==========================================
-- 1. CONTEXT SETTING FUNCTIONS (NO AUTH SCHEMA)
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
-- 2. TESTING FUNCTIONS
-- ==========================================

-- Test webhook access
CREATE OR REPLACE FUNCTION test_webhook_access(test_org_id TEXT, test_role TEXT DEFAULT 'user')
RETURNS TABLE(
    operation TEXT,
    success BOOLEAN,
    result_count INTEGER,
    error_message TEXT
) AS $$
BEGIN
    -- Set test context
    PERFORM set_organization_context(test_org_id, test_role);
    
    -- Test webhook_logs SELECT
    BEGIN
        RETURN QUERY SELECT 
            'webhook_logs_select'::TEXT, 
            true, 
            (SELECT COUNT(*)::INTEGER FROM webhook_logs),
            'Success'::TEXT;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_logs_select'::TEXT, false, 0, SQLERRM;
    END;
    
    -- Test webhook_templates SELECT
    BEGIN
        RETURN QUERY SELECT 
            'webhook_templates_select'::TEXT, 
            true, 
            (SELECT COUNT(*)::INTEGER FROM webhook_templates),
            'Success'::TEXT;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_templates_select'::TEXT, false, 0, SQLERRM;
    END;
    
END;
$$ LANGUAGE plpgsql;

-- Create test webhook log
CREATE OR REPLACE FUNCTION create_test_webhook_log(org_id TEXT)
RETURNS UUID AS $$
DECLARE
    new_log_id UUID;
BEGIN
    -- Set context
    PERFORM set_organization_context(org_id, 'user');
    
    -- Insert test log
    INSERT INTO webhook_logs (
        organization_id,
        webhook_type,
        workflow_name,
        n8n_webhook_url,
        trigger_data,
        status,
        triggered_by_user_id,
        trigger_source
    ) VALUES (
        org_id,
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
CREATE OR REPLACE FUNCTION test_webhook_templates(org_id TEXT)
RETURNS TABLE(
    template_name TEXT,
    webhook_type TEXT,
    webhook_url TEXT
) AS $$
BEGIN
    -- Set context
    PERFORM set_organization_context(org_id, 'user');
    
    -- Return accessible templates
    RETURN QUERY 
    SELECT 
        wt.name,
        wt.webhook_type,
        wt.n8n_webhook_url
    FROM webhook_templates wt
    WHERE wt.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Cleanup test data
CREATE OR REPLACE FUNCTION cleanup_test_webhooks()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM webhook_logs WHERE webhook_type = 'test_webhook';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 3. VERIFICATION QUERIES
-- ==========================================

-- Check if RLS is enabled
CREATE OR REPLACE FUNCTION check_rls_status()
RETURNS TABLE(
    table_name TEXT,
    rls_enabled BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.tablename::TEXT,
        t.rowsecurity
    FROM pg_tables t
    WHERE t.schemaname = 'public' 
    AND t.tablename IN ('webhook_logs', 'webhook_templates', 'webhook_queue');
END;
$$ LANGUAGE plpgsql;

-- Check current context
CREATE OR REPLACE FUNCTION check_current_context()
RETURNS TABLE(
    setting_name TEXT,
    setting_value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'current_organization_id'::TEXT,
        get_current_organization();
    
    RETURN QUERY
    SELECT 
        'current_user_role'::TEXT,
        get_current_user_role();
END;
$$ LANGUAGE plpgsql;

/*
===========================================
STEP-BY-STEP TESTING INSTRUCTIONS
===========================================

1. First, run this entire script in Supabase SQL editor

2. Check RLS is enabled:
   SELECT * FROM check_rls_status();

3. Set your organization context (REPLACE 'your_org_id' with actual ID):
   SELECT set_organization_context('your_org_id', 'user');

4. Verify context is set:
   SELECT * FROM check_current_context();

5. Test webhook access:
   SELECT * FROM test_webhook_access('your_org_id', 'user');

6. Test webhook templates:
   SELECT * FROM test_webhook_templates('your_org_id');

7. Create test webhook log:
   SELECT create_test_webhook_log('your_org_id');

8. Verify the test log was created:
   SELECT set_organization_context('your_org_id', 'user');
   SELECT * FROM webhook_logs WHERE webhook_type = 'test_webhook';

9. Test admin access:
   SELECT * FROM test_webhook_access('your_org_id', 'admin');

10. Cleanup when done:
    SELECT cleanup_test_webhooks();

===========================================
*/ 