# Contacts Table & Cliniko Integration Plan

## 🎯 **VISION: UNIFIED CONTACT MANAGEMENT**

**Core Principle:** A contact is anyone who interacts with the practice through ANY channel.

### Contact Sources
- 📱 **WhatsApp** (via Chatwoot/n8n)
- 📧 **Email** inquiries
- 📸 **Instagram** DMs
- 📞 **Phone** calls/SMS
- 🏥 **Cliniko** patients (appointment bookings)
- 💬 **Website** contact forms
- 🌐 **Social media** interactions

---

## 🏗️ **ARCHITECTURE DESIGN**

### 1. **Contacts Table = Central Hub**
```sql
contacts (
    id uuid PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20) UNIQUE,  -- Normalized format
    organization_id TEXT,
    
    -- Source tracking
    source VARCHAR(50),  -- 'cliniko', 'whatsapp', 'instagram', 'email', etc.
    first_contact_source VARCHAR(50),  -- Original source
    
    -- Cliniko integration
    cliniko_patient_id TEXT UNIQUE,  -- Links to Cliniko if they're a patient
    
    -- Status & metadata
    status VARCHAR(50) DEFAULT 'active',
    contact_type VARCHAR(50) DEFAULT 'contact',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
```

### 2. **Active Patients = Contacts + Recent Appointments**
```sql
active_patients (
    id BIGSERIAL PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),  -- Always links to contacts
    organization_id TEXT,
    
    -- Appointment activity (from Cliniko)
    recent_appointment_count INTEGER DEFAULT 0,
    upcoming_appointment_count INTEGER DEFAULT 0,
    last_appointment_date TIMESTAMP,
    recent_appointments JSONB DEFAULT '[]',
    upcoming_appointments JSONB DEFAULT '[]',
    
    -- Sync metadata
    search_date_from TIMESTAMP,
    search_date_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
```

---

## 🚀 **IMPLEMENTATION STRATEGY**

### **Phase 1: Cliniko Patient Import** 
**Goal:** Populate contacts table with all Cliniko patients

**Implementation:**
1. **Create Cliniko → Contacts sync job**
   - Fetch all patients from Cliniko API
   - Transform to contacts table format
   - Handle duplicates (phone/email matching)
   - Set `source = 'cliniko'` and populate `cliniko_patient_id`

2. **Data transformation logic:**
   ```python
   def cliniko_patient_to_contact(patient):
       return {
           'name': f"{patient['first_name']} {patient['last_name']}".strip(),
           'email': patient.get('email'),
           'phone': normalize_phone(patient.get('phone_mobile')),
           'source': 'cliniko',
           'contact_type': 'cliniko_patient',
           'cliniko_patient_id': patient['id'],
           'organization_id': org_id,
           'metadata': {
               'cliniko_created_at': patient.get('created_at'),
               'cliniko_updated_at': patient.get('updated_at'),
               'address': extract_address(patient),
               'date_of_birth': patient.get('date_of_birth')
           }
       }
   ```

### **Phase 2: Enhanced Active Patients Sync**
**Goal:** Current active patients logic will work perfectly

**With contacts populated:**
- ✅ `_find_contact_id()` will find matches
- ✅ Active patients will be identified
- ✅ 45-day appointment filtering works
- ✅ Complete workflow functional

### **Phase 3: Multi-Channel Contact Management**
**Goal:** Unified contact experience across all channels

**WhatsApp Integration:**
- When someone messages via WhatsApp → Create/update contact
- Check if they're already a Cliniko patient → Link via phone/email
- If linked: "Hi John! I see you have an appointment tomorrow at 2pm..."

**Email/Instagram/Other Channels:**
- Similar contact creation/linking logic
- Unified conversation history across channels
- Context-aware responses based on appointment status

---

## 📋 **TECHNICAL IMPLEMENTATION STEPS**

### **Step 1: Create Cliniko Patient Import Service**
```python
class ClinikoPatientImportService:
    def import_all_patients(self, organization_id):
        # 1. Fetch all patients from Cliniko
        # 2. Transform to contact format
        # 3. Bulk insert/update contacts table
        # 4. Handle duplicates intelligently
```

