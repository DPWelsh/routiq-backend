-- SurfRehab v2 - Useful Views
-- Analytics and reporting views for dashboard and insights

-- Patient overview view (combines contacts and active patients)
CREATE OR REPLACE VIEW patient_overview AS
SELECT 
    c.id,
    c.name,
    c.phone,
    c.email,
    c.contact_type,
    c.cliniko_patient_id,
    c.status,
    c.created_at,
    c.organization_id,
    
    -- Active patient data (if exists)
    ap.recent_appointment_count,
    ap.upcoming_appointment_count,
    ap.total_appointment_count,
    ap.last_appointment_date,
    
    -- Source information
    c.metadata->>'source' as source,
    
    -- Calculated fields
    CASE 
        WHEN ap.id IS NOT NULL THEN true 
        ELSE false 
    END as is_active_patient,
    
    CASE 
        WHEN ap.upcoming_appointment_count > 0 THEN 'scheduled'
        WHEN ap.recent_appointment_count > 0 THEN 'recent'
        ELSE 'inactive'
    END as appointment_status
    
FROM contacts c
LEFT JOIN active_patients ap ON c.id = ap.contact_id
WHERE c.deleted_at IS NULL;

-- Contact analytics view (for dashboard stats)
CREATE OR REPLACE VIEW contact_analytics AS
SELECT 
    c.organization_id,
    c.contact_type,
    c.metadata->>'source' as source,
    c.status,
    COUNT(*) as contact_count,
    COUNT(*) FILTER (WHERE c.cliniko_patient_id IS NOT NULL) as with_cliniko_id,
    COUNT(ap.id) as active_patient_count,
    DATE_TRUNC('day', c.created_at) as created_date,
    DATE_TRUNC('week', c.created_at) as created_week,
    DATE_TRUNC('month', c.created_at) as created_month
FROM contacts c
LEFT JOIN active_patients ap ON c.id = ap.contact_id
WHERE c.deleted_at IS NULL
GROUP BY 
    c.organization_id, 
    c.contact_type, 
    c.metadata->>'source', 
    c.status,
    DATE_TRUNC('day', c.created_at),
    DATE_TRUNC('week', c.created_at),
    DATE_TRUNC('month', c.created_at);

-- Conversation insights view
CREATE OR REPLACE VIEW conversation_insights AS
SELECT 
    conv.id,
    conv.contact_id,
    c.name as contact_name,
    c.phone as contact_phone,
    conv.source,
    conv.status,
    conv.overall_sentiment,
    conv.sentiment_score,
    conv.quality_rating,
    conv.escalation_flag,
    conv.user_feedback_rating,
    conv.created_at,
    conv.organization_id,
    
    -- Message statistics
    COUNT(m.id) as message_count,
    COUNT(m.id) FILTER (WHERE m.sender_type = 'patient') as patient_message_count,
    COUNT(m.id) FILTER (WHERE m.sender_type = 'agent') as agent_message_count,
    COUNT(m.id) FILTER (WHERE m.sender_type = 'bot') as bot_message_count,
    
    -- Sentiment analysis
    AVG(m.sentiment_score) as avg_message_sentiment,
    COUNT(m.id) FILTER (WHERE m.sentiment_label = 'positive') as positive_messages,
    COUNT(m.id) FILTER (WHERE m.sentiment_label = 'negative') as negative_messages,
    COUNT(m.id) FILTER (WHERE m.sentiment_label = 'neutral') as neutral_messages,
    
    -- Timing
    MIN(m.timestamp) as first_message_at,
    MAX(m.timestamp) as last_message_at,
    EXTRACT(EPOCH FROM (MAX(m.timestamp) - MIN(m.timestamp)))/3600 as conversation_duration_hours
    
FROM conversations conv
LEFT JOIN contacts c ON conv.contact_id = c.id
LEFT JOIN messages m ON conv.id = m.conversation_id AND m.deleted_at IS NULL
WHERE conv.deleted_at IS NULL
GROUP BY 
    conv.id, conv.contact_id, c.name, c.phone, conv.source, conv.status,
    conv.overall_sentiment, conv.sentiment_score, conv.quality_rating,
    conv.escalation_flag, conv.user_feedback_rating, conv.created_at, conv.organization_id;

-- Appointment summary view
CREATE OR REPLACE VIEW appointment_summary AS
SELECT 
    a.id,
    a.contact_id,
    c.name as contact_name,
    c.phone as contact_phone,
    c.email as contact_email,
    a.appointment_date,
    a.status,
    a.type,
    a.cliniko_appointment_id,
    a.google_calendar_event_id,
    a.organization_id,
    
    -- Calculated fields
    CASE 
        WHEN a.appointment_date > now() THEN 'upcoming'
        WHEN a.appointment_date > now() - interval '30 days' THEN 'recent'
        ELSE 'past'
    END as appointment_period,
    
    EXTRACT(EPOCH FROM (a.appointment_date - now()))/3600 as hours_until_appointment
    
