# Backend API Synchronization Guide

## 🏗️ Architecture Overview

This is a **Next.js 15** multi-tenant SaaS application that serves as a hub for healthcare practice management integrations. The system synchronizes data between multiple external services and provides a unified dashboard for practice analytics.

### **Core Technology Stack**
- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, Radix UI
- **Authentication**: Clerk (with organization support)
- **Database**: PostgreSQL with Prisma ORM
- **Main Database**: Supabase
- **External APIs**: Cliniko, Chatwoot, Stripe, ManyChat (configured but not implemented)
- **Deployment**: Production-ready with Docker support

---

## 🔗 Current Integration Status

### ✅ **Fully Implemented**
1. **Clerk ↔ Supabase Sync** - Complete user/organization synchronization
2. **Stripe ↔ Supabase Sync** - Billing and subscription management
3. **Chatwoot → Supabase Import** - Conversation data extraction (via Python scripts)

### 🟡 **Partially Implemented**
1. **Chatwoot API Integration** - Data access layer exists, needs real-time sync
2. **Cliniko Integration** - Database schema ready, API integration needed

### ❌ **Not Implemented**
1. **ManyChat Integration** - Schema exists, needs implementation
2. **Real-time Webhooks** - Only Clerk and Stripe webhooks are active

---

## 📊 Database Architecture

### **Multi-Tenant Organization Model**
```sql
-- Core organization table
organizations (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  cliniko_instance_id VARCHAR(255),    -- Links to Cliniko practice
  chatwoot_account_id VARCHAR(255),    -- Links to Chatwoot account
  manychat_workspace_id VARCHAR(255),  -- Links to ManyChat workspace
  stripe_customer_id VARCHAR(255),     -- Links to Stripe customer
  subscription_status VARCHAR(50),     -- trial, active, past_due, canceled
  subscription_plan VARCHAR(50),       -- basic, pro, enterprise
  settings JSONB,                      -- Organization-specific config
  -- ... audit fields
)

-- User-organization relationships
organization_users (
  id UUID PRIMARY KEY,
  organization_id UUID,
  clerk_user_id VARCHAR(255),          -- Links to Clerk user
  role VARCHAR(50),                    -- admin, staff, viewer
  permissions JSONB,                   -- Granular permissions
  status VARCHAR(50),                  -- active, inactive, pending
  -- ... audit fields
)
```

### **Patient Data Model**
```sql
patients (
  id UUID PRIMARY KEY,
  organization_id UUID,                -- Multi-tenant isolation
  phone VARCHAR(20) UNIQUE,
  email VARCHAR(255),
  name VARCHAR(255),
  cliniq_id VARCHAR(100) UNIQUE,       -- Links to Cliniko patient
  status VARCHAR(50),
  metadata JSONB,                      -- Flexible patient data
  -- ... audit fields
)

active_patients (
  id BIGSERIAL PRIMARY KEY,
  organization_id UUID,                -- Multi-tenant isolation
  cliniko_patient_id TEXT,             -- Links to Cliniko
  name TEXT,
  recent_appointment_count INTEGER,
  upcoming_appointment_count INTEGER,
  last_appointment_date TIMESTAMP,
  recent_appointments JSONB,           -- Structured appointment data
  upcoming_appointments JSONB,
  -- ... analytics fields
)
```

### **Conversation Data Model**
```sql
conversations (
  id UUID PRIMARY KEY,
  organization_id UUID,                -- Multi-tenant isolation
  patient_id UUID,                     -- Links to patient
  source VARCHAR(50),                  -- 'chatwoot', 'manychat', etc.
  external_id VARCHAR(255),            -- Source system conversation ID
  status VARCHAR(50),
  metadata JSONB,                      -- Source-specific data
  -- ... audit fields
)

messages (
  id UUID PRIMARY KEY,
  organization_id UUID,                -- Multi-tenant isolation
  conversation_id UUID,
  content TEXT,
  sender_type VARCHAR(50),             -- 'user', 'agent', 'system'
  external_id VARCHAR(255),            -- Source system message ID
  timestamp TIMESTAMP,
  metadata JSONB,                      -- Source-specific data
  -- ... audit fields
)
```

