# Railway Deployment Setup Guide

## 🚀 Quick Deployment Steps

### 1. Validate Build Before Deployment

**🛡️ Always run validation before pushing:**

```bash
# Run quick validation checks
python3 scripts/quick_check.py

# If validation passes, then push to Railway
```

### 2. Push to Railway
```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize and deploy
railway init
railway up
```

### 3. Required Environment Variables in Railway

#### **✅ REQUIRED (Minimum)**
```bash
# Development Database (replace with your production database for live deployment)
DATABASE_URL=postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres
```

#### **🔧 Optional (Railway Deployment)**
```bash
PORT=8000                   # Railway default
APP_ENV=production          # App default  
PYTHONPATH=/app/src         # May be needed for Railway
```

#### **🔐 Optional (Authentication Features)**
```bash
# Only needed if using Clerk auth endpoints
CLERK_SECRET_KEY=sk_live_your_clerk_secret_key
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret
```

#### **🔌 Optional (Integrations)**
```bash
# Only set these if using specific integrations
CLINIKO_API_KEY=your_cliniko_key         # For Cliniko sync
CHATWOOT_API_TOKEN=your_chatwoot_token   # For Chatwoot sync
CREDENTIALS_ENCRYPTION_KEY=your_key      # For encrypted credentials storage
```

### 4. Configure Clerk Webhooks (Optional)

⚠️ **Only needed if using Clerk authentication features**

In your Clerk dashboard, set up webhooks pointing to:
```
https://your-railway-app.railway.app/webhooks/clerk
```

**Required webhook events:**
- `user.created`
- `user.updated`
- `organization.created`
- `organizationMembership.created`
- `organizationMembership.updated`

### 5. Test Your Deployment

After deployment, test these endpoints:

- **Health Check**: `https://your-railway-app.railway.app/health`
- **API Docs**: `https://your-railway-app.railway.app/docs`
- **Root**: `https://your-railway-app.railway.app/`

Expected response:
```json
{
  "message": "Routiq Backend API",
  "status": "healthy",
  "version": "2.0.0"
}
```

## 🔧 Troubleshooting

### Common Issues:

1. **Database Connection Fails**
   - Verify `DATABASE_URL` format
   - Check Supabase connection string includes password
   - Ensure Supabase project allows external connections

2. **Clerk Authentication Issues**
   - Verify webhook URL is accessible from internet
   - Check webhook secret matches Clerk dashboard
   - Ensure CORS origins include your frontend domain

3. **Import Errors**
   - Check `PYTHONPATH=/app/src` is set in Railway
   - Verify all dependencies in `requirements.txt`

### Debug Commands:
```bash
# Check Railway logs
railway logs

# Check environment variables
railway variables

# Connect to Railway shell
railway shell
```

## 📊 Monitoring Your Deployment

### Health Endpoint
Monitor your API health at: `/health`

Expected healthy response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2025-06-09T..."
}
```

### API Documentation
Access interactive API docs at: `/docs`

### Available Endpoints:
- `GET /` - Root status
- `GET /health` - Health check
- `GET /docs` - API documentation
- `POST /webhooks/clerk` - Clerk webhook handler
- `GET /api/v1/auth/me` - Current user info
- `GET /api/v1/organizations` - User organizations
- `GET /api/v1/organizations/{id}/sync/status` - Sync status

## 🎯 Next Steps After Deployment

1. **Test Clerk Integration**: Sign up a test user and verify webhook processing
2. **Configure Dashboard**: Update frontend to point to your Railway API
3. **Set Up Monitoring**: Configure alerts for health check failures
4. **Database Optimization**: Proceed with Task #2 (Performance Indexes)

---

**Your Railway URL will be**: `https://your-app-name.railway.app` 