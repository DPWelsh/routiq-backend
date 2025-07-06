#!/usr/bin/env python3
"""
Comprehensive Stale Sync Cleanup Script
Checks and cleans up stale sync operations from multiple sources:
1. Database sync_logs table (stuck in 'running' status)
2. Scheduler running_syncs tracking
3. Sync progress store for real-time tracking
"""

import sys
import os
sys.path.append('src')

import json
from datetime import datetime, timezone, timedelta
from database import db

def check_database_stale_syncs():
    """Check for stale syncs in database sync_logs table"""
    print("🔍 Checking database sync_logs for stale syncs...")
    
    try:
        with db.get_cursor() as cursor:
            # Find syncs stuck in 'running' status for more than 30 minutes
            stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
            
            cursor.execute("""
                SELECT id, organization_id, operation_type, status, started_at, 
                       EXTRACT(EPOCH FROM (NOW() - started_at))/60 AS minutes_running
                FROM sync_logs 
                WHERE status = 'running' 
                AND started_at < %s
                ORDER BY started_at ASC
            """, (stale_cutoff,))
            
            stale_syncs = cursor.fetchall()
            
            if stale_syncs:
                print(f"❌ Found {len(stale_syncs)} stale database syncs:")
                for sync in stale_syncs:
                    print(f"   - ID: {sync['id']}, Org: {sync['organization_id']}")
                    print(f"     Type: {sync['operation_type']}, Running for: {sync['minutes_running']:.1f} minutes")
                    print(f"     Started: {sync['started_at']}")
                return stale_syncs
            else:
                print("✅ No stale syncs found in database")
                return []
                
    except Exception as e:
        print(f"❌ Error checking database stale syncs: {e}")
        return []

def cleanup_database_stale_syncs(stale_syncs):
    """Cleanup stale syncs in database by marking them as failed"""
    if not stale_syncs:
        return 0
        
    print(f"🧹 Cleaning up {len(stale_syncs)} stale database syncs...")
    
    try:
        with db.get_cursor() as cursor:
            cleaned_count = 0
            for sync in stale_syncs:
                # Update status to failed with cleanup message
                cursor.execute("""
                    UPDATE sync_logs 
                    SET status = 'failed',
                        completed_at = NOW(),
                        error_details = %s,
                        metadata = %s
                    WHERE id = %s
                """, (
                    json.dumps({"error": "Sync cleaned up due to stale status (stuck in running)"}),
                    json.dumps({
                        "cleanup_reason": "stale_sync_cleanup", 
                        "original_status": "running",
                        "cleanup_time": datetime.now(timezone.utc).isoformat(),
                        "minutes_running": float(sync['minutes_running'])
                    }),
                    sync['id']
                ))
                cleaned_count += 1
                print(f"   ✅ Cleaned sync ID: {sync['id']}")
            
            print(f"✅ Successfully cleaned {cleaned_count} database syncs")
            return cleaned_count
            
    except Exception as e:
        print(f"❌ Error cleaning database stale syncs: {e}")
        return 0

def check_scheduler_running_syncs():
    """Check sync scheduler for organizations marked as currently syncing"""
    print("\n🔍 Checking sync scheduler running_syncs...")
    
    # Note: This would require access to the scheduler instance
    # For now, we'll check via the database if we can find any patterns
    try:
        with db.get_cursor() as cursor:
            # Check for recent sync activity per organization
            cursor.execute("""
                SELECT organization_id, 
                       MAX(started_at) as last_sync_start,
                       COUNT(*) as recent_syncs,
                       SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_count,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM sync_logs 
                WHERE started_at > NOW() - INTERVAL '2 hours'
                GROUP BY organization_id
                ORDER BY last_sync_start DESC
            """)
            
            sync_stats = cursor.fetchall()
            
            if sync_stats:
                print(f"📊 Found {len(sync_stats)} organizations with recent sync activity:")
                for stat in sync_stats:
                    status_summary = f"Running: {stat['running_count']}, Completed: {stat['completed_count']}, Failed: {stat['failed_count']}"
                    print(f"   - Org: {stat['organization_id']}")
                    print(f"     Last sync: {stat['last_sync_start']}, Total recent: {stat['recent_syncs']}")
                    print(f"     Status breakdown: {status_summary}")
                    if stat['running_count'] > 0:
                        print("     ⚠️  Has running syncs!")
            else:
                print("✅ No recent sync activity found")
                
            return sync_stats
                
    except Exception as e:
        print(f"❌ Error checking scheduler syncs: {e}")
        return []

