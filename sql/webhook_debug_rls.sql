/*
===========================================
WEBHOOK RLS DEBUGGING SCRIPT
===========================================
Let's debug this step by step
*/

-- ==========================================
-- STEP 1: CHECK IF TABLES EXIST
-- ==========================================
SELECT 'webhook_logs' as table_name, 
       EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'webhook_logs') as exists;
       
SELECT 'webhook_templates' as table_name,
       EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'webhook_templates') as exists;

-- ==========================================
-- STEP 2: CHECK RLS STATUS
-- ==========================================
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE tablename IN ('webhook_logs', 'webhook_templates', 'webhook_queue')
AND schemaname = 'public';

-- ==========================================
-- STEP 3: CHECK RLS POLICIES
-- ==========================================
SELECT 
    schemaname,
    tablename, 
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE tablename IN ('webhook_logs', 'webhook_templates', 'webhook_queue');

-- ==========================================
-- STEP 4: TEST CONTEXT SETTING (SIMPLE)
-- ==========================================

-- First, let's test setting config directly
SELECT set_config('app.current_organization_id', 'org_2xwiHJY6BaRUIX1DanXG6ZX7', true);
SELECT set_config('app.user_role', 'user', true);

-- Check if it's set
SELECT current_setting('app.current_organization_id', true) as org_id;
SELECT current_setting('app.user_role', true) as user_role;

-- ==========================================
-- STEP 5: TEST BASIC ACCESS WITHOUT RLS
-- ==========================================

-- Temporarily disable RLS to see if tables work
ALTER TABLE webhook_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_templates DISABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_queue DISABLE ROW LEVEL SECURITY;

-- Test basic table access
SELECT COUNT(*) as webhook_logs_count FROM webhook_logs;
SELECT COUNT(*) as webhook_templates_count FROM webhook_templates;

-- Check what webhook templates exist
SELECT name, webhook_type, organization_id, is_active FROM webhook_templates;

-- ==========================================
-- STEP 6: RE-ENABLE RLS AND TEST
-- ==========================================

-- Re-enable RLS
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_queue ENABLE ROW LEVEL SECURITY;

-- Set context again
SELECT set_config('app.current_organization_id', 'org_2xwiHJY6BaRUIX1DanXG6ZX7', true);
SELECT set_config('app.user_role', 'user', true);

-- Test access with RLS enabled
SELECT COUNT(*) as webhook_logs_count_with_rls FROM webhook_logs;
SELECT COUNT(*) as webhook_templates_count_with_rls FROM webhook_templates;

-- ==========================================
-- STEP 7: TEST SPECIFIC ORGANIZATION ACCESS
-- ==========================================

-- Check what organization_id values exist in templates
SELECT DISTINCT organization_id FROM webhook_templates WHERE organization_id IS NOT NULL;

-- Test with NULL organization_id (global templates)
SELECT name, webhook_type, organization_id FROM webhook_templates WHERE organization_id IS NULL;

-- ==========================================
-- STEP 8: SIMPLIFIED WORKING FUNCTIONS
-- ==========================================

-- Simple function that definitely works
CREATE OR REPLACE FUNCTION test_simple_access(org_id TEXT)
RETURNS TABLE(
    test_name TEXT,
    result TEXT
) AS $$
BEGIN
    -- Set context
    PERFORM set_config('app.current_organization_id', org_id, true);
    PERFORM set_config('app.user_role', 'user', true);
    
    -- Test 1: Check context is set
    RETURN QUERY SELECT 'context_org_id'::TEXT, current_setting('app.current_organization_id', true);
    RETURN QUERY SELECT 'context_user_role'::TEXT, current_setting('app.user_role', true);
    
    -- Test 2: Try to access tables
    BEGIN
        RETURN QUERY SELECT 'webhook_logs_access'::TEXT, 'SUCCESS - Count: ' || COUNT(*)::TEXT FROM webhook_logs;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_logs_access'::TEXT, 'ERROR: ' || SQLERRM;
    END;
    
    BEGIN
        RETURN QUERY SELECT 'webhook_templates_access'::TEXT, 'SUCCESS - Count: ' || COUNT(*)::TEXT FROM webhook_templates;
    EXCEPTION WHEN others THEN
        RETURN QUERY SELECT 'webhook_templates_access'::TEXT, 'ERROR: ' || SQLERRM;
    END;
    
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- STEP 9: TEST INSERT CAPABILITY  
-- ==========================================

CREATE OR REPLACE FUNCTION test_insert_webhook_log(org_id TEXT)
RETURNS TEXT AS $$
DECLARE
    new_id UUID;
BEGIN
    -- Set context
    PERFORM set_config('app.current_organization_id', org_id, true);
    PERFORM set_config('app.user_role', 'user', true);
    
    -- Try to insert
    INSERT INTO webhook_logs (
        organization_id,
        webhook_type,
        workflow_name,
        n8n_webhook_url,
        status,
        trigger_source
    ) VALUES (
        org_id,
        'debug_test',
        'debug_workflow',
        'https://debug.com/webhook',
        'pending',
        'debug'
    ) RETURNING id INTO new_id;
    
    RETURN 'SUCCESS: Created webhook log with ID: ' || new_id::TEXT;
    
EXCEPTION WHEN others THEN
    RETURN 'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

/*
===========================================
RUN THESE TESTS IN ORDER:
===========================================

1. Check tables exist:
   SELECT 'webhook_logs' as table_name, EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'webhook_logs') as exists;

2. Check RLS status:
   SELECT tablename, rowsecurity as rls_enabled FROM pg_tables WHERE tablename IN ('webhook_logs', 'webhook_templates') AND schemaname = 'public';

3. Test simple access:
   SELECT * FROM test_simple_access('org_2xwiHJY6BaRUIX1DanXG6ZX7');

4. Test insert:
   SELECT test_insert_webhook_log('org_2xwiHJY6BaRUIX1DanXG6ZX7');

5. If insert works, check the data:
   SELECT set_config('app.current_organization_id', 'org_2xwiHJY6BaRUIX1DanXG6ZX7', true);
   SELECT * FROM webhook_logs WHERE webhook_type = 'debug_test';

6. Cleanup:
   DELETE FROM webhook_logs WHERE webhook_type = 'debug_test';
*/ 