---

## 🔐 Authentication & Authorization Flow

### **Clerk Integration**
```typescript
// File: src/lib/auth/clerk-sync.ts
// Handles automatic user-organization synchronization

// On user sign-up/sign-in:
1. Clerk authenticates user
2. Webhook triggers user sync: /api/webhooks/clerk
3. ensureUserInOrganization() creates organization association
4. User gains access to organization-scoped data
```

### **Webhook Handlers**
```typescript
// File: src/app/api/webhooks/clerk/route.ts
// Supported events:
- user.created, user.updated, user.deleted
- organization.created, organization.updated, organization.deleted
- organizationMembership.created, organizationMembership.updated, organizationMembership.deleted
```

### **Row Level Security (RLS)**
```sql
-- All tables have organization_id for tenant isolation
-- Supabase RLS policies filter data by organization
-- Clerk JWT tokens contain organization context
```

---

## 💳 Stripe Integration

### **Billing Sync Flow**
```typescript
// File: src/app/api/stripe/webhook/route.ts
// Supported events:

customer.subscription.created/updated:
→ Update organization.subscription_status
→ Update organization.subscription_plan
→ Link organization.stripe_customer_id

customer.subscription.deleted:
→ Set organization.subscription_status = 'canceled'

invoice.payment_succeeded:
→ Log successful payment
→ Update organization billing info

invoice.payment_failed:
→ Log failed payment
→ Trigger payment failure handling
```

### **Subscription Management**
```typescript
// Organizations table tracks:
- stripe_customer_id: Links to Stripe customer
- subscription_status: trial, active, past_due, canceled
- subscription_plan: basic, pro, enterprise
- billing_email: Customer email
- billing_address: JSON billing information
```

---

## 💬 Chatwoot Integration

### **Current Implementation**
```python
# File: scripts/chatwoot_data_access.py
# One-time data extraction via Python scripts

class ChatwootDataAccess:
    def get_conversations()          # Extracts all conversations
    def get_agent_performance()      # Calculates response times
    def get_daily_message_volume()   # Message volume analytics
```

### **Database Schema**
```sql
-- File: database/schema/chatwoot_schema.sql
chatwoot_contacts (
  id BIGINT PRIMARY KEY,
  cliniko_id VARCHAR(255),           -- Links to Cliniko patient
  phone_number VARCHAR(50),
  email VARCHAR(255),
  custom_attributes JSONB
)

chatwoot_conversations (
  id BIGINT PRIMARY KEY,
  contact_id BIGINT,
  assignee_id BIGINT,               -- Agent ID
  status VARCHAR(50),               -- open, resolved, pending
  total_messages INTEGER,
  customer_messages INTEGER,
  agent_messages INTEGER,
  avg_response_time_minutes DECIMAL
)

chatwoot_messages (
  id BIGINT PRIMARY KEY,
  conversation_id BIGINT,
  content TEXT,
  message_type VARCHAR(50),         -- incoming, outgoing, activity
  sender_type VARCHAR(50),          -- user, agent, system
  created_at TIMESTAMP
)
```

### **API Endpoints**
```typescript
// File: src/app/api/chatwoot/
GET /api/chatwoot/conversations     # Conversation summaries
GET /api/chatwoot/agent-performance # Agent metrics
GET /api/chatwoot/daily-volume     # Message volume data

// Organization-scoped access with Clerk authentication
// Currently returns mock data - needs database integration
```

---

## 🏥 Cliniko Integration

### **Planned Architecture**
```typescript
// Cliniko stores patient data, appointments, treatments
// Integration points:

1. Patient Sync:
   - Import patients from Cliniko API
   - Link patients by cliniko_patient_id
   - Sync appointment data to active_patients table

2. Appointment Analytics:
   - Recent appointment count
   - Upcoming appointment count
   - Churn analysis (patients without recent appointments)

3. Real-time Sync:
   - Webhook from Cliniko on patient/appointment changes
   - Background job to sync patient data
```

### **Database Mapping**
```sql
-- Existing fields ready for Cliniko integration:
patients.cliniq_id              → Cliniko patient ID
active_patients.cliniko_patient_id → Cliniko patient ID
organizations.cliniko_instance_id  → Cliniko practice ID
```