### **Step 2: Modify Active Patients Sync**
- **No changes needed!** Current logic will work once contacts are populated
- `_find_contact_id()` will successfully match Cliniko patients
- Active patients table will populate correctly

### **Step 3: Contact Deduplication Logic**
```python
def find_or_create_contact(name, email, phone, source):
    # 1. Try phone match (primary key)
    # 2. Try email match 
    # 3. Try name similarity match
    # 4. Create new if no match
    # 5. Merge contact sources if needed
```

### **Step 4: Cross-Channel Linking**
```python
def link_to_cliniko_patient(contact_id, phone, email):
    # Check if this contact matches a Cliniko patient
    # Update cliniko_patient_id if match found
    # Enrich contact with Cliniko data
```

---

## 🔄 **SYNC WORKFLOWS**

### **Daily Cliniko Sync:**
1. **Patient Import:** New/updated Cliniko patients → contacts table
2. **Active Patients:** Analyze 45-day appointment activity
3. **Contact Enrichment:** Update existing contacts with latest Cliniko data

### **Real-time Contact Creation:**
1. **New WhatsApp/Email/IG message** → Create contact
2. **Check for Cliniko match** → Link if patient exists
3. **Context-aware response** → Include appointment info if linked

### **Deduplication & Merging:**
- **Weekly cleanup job** to merge duplicate contacts
- **Smart matching** on phone, email, name similarity
- **Preserve source history** across merges

---

## 📊 **SUCCESS METRICS**

### **Contact Quality:**
- **Coverage:** % of Cliniko patients in contacts table
- **Accuracy:** % of contacts with correct cliniko_patient_id links
- **Completeness:** % of contacts with phone AND email

### **Active Patient Identification:**
- **Sync Success Rate:** % of syncs that complete without error
- **Active Patient Count:** Number of patients with 45-day appointments
- **Contact Matching Rate:** % of Cliniko patients found in contacts

### **Cross-Channel Integration:**
- **Link Success Rate:** % of new contacts linked to existing Cliniko patients
- **Response Context:** % of conversations that include appointment context
- **Unified Experience:** % of conversations across multiple channels

---

## 🎯 **IMMEDIATE ACTION PLAN**

### **Sprint 1: Foundation (1-2 days)**
1. ✅ Fix current active patients sync logic (DONE)
2. 🔄 Create Cliniko patient import service
3. 🔄 Import Surf Rehab patients to contacts table
4. ✅ Test active patients sync with populated contacts

### **Sprint 2: Enhancement (1-2 days)**
5. 🔄 Add contact deduplication logic
6. 🔄 Create cross-channel linking service
7. 🔄 Test with multi-source contacts

### **Sprint 3: Integration (1-2 days)**
8. 🔄 Integrate with WhatsApp/Chatwoot workflows
9. 🔄 Add context-aware messaging
10. 🔄 Complete end-to-end testing

---

## 💡 **KEY DECISIONS**

### **✅ Contacts as Central Hub**
- All interactions flow through contacts table
- Source-agnostic design
- Rich metadata for each channel

### **✅ Cliniko Integration Strategy**
- Import all patients to contacts first
- Link via cliniko_patient_id
- Existing active patients logic unchanged

### **✅ Multi-Channel Approach**
- Phone number as primary unique identifier
- Email as secondary matching
- Name similarity for edge cases

### **✅ Data Flow Priority**
1. **Cliniko** (authoritative for patient data)
2. **Direct communication** (authoritative for contact preferences)
3. **Social media** (supplementary information)

---

## 🚦 **NEXT IMMEDIATE ACTION**

**Create Cliniko Patient Import Service** to populate the contacts table with Surf Rehab's 632 patients, then test the complete active patients workflow.

**Expected Result:** 
- 632 contacts created
- ~50+ active patients identified (those with 45-day appointments)
- Complete sync workflow functional 

## 🔗 **ENHANCED: CHANNEL IDENTIFIER SYSTEM**

### **Multi-Channel Identity Management**

**Core Principle:** Different channels have different identifiers, but some should be unified (phone/WhatsApp).

