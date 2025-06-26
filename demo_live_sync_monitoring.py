#!/usr/bin/env python3
"""
Live Sync Monitoring Demo for Frontend Teams
Shows exactly how to implement real-time progress tracking
"""

import requests
import time
import json
import threading
from datetime import datetime

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORG_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"

class SyncMonitor:
    def __init__(self):
        self.monitoring = False
        self.sync_started = False
        self.sync_completed = False
        self.progress_data = []
        
    def start_monitoring(self):
        """Start monitoring sync logs in background thread"""
        self.monitoring = True
        self.sync_started = False
        self.sync_completed = False
        self.progress_data = []
        
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        print("📊 Real-time monitoring started...")
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        last_log_id = None
        check_interval = 1  # Check every 1 second for maximum responsiveness
        
        while self.monitoring:
            try:
                # Get latest sync log
                response = requests.get(f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=1")
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('logs'):
                        log = data['logs'][0]
                        log_id = log.get('id')
                        
                        # Only process new or updated logs
                        if log_id != last_log_id:
                            last_log_id = log_id
                            self._process_log_update(log)
                            
                            # Check if sync completed
                            if log.get('status') in ['completed', 'failed']:
                                self.sync_completed = True
                                break
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"   ⚠️  Monitoring error: {e}")
                time.sleep(check_interval)
    
    def _process_log_update(self, log):
        """Process a log update and display progress"""
        status = log.get('status', 'unknown')
        metadata = log.get('metadata', {})
        
        # Parse metadata if it's a string
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        step = metadata.get('step', 'unknown')
        progress_percent = metadata.get('progress_percent', 0)
        
        # Calculate elapsed time
        started_at = log.get('started_at')
        if started_at:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elapsed = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
        else:
            elapsed = 0
        
        # Mark sync as started if we see a running status
        if status == 'running' and not self.sync_started:
            self.sync_started = True
            print("🚀 Sync detected! Background task started...")
        
        # Display progress update
        self._display_progress_update(status, step, progress_percent, elapsed, metadata, log)
        
        # Store progress data for analysis
        self.progress_data.append({
            'timestamp': datetime.now().isoformat(),
            'elapsed': elapsed,
            'status': status,
            'step': step,
            'progress': progress_percent,
            'metadata': metadata
        })
    
    def _display_progress_update(self, status, step, progress, elapsed, metadata, log):
        """Display formatted progress update"""
        elapsed_str = f"{int(elapsed):3d}s"
        
        # Different displays based on step
        if step == "initializing":
            print(f"[{elapsed_str}] 🔄 Initializing sync process...")
        elif step == "checking_config":
            print(f"[{elapsed_str}] 🔍 Validating service configuration...")
        elif step == "validating_credentials":
            print(f"[{elapsed_str}] 🔑 Testing Cliniko API credentials...")
        elif step == "fetching_patients":
            current_page = metadata.get('current_page', 0)
            patients_loaded = metadata.get('patients_loaded', 0)
            total_pages = metadata.get('total_pages', '?')
            print(f"[{elapsed_str}] 📡 Fetching from Cliniko API")
            print(f"         Page {current_page}/{total_pages} - {patients_loaded} patients loaded")
        elif step == "patients_fetched":
            total_pages = metadata.get('total_pages', 0)
            patients_found = metadata.get('patients_found', 0)
            print(f"[{elapsed_str}] ✅ API Fetch Complete")
            print(f"         {patients_found} patients from {total_pages} pages")
        elif step == "processing_patients":
            patients_found = metadata.get('patients_found', 0)
            print(f"[{elapsed_str}] 🔍 Processing {patients_found} patients for database...")
        elif step == "storing_patients":
            patients_processed = metadata.get('patients_processed', 0)
            patients_stored = metadata.get('patients_stored', 0)
            total_patients = metadata.get('total_patients', 0)
            print(f"[{elapsed_str}] 💾 Storing in database ({progress:.1f}%)")
            print(f"         {patients_stored}/{total_patients} patients stored")
        elif step == "completed":
            patients_found = metadata.get('patients_found', 0)
            patients_stored = metadata.get('patients_stored', 0)
            success_rate = metadata.get('success_rate', 0)
            print(f"[{elapsed_str}] ✅ SYNC COMPLETED!")
            print(f"         {patients_stored}/{patients_found} patients ({success_rate:.1f}% success)")
        elif status == "completed":
            # Fallback for completed status without specific step
            records_processed = log.get('records_processed', 0)
            records_success = log.get('records_success', 0)
            success_rate = (records_success / records_processed * 100) if records_processed > 0 else 0
            print(f"[{elapsed_str}] ✅ SYNC COMPLETED!")
            print(f"         {records_success}/{records_processed} patients ({success_rate:.1f}% success)")
        else:
            print(f"[{elapsed_str}] 🔄 {step} ({progress:.1f}%)")
    
    def get_progress_summary(self):
        """Get summary of collected progress data"""
        if not self.progress_data:
            return "No progress data collected"
        
        total_time = max([p['elapsed'] for p in self.progress_data])
        steps = list(set([p['step'] for p in self.progress_data]))
        
        return {
            'total_duration': f"{total_time:.1f} seconds",
            'steps_observed': steps,
            'updates_captured': len(self.progress_data),
            'final_status': self.progress_data[-1]['status'] if self.progress_data else 'unknown'
        }