---

## 📱 ManyChat Integration (Future)

### **Planned Implementation**
```typescript
// ManyChat handles WhatsApp automation and flows
// Integration points:

1. Contact Sync:
   - Sync ManyChat subscribers with patients
   - Link by phone number or email

2. Conversation Import:
   - Import ManyChat conversation data
   - Unified conversation view with Chatwoot

3. Automation Triggers:
   - Trigger ManyChat flows from app events
   - Appointment reminders, follow-ups
```

### **Database Schema**
```sql
-- Ready for ManyChat integration:
organizations.manychat_workspace_id → ManyChat workspace
conversations.source = 'manychat'   → ManyChat conversations
```

---

## 🔄 Data Synchronization Patterns

### **Current Sync Methods**

#### 1. **Webhook-Based (Real-time)**
```typescript
// Used for: Clerk, Stripe
// Pattern: External service → Webhook → Database update
// Files: /api/webhooks/clerk/, /api/webhooks/stripe/

Pros: Real-time, reliable
Cons: Requires webhook endpoint management
```

#### 2. **Batch Import (Python Scripts)**
```python
# Used for: Chatwoot historical data
# Pattern: Script → External API → Database bulk insert
# Files: scripts/extract_conversations.py

Pros: Handles large datasets, historical data
Cons: Not real-time, manual execution
```

#### 3. **API Polling (Not implemented)**
```typescript
// Planned for: Cliniko, ManyChat
// Pattern: Scheduled job → External API → Database update

Pros: Works without webhooks
Cons: Potential delays, rate limiting
```

### **Recommended Sync Strategy**

#### **For Cliniko Integration:**
```typescript
// 1. Initial Import (Batch)
async function importClinikoPatients(organizationId: string) {
  const clinikoApi = new ClinikoAPI(organization.cliniko_instance_id)
  const patients = await clinikoApi.getPatients()
  
  for (const patient of patients) {
    await upsertPatient({
      organizationId,
      clinikoId: patient.id,
      name: patient.name,
      email: patient.email,
      phone: patient.phone
    })
  }
}

// 2. Real-time Sync (Webhook)
POST /api/webhooks/cliniko
→ Verify webhook signature
→ Update patient record
→ Trigger analytics recalculation

// 3. Incremental Sync (Scheduled)
// Daily job to sync appointment changes
async function syncClinikoAppointments() {
  const since = lastSyncTime()
  const appointments = await clinikoApi.getAppointments({ since })
  await updateActivePatients(appointments)
}
```

#### **For ManyChat Integration:**
```typescript
// 1. Contact Sync
async function syncManyChatContacts(organizationId: string) {
  const manychatApi = new ManyChatAPI(organization.manychat_workspace_id)
  const subscribers = await manychatApi.getSubscribers()
  
  for (const subscriber of subscribers) {
    const patient = await findPatientByPhone(subscriber.phone)
    if (patient) {
      await linkManyChatContact(patient.id, subscriber.id)
    }
  }
}

// 2. Conversation Import
async function importManyChatConversations() {
  const conversations = await manychatApi.getConversations()
  await importConversations(conversations, 'manychat')
}
```

---

## 🔧 Implementation Priorities

### **Phase 1: Complete Chatwoot Integration**
```typescript
// 1. Replace mock data with real database queries
// File: src/app/api/chatwoot/*/route.ts
- Connect to chatwoot_conversations table
- Implement organization filtering
- Add real-time conversation sync

// 2. Set up Chatwoot webhook endpoint
// File: src/app/api/webhooks/chatwoot/route.ts
- Handle conversation.created, conversation.updated
- Handle message.created events
- Update conversation analytics
```

### **Phase 2: Implement Cliniko Integration**
```typescript
// 1. Create Cliniko API client
// File: src/lib/integrations/cliniko-api.ts
- Patient management
- Appointment retrieval
- Practice information

// 2. Patient synchronization
// File: src/lib/sync/cliniko-sync.ts
- Initial patient import
- Incremental sync
- Appointment analytics

// 3. Webhook endpoint
// File: src/app/api/webhooks/cliniko/route.ts
- Patient updates
- Appointment changes
- Practice updates
```

