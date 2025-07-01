/*
===========================================
WEBHOOK SYSTEM - SUPABASE TABLES
===========================================
Phase 1: Database Setup for N8N Webhook Integration
Created: 2025-01-01
Version: 1.0

This script creates:
✅ webhook_logs - Complete audit trail of all webhook executions
✅ webhook_templates - Reusable webhook configurations
✅ Performance indexes
✅ RLS (Row Level Security) policies
*/

-- ==========================================
-- 1. WEBHOOK LOGS TABLE
-- ==========================================
-- Stores complete audit trail of all webhook executions
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Organization & Patient Context
    organization_id VARCHAR(255) NOT NULL,
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    
    -- Webhook Identification  
    webhook_type VARCHAR(100) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    n8n_webhook_url TEXT NOT NULL,
    
    -- Payload Data (stored as JSONB for querying)
    trigger_data JSONB,
    request_payload JSONB,
    response_data JSONB,
    
    -- Execution Status & Timing
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed', 'retrying', 'timeout', 'cancelled')),
    http_status_code INTEGER,
    error_message TEXT,
    execution_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- User & Context Tracking
    triggered_by_user_id VARCHAR(255),
    trigger_source VARCHAR(100), -- 'dashboard', 'bulk_action', 'automated', 'api'
    
    -- Timestamps
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE webhook_logs IS 'Complete audit trail of all webhook executions to N8N workflows';
COMMENT ON COLUMN webhook_logs.trigger_data IS 'Original data that triggered the webhook';
COMMENT ON COLUMN webhook_logs.request_payload IS 'Actual payload sent to N8N webhook';
COMMENT ON COLUMN webhook_logs.response_data IS 'Response received from N8N workflow';
COMMENT ON COLUMN webhook_logs.execution_time_ms IS 'Total execution time in milliseconds';
COMMENT ON COLUMN webhook_logs.retry_count IS 'Number of retry attempts made';

-- ==========================================
-- 2. WEBHOOK TEMPLATES TABLE  
-- ==========================================
-- Stores reusable webhook configurations and N8N workflow mappings
CREATE TABLE IF NOT EXISTS webhook_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template Identification
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    webhook_type VARCHAR(100) NOT NULL,
    
    -- N8N Configuration
    n8n_webhook_url TEXT NOT NULL,
    workflow_id VARCHAR(255), -- N8N workflow ID for reference
    
    -- Request Configuration
    payload_template JSONB, -- Template for building request payload
    headers JSONB DEFAULT '{"Content-Type": "application/json"}',
    http_method VARCHAR(10) DEFAULT 'POST' CHECK (http_method IN ('POST', 'PUT', 'PATCH')),
    
    -- Execution Settings
    timeout_seconds INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 5,
    
    -- Template Status & Organization
    is_active BOOLEAN DEFAULT true,
    organization_id VARCHAR(255), -- NULL = global template, specific org_id = org-specific
    
    -- Metadata
    created_by_user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE webhook_templates IS 'Reusable webhook configurations and N8N workflow mappings';
COMMENT ON COLUMN webhook_templates.payload_template IS 'JSON template for building webhook payloads with variable substitution';
COMMENT ON COLUMN webhook_templates.organization_id IS 'NULL for global templates, org_id for organization-specific templates';

-- ==========================================
-- 3. WEBHOOK QUEUE TABLE (For Async Processing)
-- ==========================================
-- Optional: For handling high-volume webhook processing
CREATE TABLE IF NOT EXISTS webhook_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference to webhook log
    webhook_log_id UUID REFERENCES webhook_logs(id) ON DELETE CASCADE,
    
    -- Queue Management
    status VARCHAR(50) DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 1, -- 1=high, 2=medium, 3=low
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Processing Data
    payload JSONB NOT NULL,
    webhook_url TEXT NOT NULL,
    headers JSONB DEFAULT '{}',
    
    -- Timing
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE webhook_queue IS 'Queue for async webhook processing to handle high volumes';

-- ==========================================
-- 4. PERFORMANCE INDEXES
-- ==========================================

-- Primary lookup indexes for webhook_logs
CREATE INDEX IF NOT EXISTS idx_webhook_logs_org_triggered 
ON webhook_logs(organization_id, triggered_at DESC);

CREATE INDEX IF NOT EXISTS idx_webhook_logs_patient_type 
ON webhook_logs(patient_id, webhook_type) WHERE patient_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_webhook_logs_status_triggered 
ON webhook_logs(status, triggered_at DESC);

CREATE INDEX IF NOT EXISTS idx_webhook_logs_workflow_status 
ON webhook_logs(workflow_name, status);

-- Index for retry processing
CREATE INDEX IF NOT EXISTS idx_webhook_logs_retry_due 
ON webhook_logs(next_retry_at) WHERE status = 'retrying' AND next_retry_at IS NOT NULL;