def main():
    print("🧪 LIVE SYNC MONITORING DEMONSTRATION")
    print("="*70)
    print("This shows exactly how frontend teams should implement real-time progress")
    print()
    
    monitor = SyncMonitor()
    
    # Step 1: Get baseline info
    print("📊 STEP 1: Getting Current State")
    print("-" * 40)
    
    try:
        # Test connection to get patient count
        conn_response = requests.get(f"{BASE_URL}/api/v1/cliniko/test-connection/{ORG_ID}")
        if conn_response.status_code == 200:
            conn_data = conn_response.json()
            cliniko_total = conn_data.get('total_patients_available', 0)
            print(f"✅ Cliniko Total Patients: {cliniko_total}")
        else:
            print("❌ Failed to get Cliniko patient count")
            return
        
        # Get database count
        status_response = requests.get(f"{BASE_URL}/api/v1/cliniko/status/{ORG_ID}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            db_total = status_data.get('total_patients', 0)
            last_sync = status_data.get('last_sync_time', 'Never')
            print(f"📊 Database Patients: {db_total}")
            print(f"📅 Last Sync: {last_sync}")
        
    except Exception as e:
        print(f"❌ Failed to get baseline: {e}")
        return
    
    print()
    input("Press Enter to start live sync monitoring demo...")
    
    # Step 2: Start monitoring BEFORE triggering sync
    print("\n📊 STEP 2: Starting Real-Time Monitoring")
    print("-" * 40)
    print("🔄 Starting background monitoring thread...")
    monitor_thread = monitor.start_monitoring()
    
    # Give monitoring time to establish
    time.sleep(2)
    
    # Step 3: Trigger sync
    print("\n🚀 STEP 3: Triggering Sync")
    print("-" * 40)
    print("📡 Sending sync request to API...")
    
    try:
        sync_response = requests.post(f"{BASE_URL}/api/v1/cliniko/sync-all/{ORG_ID}")
        if sync_response.status_code == 200:
            sync_data = sync_response.json()
            print(f"✅ API Response: {sync_data.get('message')}")
            print("⏳ Sync runs in background - monitoring for progress...")
        else:
            print(f"❌ Sync request failed: {sync_response.status_code}")
            monitor.stop_monitoring()
            return
    except Exception as e:
        print(f"❌ Sync request error: {e}")
        monitor.stop_monitoring()
        return
    
    # Step 4: Wait for sync completion
    print("\n📊 STEP 4: Live Progress Updates")
    print("-" * 40)
    print("Frontend Implementation: Poll /sync-logs/{orgId}?limit=1 every 1-2 seconds")
    print()
    
    # Wait for sync to be detected
    wait_time = 0
    max_wait = 10  # Wait up to 10 seconds for sync to start
    
    while not monitor.sync_started and wait_time < max_wait:
        print(f"   ⏳ Waiting for background sync to start... ({wait_time}s)")
        time.sleep(1)
        wait_time += 1
    
    if not monitor.sync_started:
        print("   ⚠️  Sync may have completed too quickly or failed to start")
        print("   📊 Checking if sync completed during startup...")
        
        # Check final logs
        logs_response = requests.get(f"{BASE_URL}/api/v1/cliniko/sync-logs/{ORG_ID}?limit=1")
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            if logs_data.get('logs'):
                latest_log = logs_data['logs'][0]
                started_at = latest_log.get('started_at')
                completed_at = latest_log.get('completed_at')
                
                if started_at and completed_at:
                    start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds()
                    
                    print(f"   ✅ Sync completed in {duration:.1f} seconds")
                    print(f"   📊 {latest_log.get('records_success', 0)}/{latest_log.get('records_processed', 0)} patients processed")
    else:
        # Wait for completion
        max_sync_wait = 120  # 2 minutes max
        sync_wait = 0
        
        while not monitor.sync_completed and sync_wait < max_sync_wait:
            time.sleep(1)
            sync_wait += 1
        
        if monitor.sync_completed:
            print("\n🎉 Sync monitoring completed!")
        else:
            print(f"\n⏰ Monitoring timeout after {max_sync_wait}s")
    
    # Stop monitoring
    monitor.stop_monitoring()
    monitor_thread.join(timeout=5)
    
    # Step 5: Summary and frontend guidance
    print("\n📋 STEP 5: Implementation Summary")
    print("-" * 40)
    
    summary = monitor.get_progress_summary()
    print(f"📊 Monitoring Results:")
    print(f"   - Duration: {summary.get('total_duration', 'N/A')}")
    print(f"   - Updates: {summary.get('updates_captured', 0)} progress updates captured")
    print(f"   - Steps: {len(summary.get('steps_observed', []))} different steps observed")
    print(f"   - Final Status: {summary.get('final_status', 'unknown')}")
    
    print(f"\n💡 Frontend Implementation Guide:")
    print(f"   🔄 Start monitoring BEFORE triggering sync")
    print(f"   📡 POST /api/v1/cliniko/sync-all/{{orgId}} to start sync")
    print(f"   📊 Poll GET /api/v1/cliniko/sync-logs/{{orgId}}?limit=1 every 1-2 seconds")
    print(f"   📈 Use metadata.progress_percent for progress bars (0-100)")
    print(f"   📝 Use metadata.step for user-friendly status messages")
    print(f"   ⏱️  Expected duration: 60-120 seconds for 600+ patients")
    print(f"   ✅ Success criteria: status='completed' AND records_success > 0")
    
    print(f"\n🎯 Available Progress Steps:")
    steps_observed = summary.get('steps_observed', [])
    if steps_observed:
        for step in steps_observed:
            print(f"   - {step}")
    else:
        print("   - checking_config, validating_credentials, fetching_patients")
        print("   - patients_fetched, processing_patients, storing_patients, completed")

if __name__ == "__main__":
    main() 