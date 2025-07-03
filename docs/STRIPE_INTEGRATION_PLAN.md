# Stripe Integration Implementation Plan

Based on the current codebase analysis, here's a comprehensive plan to implement Stripe billing integration with Clerk authentication.

## 📊 Current State Analysis

### ✅ What's Already Set Up:
- Organization-level billing schema (`stripe_customer_id`, `subscription_status`, `subscription_plan`)
- Clerk authentication and organization management
- Webhook infrastructure (for N8N, can be extended for Stripe)
- Multi-tenant architecture with RLS

### ❌ What's Missing:
- Stripe API client and configuration
- Stripe webhook endpoints and signature verification
- Clerk ↔ Stripe customer mapping
- Subscription lifecycle management
- Payment failure handling
- Customer Portal integration

---

## 🎯 Implementation Plan

### Phase 1: Core Stripe Setup (Week 1)

#### 1.1 Environment Configuration
```bash
# Add to .env and config/env.example
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_ENVIRONMENT=test  # or 'live'
```

#### 1.2 Stripe Client Setup
```python
# src/integrations/stripe_client.py
import stripe
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StripeClient:
    """Stripe integration for subscription billing"""
    
    def __init__(self):
        self.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable required")
        
        stripe.api_key = self.api_key
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
    async def create_customer(self, organization_id: str, email: str, name: str) -> Dict[str, Any]:
        """Create Stripe customer for organization"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'organization_id': organization_id,
                    'source': 'routiq_app'
                }
            )
            
            # Update organization with Stripe customer ID
            with db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE organizations 
                    SET stripe_customer_id = %s, updated_at = NOW()
                    WHERE id = %s
                """, [customer.id, organization_id])
                db.connection.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for org {organization_id}")
            return {
                "success": True,
                "customer_id": customer.id,
                "organization_id": organization_id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_subscription(self, customer_id: str, price_id: str) -> Dict[str, Any]:
        """Create subscription for customer"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                payment_settings={
                    'save_default_payment_method': 'on_subscription'
                },
                expand=['latest_invoice.payment_intent']
            )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                "status": subscription.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation failed: {e}")
            return {"success": False, "error": str(e)}
```

#### 1.3 Stripe API Endpoints
```python
# src/api/stripe_billing.py
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from src.api.auth import verify_organization_access
from src.integrations.stripe_client import StripeClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
stripe_client = StripeClient()

class CreateCustomerRequest(BaseModel):
    email: str
    name: str

class CreateSubscriptionRequest(BaseModel):
    price_id: str

@router.post("/{organization_id}/customer")
async def create_stripe_customer(
    request: CreateCustomerRequest,
    organization_id: str = Depends(verify_organization_access)
):
    """Create Stripe customer for organization"""
    result = await stripe_client.create_customer(
        organization_id=organization_id,
        email=request.email,
        name=request.name
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/{organization_id}/subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    organization_id: str = Depends(verify_organization_access)
):
    """Create subscription for organization"""
    # Get Stripe customer ID
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT stripe_customer_id FROM organizations WHERE id = %s",
            [organization_id]
        )
        result = cursor.fetchone()
        
    if not result or not result['stripe_customer_id']:
        raise HTTPException(
            status_code=400, 
            detail="Organization must have Stripe customer before creating subscription"
        )
    
    subscription_result = await stripe_client.create_subscription(
        customer_id=result['stripe_customer_id'],
        price_id=request.price_id
    )
    
    if not subscription_result["success"]:
        raise HTTPException(status_code=400, detail=subscription_result["error"])
    
    return subscription_result

@router.get("/{organization_id}/portal")
async def get_customer_portal_url(
    organization_id: str = Depends(verify_organization_access)
):
    """Get Stripe Customer Portal URL"""
    # Get Stripe customer ID
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT stripe_customer_id FROM organizations WHERE id = %s",
            [organization_id]
        )
        result = cursor.fetchone()
        
    if not result or not result['stripe_customer_id']:
        raise HTTPException(
            status_code=400, 
            detail="No Stripe customer found for organization"
        )
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=result['stripe_customer_id'],
            return_url=f"{os.getenv('FRONTEND_URL')}/billing"
        )
        
        return {"portal_url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

### Phase 2: Webhook Integration (Week 2)

#### 2.1 Stripe Webhook Handler
```python
# src/api/stripe_webhooks.py
from fastapi import APIRouter, HTTPException, Request
import stripe
import json
import logging
from src.database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-webhooks"])

