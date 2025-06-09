#!/usr/bin/env python3
"""
Manual sync script for SurfRehab v2
Can be run manually or via cron/Railway scheduled jobs
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sync_manager import SyncManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run manual sync"""
    print(f"🔄 SurfRehab v2 - Manual Sync")
    print(f"Started at: {datetime.now()}")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    organization_id = os.getenv('ORGANIZATION_ID', 'default')
    sync_manager = SyncManager(organization_id=organization_id)
    
    try:
        # Run full sync
        results = await sync_manager.full_sync()
        
        # Print results
        print("\n📊 Sync Results:")
        print(json.dumps(results, indent=2, default=str))
        
        # Show current status
        status = sync_manager.get_sync_status()
        print("\n📈 Current Status:")
        if status.get('success'):
            for contact_type, stats in status.get('contact_stats', {}).items():
                print(f"   - {contact_type}: {stats['count']} contacts")
            print(f"   - Active patients: {status.get('active_patients_count', 0)}")
            print(f"   - Conversations: {status.get('conversations_count', 0)}")
        
        # Exit with appropriate code
        if results.get('success'):
            print("\n✅ Sync completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Sync failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Sync failed with exception: {e}")
        print(f"\n💥 Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())