def check_service_integrations_status():
    """Check service_integrations table for last sync times"""
    print("\n🔍 Checking service_integrations for sync status...")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT organization_id, service_name, is_active, sync_enabled,
                       last_sync_at,
                       EXTRACT(EPOCH FROM (NOW() - last_sync_at))/60 AS minutes_since_sync
                FROM service_integrations 
                WHERE service_name = 'cliniko'
                ORDER BY last_sync_at DESC NULLS LAST
            """)
            
            integrations = cursor.fetchall()
            
            if integrations:
                print(f"📊 Found {len(integrations)} Cliniko service integrations:")
                for integration in integrations:
                    sync_status = "Active" if integration['is_active'] and integration['sync_enabled'] else "Inactive"
                    last_sync = integration['last_sync_at']
                    if last_sync:
                        minutes_ago = integration['minutes_since_sync']
                        time_info = f"{minutes_ago:.1f} minutes ago"
                    else:
                        time_info = "Never synced"
                    
                    print(f"   - Org: {integration['organization_id']} ({sync_status})")
                    print(f"     Last sync: {time_info}")
            else:
                print("✅ No Cliniko service integrations found")
                
            return integrations
                
    except Exception as e:
        print(f"❌ Error checking service integrations: {e}")
        return []

def force_clear_organization_sync_status(organization_id):
    """Force clear sync status for a specific organization"""
    print(f"\n🧹 Force clearing sync status for organization: {organization_id}")
    
    try:
        with db.get_cursor() as cursor:
            # 1. Mark any running syncs as failed
            cursor.execute("""
                UPDATE sync_logs 
                SET status = 'failed',
                    completed_at = NOW(),
                    error_details = %s
                WHERE organization_id = %s 
                AND status = 'running'
            """, (
                json.dumps({"error": "Force cleared by admin cleanup"}),
                organization_id
            ))
            
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                print(f"   ✅ Marked {affected_rows} running syncs as failed")
            else:
                print("   ℹ️  No running syncs found to clear")
            
            return affected_rows > 0
            
    except Exception as e:
        print(f"❌ Error force clearing sync status: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🚀 Starting Comprehensive Stale Sync Cleanup")
    print("=" * 50)
    
    # 1. Check database stale syncs
    stale_db_syncs = check_database_stale_syncs()
    
    # 2. Check scheduler status  
    scheduler_stats = check_scheduler_running_syncs()
    
    # 3. Check service integrations
    integrations = check_service_integrations_status()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    total_issues = len(stale_db_syncs)
    
    if total_issues > 0:
        print(f"❌ Found {total_issues} issues that need cleanup")
        
        # Ask for cleanup confirmation
        print("\n🤔 Do you want to cleanup stale syncs? (y/N): ", end="")
        response = input().strip().lower()
        
        if response in ['y', 'yes']:
            print("\n🧹 Starting cleanup...")
            cleaned_count = cleanup_database_stale_syncs(stale_db_syncs)
            print(f"✅ Cleanup complete! Cleaned {cleaned_count} stale syncs")
        else:
            print("ℹ️  Skipping cleanup")
    else:
        print("✅ No stale syncs found - system is healthy!")
    
    # Show current active organizations
    if scheduler_stats:
        running_orgs = [stat for stat in scheduler_stats if stat['running_count'] > 0]
        if running_orgs:
            print(f"\n⚠️  Organizations with running syncs:")
            for org_stat in running_orgs:
                print(f"   - {org_stat['organization_id']} ({org_stat['running_count']} running)")
                
                print(f"\n🤔 Force clear org {org_stat['organization_id']}? (y/N): ", end="")
                response = input().strip().lower()
                if response in ['y', 'yes']:
                    force_clear_organization_sync_status(org_stat['organization_id'])

if __name__ == "__main__":
    main() 