### **Channel-Specific Identifiers:**
- **Phone/WhatsApp:** `+61412345678` (same identifier - WhatsApp is phone-based)
- **Email:** `john@example.com`
- **Instagram:** `@john_surfer` or Instagram user ID  
- **Facebook:** Facebook user ID
- **Chatwoot:** Chatwoot contact ID
- **Cliniko:** Cliniko patient ID
- **Website:** Usually email, sometimes anonymous session

### **Schema Enhancements:**
```sql
-- Make phone nullable for multi-channel flexibility
ALTER TABLE contacts ALTER COLUMN phone DROP NOT NULL;
ALTER TABLE contacts DROP CONSTRAINT contacts_phone_key;
CREATE UNIQUE INDEX contacts_phone_key ON contacts (phone) WHERE phone IS NOT NULL;

-- Add channel-specific identifier index
CREATE INDEX IF NOT EXISTS idx_contacts_external_ids_channels 
ON contacts USING GIN ((external_ids->'channels'));
```

### **Enhanced Contact Structure:**
```python
contact_example = {
    'id': 'uuid',
    'name': 'John Smith',
    'email': 'john@example.com',  # Can be null
    'phone': '+61412345678',      # Can be null
    'organization_id': 'org_123',
    
    # Channel identifiers - UNIFIED IDENTITY SYSTEM
    'external_ids': {
        'channels': {
            'phone': '+61412345678',
            'whatsapp': '+61412345678',        # Same as phone!
            'email': 'john@example.com',
            'instagram': '@john_surfer',
            'cliniko': '1704294729383945772',
            'chatwoot': '12345'
        },
        'original_cliniko_data': {...}  # Keep original data
    },
    
    # Source tracking
    'primary_source': 'whatsapp',           # First contact method
    'source_systems': ['whatsapp', 'cliniko', 'email'],  # All channels used
    
    # Contact matching
    'contact_type': 'cliniko_patient',
    'status': 'active'
}
```

### **Contact Linking Logic:**
```python
def find_or_create_contact(channel, identifier, name=None, email=None, org_id=None):
    """
    Find existing contact or create new one based on channel identifier
    """
    
    # 1. Try exact channel match first
    existing = find_contact_by_channel(channel, identifier, org_id)
    if existing:
        return existing
    
    # 2. For phone/whatsapp, check both channels (unified identity)
    if channel in ['phone', 'whatsapp']:
        existing = find_contact_by_phone_or_whatsapp(identifier, org_id)
        if existing:
            # Add new channel to existing contact
            update_contact_channels(existing, channel, identifier)
            return existing
    
    # 3. Try email match (cross-channel linking)
    if email:
        existing = find_contact_by_email(email, org_id)
        if existing:
            # Link new channel to existing contact
            update_contact_channels(existing, channel, identifier)
            return existing
    
    # 4. Create new contact
    return create_contact_with_channel(channel, identifier, name, email, org_id)
```

### **Channel Integration Examples:**

**WhatsApp Message:**
```python
# Someone messages: +61412345678
contact = find_or_create_contact(
    channel='whatsapp',
    identifier='+61412345678', 
    name='John from WhatsApp',
    org_id='org_surf_rehab'
)
# Auto-links to existing Cliniko patient if phone matches
```

**Instagram DM:**
```python
# Someone DMs from @john_surfer
contact = find_or_create_contact(
    channel='instagram',
    identifier='@john_surfer',
    name='John Surfer', 
    org_id='org_surf_rehab'
)
# Can be linked later via email/phone cross-reference
```

**Cliniko Patient Import:**
```python
contact = {
    'phone': '+61412345678',  # Nullable
    'email': 'john@example.com',
    'external_ids': {
        'channels': {
            'cliniko': '1704294729383945772',
            'phone': '+61412345678',    # If available
            'whatsapp': '+61412345678', # Same as phone
            'email': 'john@example.com'
        }
    },
    'primary_source': 'cliniko',
    'source_systems': ['cliniko']
}
```

### **Unified Experience Benefits:**
1. **Cross-channel context:** "I see you have an appointment tomorrow" (from any channel)
2. **Smart responses:** "Thanks for your WhatsApp message, John. Your physio session is confirmed."
3. **Channel preferences:** "Would you prefer reminders via WhatsApp or email?"
4. **Seamless handoffs:** Start on Instagram, continue on WhatsApp, book via Cliniko

--- 