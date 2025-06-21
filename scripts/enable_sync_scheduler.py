#!/usr/bin/env python3
"""
Enable and Test Sync Scheduler
"""

import os
import sys
from pathlib import Path

print("🔧 Enabling Sync Scheduler")
print("=" * 40)

# Set environment variables to enable scheduler
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'
os.environ['CREDENTIALS_ENCRYPTION_KEY'] = 'q6C7_Ro3_sSDMnXwvaL3nciC2cVYCFJz4V-iqVteJOM='
os.environ['ENABLE_SYNC_SCHEDULER'] = 'true'
os.environ['SYNC_INTERVAL_MINUTES'] = '30'
os.environ['SYNC_ENABLED'] = 'true'

print("✅ Environment variables set:")
print(f"   ENABLE_SYNC_SCHEDULER: {os.getenv('ENABLE_SYNC_SCHEDULER')}")
print(f"   SYNC_INTERVAL_MINUTES: {os.getenv('SYNC_INTERVAL_MINUTES')}")
print(f"   SYNC_ENABLED: {os.getenv('SYNC_ENABLED')}")

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    print("\n🔍 Testing Scheduler Import...")
    from services.sync_scheduler import scheduler
    print("✅ Scheduler imported successfully")
    
    print("\n🔍 Testing Scheduler Status...")
    org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    status = scheduler.get_sync_status(org_id)
    
    print("📊 Scheduler Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n💡 NEXT STEPS:")
    print("1. Set ENABLE_SYNC_SCHEDULER=true in your production environment")
    print("2. Restart your FastAPI application")
    print("3. The scheduler will automatically run every 30 minutes")
    print("4. Check sync_logs table for new cliniko/active_patients entries")
    
    print("\n🚀 IMMEDIATE TEST:")
    print("You can also trigger a manual sync via API:")
    print("POST /api/sync/trigger/{organization_id}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 