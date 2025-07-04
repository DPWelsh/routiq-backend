-- Patient Conversation Profile View v1.0
-- Comprehensive per-patient view for conversations page
-- Combines patient info, appointments, conversations, engagement metrics

DROP VIEW IF EXISTS patient_conversation_profile;
CREATE VIEW patient_conversation_profile AS
SELECT 
    -- Patient Core Information
    p.id as patient_id,
    p.organization_id,
    p.name as patient_name,
    p.email,
    p.phone,
    p.cliniko_patient_id,
    p.is_active,
    p.activity_status,
    p.contact_type,
    
    -- Contact Information (from deprecated table for treatment notes)
    cd.treatment_summary,
    cd.last_treatment_note,
    cd.patient_status,
    cd.medical_record_number,
    
    -- Appointment Information
    p.total_appointment_count,
    p.recent_appointment_count,
    p.upcoming_appointment_count,
    p.first_appointment_date,
    p.last_appointment_date,
    p.next_appointment_time,
    p.next_appointment_type,
    p.primary_appointment_type,
    p.treatment_notes,
    
    -- Current Appointment Details (most recent)
    recent_apt.current_appointment_type,
    recent_apt.current_appointment_status,
    recent_apt.current_appointment_notes,
    
    -- Next Appointment Details
    next_apt.next_appointment_date,
    next_apt.next_appointment_status,
    next_apt.next_appointment_notes,
    
    -- Conversation Metrics
    conv_stats.total_conversations,
    conv_stats.active_conversations,
    conv_stats.last_conversation_date,
    conv_stats.days_since_last_conversation,
    conv_stats.overall_sentiment,
    conv_stats.avg_sentiment_score,
    conv_stats.escalation_count,
    conv_stats.quality_rating_avg,
    
    -- Message Metrics
    msg_stats.total_messages,
    msg_stats.patient_messages,
    msg_stats.agent_messages,
    msg_stats.last_message_date,
    msg_stats.last_message_sentiment,
    msg_stats.avg_message_sentiment,
    msg_stats.days_since_last_message,
    
    -- Outreach Metrics
    outreach_stats.total_outreach_attempts,
    outreach_stats.successful_outreach,
    outreach_stats.last_outreach_date,
    outreach_stats.last_outreach_method,
    outreach_stats.last_outreach_outcome,
    outreach_stats.outreach_success_rate,
    outreach_stats.days_since_last_outreach,
    
    -- Engagement Metrics
    CASE 
        WHEN conv_stats.days_since_last_conversation <= 7 THEN 'highly_engaged'
        WHEN conv_stats.days_since_last_conversation <= 30 THEN 'moderately_engaged'
        WHEN conv_stats.days_since_last_conversation <= 90 THEN 'low_engagement'
        ELSE 'disengaged'
    END as engagement_level,
    
    -- Risk Assessment
    CASE 
        WHEN conv_stats.days_since_last_conversation > 90 
             AND EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400 > 180 THEN 'critical'
        WHEN conv_stats.days_since_last_conversation > 60 
             AND EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400 > 120 THEN 'high'
        WHEN conv_stats.days_since_last_conversation > 30 
             AND EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400 > 60 THEN 'medium'
        ELSE 'low'
    END as churn_risk,
    
    -- Lifetime Value Calculation (simplified)
    COALESCE(p.total_appointment_count * 150, 0) as estimated_lifetime_value,
    
    -- Contact Success Prediction
    CASE 
        WHEN outreach_stats.outreach_success_rate > 0.8 THEN 'very_high'
        WHEN outreach_stats.outreach_success_rate > 0.6 THEN 'high'
        WHEN outreach_stats.outreach_success_rate > 0.4 THEN 'medium'
        WHEN outreach_stats.outreach_success_rate > 0.2 THEN 'low'
        ELSE 'very_low'
    END as contact_success_prediction,
    
    -- Action Priority
    CASE 
        WHEN conv_stats.days_since_last_conversation > 90 
             AND EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400 > 180 THEN 1
        WHEN conv_stats.escalation_count > 0 THEN 2
        WHEN conv_stats.days_since_last_conversation > 60 THEN 3
        WHEN conv_stats.days_since_last_conversation > 30 THEN 4
        ELSE 5
    END as action_priority,
    
    -- Calculated Fields
    EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400 as days_since_last_appointment,
    EXTRACT(EPOCH FROM (p.next_appointment_time - NOW()))/86400 as days_until_next_appointment,
    EXTRACT(EPOCH FROM (next_apt.next_appointment_date - NOW()))/86400 as days_until_next_appointment_detailed,
    
    -- Timestamps
    p.created_at as patient_created_at,
    p.updated_at as patient_updated_at,
    p.last_synced_at,
    NOW() as view_generated_at

