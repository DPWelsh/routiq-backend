-- Test Script for HIPAA Audit Logs
-- Run this after creating the audit_logs table to verify it works

-- Step 1: Check what organizations exist
SELECT 'Available Organizations:' as info;
SELECT id, name, created_at 
FROM organizations 
ORDER BY created_at DESC 
LIMIT 5;

-- Step 2: Test audit log insertion with a real organization ID
-- Replace 'your_org_id_here' with an actual organization ID from above
DO $$
DECLARE
    test_org_id VARCHAR;
BEGIN
    -- Get the first available organization ID
    SELECT id INTO test_org_id FROM organizations LIMIT 1;
    
    IF test_org_id IS NOT NULL THEN
        -- Insert test audit log
        INSERT INTO audit_logs (
            organization_id, user_id, action, resource_type, 
            resource_id, details, success
        ) VALUES (
            test_org_id, 'setup_test', 'table_creation_test', 'system',
            'audit_logs', 
            ('{"message": "HIPAA audit logs table test successful", "timestamp": "' || NOW() || '"}')::jsonb,
            true
        );
        
        RAISE NOTICE 'Test audit log created successfully for organization: %', test_org_id;
    ELSE
        RAISE NOTICE 'No organizations found. Create an organization first.';
    END IF;
END $$;

-- Step 3: Verify the audit log was created
SELECT 'Recent Audit Logs:' as info;
SELECT 
    id,
    organization_id,
    user_id,
    action,
    resource_type,
    success,
    created_at
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 5;

-- Step 4: Test the PHI access view
SELECT 'PHI Access Logs (should be empty):' as info;
SELECT COUNT(*) as phi_access_count FROM phi_access_log;

-- Step 5: Test audit statistics function
DO $$
DECLARE
    test_org_id VARCHAR;
    stats_result RECORD;
BEGIN
    SELECT id INTO test_org_id FROM organizations LIMIT 1;
    
    IF test_org_id IS NOT NULL THEN
        SELECT * INTO stats_result FROM get_audit_statistics(test_org_id, 30);
        RAISE NOTICE 'Audit Statistics for org %: total_actions=%, unique_users=%, phi_access=%, failed_attempts=%', 
            test_org_id, stats_result.total_actions, stats_result.unique_users, 
            stats_result.phi_access_count, stats_result.failed_attempts;
    END IF;
END $$; 