-- Performance index for analytics queries
CREATE INDEX IF NOT EXISTS idx_webhook_logs_analytics 
ON webhook_logs(organization_id, webhook_type, status, triggered_at);

-- Indexes for webhook_templates
CREATE INDEX IF NOT EXISTS idx_webhook_templates_type_active 
ON webhook_templates(webhook_type, is_active);

CREATE INDEX IF NOT EXISTS idx_webhook_templates_org 
ON webhook_templates(organization_id) WHERE organization_id IS NOT NULL;

-- Queue processing indexes
CREATE INDEX IF NOT EXISTS idx_webhook_queue_processing 
ON webhook_queue(status, scheduled_for, priority);

CREATE INDEX IF NOT EXISTS idx_webhook_queue_log_ref 
ON webhook_queue(webhook_log_id);

-- ==========================================
-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================

-- Enable RLS on all tables
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_queue ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- RLS POLICIES FOR webhook_logs
-- ==========================================

-- Organizations can only see their own webhook logs
CREATE POLICY "webhook_logs_org_isolation" ON webhook_logs
    FOR ALL 
    USING (organization_id = current_setting('app.current_organization_id', true));

-- Users can insert logs for their organization (for service accounts)
CREATE POLICY "webhook_logs_org_insert" ON webhook_logs
    FOR INSERT
    WITH CHECK (organization_id = current_setting('app.current_organization_id', true));

-- Admin users can see all logs (for system monitoring)
CREATE POLICY "webhook_logs_admin_access" ON webhook_logs
    FOR ALL
    USING (
        current_setting('app.user_role', true) = 'admin' 
        OR current_setting('app.user_role', true) = 'super_admin'
    );

-- ==========================================
-- RLS POLICIES FOR webhook_templates  
-- ==========================================

-- Users can see global templates (organization_id IS NULL) or their org templates
CREATE POLICY "webhook_templates_access" ON webhook_templates
    FOR SELECT
    USING (
        organization_id IS NULL 
        OR organization_id = current_setting('app.current_organization_id', true)
    );

-- Only admins can create/modify templates
CREATE POLICY "webhook_templates_admin_modify" ON webhook_templates
    FOR ALL
    USING (current_setting('app.user_role', true) IN ('admin', 'super_admin'))
    WITH CHECK (current_setting('app.user_role', true) IN ('admin', 'super_admin'));

-- ==========================================
-- RLS POLICIES FOR webhook_queue
-- ==========================================

-- Queue items follow same org isolation as logs
CREATE POLICY "webhook_queue_org_isolation" ON webhook_queue
    FOR ALL
    USING (
        webhook_log_id IN (
            SELECT id FROM webhook_logs 
            WHERE organization_id = current_setting('app.current_organization_id', true)
        )
    );

-- ==========================================
-- 6. HELPER FUNCTIONS
-- ==========================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER update_webhook_logs_updated_at 
    BEFORE UPDATE ON webhook_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhook_templates_updated_at 
    BEFORE UPDATE ON webhook_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 7. INITIAL WEBHOOK TEMPLATES
-- ==========================================

-- Insert some common webhook templates
INSERT INTO webhook_templates (name, description, webhook_type, n8n_webhook_url, payload_template, workflow_id) VALUES
(
    'patient_followup_basic',
    'Basic patient follow-up workflow trigger',
    'patient_followup',
    'https://your-n8n-instance.com/webhook/patient-followup',
    '{
        "patient": {
            "id": "{{patient_id}}",
            "name": "{{patient_name}}",
            "email": "{{patient_email}}",
            "phone": "{{patient_phone}}"
        },
        "organization": {
            "id": "{{organization_id}}",
            "name": "{{organization_name}}"
        },
        "trigger": {
            "type": "followup",
            "source": "{{trigger_source}}",
            "user_id": "{{user_id}}",
            "timestamp": "{{timestamp}}"
        },
        "context": {
            "last_appointment": "{{last_appointment_date}}",
            "risk_level": "{{risk_level}}",
            "engagement_status": "{{engagement_status}}"
        }
    }',
    'wf_followup_001'
),
(
    'appointment_reminder',
    'Send appointment reminder to patient',
    'appointment_reminder',
    'https://your-n8n-instance.com/webhook/appointment-reminder',
    '{
        "patient": {
            "id": "{{patient_id}}",
            "name": "{{patient_name}}",
            "email": "{{patient_email}}",
            "phone": "{{patient_phone}}"
        },
        "appointment": {
            "id": "{{appointment_id}}",
            "date": "{{appointment_date}}",
            "time": "{{appointment_time}}",
            "type": "{{appointment_type}}",
            "practitioner": "{{practitioner_name}}"
        },
        "reminder": {
            "type": "{{reminder_type}}",
            "days_before": "{{days_before}}",
            "method": "{{preferred_method}}"
        }
    }',
    'wf_reminder_001'
),
(
    'reengagement_campaign',
    'Start automated reengagement campaign for dormant patients',
    'reengagement_campaign', 
    'https://your-n8n-instance.com/webhook/reengagement',
    '{
        "patient": {
            "id": "{{patient_id}}",
            "name": "{{patient_name}}",
            "email": "{{patient_email}}",
            "phone": "{{patient_phone}}"
        },
        "engagement": {
            "status": "{{engagement_status}}",
            "risk_level": "{{risk_level}}",
            "days_since_contact": "{{days_since_last_contact}}",
            "total_appointments": "{{total_appointment_count}}",
            "lifetime_value": "{{lifetime_value_aud}}"
        },
        "campaign": {
            "type": "reengagement",
            "priority": "{{action_priority}}",
            "recommended_action": "{{recommended_action}}"
        }
    }',
    'wf_reengage_001'
)
ON CONFLICT (name) DO NOTHING;

