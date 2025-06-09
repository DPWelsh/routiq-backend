#!/usr/bin/env python3
"""
SurfRehab v2 - Project Setup Script
Initialize clean project with Supabase database and API sync
"""

import os
import sys
import subprocess
import asyncio
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import db
from sync_manager import SyncManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_sql_files():
    """Run SQL schema files against Supabase database"""
    sql_dir = Path(__file__).parent.parent / 'sql'
    sql_files = sorted(sql_dir.glob('*.sql'))
    
    database_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL environment variable required")
    
    for sql_file in sql_files:
        logger.info(f"Running {sql_file.name}...")
        
        cmd = f"psql '{database_url}' -f '{sql_file}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to run {sql_file.name}: {result.stderr}")
            raise Exception(f"SQL execution failed: {result.stderr}")
        
        logger.info(f"✅ {sql_file.name} executed successfully")

async def initial_data_sync():
    """Run initial data synchronization"""
    organization_id = os.getenv('ORGANIZATION_ID', 'default')
    sync_manager = SyncManager(organization_id=organization_id)
    
    logger.info("🔄 Running initial data sync...")
    
    # Run full sync
    results = await sync_manager.full_sync()
    
    if results.get('success'):
        logger.info("✅ Initial sync completed successfully")
        
        # Show status
        status = sync_manager.get_sync_status()
        if status.get('success'):
            logger.info("📊 Data Summary:")
            for contact_type, stats in status.get('contact_stats', {}).items():
                logger.info(f"   - {contact_type}: {stats['count']} contacts")
            logger.info(f"   - Active patients: {status.get('active_patients_count', 0)}")
            logger.info(f"   - Conversations: {status.get('conversations_count', 0)}")
    else:
        logger.error("❌ Initial sync failed")
        for system, result in results.items():
            if isinstance(result, dict) and not result.get('success'):
                logger.error(f"   - {system}: {result.get('error')}")

def verify_environment():
    """Verify required environment variables"""
    required_vars = [
        'SUPABASE_DB_URL',
        'CLINIKO_API_KEY',
        'CHATWOOT_API_TOKEN',
        'ORGANIZATION_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Copy config/env.example to .env and fill in your values")
        return False
    
    return True

async def main():
    """Main setup function"""
    print("🚀 SurfRehab v2 - Project Setup")
    print("=" * 50)
    
    # 1. Verify environment
    print("\n1️⃣ Verifying environment...")
    if not verify_environment():
        return
    print("✅ Environment verified")
    
    # 2. Test database connection
    print("\n2️⃣ Testing database connection...")
    if not db.health_check():
        print("❌ Database connection failed")
        return
    print("✅ Database connection successful")
    
    # 3. Create database schema
    print("\n3️⃣ Creating database schema...")
    try:
        run_sql_files()
        print("✅ Database schema created")
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return
    
    # 4. Run initial data sync
    print("\n4️⃣ Running initial data sync...")
    try:
        await initial_data_sync()
    except Exception as e:
        print(f"❌ Data sync failed: {e}")
        return
    
    # 5. Success summary
    print("\n🎉 Project setup complete!")
    print("\n📝 Next steps:")
    print("   1. Verify data in Supabase dashboard")
    print("   2. Set up scheduled syncs (cron or Railway cron)")
    print("   3. Build ManyChat/Momence/Google Calendar integrations")
    print("   4. Deploy to Railway for production")
    print("   5. Set up monitoring and alerts")
    
    print(f"\n🔗 Useful commands:")
    print(f"   - Check sync status: python -m src.sync_manager")
    print(f"   - Run manual sync: python scripts/manual_sync.py")
    print(f"   - View database: psql '{os.getenv('SUPABASE_DB_URL')}'")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main()) 