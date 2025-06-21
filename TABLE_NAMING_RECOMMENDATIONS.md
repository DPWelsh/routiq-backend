# Table Naming Recommendations

## Current Issues

### 1. **Confusing Names**
- `patients_new` - Temporary migration name, not descriptive
- `active_patients` - Contains inactive patients (misleading)
- `contacts` - Too generic, actually stores patients
- `api_credentials` - Redundant "api" prefix

### 2. **Inconsistent Naming**
- Some tables use underscores (`organization_members`)
- Some use singular (`users`) vs plural (`messages`)
- No clear naming convention

### 3. **Poor Semantic Clarity**
- `organization_services` - Could be clearer about purpose
- Table purposes not obvious from names

## Recommended Naming Convention

### **Principles:**
1. **Clear Purpose** - Name should indicate what the table stores
2. **Consistent Format** - All tables use singular nouns
3. **Domain-Specific** - Use healthcare/practice management terminology
4. **No Redundancy** - Avoid prefixes like "api_" or "data_"

## Proposed Table Renames

### **BEFORE → AFTER**

```sql
-- Core Patient Data
patients_new           → patients
active_patients        → active_patients_deprecated (then delete)
contacts              → contacts_deprecated (then delete)

-- Integration & Services  
organization_services → service_integrations
api_credentials       → service_credentials

-- Keep As-Is (already well named)
appointments          → appointments ✓
conversations         → conversations ✓
messages             → messages ✓
organizations        → organizations ✓
organization_members → organization_members ✓
users                → users ✓
sync_logs            → sync_logs ✓
audit_logs           → audit_logs ✓
```

## Final Schema Structure

### **Core Healthcare Entities**
```
patients
├── Unified patient records with activity status
├── Replaces: contacts + active_patients
└── Clear semantic meaning

appointments
├── Individual appointment records
└── Links to patients table

conversations
├── Communication threads (SMS, chat, etc.)
└── Links to patients table

messages
├── Individual messages within conversations
└── Links to conversations table
```

### **Organization Management**
```
organizations
├── Healthcare practices/clinics
└── Root entity for multi-tenancy

organization_members  
├── User memberships and roles
└── Links users to organizations

users
├── User accounts (practitioners, staff, admins)
└── Authentication and profile data
```

### **Integration & Sync**
```
service_integrations
├── Which services are enabled per organization
├── Renamed from: organization_services
└── Clearer purpose indication

service_credentials
├── Encrypted API keys and credentials
├── Renamed from: api_credentials  
└── Removed redundant "api" prefix

sync_logs
├── History of data synchronization operations
└── Already well named
```

### **Audit & Security**
```
audit_logs
├── User action and system event tracking
└── Already well named
```

## Benefits of New Naming

### 1. **Clear Semantic Meaning**
```sql
-- Before (confusing)
SELECT * FROM contacts WHERE contact_type = 'cliniko_patient';
SELECT * FROM active_patients WHERE upcoming_appointment_count = 0;

-- After (clear)
SELECT * FROM patients WHERE is_active = TRUE;
SELECT * FROM patients WHERE activity_status = 'recently_active';
```

### 2. **Consistent API Endpoints**
```javascript
// Before (inconsistent)
GET /api/contacts
GET /api/active-patients  
GET /api/organization-services

// After (consistent)
GET /api/patients
GET /api/service-integrations
GET /api/service-credentials
```

### 3. **Self-Documenting Code**
```python
# Before (unclear)
from models import Contacts, ActivePatients, OrganizationServices

# After (clear)  
from models import Patients, ServiceIntegrations, ServiceCredentials
```

## Migration Strategy

### **Phase 1: Core Patient Data**
1. ✅ Create unified `patients` table
2. ✅ Migrate data from `contacts` + `active_patients`
3. 🔄 Rename `patients_new` → `patients`
4. 🔄 Rename old tables to `*_deprecated`

### **Phase 2: Service Tables**
1. 🔄 Rename `organization_services` → `service_integrations`
2. 🔄 Rename `api_credentials` → `service_credentials`
3. 🔄 Update foreign key references

### **Phase 3: Application Updates**
1. 🔄 Update API endpoints
2. 🔄 Update model classes
3. 🔄 Update database queries
4. 🔄 Update documentation

### **Phase 4: Cleanup**
1. 🔄 Drop deprecated tables
2. 🔄 Remove old indexes
3. 🔄 Update monitoring/alerts

## Implementation Commands

```sql
-- Execute the naming cleanup
\i sql/table_naming_cleanup.sql

-- Verify changes
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

## API Impact

### **Endpoint Changes**
```
OLD ENDPOINTS              NEW ENDPOINTS
/api/contacts              → /api/patients
/api/active-patients       → /api/patients?active=true
/api/organization-services → /api/service-integrations
```

### **Response Structure** (Enhanced)
```json
{
  "id": "patient-uuid",
  "name": "John Doe", 
  "phone": "+61123456789",
  "is_active": true,
  "activity_status": "active",
  "next_appointment_type": "Follow-up",
  "primary_appointment_type": "Physiotherapy"
}
```

## Recommendation

**YES - Implement the naming cleanup immediately!**

### **Why Now:**
1. ✅ **Better Developer Experience** - Clear, intuitive table names
2. ✅ **Easier Onboarding** - New developers understand schema immediately  
3. ✅ **Self-Documenting** - Code becomes more readable
4. ✅ **API Consistency** - Uniform endpoint naming
5. ✅ **Future-Proof** - Easier to extend and maintain

### **Low Risk:**
- ✅ Views provide backward compatibility
- ✅ Rollback plan available
- ✅ Can be done incrementally

The proposed naming creates a **clean, professional, healthcare-focused schema** that clearly communicates purpose and improves maintainability! 🎯 