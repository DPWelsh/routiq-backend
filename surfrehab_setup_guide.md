# SurfRehab Organization Setup Guide

## 🎯 Objective
Set up the SurfRehab organization with proper Cliniko integration to test **upcoming appointments** functionality.

## ✅ Key Improvements Made

### 1. Enhanced Sync Logic
The `ClinikoSyncService` has been improved to include patients with:
- ✅ Recent appointments (last 45 days)
- ✅ **Upcoming appointments (next 30 days)**
- ✅ **OR BOTH** (previously only included patients with recent appointments)

**Code Change Made:**
```python
# OLD: Only patients with recent appointments
if recent_count > 0:

# NEW: Patients with recent OR upcoming appointments  
if recent_count > 0 or upcoming_count > 0:
```

### 2. New Upcoming Appointments Endpoint
Added dedicated endpoint: `/api/v1/admin/cliniko/patients/{org}/upcoming`
- Shows only patients with upcoming appointments
- Ordered by upcoming appointment count
- Includes full appointment details

## 🛠️ Database Setup

Execute these SQL commands in your **production database**:

### 1. Create/Update Organization
```sql
INSERT INTO organizations (id, name, slug, subscription_status, subscription_plan, created_at, updated_at)
VALUES ('surfrehab', 'SurfRehab', 'surfrehab', 'active', 'professional', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    updated_at = NOW();
```

### 2. Create Cliniko Service Configuration
```sql
INSERT INTO organization_services (
    organization_id, service_name, is_active, is_primary, sync_enabled,
    service_config, created_at, updated_at
) VALUES (
    'surfrehab', 'cliniko', true, true, true,
    '{"region": "au", "api_version": "v1"}',
    NOW(), NOW()
) ON CONFLICT (organization_id, service_name) DO UPDATE SET
    is_active = true,
    sync_enabled = true,
    updated_at = NOW();
```

### 3. Add Cliniko API Credentials
⚠️ **Replace with actual SurfRehab Cliniko credentials**

```sql
-- You need to encrypt the credentials using your CREDENTIALS_ENCRYPTION_KEY
-- Structure should be:
-- {
--   "api_key": "ACTUAL_SURFREHAB_CLINIKO_API_KEY",
--   "api_url": "https://api.au4.cliniko.com/v1",  -- Adjust for region
--   "region": "au",
--   "account_name": "SurfRehab"
-- }

INSERT INTO api_credentials (
    organization_id, service_name, is_active,
    credentials_encrypted, created_at, updated_at, last_validated_at
) VALUES (
    'surfrehab', 'cliniko', true,
    '{"encrypted_data": "ENCRYPTED_CREDENTIALS_HERE"}',
    NOW(), NOW(), NOW()
) ON CONFLICT (organization_id, service_name) DO UPDATE SET
    is_active = true,
    credentials_encrypted = EXCLUDED.credentials_encrypted,
    updated_at = NOW();
```

## 🧪 Testing Commands

Once the database is configured with **actual Cliniko credentials**:

### 1. Test Sync (This will pull upcoming appointments!)
```bash
curl -X POST "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/sync/surfrehab"
```

### 2. Check Summary (Should show upcoming appointments count)
```bash
curl -X GET "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/patients/surfrehab/active/summary"
```

### 3. List Upcoming Appointments (NEW endpoint!)
```bash
curl -X GET "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/patients/surfrehab/upcoming"
```

### 4. List All Active Patients (Including those with upcoming appointments)
```bash
curl -X GET "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/cliniko/patients/surfrehab/active"
```

## 📊 Expected Results

After proper setup and sync:

### Summary Response:
```json
{
  "organization_id": "surfrehab",
  "total_active_patients": 15,  // Includes patients with upcoming appointments
  "patients_with_recent_appointments": 8,
  "patients_with_upcoming_appointments": 12,  // Should be > 0 if working
  "last_sync_date": "2025-06-10T...",
  "timestamp": "2025-06-10T..."
}
```

### Upcoming Appointments Response:
```json
{
  "organization_id": "surfrehab",
  "patients": [
    {
      "id": 1,
      "contact_id": "uuid",
      "contact_name": "Patient Name",
      "contact_phone": "+61...",
      "recent_appointment_count": 0,
      "upcoming_appointment_count": 2,  // > 0
      "upcoming_appointments": [
        {
          "id": "appointment_id",
          "date": "2025-06-15T10:00:00Z",
          "type": "Consultation"
        }
      ]
    }
  ],
  "total_count": 12,
  "timestamp": "2025-06-10T..."
}
```

## 🔄 Sync Process Improvements

The sync now:
1. ✅ Fetches appointments from **last 45 days + next 30 days**
2. ✅ Identifies patients with **recent OR upcoming appointments**
3. ✅ Stores detailed upcoming appointment data
4. ✅ Updates counts for both recent and upcoming appointments

## 🚀 Next Steps

1. **Get actual SurfRehab Cliniko API credentials**
2. **Encrypt credentials using your production CREDENTIALS_ENCRYPTION_KEY**
3. **Execute the SQL commands above in production database**
4. **Test the sync and endpoints**
5. **Verify upcoming appointments are being detected**

## 🎉 Success Indicators

✅ **Sync command returns:** `"patients_found": > 0, "appointments_found": > 0`  
✅ **Summary shows:** `"patients_with_upcoming_appointments": > 0`  
✅ **Upcoming endpoint returns:** Patients with `upcoming_appointment_count > 0`  
✅ **Active patients list includes:** Patients with only upcoming appointments

---

**Ready to test upcoming appointments functionality! 🏄‍♂️** 