@router.post("/webhook")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event['type']
    data = event['data']['object']
    
    try:
        if event_type == 'customer.subscription.created':
            await handle_subscription_created(data)
        elif event_type == 'customer.subscription.updated':
            await handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            await handle_subscription_cancelled(data)
        elif event_type == 'invoice.payment_succeeded':
            await handle_payment_succeeded(data)
        elif event_type == 'invoice.payment_failed':
            await handle_payment_failed(data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
    
    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
    
    return {"status": "success"}

async def handle_subscription_created(subscription):
    """Handle new subscription creation"""
    customer_id = subscription['customer']
    subscription_id = subscription['id']
    status = subscription['status']
    
    # Find organization by Stripe customer ID
    with db.get_cursor() as cursor:
        cursor.execute("""
            UPDATE organizations 
            SET subscription_status = %s,
                subscription_plan = %s,
                updated_at = NOW()
            WHERE stripe_customer_id = %s
            RETURNING id
        """, [status, 'pro', customer_id])  # Map to your plan names
        
        result = cursor.fetchone()
        db.connection.commit()
        
    if result:
        logger.info(f"Updated subscription for org {result['id']}: {status}")
    else:
        logger.warning(f"No organization found for Stripe customer {customer_id}")

async def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice['customer']
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            UPDATE organizations 
            SET subscription_status = 'past_due',
                updated_at = NOW()
            WHERE stripe_customer_id = %s
            RETURNING id, name
        """, [customer_id])
        
        result = cursor.fetchone()
        db.connection.commit()
        
    if result:
        org_id = result['id']
        org_name = result['name']
        
        # Log the failed payment
        logger.warning(f"Payment failed for organization {org_name} ({org_id})")
        
        # TODO: Send notification email
        # TODO: Trigger reengagement workflow
```

### Phase 3: Frontend Integration (Week 3)

#### 3.1 React Billing Component
```tsx
// Frontend billing component
import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY);

const BillingDashboard = ({ organizationId }) => {
  const [billingInfo, setBillingInfo] = useState(null);
  
  const openCustomerPortal = async () => {
    try {
      const response = await fetch(`/api/v1/billing/${organizationId}/portal`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      const data = await response.json();
      window.location.href = data.portal_url;
      
    } catch (error) {
      console.error('Failed to open customer portal:', error);
    }
  };

  return (
    <div className="billing-dashboard">
      <div className="billing-header">
        <h2>Billing & Subscription</h2>
        <button onClick={openCustomerPortal} className="btn-secondary">
          Manage Billing
        </button>
      </div>
      
      <Elements stripe={stripePromise}>
        <SubscriptionForm organizationId={organizationId} />
      </Elements>
    </div>
  );
};

const SubscriptionForm = ({ organizationId }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    if (!stripe || !elements) return;

    // Create subscription
    const response = await fetch(`/api/v1/billing/${organizationId}/subscription`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        price_id: 'price_pro_monthly'  // Your Stripe price ID
      })
    });

    const { client_secret } = await response.json();

    // Confirm payment
    const result = await stripe.confirmCardPayment(client_secret, {
      payment_method: {
        card: elements.getElement(CardElement)
      }
    });

    if (result.error) {
      console.error('Payment failed:', result.error);
    } else {
      console.log('Payment succeeded!');
      // Redirect to success page
    }
    
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement />
      <button type="submit" disabled={!stripe || loading}>
        {loading ? 'Processing...' : 'Subscribe'}
      </button>
    </form>
  );
};
```

### Phase 4: Database Schema Updates

```sql
-- Add subscription tracking tables
CREATE TABLE IF NOT EXISTS subscription_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    stripe_subscription_id TEXT,
    stripe_customer_id TEXT,
    event_type TEXT NOT NULL,
    event_data JSONB,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_subscription_events_org 
ON subscription_events(organization_id);

CREATE INDEX IF NOT EXISTS idx_subscription_events_stripe_sub 
ON subscription_events(stripe_subscription_id);

-- Update organizations table
ALTER TABLE organizations 
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP WITH TIME ZONE;
```

---

## 🎯 Pricing & Product Recommendations

### Suggested Stripe Products:
1. **Basic Plan**: $29/month - Single organization, basic features
2. **Professional Plan**: $79/month - Advanced reengagement, webhooks
3. **Enterprise Plan**: $199/month - Custom features, priority support

### Usage-Based Components (Optional):
- **SMS Credits**: $0.05 per SMS for reengagement campaigns
- **Email Credits**: $0.01 per email
- **Webhook Calls**: $0.001 per webhook trigger

---

## 📋 Implementation Checklist

### Week 1: Core Setup
- [ ] Add Stripe environment variables
- [ ] Implement StripeClient class
- [ ] Create billing API endpoints
- [ ] Test customer creation with Clerk integration

### Week 2: Webhooks
- [ ] Implement webhook signature verification
- [ ] Handle subscription lifecycle events
- [ ] Add failed payment processing
- [ ] Test webhook endpoints with Stripe CLI

### Week 3: Frontend
- [ ] Add Stripe.js to frontend
- [ ] Implement subscription form
- [ ] Add Customer Portal integration
- [ ] Test end-to-end billing flow

### Week 4: Production Readiness
- [ ] Set up production Stripe account
- [ ] Configure webhook endpoints in Stripe dashboard
- [ ] Add monitoring and error handling
- [ ] Deploy and test with real payments

---

## 🔒 Security Considerations

1. **Webhook Security**: Always verify Stripe webhook signatures
2. **API Key Management**: Store keys in secure environment variables
3. **Customer Data**: Never store payment method details (use Stripe vault)
4. **RLS Compliance**: Ensure billing data respects organization boundaries
5. **PCI Compliance**: Use Stripe Elements for card collection

---

## 📊 Monitoring & Analytics

```python
# Add to audit_logs for billing events
async def log_billing_event(organization_id: str, event_type: str, details: Dict):
    with db.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO audit_logs (
                organization_id, action, resource_type, details, created_at
            ) VALUES (%s, %s, 'billing', %s, NOW())
        """, [organization_id, event_type, json.dumps(details)])
        db.connection.commit()
```

This implementation plan integrates seamlessly with your existing Clerk authentication and multi-tenant architecture while providing comprehensive billing functionality. 