FROM patients p

-- Join with contact info for treatment notes
LEFT JOIN contacts_deprecated cd ON p.cliniko_patient_id = cd.cliniko_patient_id 
    AND p.organization_id = cd.organization_id

-- Recent Appointment Details
LEFT JOIN LATERAL (
    SELECT 
        a.type as current_appointment_type,
        a.status as current_appointment_status,
        a.notes as current_appointment_notes
    FROM appointments a
    WHERE a.patient_id = p.id 
        AND a.appointment_date <= NOW()
        AND a.deleted_at IS NULL
    ORDER BY a.appointment_date DESC
    LIMIT 1
) recent_apt ON true

-- Next Appointment Details
LEFT JOIN LATERAL (
    SELECT 
        a.appointment_date as next_appointment_date,
        a.status as next_appointment_status,
        a.notes as next_appointment_notes
    FROM appointments a
    WHERE a.patient_id = p.id 
        AND a.appointment_date > NOW()
        AND a.deleted_at IS NULL
    ORDER BY a.appointment_date ASC
    LIMIT 1
) next_apt ON true

-- Conversation Statistics
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*) as total_conversations,
        COUNT(*) FILTER (WHERE c.status = 'active') as active_conversations,
        MAX(c.created_at) as last_conversation_date,
        EXTRACT(EPOCH FROM (NOW() - MAX(c.created_at)))/86400 as days_since_last_conversation,
        MODE() WITHIN GROUP (ORDER BY c.overall_sentiment) as overall_sentiment,
        AVG(c.sentiment_score) as avg_sentiment_score,
        COUNT(*) FILTER (WHERE c.escalation_flag = true) as escalation_count,
        AVG(c.quality_rating) as quality_rating_avg
    FROM conversations c
    WHERE c.contact_id = cd.id
        AND c.organization_id = p.organization_id
        AND c.deleted_at IS NULL
) conv_stats ON true

-- Message Statistics
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*) as total_messages,
        COUNT(*) FILTER (WHERE m.sender_type = 'patient') as patient_messages,
        COUNT(*) FILTER (WHERE m.sender_type = 'agent') as agent_messages,
        MAX(m.timestamp) as last_message_date,
        EXTRACT(EPOCH FROM (NOW() - MAX(m.timestamp)))/86400 as days_since_last_message,
        (SELECT sentiment_label FROM messages WHERE conversation_id IN (
            SELECT id FROM conversations WHERE contact_id = cd.id
        ) ORDER BY timestamp DESC LIMIT 1) as last_message_sentiment,
        AVG(m.sentiment_score) as avg_message_sentiment
    FROM messages m
    WHERE m.conversation_id IN (
        SELECT c.id FROM conversations c 
        WHERE c.contact_id = cd.id 
            AND c.organization_id = p.organization_id
            AND c.deleted_at IS NULL
    )
    AND m.deleted_at IS NULL
) msg_stats ON true

-- Outreach Statistics
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*) as total_outreach_attempts,
        COUNT(*) FILTER (WHERE o.outcome = 'success') as successful_outreach,
        MAX(o.created_at) as last_outreach_date,
        EXTRACT(EPOCH FROM (NOW() - MAX(o.created_at)))/86400 as days_since_last_outreach,
        (SELECT method FROM outreach_log WHERE patient_id = p.id ORDER BY created_at DESC LIMIT 1) as last_outreach_method,
        (SELECT outcome FROM outreach_log WHERE patient_id = p.id ORDER BY created_at DESC LIMIT 1) as last_outreach_outcome,
        CASE 
            WHEN COUNT(*) > 0 THEN COUNT(*) FILTER (WHERE o.outcome = 'success')::float / COUNT(*)::float
            ELSE 0
        END as outreach_success_rate
    FROM outreach_log o
    WHERE o.patient_id = p.id
        AND o.organization_id = p.organization_id
) outreach_stats ON true

WHERE p.is_active IS NOT NULL
ORDER BY 
    CASE 
        WHEN conv_stats.days_since_last_conversation > 90 
             AND EXTRACT(EPOCH FROM (NOW() - p.last_appointment_date))/86400 > 180 THEN 1
        WHEN conv_stats.escalation_count > 0 THEN 2
        WHEN conv_stats.days_since_last_conversation > 60 THEN 3
        WHEN conv_stats.days_since_last_conversation > 30 THEN 4
        ELSE 5
    END,
    conv_stats.last_conversation_date DESC NULLS LAST; 