### **Phase 3: Add ManyChat Integration**
```typescript
// 1. ManyChat API client
// File: src/lib/integrations/manychat-api.ts
- Subscriber management
- Conversation retrieval
- Flow triggering

// 2. Contact synchronization
// File: src/lib/sync/manychat-sync.ts
- Link subscribers to patients
- Import conversation history
- Automation triggers

// 3. Webhook endpoint
// File: src/app/api/webhooks/manychat/route.ts
- Subscriber updates
- Message events
- Flow completions
```

---

## 🔒 Security & Compliance

### **Multi-Tenant Data Isolation**
```typescript
// Every database query includes organization filtering:
const conversations = await prisma.conversation.findMany({
  where: {
    organizationId: context.organizationId  // Always filter by org
  }
})

// Row Level Security (RLS) in Supabase provides additional protection
// Clerk JWT tokens contain organization context
```

### **API Authentication**
```typescript
// All API routes use Clerk authentication:
import { auth } from '@clerk/nextjs/server'

export async function GET(request: NextRequest) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  // Get organization context
  const context = await getOrganizationContext(userId)
  // ... organization-scoped data access
}
```

### **Webhook Security**
```typescript
// All webhooks verify signatures:
// Clerk: Svix signature verification
// Stripe: Stripe signature verification
// Custom webhooks should implement HMAC verification
```

### **Data Encryption**
```typescript
// Database: PostgreSQL with encryption at rest
// API: HTTPS only
// Sensitive data: Encrypted in JSONB fields where needed
```

---

## 🚀 Getting Started - Implementation Steps

### **1. Environment Setup**
```bash
# Required environment variables:
DATABASE_URL=postgresql://...                    # Main Supabase database
CHATWOOT_DATABASE_URL=postgresql://...          # Chatwoot database (optional)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...        # Clerk public key
CLERK_SECRET_KEY=sk_...                         # Clerk secret key
CLERK_WEBHOOK_SECRET=whsec_...                  # Clerk webhook secret
STRIPE_SECRET_KEY=sk_...                        # Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_...                 # Stripe webhook secret

# Future integrations:
CLINIKO_API_KEY=...                             # Cliniko API key
MANYCHAT_API_TOKEN=...                          # ManyChat API token
```

### **2. Database Migration**
```sql
-- Apply the complete schema:
-- File: prisma/schema.prisma
npx prisma generate
npx prisma db push

-- Import Chatwoot schema (if using separate database):
-- File: database/schema/chatwoot_schema.sql
```

### **3. Complete Chatwoot Integration**
```typescript
// Replace mock data in API endpoints:
// Files: src/app/api/chatwoot/*/route.ts

// 1. Update conversation endpoint:
const conversations = await getChatwootConversations(status, daysBack)

// 2. Add organization filtering:
conversations = conversations.filter(conv => 
  conv.organization_id === context.organizationId
)

// 3. Implement real-time webhook:
// File: src/app/api/webhooks/chatwoot/route.ts
```

### **4. Implement Cliniko Integration**
```typescript
// 1. Create API client:
// File: src/lib/integrations/cliniko-api.ts
export class ClinikoAPI {
  constructor(instanceId: string, apiKey: string) {}
  
  async getPatients(params?: GetPatientsParams) {}
  async getAppointments(params?: GetAppointmentsParams) {}
  async getPatient(id: string) {}
}

// 2. Create sync service:
// File: src/lib/sync/cliniko-sync.ts
export async function syncClinikoPatients(organizationId: string) {}
export async function syncClinikoAppointments(organizationId: string) {}

// 3. Add webhook endpoint:
// File: src/app/api/webhooks/cliniko/route.ts
```

### **5. Add Background Jobs**
```typescript
// Use Vercel Cron or external job scheduler:
// File: src/app/api/cron/sync-cliniko/route.ts
export async function GET() {
  const organizations = await getActiveOrganizations()
  
  for (const org of organizations) {
    if (org.cliniko_instance_id) {
      await syncClinikoAppointments(org.id)
    }
  }
}

// Schedule: Daily at 3 AM
// Vercel cron: 0 3 * * *
```

