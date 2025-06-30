#!/usr/bin/env python3
"""
Enable Hourly Sync Scheduler
Sets up automatic syncing every hour for all organizations
"""

import os
import sys
from pathlib import Path

print("⏰ Enabling Hourly Sync Scheduler")
print("=" * 40)

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def check_scheduler_setup():
    """Check if the scheduler is properly configured"""
    try:
        from services.sync_scheduler import scheduler
        from services.comprehensive_cliniko_sync import ComprehensiveClinikoSync
        
        print("✅ Scheduler imports successful")
        
        # Test organization lookup
        org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
        status = scheduler.get_sync_status(org_id)
        
        print("📊 Scheduler Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_environment_setup():
    """Show the environment variables needed"""
    print("\n🔧 Environment Variables for Railway:")
    print("Add these to your Railway environment:")
    print()
    print("ENABLE_SYNC_SCHEDULER=true")
    print("SYNC_INTERVAL_MINUTES=60")
    print()
    print("💡 This will:")
    print("   • Enable automatic sync scheduling")
    print("   • Run syncs every 60 minutes (hourly)")
    print("   • Use comprehensive sync for better data quality")
    print("   • Process all organizations with active patients")

def main():
    print("🔍 Testing Scheduler Components...")
    
    if check_scheduler_setup():
        print("\n✅ Scheduler is ready!")
        show_environment_setup()
        
        print("\n🚀 Next Steps:")
        print("1. Add the environment variables to Railway")
        print("2. Redeploy your application")
        print("3. Check logs for '✅ Sync scheduler started successfully'")
        print("4. Monitor sync_logs table for hourly sync entries")
        
        print("\n📊 Manual Testing:")
        print("You can test the scheduler API endpoints:")
        print("• GET /api/v1/sync/scheduler/status")
        print("• POST /api/v1/sync/scheduler/trigger")
        
    else:
        print("\n❌ Scheduler setup failed")
        print("Please check the error messages above")

if __name__ == "__main__":
    main() 