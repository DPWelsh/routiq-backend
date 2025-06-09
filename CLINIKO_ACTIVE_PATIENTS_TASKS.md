# Cliniko Active Patients Sync Implementation Tasks

## Overview
Implement a multi-tenant Cliniko sync service that uses stored API credentials to pull active patients data and populate the `active_patients` table with proper organization mapping.

## Task Progress

### Phase 1: Service Foundation ✅
- [x] Create `src/services/cliniko_sync_service.py` stub
- [x] Set up encryption/decryption for stored credentials
- [x] Define date ranges (60 days ago to current date)

### Phase 2: Credential Management ✅
- [x] Implement `get_organization_cliniko_credentials()` method
- [x] Implement `_decrypt_credentials()` method  
- [x] Add credential validation logic (added `validate_cliniko_credentials()` method)
- [x] Test credential retrieval with Surf Rehab organization

**Phase 2 Test Results:**
✅ Credential encryption/decryption mechanism works with sample data
✅ Real credential retrieval from production database works (via API)
✅ Cliniko API authentication successful with stored credentials
✅ Can access patient data (631 patients found in Surf Rehab system)
✅ End-to-end credential flow validated

**What's Actually Implemented and Tested:**
- `_decrypt_credentials()`: Handles both string and dict formats from database
- `get_organization_cliniko_credentials()`: Retrieves and decrypts org credentials  
- `validate_cliniko_credentials()`: Tests API connection with `/patients` endpoint
- **Real API validation**: Successfully authenticated and retrieved patient data from Cliniko
- **Database integration**: Can retrieve stored credentials from production database

### Phase 3: Cliniko API Integration
- [ ] Implement `_create_auth_headers()` method
- [ ] Implement `_make_cliniko_request()` with rate limiting
- [ ] Implement `get_cliniko_patients()` with pagination
- [ ] Implement `get_cliniko_appointments()` with date filtering
- [ ] Test API connectivity with stored credentials

### Phase 4: Data Analysis & Processing
- [ ] Implement `analyze_active_patients()` method
- [ ] Create patient-to-appointment mapping logic
- [ ] Filter for patients with appointments in last 60 days
- [ ] Calculate appointment counts (recent vs upcoming)
- [ ] Prepare data structure for database storage

### Phase 5: Database Integration
- [ ] Implement `_find_contact_id()` method
- [ ] Create patient-to-contact matching logic:
  - [ ] Match by `cliniko_patient_id` 
  - [ ] Fallback to email matching
  - [ ] Fallback to name matching
- [ ] Implement `store_active_patients()` method
- [ ] Add upsert logic to handle existing records
- [ ] Test data storage with sample data

### Phase 6: Organization Context & Multi-tenancy
- [ ] Ensure all queries use `organization_id` filtering
- [ ] Implement organization context setting
- [ ] Add proper error handling for missing contacts
- [ ] Validate data isolation between organizations

### Phase 7: Sync Orchestration
- [ ] Complete `sync_organization_active_patients()` method
- [ ] Implement `sync_all_organizations()` method
- [ ] Add comprehensive error handling
- [ ] Implement sync result logging
- [ ] Add progress tracking and statistics

### Phase 8: API Endpoints
- [ ] Create API endpoint for manual sync trigger
- [ ] Add endpoint to get sync status/results
- [ ] Add endpoint to view active patients by organization
- [ ] Implement proper authentication/authorization

### Phase 9: Testing & Validation
- [ ] Test with Surf Rehab Cliniko credentials
- [ ] Verify data accuracy against Cliniko dashboard
- [ ] Test error scenarios (invalid credentials, API failures)
- [ ] Validate multi-tenant isolation
- [ ] Performance testing with large datasets

### Phase 10: Automation & Scheduling
- [ ] Create scheduled job for regular syncing
- [ ] Add webhook support for real-time updates
- [ ] Implement retry logic for failed syncs
- [ ] Add monitoring and alerting

## Current Implementation Status

### Completed
- Basic service structure
- Encryption key setup
- Date range calculation

### In Progress
- None

### Next Steps
1. Implement credential management (Phase 2)
2. Test credential retrieval with existing Surf Rehab data
3. Move to API integration (Phase 3)

## Key Requirements

### Data Mapping
```sql
-- Target table structure
create table public.active_patients (
  id bigserial not null,
  contact_id uuid not null,                    -- Links to contacts table
  recent_appointment_count integer not null,   -- Appointments in last 60 days
  upcoming_appointment_count integer not null, -- Future appointments
  total_appointment_count integer not null,    -- All appointments for patient
  last_appointment_date timestamp,             -- Most recent appointment
  recent_appointments jsonb,                   -- Recent appointment details
  upcoming_appointments jsonb,                 -- Upcoming appointment details
  search_date_from timestamp,                  -- Search range start (60 days ago)
  search_date_to timestamp,                    -- Search range end (today)
  organization_id text,                        -- Organization isolation
  created_at timestamp,
  updated_at timestamp
);
```

### API Credentials Required
- `api_key`: Cliniko API key
- `region`: Cliniko region (e.g., "au4") 
- `api_url`: Full API URL (e.g., "https://api.au4.cliniko.com/v1")

### Success Criteria
- [x] Credentials stored securely for Surf Rehab
- [x] Can retrieve and decrypt credentials
- [x] Can authenticate with Cliniko API
- [ ] Can fetch patients and appointments
- [ ] Can identify active patients (1+ appointments in 60 days)
- [ ] Can map Cliniko patients to contacts table
- [ ] Can store results in active_patients table
- [ ] Multi-tenant isolation working correctly
- [ ] Proper error handling and logging

## Notes
- Using existing credential storage system in `api_credentials` table
- Leveraging Fernet encryption with `CREDENTIALS_ENCRYPTION_KEY`
- Building on patterns from `cliniko_backup/` folder
- Need to handle Cliniko API rate limits
- Active patient definition: 1+ appointments in last 60 days 