---

## 📋 API Reference

### **Organization Management**
```typescript
GET    /api/organization                        # Get current organization
PUT    /api/organization                        # Update organization
POST   /api/organization/integrations           # Configure integrations
```

### **Patient Management**
```typescript
GET    /api/patients                            # List patients (org-scoped)
GET    /api/patients/[id]                       # Get patient details
POST   /api/patients                            # Create patient
PUT    /api/patients/[id]                       # Update patient
GET    /api/active-patients                     # Get active patients with analytics
```

### **Conversation Management**
```typescript
GET    /api/conversations                       # List conversations (org-scoped)
GET    /api/conversations/[id]                  # Get conversation details
GET    /api/conversations/phone/[phone]         # Get conversation by phone
POST   /api/conversations                       # Create conversation
```

### **Chatwoot Integration**
```typescript
GET    /api/chatwoot/conversations              # Chatwoot conversation summaries
GET    /api/chatwoot/agent-performance          # Agent metrics
GET    /api/chatwoot/daily-volume               # Message volume analytics
```

### **Analytics & Reporting**
```typescript
GET    /api/dashboard/metrics                   # Dashboard metrics
GET    /api/analytics/conversations             # Conversation analytics
GET    /api/analytics/patients                  # Patient analytics
```

### **Webhook Endpoints**
```typescript
POST   /api/webhooks/clerk                      # Clerk user/org sync
POST   /api/webhooks/stripe                     # Stripe billing sync
POST   /api/webhooks/chatwoot                   # Chatwoot conversation sync
POST   /api/webhooks/cliniko                    # Cliniko patient/appointment sync
POST   /api/webhooks/manychat                   # ManyChat conversation sync
```

---

## 🐛 Common Issues & Solutions

### **1. Organization Context Missing**
```typescript
// Error: User not associated with organization
// Solution: Ensure user is created in organization_users table
await ensureUserInOrganization(clerkUserId, organizationId)
```

### **2. Cross-Organization Data Exposure**
```typescript
// Error: User sees data from other organizations
// Solution: Always filter by organization_id
const data = await prisma.table.findMany({
  where: { organizationId: context.organizationId }
})
```

### **3. Webhook Signature Verification Fails**
```typescript
// Error: Webhook signature invalid
// Solution: Check webhook secret configuration
const signature = headers.get('stripe-signature')
const event = stripe.webhooks.constructEvent(body, signature, webhookSecret)
```

### **4. Database Connection Issues**
```typescript
// Error: Cannot connect to Chatwoot database
// Solution: Set CHATWOOT_DATABASE_URL or use main database
const dbUrl = process.env.CHATWOOT_DATABASE_URL || process.env.DATABASE_URL
```

---

## 📈 Monitoring & Observability

### **Audit Logging**
```typescript
// All sensitive operations are logged:
console.log(`[AUDIT] Organization access`, {
  userId: context.clerkUserId,
  organizationId: context.organizationId,
  action: 'READ_CONVERSATIONS',
  timestamp: new Date().toISOString()
})
```

### **Error Tracking**
```typescript
// File: src/lib/logging/logger.ts
// Structured logging for API errors
logger.error('Chatwoot API Error', {
  organizationId,
  error: error.message,
  requestId
})
```

### **Performance Monitoring**
```typescript
// Request timing and organization metrics
const startTime = Date.now()
// ... process request
const processingTime = Date.now() - startTime
```

---

## 🔄 Data Flow Diagrams

### **User Authentication Flow**
```
User Sign-in → Clerk → Webhook → Database → Organization Context → API Access
```

### **Patient Data Sync Flow**
```
Cliniko API → Background Job → Database → Dashboard Updates
```

### **Conversation Data Flow**
```
Chatwoot → Webhook → Database → Real-time Updates → Dashboard
```

### **Billing Flow**
```
Stripe Event → Webhook → Organization Update → Access Control Update
```

---

This guide provides a complete foundation for understanding and extending the backend API synchronization in the RoutIQ Hub Dashboard. Each integration follows consistent patterns for authentication, organization scoping, and data management. 