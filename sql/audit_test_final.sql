-- FOOLPROOF Audit Logs Test - Guaranteed to use real IDs

-- First, let's see what we have to work with
SELECT 'Step 1: Available Users' as step;
SELECT id, email, created_at FROM users ORDER BY created_at DESC LIMIT 3;

SELECT 'Step 2: Available Organizations' as step;
SELECT id, name, created_at FROM organizations ORDER BY created_at DESC LIMIT 3;

-- Only proceed if we have both users and organizations
DO $$
DECLARE
    user_count INTEGER;
    org_count INTEGER;
    test_user_id VARCHAR;
    test_org_id VARCHAR;
BEGIN
    -- Check counts
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO org_count FROM organizations;
    
    RAISE NOTICE 'Found % users and % organizations', user_count, org_count;
    
    IF user_count > 0 AND org_count > 0 THEN
        -- Get the first available user and org
        SELECT id INTO test_user_id FROM users ORDER BY created_at DESC LIMIT 1;
        SELECT id INTO test_org_id FROM organizations ORDER BY created_at DESC LIMIT 1;
        
        RAISE NOTICE 'Testing with user_id: % and organization_id: %', test_user_id, test_org_id;
        
        -- Now insert the audit log with 100% real IDs using proper JSON construction
        INSERT INTO audit_logs (
            organization_id, 
            user_id, 
            action, 
            resource_type, 
            resource_id, 
            details, 
            success
        ) VALUES (
            test_org_id,
            test_user_id,
            'table_creation_test',
            'system',
            'audit_logs',
            json_build_object(
                'message', 'Audit logs table test successful!',
                'timestamp', NOW(),
                'test', true,
                'method', 'foolproof_test'
            )::jsonb,
            true
        );
        
        RAISE NOTICE 'SUCCESS: Audit log created successfully!';
        
    ELSE
        RAISE NOTICE 'ERROR: Need at least 1 user and 1 organization to test audit logs';
        RAISE NOTICE 'Users found: %, Organizations found: %', user_count, org_count;
    END IF;
END $$;

-- Verify the test worked
SELECT 'Step 3: Verification' as step;
SELECT 
    id,
    organization_id,
    user_id,
    action,
    resource_type,
    details,
    success,
    created_at
FROM audit_logs 
WHERE action = 'table_creation_test'
ORDER BY created_at DESC 
LIMIT 1;

-- Show total audit logs
SELECT 'Step 4: Summary' as step;
SELECT COUNT(*) as total_audit_logs FROM audit_logs; 