-- ==========================================
-- 8. VIEWS FOR ANALYTICS
-- ==========================================

-- Webhook execution analytics view
CREATE OR REPLACE VIEW webhook_analytics AS
SELECT 
    w.organization_id,
    w.webhook_type,
    w.workflow_name,
    DATE_TRUNC('day', w.triggered_at) as execution_date,
    
    -- Execution Counts
    COUNT(*) as total_executions,
    COUNT(*) FILTER (WHERE w.status = 'success') as successful_executions,
    COUNT(*) FILTER (WHERE w.status = 'failed') as failed_executions,
    COUNT(*) FILTER (WHERE w.status = 'timeout') as timeout_executions,
    COUNT(*) FILTER (WHERE w.retry_count > 0) as retried_executions,
    
    -- Success Rate
    ROUND(
        (COUNT(*) FILTER (WHERE w.status = 'success') * 100.0 / COUNT(*)), 2
    ) as success_rate_percent,
    
    -- Performance Metrics
    ROUND(AVG(w.execution_time_ms)) as avg_execution_time_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY w.execution_time_ms)) as p95_execution_time_ms,
    MAX(w.execution_time_ms) as max_execution_time_ms,
    
    -- Retry Analysis
    ROUND(AVG(w.retry_count), 2) as avg_retry_count,
    MAX(w.retry_count) as max_retry_count
    
FROM webhook_logs w
WHERE w.triggered_at >= NOW() - INTERVAL '30 days'
GROUP BY w.organization_id, w.webhook_type, w.workflow_name, DATE_TRUNC('day', w.triggered_at);

COMMENT ON VIEW webhook_analytics IS 'Daily webhook execution analytics for monitoring and optimization';

-- Recent webhook activity view
CREATE OR REPLACE VIEW webhook_recent_activity AS
SELECT 
    w.id,
    w.organization_id,
    w.patient_id,
    p.name as patient_name,
    w.webhook_type,
    w.workflow_name,
    w.status,
    w.execution_time_ms,
    w.retry_count,
    w.triggered_by_user_id,
    w.trigger_source,
    w.triggered_at,
    w.completed_at,
    w.error_message,
    
    -- Status indicators
    CASE 
        WHEN w.status = 'pending' THEN '🟡 Pending'
        WHEN w.status = 'success' THEN '🟢 Success'
        WHEN w.status = 'failed' THEN '🔴 Failed'
        WHEN w.status = 'retrying' THEN '🟠 Retrying'
        WHEN w.status = 'timeout' THEN '⏰ Timeout'
        WHEN w.status = 'cancelled' THEN '⚫ Cancelled'
    END as status_display
    
FROM webhook_logs w
LEFT JOIN patients p ON w.patient_id = p.id
WHERE w.triggered_at >= NOW() - INTERVAL '7 days'
ORDER BY w.triggered_at DESC;

COMMENT ON VIEW webhook_recent_activity IS 'Recent webhook executions with patient context for dashboard display';

-- ==========================================
-- SETUP COMPLETE
-- ==========================================

/*
===========================================
WEBHOOK DATABASE SETUP COMPLETE! ✅
===========================================

Created:
✅ webhook_logs - Complete execution audit trail
✅ webhook_templates - Reusable workflow configurations  
✅ webhook_queue - Async processing support
✅ Performance indexes for fast queries
✅ RLS policies for multi-tenant security
✅ Helper functions and triggers
✅ Sample webhook templates
✅ Analytics views for monitoring

Next Steps:
1. Update N8N webhook URLs in webhook_templates
2. Set up Supabase environment variables:
   - app.current_organization_id 
   - app.user_role
3. Test RLS policies with your auth system
4. Implement backend WebhookService (Phase 2)

Security Notes:
- All tables have RLS enabled
- Organizations are isolated by organization_id
- Admin users can access all data
- Webhook templates support both global and org-specific configurations

Performance Notes:
- Indexes optimized for common query patterns
- Analytics views pre-aggregate metrics
- Queue table supports async processing for high volumes
*/ 