-- Quick Audit Logs Test - Run this after creating the audit_logs table

-- Test 1: Simple insert with proper JSONB casting
INSERT INTO audit_logs (
    organization_id, user_id, action, resource_type, 
    resource_id, details, success
) 
SELECT 
    id as organization_id,
    'test_user' as user_id,
    'table_test' as action,
    'system' as resource_type,
    'audit_logs' as resource_id,
    '{"message": "Audit logs table working!", "test": true}'::jsonb as details,
    true as success
FROM organizations 
LIMIT 1;

-- Test 2: Verify the insert worked
SELECT 
    'Audit Log Test Results:' as info,
    COUNT(*) as total_logs,
    MAX(created_at) as latest_log
FROM audit_logs;

-- Test 3: Show the actual log entry
SELECT 
    organization_id,
    user_id, 
    action,
    details,
    created_at
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 1; 