-- Safe Audit Logs Test - Uses existing user and organization IDs

-- Step 1: Check what users and organizations exist
SELECT 'Available Users:' as info;
SELECT id, email, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 3;

SELECT 'Available Organizations:' as info;  
SELECT id, name, created_at
FROM organizations
ORDER BY created_at DESC
LIMIT 3;

-- Step 2: Test insert with real user and organization IDs
INSERT INTO audit_logs (
    organization_id, user_id, action, resource_type, 
    resource_id, details, success
) 
SELECT 
    o.id as organization_id,
    u.id as user_id,
    'table_test' as action,
    'system' as resource_type,
    'audit_logs' as resource_id,
    '{"message": "Audit logs table working!", "test": true, "method": "safe_test"}'::jsonb as details,
    true as success
FROM organizations o
CROSS JOIN users u
LIMIT 1;

-- Step 3: Verify the test worked
SELECT 
    'Audit Log Test Results:' as status,
    COUNT(*) as total_audit_logs,
    MAX(created_at) as latest_entry
FROM audit_logs;

-- Step 4: Show the test entry details
SELECT 
    'Test Entry Details:' as info,
    organization_id,
    user_id,
    action,
    resource_type,
    details,
    success,
    created_at
FROM audit_logs 
WHERE action = 'table_test'
ORDER BY created_at DESC 
LIMIT 1;

-- Step 5: Test the audit statistics function
DO $$
DECLARE
    test_org_id VARCHAR;
    test_user_id VARCHAR;
    stats_result RECORD;
BEGIN
    -- Get real IDs
    SELECT o.id, u.id INTO test_org_id, test_user_id
    FROM organizations o
    CROSS JOIN users u
    LIMIT 1;
    
    IF test_org_id IS NOT NULL THEN
        -- Test the statistics function
        SELECT * INTO stats_result FROM get_audit_statistics(test_org_id, 30);
        RAISE NOTICE 'Audit Statistics for org %: total_actions=%, unique_users=%, phi_access=%, failed_attempts=%', 
            test_org_id, stats_result.total_actions, stats_result.unique_users, 
            stats_result.phi_access_count, stats_result.failed_attempts;
            
        -- Test another audit entry for variety
        INSERT INTO audit_logs (
            organization_id, user_id, action, resource_type, 
            resource_id, details, success
        ) VALUES (
            test_org_id, test_user_id, 'function_test', 'system',
            'statistics', 
            '{"message": "Statistics function tested", "function": "get_audit_statistics"}'::jsonb,
            true
        );
        
        RAISE NOTICE 'Additional test audit log created successfully';
    ELSE
        RAISE NOTICE 'No users or organizations found. Please create some first.';
    END IF;
END $$; 