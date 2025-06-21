postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres

# Clerk Data Synchronization

This document explains how to sync existing Clerk user and organization data with your local database.

## Overview

The Clerk sync system pulls all users, organizations, and memberships from your Clerk application and syncs them to your PostgreSQL database. This is essential for:

- Initial database population with existing Clerk data
- Ensuring data consistency between Clerk and your application
- Recovering from database issues or migrations

## Components

### 1. ClerkSyncService (`src/integrations/clerk_sync.py`)

Core service that handles:
- Fetching all users from Clerk API with pagination
- Fetching all organizations from Clerk API with pagination  
- Fetching all organization memberships from Clerk API
- Using existing webhook handlers to sync data consistently
- Comprehensive error handling and logging

### 2. Admin API Endpoints (`src/api/clerk_admin.py`)

REST API endpoints for managing Clerk sync:

- `GET /api/v1/admin/clerk/status` - Check sync status and database counts
- `POST /api/v1/admin/clerk/sync` - Trigger comprehensive sync (runs in background)
- `GET /api/v1/admin/clerk/sync-logs` - View recent sync logs
- `GET /api/v1/admin/clerk/database-summary` - Get detailed database summary
- `POST /api/v1/admin/clerk/test-connection` - Test Clerk API connectivity
- `GET /api/v1/admin/clerk/organizations` - List all organizations with IDs and names
- `POST /api/v1/admin/clerk/store-credentials` - Store encrypted API credentials for organizations

### 3. Command Line Script (`scripts/sync_clerk_data.py`)

Standalone script for administrative sync operations:

```bash
# Test connection only
python scripts/sync_clerk_data.py --dry-run

# Full sync with verbose output  
python scripts/sync_clerk_data.py --verbose

# Standard sync
python scripts/sync_clerk_data.py
```

## Usage

### Option 1: API Endpoints (Recommended for Production)

1. **Check Status First:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/admin/clerk/status"
   ```

2. **Trigger Sync:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/admin/clerk/sync"
   ```

3. **Monitor Progress:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/admin/clerk/sync-logs"
   ```

### Option 3: Credentials Management (New!)

1. **List Organizations:**
   ```bash
   curl -X GET "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/clerk/organizations"
   ```

2. **Store API Credentials for an Organization:**
   ```bash
   curl -X POST "https://routiq-backend-v10-production.up.railway.app/api/v1/admin/clerk/store-credentials" \
     -H "Content-Type: application/json" \
     -d '{
       "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
       "service_name": "cliniko",
       "api_key": "MS0xNjUyNzI0NDI2Njk4OTI1ODQ0LXVKOUR0aHU0SDFUTlJ6NncxUlFhdzY1U0g4OTIveWJN-au4",
       "region": "au4"
     }'
   ```

### Option 2: Command Line Script (Good for Testing/Initial Setup)

1. **Test Connection:**
   ```bash
   python scripts/sync_clerk_data.py --dry-run
   ```

2. **Full Sync:**
   ```bash
   python scripts/sync_clerk_data.py --verbose
   ```

## Prerequisites

### Required Environment Variables

The sync system requires your Clerk Secret Key:

```bash
# In .env file
CLERK_SECRET_KEY=sk_test_your_secret_key_here
```

### Database Tables

Ensure these tables exist (should be created by migrations):

- `users` - Stores Clerk user data
- `organizations` - Stores Clerk organization data  
- `organization_members` - Stores membership relationships
- `audit_logs` - Stores sync operation logs

## What Gets Synced

### Users
- All Clerk user accounts with metadata
- Email addresses, names, profile data
- Creation/update timestamps
- Login history (if available)

### Organizations  
- All Clerk organizations
- Organization metadata and settings
- Creation/update timestamps
- Organization status

### Memberships
- User-organization relationships
- Membership roles (admin, member, etc.)
- Membership status and permissions
- Join dates and metadata

## API Credentials Storage

The system now supports secure storage of API credentials for external integrations:

### Supported Services
- **Cliniko**: Practice management system credentials
  - API Key: Your Cliniko API key
  - Region: Cliniko instance region (e.g., 'au4', 'au2', 'uk1')
- **Chatwoot**: Customer communication platform credentials
  - API Token: Your Chatwoot API token
  - Account ID: Your Chatwoot account identifier
  - Base URL: Chatwoot instance URL (optional, defaults to app.chatwoot.com)

### Security Features
- **Encryption**: All credentials encrypted using Fernet symmetric encryption
- **Organization Isolation**: Credentials scoped to specific organizations
- **Audit Logging**: All credential operations logged to audit trail
- **Environment Key**: Uses `CREDENTIALS_ENCRYPTION_KEY` environment variable

### Storage Format
```json
{
  "organization_id": "org_2xwHiNrj68eaRUlX10anlXGvzX7",
  "service_name": "cliniko",
  "credentials_encrypted": "gAAAAABh...", // Base64 encoded encrypted JSON
  "is_active": true,
  "created_by": "system",
  "created_at": "2025-06-09T07:00:00Z"
}
```

## Error Handling

The sync system includes comprehensive error handling:

- **API Errors:** Retries and detailed error logging
- **Database Errors:** Transaction rollbacks and error reporting
- **Partial Failures:** Continues processing other records
- **Audit Trail:** All sync operations logged to `audit_logs` table

## Monitoring

### Sync Logs

All sync operations are logged with:
- Start/completion timestamps
- Success/failure status
- Detailed error messages
- Record counts processed

### Database Summary

Check data integrity with the summary endpoint:
```bash
curl -X GET "http://localhost:8000/api/v1/admin/clerk/database-summary"
```

## Performance

- **Pagination:** Processes data in batches (100 records at a time)
- **Background Processing:** API endpoint runs sync in background
- **Connection Pooling:** Reuses database connections efficiently
- **Timeout Handling:** 30-second timeouts for API calls

## Security

- **Admin Only:** Endpoints require admin authentication (implement your auth logic)
- **API Key Security:** Clerk secret key handled securely via environment variables
- **Audit Logging:** All operations tracked for security compliance

## Troubleshooting

### Common Issues

1. **"Clerk API not accessible"**
   - Check `CLERK_SECRET_KEY` environment variable
   - Verify API key has correct permissions
   - Test with `--dry-run` first

2. **Database connection errors**
   - Verify `DATABASE_URL` is correct
   - Check database server is running
   - Ensure tables exist

3. **Partial sync failures**
   - Check sync logs for specific errors
   - Individual record failures don't stop overall sync
   - Re-run sync to catch missed records

### Debug Mode

Enable verbose logging:
```bash
python scripts/sync_clerk_data.py --verbose
```

Or set log level:
```bash
export LOG_LEVEL=DEBUG
```

## Best Practices

1. **Initial Setup:** Run sync after database migrations
2. **Regular Maintenance:** Schedule periodic syncs if needed
3. **Monitor Logs:** Check audit logs for sync health
4. **Test First:** Always use `--dry-run` in new environments
5. **Backup:** Backup database before large sync operations

## Next Steps

After successful sync:
1. Verify data integrity with database summary
2. Test user authentication flows
3. Configure ongoing webhook handlers for real-time sync
4. Set up monitoring/alerting for sync failures 