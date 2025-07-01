# 🔗 Webhook System Testing Guide

## ✅ **What You've Completed**

**Phase 1: Database Setup** ✅
- ✅ Webhook tables created in Supabase
- ✅ RLS policies working
- ✅ Webhook templates available 
- ✅ Analytics views created

**Phase 2: Backend Implementation** ✅
- ✅ WebhookService created (`src/services/webhook_service.py`)
- ✅ Webhook API endpoints created (`src/api/webhooks.py`)
- ✅ Complete logging and retry logic

## 🔧 **Step 1: Register Webhook Router**

Add the webhook router to your main FastAPI app. In your main app file (usually `main.py` or `app.py`):

```python
from src.api import webhooks

# Register the webhook router
app.include_router(webhooks.router)
```

## 🧪 **Step 2: Test the API Endpoints**

### **A. Health Check**
```bash
GET /api/v1/webhooks/health
```

### **B. Get Available Templates**
```bash
GET /api/v1/webhooks/org_2xwiHJY6BaRUIX1DanXG6ZX7/templates
```

### **C. Trigger a Webhook**
```bash
POST /api/v1/webhooks/org_2xwiHJY6BaRUIX1DanXG6ZX7/trigger

{
    "webhook_type": "patient_followup",
    "patient_id": "your_patient_uuid",
    "trigger_data": {
        "campaign_type": "reengagement",
        "priority": "high"
    },
    "user_id": "user_123",
    "trigger_source": "dashboard"
}
```

### **D. Check Webhook Logs**
```bash
GET /api/v1/webhooks/org_2xwiHJY6BaRUIX1DanXG6ZX7/logs
```

### **E. Get Webhook Status**
```bash
GET /api/v1/webhooks/org_2xwiHJY6BaRUIX1DanXG6ZX7/status/{log_id}
```

## 🎯 **Step 3: Test with Frontend Button**

Create a simple test button in your frontend:

```javascript
// Example: Trigger webhook from patient dashboard
const triggerWebhook = async (patientId, webhookType) => {
    try {
        const response = await fetch(`/api/v1/webhooks/${orgId}/trigger`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                webhook_type: webhookType,
                patient_id: patientId,
                trigger_source: 'dashboard',
                user_id: currentUserId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Webhook triggered:', result.log_id);
            // Show success message
        } else {
            console.error('Webhook failed:', result.error);
            // Show error message
        }
    } catch (error) {
        console.error('Failed to trigger webhook:', error);
    }
};

// Usage in React component
<button onClick={() => triggerWebhook(patient.id, 'patient_followup')}>
    Send Follow-up
</button>
```

## 📊 **Step 4: Monitor Webhook Execution**

### **In Supabase:**
```sql
-- Check recent webhook logs
SELECT set_organization_context('org_2xwiHJY6BaRUIX1DanXG6ZX7', 'user');
SELECT * FROM webhook_logs ORDER BY triggered_at DESC LIMIT 10;

-- Check webhook analytics
SELECT * FROM webhook_analytics WHERE organization_id = 'org_2xwiHJY6BaRUIX1DanXG6ZX7';
```

### **API Analytics:**
```bash
GET /api/v1/webhooks/org_2xwiHJY6BaRUIX1DanXG6ZX7/analytics
```

## 🔄 **Step 5: Test Retry Logic**

1. **Trigger a webhook** to a non-existent URL (should fail)
2. **Check the log status** - should show "failed"
3. **Retry the webhook:**
```bash
POST /api/v1/webhooks/org_2xwiHJY6BaRUIX1DanXG6ZX7/retry/{log_id}
```

## 🚨 **Common Issues & Solutions**

### **Issue: "No webhook template found"**
```sql
-- Check your templates
SELECT set_organization_context('your_org_id', 'user');
SELECT name, webhook_type, is_active FROM webhook_templates;
```

### **Issue: RLS Permission Denied**
```sql
-- Reset organization context
SELECT set_organization_context('your_org_id', 'user');
```

### **Issue: N8N Webhook Not Responding**
- Check your N8N webhook URL is correct
- Test the N8N webhook directly with curl
- Check N8N workflow is active

## 📝 **Sample Payloads Sent to N8N**

When you trigger a `patient_followup` webhook, N8N receives:

```json
{
    "patient": {
        "id": "patient_uuid",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890"
    },
    "organization": {
        "id": "org_2xwiHJY6BaRUIX1DanXG6ZX7",
        "name": "Healthcare Clinic"
    },
    "trigger": {
        "type": "followup",
        "source": "dashboard",
        "user_id": "user_123",
        "timestamp": "2025-01-01T10:30:00Z"
    },
    "context": {
        "last_appointment": "2024-12-15",
        "risk_level": "high",
        "engagement_status": "dormant"
    }
}
```

## 🎉 **Success Indicators**

You'll know everything is working when:

- ✅ Webhook API endpoints respond successfully
- ✅ Templates are retrieved correctly
- ✅ Webhook triggers create log entries in Supabase
- ✅ N8N workflows receive the payload and execute
- ✅ Response data is logged back to Supabase
- ✅ Frontend buttons show real-time status

## 🚀 **Next Steps: Frontend Integration**

Ready for **Phase 4: Frontend Integration**?

1. Add webhook trigger buttons to patient dashboard
2. Implement real-time status indicators
3. Create webhook history views
4. Add bulk webhook actions

The backend is now complete and ready for frontend integration! 🎯 