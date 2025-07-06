-- Fix the stale sync that's stuck in running status
UPDATE sync_logs 
SET status = 'failed',
    completed_at = NOW(),
    error_details = '{"error": "Sync cleaned up due to stale status (stuck in running)", "cleanup_reason": "manual_cleanup"}'
WHERE id = 'f5cce669-a656-4a26-b756-8199d4a99be6' 
  AND status = 'running';

-- Verify the update
SELECT id, status, started_at, completed_at, operation_type, organization_id 
FROM sync_logs 
WHERE id = 'f5cce669-a656-4a26-b756-8199d4a99be6';