FROM appointments a
LEFT JOIN contacts c ON a.contact_id = c.id
WHERE a.deleted_at IS NULL;

-- Organization dashboard view
CREATE OR REPLACE VIEW organization_dashboard AS
SELECT 
    o.id,
    o.name,
    o.slug,
    o.subscription_status,
    o.subscription_plan,
    o.created_at,
    
    -- Contact statistics
    COUNT(DISTINCT c.id) as total_contacts,
    COUNT(DISTINCT c.id) FILTER (WHERE c.contact_type = 'cliniko_patient') as cliniko_patients,
    COUNT(DISTINCT c.id) FILTER (WHERE c.contact_type = 'chatwoot_contact') as chatwoot_contacts,
    COUNT(DISTINCT ap.id) as active_patients,
    
    -- Conversation statistics
    COUNT(DISTINCT conv.id) as total_conversations,
    COUNT(DISTINCT conv.id) FILTER (WHERE conv.status = 'active') as active_conversations,
    COUNT(DISTINCT conv.id) FILTER (WHERE conv.escalation_flag = true) as escalated_conversations,
    
    -- Appointment statistics
    COUNT(DISTINCT a.id) as total_appointments,
    COUNT(DISTINCT a.id) FILTER (WHERE a.appointment_date > now()) as upcoming_appointments,
    COUNT(DISTINCT a.id) FILTER (WHERE a.appointment_date > now() - interval '30 days' AND a.appointment_date <= now()) as recent_appointments,
    
    -- Activity metrics
    MAX(c.created_at) as last_contact_added,
    MAX(conv.created_at) as last_conversation,
    MAX(a.created_at) as last_appointment_created
    
FROM organizations o
LEFT JOIN contacts c ON o.id = c.organization_id AND c.deleted_at IS NULL
LEFT JOIN active_patients ap ON c.id = ap.contact_id
LEFT JOIN conversations conv ON c.id = conv.contact_id AND conv.deleted_at IS NULL
LEFT JOIN appointments a ON c.id = a.contact_id AND a.deleted_at IS NULL
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.name, o.slug, o.subscription_status, o.subscription_plan, o.created_at;

-- Sync status view (for monitoring API integrations)
CREATE OR REPLACE VIEW sync_status AS
SELECT 
    sl.organization_id,
    sl.source_system,
    sl.operation_type,
    sl.status,
    COUNT(*) as sync_count,
    MAX(sl.started_at) as last_sync_at,
    SUM(sl.records_processed) as total_records_processed,
    SUM(sl.records_success) as total_records_success,
    SUM(sl.records_failed) as total_records_failed,
    ROUND(
        (SUM(sl.records_success)::numeric / NULLIF(SUM(sl.records_processed), 0)) * 100, 
        2
    ) as success_rate_percent
FROM sync_logs sl
WHERE sl.started_at > now() - interval '30 days'
GROUP BY sl.organization_id, sl.source_system, sl.operation_type, sl.status
ORDER BY last_sync_at DESC;

-- Messages by contact view (individual messages with contact details)
CREATE OR REPLACE VIEW messages_by_contact AS
SELECT 
    -- Contact information
    c.phone,
    c.name as contact_name,
    c.email as contact_email,
    c.contact_type,
    c.cliniko_patient_id,
    c.organization_id,
    
    -- Conversation details
    conv.id as conversation_id,
    conv.source as conversation_source,
    conv.status as conversation_status,
    conv.chatwoot_conversation_id,
    
    -- Message details
    m.id as message_id,
    m.content as message_content,
    m.sender_type,
    m.timestamp as message_timestamp,
    m.external_id as message_external_id,
    
    -- Sentiment analysis
    m.sentiment_score,
    m.sentiment_label,
    m.confidence_score,
    m.analyzed_at,
    
    -- User feedback
    m.user_feedback_rating,
    m.user_feedback_note,
    m.user_feedback_timestamp,
    
    -- Metadata
    m.is_private,
    m.metadata as message_metadata,
    m.created_at as message_created_at
    
FROM contacts c
INNER JOIN conversations conv ON c.id = conv.contact_id
INNER JOIN messages m ON conv.id = m.conversation_id
WHERE 
    c.deleted_at IS NULL 
    AND conv.deleted_at IS NULL 
    AND m.deleted_at IS NULL
ORDER BY c.phone, conv.created_at, m.timestamp; 