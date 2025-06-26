-- HIPAA Compliance Audit Logging - Simplified for Supabase
-- Creates audit_logs table for tracking all PHI access and critical system actions

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    details JSONB,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance and compliance queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_created 
    ON audit_logs (organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created 
    ON audit_logs (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource 
    ON audit_logs (resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action_created 
    ON audit_logs (action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_phi_access 
    ON audit_logs (organization_id, resource_type, created_at DESC) 
    WHERE resource_type IN ('patient', 'appointment', 'medical_record');

-- Partial index for failed authentication attempts
CREATE INDEX IF NOT EXISTS idx_audit_logs_failed_auth 
    ON audit_logs (organization_id, user_id, created_at DESC) 
    WHERE success = false AND action LIKE 'auth_%';

-- Create view for PHI access monitoring
CREATE OR REPLACE VIEW phi_access_log AS
SELECT 
    organization_id,
    user_id,
    action,
    resource_type,
    resource_id,
    ip_address,
    created_at,
    success,
    error_message
FROM audit_logs
WHERE resource_type IN ('patient', 'appointment', 'medical_record')
ORDER BY created_at DESC;

-- Create function for automated audit log cleanup (retain 7 years for HIPAA)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete audit logs older than 7 years (HIPAA retention requirement)
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '7 years';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup operation (only if a valid organization exists)
    IF EXISTS (SELECT 1 FROM organizations LIMIT 1) THEN
        INSERT INTO audit_logs (
            organization_id, user_id, action, resource_type, 
            resource_id, details, success, created_at
        ) VALUES (
            (SELECT id FROM organizations LIMIT 1), 'cleanup_function', 'audit_log_cleanup', 'system',
            'audit_logs', 
            json_build_object('deleted_count', deleted_count, 'retention_period', '7 years'),
            true, NOW()
        );
    END IF;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function for audit statistics
CREATE OR REPLACE FUNCTION get_audit_statistics(org_id VARCHAR, days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    total_actions BIGINT,
    unique_users BIGINT,
    phi_access_count BIGINT,
    failed_attempts BIGINT,
    top_actions JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH stats AS (
        SELECT 
            COUNT(*) as total_actions,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(*) FILTER (WHERE resource_type IN ('patient', 'appointment', 'medical_record')) as phi_access_count,
            COUNT(*) FILTER (WHERE success = false) as failed_attempts
        FROM audit_logs 
        WHERE organization_id = org_id 
        AND created_at >= NOW() - INTERVAL '%s days' % days_back
    ),
    top_actions_agg AS (
        SELECT json_agg(
            json_build_object(
                'action', action,
                'count', action_count
            ) ORDER BY action_count DESC
        ) as top_actions
        FROM (
            SELECT action, COUNT(*) as action_count
            FROM audit_logs 
            WHERE organization_id = org_id 
            AND created_at >= NOW() - INTERVAL '%s days' % days_back
            GROUP BY action
            ORDER BY action_count DESC
            LIMIT 10
        ) t
    )
    SELECT 
        stats.total_actions,
        stats.unique_users,
        stats.phi_access_count,
        stats.failed_attempts,
        COALESCE(top_actions_agg.top_actions, '[]'::jsonb)
    FROM stats, top_actions_agg;
END;
$$ LANGUAGE plpgsql;

-- Add table comments
COMMENT ON TABLE audit_logs IS 'HIPAA-compliant audit trail for all PHI access and system actions';
COMMENT ON COLUMN audit_logs.organization_id IS 'Multi-tenant organization identifier';
COMMENT ON COLUMN audit_logs.user_id IS 'Clerk user ID or system identifier';
COMMENT ON COLUMN audit_logs.action IS 'Action performed (view_patient, export_data, etc.)';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource accessed (patient, appointment, etc.)';
COMMENT ON COLUMN audit_logs.resource_id IS 'Specific resource identifier';
COMMENT ON COLUMN audit_logs.ip_address IS 'Client IP address for security tracking';
COMMENT ON COLUMN audit_logs.user_agent IS 'Client user agent string';
COMMENT ON COLUMN audit_logs.session_id IS 'Session identifier for correlation';
COMMENT ON COLUMN audit_logs.details IS 'Additional context as JSON';
COMMENT ON COLUMN audit_logs.success IS 'Whether the action succeeded';
COMMENT ON COLUMN audit_logs.error_message IS 'Error details if action failed';
COMMENT ON COLUMN audit_logs.created_at IS 'Timestamp of the action';

-- 
-- TESTING: To test the audit logs after creation, run this with a valid organization ID:
-- 
-- INSERT INTO audit_logs (
--     organization_id, user_id, action, resource_type, 
--     resource_id, details, success
-- ) VALUES (
--     'your_actual_org_id_here', 'setup', 'table_creation', 'system',
--     'audit_logs', 
--     '{"message": "HIPAA audit logs table created successfully"}',
--     true
-- );
--