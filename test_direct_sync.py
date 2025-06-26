#!/usr/bin/env python3
"""
Direct Sync Test - Bypasses API to show real sync progress
This demonstrates the actual sync logging for frontend teams
"""

import os
import sys
import time
import json
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import the sync service directly
from src.services.cliniko_sync_service import cliniko_sync_service
from src.database import db

ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

def print_step(step_num, title):
    print(f"\n{'='*70}")
    print(f"📋 STEP {step_num}: {title}")
    print(f"{'='*70}")

def monitor_sync_logs_realtime(org_id, duration=120):
    """Monitor sync logs in real-time during actual sync"""
    print("📊 Starting real-time sync log monitoring...")
    print("   (This shows what frontend can poll from /sync-logs/ endpoint)")
    print()
    
    start_time = time.time()
    last_log_id = 0
    
    while time.time() - start_time < duration:
        try:
            # Get latest sync log
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, status, records_processed, records_success, 
                           metadata, started_at, completed_at
                    FROM sync_logs 
                    WHERE organization_id = %s AND source_system = 'cliniko'
                    ORDER BY started_at DESC 
                    LIMIT 1
                """, (org_id,))
                
                result = cursor.fetchone()
                
            if result and result['id'] != last_log_id:
                last_log_id = result['id']
                
                # Parse metadata
                metadata = result['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                elapsed = int(time.time() - start_time)
                status = result['status']
                step = metadata.get('step', 'unknown')
                progress = metadata.get('progress_percent', 0)
                
                # Print status update
                print(f"[{elapsed:3d}s] Status: {status} | Step: {step} | Progress: {progress:.1f}%")
                
                # Print step-specific details
                if step == "fetching_patients":
                    current_page = metadata.get('current_page', 0)
                    patients_loaded = metadata.get('patients_loaded', 0)
                    print(f"       📡 API: Page {current_page} - {patients_loaded} patients loaded")
                elif step == "storing_patients":
                    processed = metadata.get('patients_processed', 0)
                    stored = metadata.get('patients_stored', 0)
                    total = metadata.get('total_patients', 0)
                    print(f"       💾 DB: {stored}/{total} patients stored ({processed} processed)")
                elif step == "completed":
                    patients_found = metadata.get('patients_found', 0)
                    patients_stored = metadata.get('patients_stored', 0)
                    success_rate = metadata.get('success_rate', 0)
                    print(f"       ✅ DONE: {patients_stored}/{patients_found} patients ({success_rate:.1f}% success)")
                    break
                elif step == "patients_fetched":
                    total_pages = metadata.get('total_pages', 0)
                    patients_found = metadata.get('patients_found', 0)
                    print(f"       ✅ API Complete: {patients_found} patients from {total_pages} pages")
                
                # Check if completed
                if status in ['completed', 'failed']:
                    print(f"       🏁 Sync {status}")
                    break
            
            time.sleep(2)  # Poll every 2 seconds
            
        except Exception as e:
            print(f"       ⚠️  Monitoring error: {e}")
            time.sleep(2)
    
    print("\n📊 Real-time monitoring completed")

def main():
    print("🧪 DIRECT SYNC TEST - REAL LOGGING DEMONSTRATION")
    print("="*70)
    print("This bypasses the API to show actual sync progress for frontend teams")
    
    # Step 1: Get baseline
    print_step(1, "Getting Current State")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM patients 
                WHERE organization_id = %s
            """, (ORG_ID,))
            
            result = cursor.fetchone()
            db_before = result['total'] if result else 0
            
    except Exception as e:
        print(f"❌ Failed to get baseline: {e}")
        return
    
    print(f"📊 Database Before: {db_before} patients")
    
    # Step 2: Test credentials
    print_step(2, "Testing Cliniko Connection")
    
    try:
        credentials = cliniko_sync_service.get_organization_cliniko_credentials(ORG_ID)
        if not credentials:
            print("❌ No credentials found")
            return
        
        print("✅ Credentials found")
        print(f"📡 API URL: {credentials.get('api_url')}")
        
    except Exception as e:
        print(f"❌ Credential check failed: {e}")
        return
    
    # Step 3: Run direct sync with monitoring
    print_step(3, "Running Direct Sync with Real-Time Monitoring")
    
    print("🚀 Starting sync in separate thread...")
    print("📊 This will show the REAL sync progress that frontend can monitor")
    print()
    
    # Start monitoring in background thread
    import threading
    
    monitor_thread = threading.Thread(
        target=monitor_sync_logs_realtime, 
        args=(ORG_ID, 120)
    )
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Give monitor thread time to start
    time.sleep(1)
    
    # Run the actual sync
    try:
        print("🔄 Executing sync_all_patients()...")
        result = cliniko_sync_service.sync_all_patients(ORG_ID)
        
        print(f"\n✅ Sync completed!")
        print(f"   - Success: {result.get('success')}")
        print(f"   - Patients found: {result.get('patients_found', 0)}")
        print(f"   - Patients stored: {result.get('patients_stored', 0)}")
        print(f"   - Errors: {len(result.get('errors', []))}")
        
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
    
    # Wait for monitor thread to finish
    monitor_thread.join(timeout=10)
    
    # Step 4: Final verification
    print_step(4, "Final Verification")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM patients 
                WHERE organization_id = %s
            """, (ORG_ID,))
            
            result = cursor.fetchone()
            db_after = result['total'] if result else 0
            
    except Exception as e:
        print(f"❌ Failed to get final count: {e}")
        return
    
    print(f"📊 Database After: {db_after} patients")
    print(f"📈 Change: {db_after - db_before:+d} patients")
    
    # Step 5: Frontend integration notes
    print_step(5, "Frontend Integration Summary")
    
    print("💡 Key Points for Frontend Teams:")
    print("   🔄 Background sync: API responds immediately, actual sync runs in background")
    print("   📊 Poll /sync-logs/{orgId}?limit=1 every 2-3 seconds for progress")
    print("   📝 Use metadata.step to show current operation to users")
    print("   📈 Use metadata.progress_percent for progress bars")
    print("   ⏱️  Expected duration: 30-120 seconds for large datasets")
    print("   ✅ Success rate: Should be 100% for patient storage")
    print()
    print("🎯 Available metadata.step values:")
    print("   - checking_config: Validating service setup")
    print("   - validating_credentials: Testing API connection") 
    print("   - fetching_patients: Downloading from Cliniko API")
    print("   - patients_fetched: API download complete")
    print("   - processing_patients: Preparing data for database")
    print("   - storing_patients: Saving to database with progress")
    print("   - completed: Sync finished successfully")

if __name__ == "__main__":
    main() 