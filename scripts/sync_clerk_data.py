#!/usr/bin/env python3
"""
Clerk Data Sync Script
Command-line utility to sync all Clerk data to database
"""

import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('clerk_sync.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main sync function"""
    parser = argparse.ArgumentParser(description="Sync Clerk data to database")
    parser.add_argument('--dry-run', action='store_true', help='Test connection without syncing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Import after path setup
        from integrations.clerk_sync import clerk_sync
        
        logger.info("🚀 Starting Clerk data sync script...")
        
        if args.dry_run:
            logger.info("🧪 Running connection test only (dry-run mode)")
            
            # Test Clerk API connection
            status = await clerk_sync.get_clerk_api_status()
            
            if status.get("connected"):
                logger.info("✅ Clerk API connection successful")
                logger.info(f"📊 Users available: {status.get('approximate_users')}")
                logger.info(f"🏢 Organizations available: {status.get('approximate_organizations')}")
            else:
                logger.error(f"❌ Clerk API connection failed: {status.get('error')}")
                return 1
            
            return 0
        
        # Perform full sync
        logger.info("🔄 Starting comprehensive Clerk data synchronization...")
        start_time = datetime.now()
        
        sync_result = await clerk_sync.sync_all_data()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Print results
        print("\n" + "="*60)
        print("📋 CLERK DATA SYNC RESULTS")
        print("="*60)
        
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Success: {sync_result['success']}")
        
        if sync_result['success']:
            print(f"👥 Users synced: {sync_result['users']['synced']}")
            print(f"🏢 Organizations synced: {sync_result['organizations']['synced']}")
            print(f"🔗 Memberships synced: {sync_result['memberships']['synced']}")
        else:
            print(f"❌ Error: {sync_result.get('error', 'Unknown error')}")
        
        # Print any errors
        total_errors = (
            len(sync_result['users']['errors']) +
            len(sync_result['organizations']['errors']) +
            len(sync_result['memberships']['errors'])
        )
        
        if total_errors > 0:
            print(f"\n⚠️  {total_errors} errors occurred:")
            
            for category in ['users', 'organizations', 'memberships']:
                errors = sync_result[category]['errors']
                if errors:
                    print(f"\n{category.title()} errors:")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"  • {error}")
                    if len(errors) > 3:
                        print(f"  • ... and {len(errors) - 3} more")
        
        print("="*60)
        
        return 0 if sync_result['success'] else 1
        
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Script interrupted by user")
        sys.exit(130) 