# Stripe Integration Analysis & Implementation Plan

Based on codebase analysis, here's the comprehensive status of your Stripe integration:

## 📊 **Current Status Analysis**

### ✅ **What's Already Set Up:**
- **Database Schema**: Organizations table has Stripe fields:
  ```sql
  stripe_customer_id character varying UNIQUE,
  subscription_status character varying DEFAULT 'trial'::character varying,
  subscription_plan character varying DEFAULT 'basic'::character varying,
  ```
- **Multi-tenant Architecture**: Perfect for organization-level billing
- **Clerk Authentication**: Strong foundation for user management
- **Webhook Infrastructure**: Existing webhook system can be extended

### ❌ **What's Missing (All of it):**
- **No Stripe API keys configured** (no STRIPE_ env vars)
- **No /api/stripe/webhook/ endpoint** (only Clerk webhooks exist)
- **No Clerk → Stripe customer mapping implementation**
- **No webhook signature verification**
- **No subscription lifecycle handling**
- **No payment failure/dunning management**
- **No Customer Portal integration**

---

## 🚀 **Immediate Implementation Needs**

### 1. **Environment Setup**
```bash
# Add to .env
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. **Core Stripe Client** 
```python
# src/integrations/stripe_client.py
import stripe
import os

class StripeClient:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
    async def create_customer_for_organization(self, org_id, email, name):
        """Map Clerk org to Stripe customer"""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={'organization_id': org_id}
        )
        
        # Update org record
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE organizations 
                SET stripe_customer_id = %s 
                WHERE id = %s
            """, [customer.id, org_id])
        
        return customer.id
```

### 3. **Billing API Endpoints**
```python
# src/api/billing.py
@router.post("/{organization_id}/customer")
async def create_stripe_customer(org_id: str = Depends(verify_organization_access)):
    """Create Stripe customer for Clerk organization"""
    
@router.post("/{organization_id}/subscription") 
async def create_subscription(org_id: str = Depends(verify_organization_access)):
    """Start subscription for organization"""
    
@router.get("/{organization_id}/portal")
async def customer_portal_url(org_id: str = Depends(verify_organization_access)):
    """Get Customer Portal URL for billing management"""
```

### 4. **Webhook Handler**
```python
# src/api/stripe_webhooks.py
@router.post("/stripe/webhook")
async def stripe_webhook_handler(request: Request):
    """Handle Stripe events with signature verification"""
    # Verify webhook signature
    # Handle subscription.created, updated, deleted
    # Handle payment.succeeded, payment.failed
    # Update organization subscription_status
```

---

## 📋 **Critical Questions for You**

### **Product/Pricing Setup:**
1. **What pricing tiers do you want?**
   - Suggestion: Basic ($29/mo), Pro ($79/mo), Enterprise ($199/mo)
   
2. **Usage-based billing?**
   - SMS/Email credits for reengagement campaigns?
   - Webhook call metering?
   
3. **Trial period?**
   - Free trial length (7/14/30 days)?
   - Feature limitations during trial?

### **Business Logic:**
1. **Billing at organization level?** (Yes, based on your schema)
2. **How to handle failed payments?**
   - Grace period before feature restrictions?
   - Automated dunning emails?
   
3. **Feature restrictions per plan?**
   - Patient limits per tier?
   - Reengagement features gated?

---

## 🎯 **3-Week Implementation Plan**

### **Week 1: Core Integration**
- [ ] Set up Stripe test account & webhook endpoints
- [ ] Implement StripeClient and basic customer creation
- [ ] Create billing API endpoints
- [ ] Test Clerk org → Stripe customer mapping

### **Week 2: Subscription Management**
- [ ] Implement subscription creation/updates
- [ ] Add webhook signature verification
- [ ] Handle subscription lifecycle events
- [ ] Update organization status based on events

### **Week 3: Frontend & Polish**
- [ ] Add Stripe.js to frontend
- [ ] Customer Portal integration
- [ ] Payment form with Stripe Elements
- [ ] Failed payment handling UI

---

## 💡 **Integration with Your Existing Features**

### **Reengagement API Billing Gates:**
```python
# Gate premium reengagement features by subscription
@router.get("/{organization_id}/prioritized")
async def get_prioritized_patients(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    # Check subscription status
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT subscription_status, subscription_plan 
            FROM organizations WHERE id = %s
        """, [organization_id])
        org = cursor.fetchone()
    
    # Limit features based on plan
    if org['subscription_plan'] == 'basic':
        limit = min(limit, 10)  # Basic: max 10 results
    elif org['subscription_status'] != 'active':
        raise HTTPException(403, "Subscription required")
```

### **Treatment Notes Access Control:**
```python
# Gate treatment notes by subscription level
if org['subscription_plan'] in ['basic'] and include_treatment_notes:
    raise HTTPException(403, "Treatment notes require Pro subscription")
```

---

## 🔒 **Security Implementation**

### **Webhook Security:**
```python
import stripe

def verify_stripe_webhook(payload, signature, secret):
    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
        return event
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid webhook signature")
```

### **Payment Method Security:**
- **Never store card details** (use Stripe vault)
- **Use Stripe Elements** for PCI compliance
- **Environment variable protection** for API keys

---

## 📈 **Recommended Stripe Dashboard Setup**

### **Products to Create:**
1. **Routiq Basic** - $29/month
   - 50 patients max
   - Basic reengagement features
   
2. **Routiq Professional** - $79/month  
   - Unlimited patients
   - Advanced reengagement with treatment notes
   - Webhook integrations
   
3. **Routiq Enterprise** - $199/month
   - Everything in Pro
   - Priority support
   - Custom features

### **Webhook Events to Monitor:**
- `customer.subscription.created`
- `customer.subscription.updated` 
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

---

## 🎯 **Next Steps**

1. **Set up Stripe test account** with webhook endpoints
2. **Choose your pricing strategy** (fixed vs usage-based)
3. **Implement the StripeClient** for customer/subscription management
4. **Add billing endpoints** to your existing API structure
5. **Test the integration** with your existing Clerk organizations

Your foundation is solid - you just need to build the Stripe layer on top of your existing architecture. The patient reengagement API we just built will integrate perfectly with subscription-based feature gating! 