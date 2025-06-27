#!/usr/bin/env python3
"""
Fix Stale Sync Operation
Clean up the sync that's been stuck in "running" state for 16+ hours
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Set the database URL
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def fix_stale_sync():
    """Fix the stale sync operation"""
    print("🔧 Fixing Stale Sync Operation")
    print("=" * 50)
    
    try:
        # Find the stale sync
        stale_sync_id = "bfdb0ef9-bd24-4fe9-96a4-a5c717f270b8"
        
        with db.get_cursor() as cursor:
            # First, check the current status
            cursor.execute("""
                SELECT id, organization_id, status, started_at, completed_at, records_processed
                FROM sync_logs 
                WHERE id = %s
            """, (stale_sync_id,))
            
            sync_record = cursor.fetchone()
            
            if sync_record:
                print(f"📋 Found stale sync:")
                print(f"   ID: {sync_record['id']}")
                print(f"   Organization: {sync_record['organization_id']}")
                print(f"   Status: {sync_record['status']}")
                print(f"   Started: {sync_record['started_at']}")
                print(f"   Completed: {sync_record['completed_at']}")
                print(f"   Records: {sync_record['records_processed']}")
                
                if sync_record['status'] == 'running':
                    print(f"\n🔄 Updating stale sync to 'failed' status...")
                    
                    # Update the sync to failed status
                    cursor.execute("""
                        UPDATE sync_logs 
                        SET status = 'failed',
                            completed_at = %s
                        WHERE id = %s
                    """, (
                        datetime.now(timezone.utc),
                        stale_sync_id
                    ))
                    
                    db.connection.commit()
                    print(f"✅ Successfully updated stale sync to 'failed' status")
                    
                    # Verify the update
                    cursor.execute("""
                        SELECT status, completed_at
                        FROM sync_logs 
                        WHERE id = %s
                    """, (stale_sync_id,))
                    
                    updated_record = cursor.fetchone()
                    print(f"📋 Updated record:")
                    print(f"   Status: {updated_record['status']}")
                    print(f"   Completed: {updated_record['completed_at']}")
                    
                else:
                    print(f"ℹ️  Sync is not in 'running' status, current status: {sync_record['status']}")
            else:
                print(f"❌ Sync record not found with ID: {stale_sync_id}")
                
        # Also check for any other running syncs
        print(f"\n🔍 Checking for other stale syncs...")
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, organization_id, status, started_at, 
                       EXTRACT(EPOCH FROM (NOW() - started_at))/3600 as hours_running
                FROM sync_logs 
                WHERE status = 'running' 
                AND started_at < NOW() - INTERVAL '1 hour'
                ORDER BY started_at DESC
            """)
            
            stale_syncs = cursor.fetchall()
            
            if stale_syncs:
                print(f"📋 Found {len(stale_syncs)} stale sync(s):")
                for sync in stale_syncs:
                    print(f"   - {sync['id']}: {sync['organization_id']} ({sync['hours_running']:.1f} hours)")
                    
                    # Update each stale sync
                    cursor.execute("""
                        UPDATE sync_logs 
                        SET status = 'failed',
                            completed_at = %s
                        WHERE id = %s
                    """, (
                        datetime.now(timezone.utc),
                        sync['id']
                    ))
                
                db.connection.commit()
                print(f"✅ Updated {len(stale_syncs)} stale sync(s) to 'failed' status")
            else:
                print(f"✅ No other stale syncs found")
        
        print(f"\n🎉 Stale sync cleanup completed!")
        print(f"💡 Your frontend should now show the correct sync status")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing stale sync: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_stale_sync()
    sys.exit(0 if success else 1) 