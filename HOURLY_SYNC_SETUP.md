# Hourly Sync Setup Guide

## 🎯 Goal
Enable automatic syncing every hour for all organizations with active patients.

## ✅ Code Changes (Already Done)
- ✅ Updated sync scheduler to use comprehensive sync
- ✅ Fixed async/await issue in scheduler
- ✅ Configured 60-minute default interval
- ✅ Enhanced startup logging

## 🔧 Railway Environment Variables

Add these to your Railway project:

```bash
ENABLE_SYNC_SCHEDULER=true
SYNC_INTERVAL_MINUTES=60
```

### How to Add:
1. Go to Railway Dashboard
2. Select your `routiq-backend` project
3. Click "Variables" tab
4. Add the two variables above
5. Railway will auto-redeploy

## 📊 What Will Happen

Once enabled, you'll see in the logs:
```
🔄 Starting sync scheduler with 60 minute intervals
✅ Sync scheduler started successfully
```

Then every hour:
```
Starting automated sync for organization org_2xwHiNrj68eaRUlX10anlXGvzX7
✅ Comprehensive sync completed:
   - Patients: 651 processed
   - Appointments: 296 processed
```

## 🔍 Monitoring

### 1. Railway Logs
Check for scheduler messages every hour

### 2. API Endpoints
- `GET /api/v1/sync/scheduler/status` - Check if scheduler is running
- `POST /api/v1/sync/scheduler/trigger` - Manual trigger

### 3. Database
Check `sync_logs` table for entries with:
- `source_system = 'cliniko'`
- `operation_type = 'comprehensive_sync'`
- Regular hourly entries

## 🚨 Current Status

**Latest Deploy**: ✅ Successful (fixed await issue)
**Scheduler**: ⏳ Waiting for environment variables
**Next Step**: Add environment variables to Railway

## 🎉 Expected Results

After setup:
- Automatic hourly syncs
- Up-to-date patient data
- Fresh appointment counts
- Updated dashboard metrics
- No manual intervention needed 