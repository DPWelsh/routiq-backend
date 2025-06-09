# SurfRehab v2 - Clean Data Pipeline

A production-ready data synchronization platform for healthcare practices, integrating **Cliniko**, **Chatwoot**, **ManyChat**, **Momence**, and **Google Calendar** with a clean, normalized **Supabase** database.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Cliniko   │    │  Chatwoot   │    │  ManyChat   │
│ (Patients)  │    │ (Messages)  │    │ (Marketing) │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      └──────────┬───────────────┬──────────┘
                 │               │
            ┌────▼───────────────▼────┐
            │    SurfRehab v2 API     │
            │   (Sync Manager)        │
            └─────────┬───────────────┘
                      │
            ┌─────────▼───────────────┐
            │     Supabase DB         │
            │  (Clean Schema)         │
            └─────────────────────────┘
```

## ✨ Features

- ✅ **Clean, normalized database schema** (no redundant fields)
- ✅ **Direct API integration** (no CSV imports)
- ✅ **Automatic phone number normalization** (international format)
- ✅ **Contact type classification** (Cliniko vs Chatwoot contacts)
- ✅ **Comprehensive sync logging** and error tracking
- ✅ **Multi-tenant support** (organization-based)
- ✅ **Production-ready** for Railway deployment

## 🚀 Quick Start

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your database URL: `postgresql://postgres:password@db.xxx.supabase.co:5432/postgres`

### 2. Clone and Setup

```bash
git clone <this-repo>
cd surfrehab-v2

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/env.example .env
# Edit .env with your API keys and database URL
```

### 3. Initialize Database and Sync

```bash
# Run complete setup
python scripts/setup_project.py
```

This will:
- Create clean database schema in Supabase
- Sync data from Cliniko and Chatwoot APIs
- Validate and normalize all data
- Show summary statistics

## 📊 Database Schema

### Core Tables

- **`contacts`** - Unified contacts from all sources
- **`active_patients`** - Cliniko patients with appointment data
- **`conversations`** - Chatwoot conversations and messages
- **`appointments`** - Future Google Calendar integration
- **`organizations`** - Multi-tenant support
- **`sync_logs`** - API sync audit trail

### Key Views

- **`patient_overview`** - Combined contact and patient data
- **`conversation_insights`** - Message analytics with sentiment
- **`organization_dashboard`** - High-level metrics

## 🔧 Configuration

### Environment Variables

```bash
# Database
SUPABASE_DB_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# APIs
CLINIKO_API_KEY=your-cliniko-key
CHATWOOT_API_TOKEN=your-chatwoot-token
ORGANIZATION_ID=your-org-id

# Optional (future integrations)
MANYCHAT_API_TOKEN=your-manychat-token
GOOGLE_CALENDAR_CREDENTIALS_JSON=path/to/credentials.json
```

## 📡 API Integration

### Cliniko → Contacts + Active Patients
```python
from src.sync_manager import SyncManager

sync = SyncManager(organization_id="your-org")
result = await sync.sync_cliniko_patients()
```

### Chatwoot → Contacts + Conversations
```python
result = await sync.sync_chatwoot_conversations()
```

### Full Sync
```python
result = await sync.full_sync()
```

## 🗂️ Project Structure

```
surfrehab-v2/
├── sql/                     # Database schema
│   ├── 01_create_tables.sql # Main tables
│   ├── 02_create_triggers.sql # Auto-update triggers
│   └── 03_create_views.sql  # Analytics views
├── src/                     # Application code
│   ├── database.py          # Supabase client
│   ├── sync_manager.py      # Main sync logic
│   └── integrations/        # API clients
├── scripts/                 # Setup and maintenance
│   └── setup_project.py     # Initial setup
├── config/                  # Configuration templates
└── requirements.txt         # Python dependencies
```

## 🚂 Railway Deployment

### 1. Create Railway Project
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 2. Configure Environment Variables in Railway
- Add all variables from `config/env.example`
- Set `PORT=8000` for Railway

### 3. Add Scheduled Sync (Railway Cron)
```python
# Add to railway.toml
[build]
command = "pip install -r requirements.txt"

[deploy]
command = "python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT"

# Cron job for regular sync
[[cron]]
schedule = "0 */6 * * *"  # Every 6 hours
command = "python scripts/manual_sync.py"
```

## 📈 Monitoring & Analytics

### Sync Status Dashboard
```python
from src.sync_manager import SyncManager

sync = SyncManager()
status = sync.get_sync_status()

print(f"Contacts: {status['contact_stats']}")
print(f"Recent syncs: {status['recent_syncs']}")
```

### Database Views for Analytics
- `SELECT * FROM patient_overview` - All patient data
- `SELECT * FROM conversation_insights` - Message analytics
- `SELECT * FROM organization_dashboard` - Summary metrics

## 🔮 Future Integrations

Ready-to-implement when needed:

### ManyChat Integration
- **Purpose**: Send targeted WhatsApp campaigns
- **Data Source**: `contacts` table with `contact_type = 'chatwoot_contact'`
- **Implementation**: Add `src/integrations/manychat_client.py`

### Google Calendar Integration
- **Purpose**: Sync appointment scheduling
- **Data Source**: Cliniko appointments → `appointments` table
- **Implementation**: Add calendar sync to existing patient workflow

### Momence Integration
- **Purpose**: Online booking and payments
- **Data Source**: Cross-reference with Cliniko patient IDs
- **Implementation**: Add booking webhook handlers

## 🛠️ Maintenance

### Manual Sync
```bash
python scripts/manual_sync.py
```

### Check Database Health
```bash
python -c "from src.database import db; print('✅' if db.health_check() else '❌')"
```

### View Recent Logs
```sql
SELECT * FROM sync_logs ORDER BY started_at DESC LIMIT 10;
```

## 🆘 Troubleshooting

### Common Issues

1. **Phone number format errors**
   - Check `contacts_phone_format` constraint
   - Verify international format: `+61xxxxxxxxx`

2. **API sync failures**
   - Check `sync_logs` table for error details
   - Verify API keys in environment variables

3. **Database connection issues**
   - Verify Supabase URL format
   - Check firewall/network connectivity

### Support

- Check `sync_logs` table for detailed error information
- Review application logs for sync failures
- Validate API credentials and permissions

---

**Built for production healthcare data workflows** 🏥 → 📊 → 🚀 # Deployment fix - added CREDENTIALS_ENCRYPTION_KEY
# Deployment fix - added all Supabase keys
