# Patients Table Architecture Recommendation

## Current Issues

### 1. **Data Duplication**
- Patient information stored in both `contacts` and `active_patients` tables
- Risk of data inconsistency between tables
- Complex sync logic to maintain two tables

### 2. **Confusing Semantics**
- `active_patients` table contains patients who may not be currently active
- "Active" status is implicit rather than explicit
- 54 records in table but varying definitions of "active"

### 3. **Maintenance Complexity**
- Need to JOIN tables for complete patient view
- Foreign key relationships add complexity
- Sync process must manage two separate tables

## Recommended Solution: Unified `patients` Table

### **Single Source of Truth**
Replace `contacts` + `active_patients` with one comprehensive `patients` table:

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    organization_id TEXT NOT NULL,
    
    -- Core Information
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    cliniko_patient_id TEXT,
    
    -- Activity Status (Explicit)
    is_active BOOLEAN DEFAULT FALSE,
    activity_status TEXT, -- 'active', 'recently_active', 'upcoming_only', 'inactive'
    
    -- Appointment Statistics
    recent_appointment_count INTEGER DEFAULT 0,
    upcoming_appointment_count INTEGER DEFAULT 0,
    total_appointment_count INTEGER DEFAULT 0,
    
    -- Enhanced Visibility Fields
    next_appointment_time TIMESTAMPTZ,
    next_appointment_type TEXT,
    primary_appointment_type TEXT,
    treatment_notes TEXT,
    
    -- Detailed Data (JSON)
    recent_appointments JSONB DEFAULT '[]',
    upcoming_appointments JSONB DEFAULT '[]',
    
    -- Metadata
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Benefits of Unified Architecture

### 1. **Simplified Queries**
```sql
-- Current (complex JOIN)
SELECT c.name, ap.next_appointment_type 
FROM contacts c 
JOIN active_patients ap ON ap.contact_id = c.id;

-- New (simple query)
SELECT name, next_appointment_type 
FROM patients 
WHERE is_active = TRUE;
```

### 2. **Clear Activity Status**
```sql
-- Get patients by activity level
SELECT activity_status, COUNT(*) 
FROM patients 
GROUP BY activity_status;

-- Results:
-- active: 15 patients (recent + upcoming appointments)
-- recently_active: 37 patients (recent only)
-- upcoming_only: 2 patients (upcoming only)
-- inactive: 578 patients (no recent/upcoming)
```

### 3. **Simplified Sync Logic**
```python
# Current: Update two tables
def store_active_patients(self, patients_data):
    # Update contacts table
    # Update active_patients table
    # Manage foreign keys

# New: Update one table
def store_patients(self, patients_data):
    # Single UPSERT operation
    # Set is_active and activity_status
```

### 4. **Better Performance**
- No JOINs required for patient queries
- Single table indexes
- Reduced query complexity

## Migration Strategy

### Phase 1: Create New Table
1. Create `patients_new` table with unified schema
2. Migrate data from `contacts` + `active_patients`
3. Create views for backward compatibility

### Phase 2: Update Application Code
1. Update sync service to use new table
2. Update API endpoints to query new table
3. Test with existing views

### Phase 3: Complete Migration
1. Drop old tables (`contacts`, `active_patients`)
2. Rename `patients_new` to `patients`
3. Update all references

## API Impact

### Current API Response
```json
{
  "id": "contact-uuid",
  "name": "John Doe",
  "phone": "+61123456789",
  "recent_appointment_count": 3,
  "next_appointment_type": "Follow-up"
}
```

### New API Response (Enhanced)
```json
{
  "id": "patient-uuid",
  "name": "John Doe",
  "phone": "+61123456789",
  "is_active": true,
  "activity_status": "active",
  "recent_appointment_count": 3,
  "upcoming_appointment_count": 1,
  "next_appointment_type": "Follow-up",
  "primary_appointment_type": "Physiotherapy",
  "last_synced_at": "2025-06-21T08:22:35Z"
}
```

## Implementation Priority

### **Immediate Benefits**
- ✅ Cleaner architecture
- ✅ Simplified queries
- ✅ Better performance
- ✅ Explicit activity status

### **Long-term Benefits**
- 📈 Easier to add new patient fields
- 🔍 Better analytics capabilities
- 🚀 Faster development of patient features
- 📊 Simplified reporting

## Recommendation

**Yes, absolutely consolidate into a single `patients` table!**

The current dual-table approach is an anti-pattern that creates unnecessary complexity. A unified table with explicit `is_active` and `activity_status` columns provides:

1. **Clear semantics** - Every patient has an explicit activity status
2. **Single source of truth** - No data duplication or sync issues
3. **Better performance** - No JOINs required
4. **Easier maintenance** - One table to manage
5. **Future-proof** - Easy to extend with new patient fields

The proposed `sql/proposed_patients_table_redesign.sql` provides a complete migration path with backward-compatible views to ensure zero downtime during the transition.

## Next Steps

1. **Review** the proposed schema in `sql/proposed_patients_table_redesign.sql`
2. **Test** the migration on a copy of your data
3. **Update** sync service to use the new table
4. **Migrate** in production with the provided script
5. **Enjoy** the simplified architecture! 🎉 