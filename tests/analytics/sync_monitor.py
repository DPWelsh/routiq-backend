#!/usr/bin/env python3
"""
Simple Sync Monitor - Track Cliniko sync status and detect issues
Phase 1 Task 1.3: Verify Sync Actually Works
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class SimpleSyncMonitor:
    def __init__(self, base_url="https://routiq-backend-prod.up.railway.app"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.timeout = 30
        
        # Real organization ID
        self.org_id = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
        self.org_name = "Surf Rehab"
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/cliniko/status/{self.org_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def trigger_sync(self) -> Dict[str, Any]:
        """Trigger a new sync"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/cliniko/sync/{self.org_id}",
                headers=self.headers,
                timeout=self.timeout,
                data=""
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "response": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def monitor_sync_progress(self, max_wait_minutes=10):
        """Monitor sync progress after triggering"""
        print(f"🔄 SYNC MONITORING - {self.org_name}")
        print("=" * 60)
        
        # Get baseline status
        print("📊 Getting baseline status...")
        baseline = self.get_current_status()
        
        if "error" in baseline:
            print(f"❌ Failed to get baseline: {baseline['error']}")
            return
            
        baseline_time = baseline.get("last_sync_time")
        print(f"📅 Baseline sync time: {baseline_time}")
        print(f"👥 Current data: {baseline.get('total_contacts', 0)} contacts, {baseline.get('active_patients', 0)} patients")
        
        # Trigger sync
        print(f"\n🚀 Triggering sync...")
        sync_response = self.trigger_sync()
        
        if "error" in sync_response:
            print(f"❌ Failed to trigger sync: {sync_response['error']}")
            return
            
        print(f"✅ Sync triggered: {sync_response.get('message', 'Started')}")
        trigger_time = datetime.now()
        
        # Monitor progress
        print(f"\n⏱️  Monitoring sync progress for {max_wait_minutes} minutes...")
        print("   Checking every 30 seconds...")
        
        checks = 0
        max_checks = max_wait_minutes * 2  # 30-second intervals
        
        while checks < max_checks:
            time.sleep(30)  # Wait 30 seconds
            checks += 1
            elapsed = checks * 30
            
            print(f"\n🔍 Check #{checks} ({elapsed}s elapsed)")
            current = self.get_current_status()
            
            if "error" in current:
                print(f"❌ Status check failed: {current['error']}")
                continue
                
            current_time = current.get("last_sync_time")
            
            # Check if sync completed
            if current_time != baseline_time:
                print(f"🎉 SYNC COMPLETED!")
                print(f"📅 New sync time: {current_time}")
                print(f"⏱️  Total duration: {elapsed} seconds")
                print(f"👥 Updated data: {current.get('total_contacts', 0)} contacts, {current.get('active_patients', 0)} patients")
                
                # Check for changes
                if current.get('total_contacts', 0) != baseline.get('total_contacts', 0):
                    print(f"📈 Contacts changed: {baseline.get('total_contacts', 0)} → {current.get('total_contacts', 0)}")
                if current.get('active_patients', 0) != baseline.get('active_patients', 0):
                    print(f"📈 Patients changed: {baseline.get('active_patients', 0)} → {current.get('active_patients', 0)}")
                
                return {
                    "success": True,
                    "duration_seconds": elapsed,
                    "baseline": baseline,
                    "final": current
                }
            else:
                print(f"⏳ Still syncing... (sync time unchanged)")
        
        # Sync didn't complete within time limit
        print(f"\n⚠️  SYNC TIMEOUT after {max_wait_minutes} minutes")
        print(f"❌ Sync appears to have failed or is taking too long")
        print(f"📅 Last sync time still: {baseline_time}")
        
        return {
            "success": False,
            "error": "timeout",
            "duration_seconds": max_wait_minutes * 60,
            "baseline": baseline,
            "final": current
        }
    
    def check_sync_health(self):
        """Quick sync health check"""
        print(f"🏥 SYNC HEALTH CHECK - {self.org_name}")
        print("=" * 60)
        
        status = self.get_current_status()
        
        if "error" in status:
            print(f"❌ Status check failed: {status['error']}")
            return
        
        last_sync = status.get("last_sync_time")
        if last_sync:
            # Parse timestamp
            try:
                sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                age_hours = (datetime.now(sync_dt.tzinfo) - sync_dt).total_seconds() / 3600
                
                print(f"📅 Last sync: {last_sync}")
                print(f"⏰ Age: {age_hours:.1f} hours ago")
                
                if age_hours < 1:
                    health = "🟢 EXCELLENT"
                elif age_hours < 24:
                    health = "🟡 GOOD"
                elif age_hours < 168:  # 1 week
                    health = "🟠 STALE"
                else:
                    health = "🔴 VERY STALE"
                
                print(f"🔋 Sync Health: {health}")
                
            except Exception as e:
                print(f"⚠️  Could not parse sync time: {e}")
        else:
            print(f"❌ No sync time available")
        
        print(f"👥 Data: {status.get('total_contacts', 0)} contacts, {status.get('active_patients', 0)} patients, {status.get('upcoming_appointments', 0)} appointments")

def main():
    monitor = SimpleSyncMonitor()
    
    print("🚀 SYNC MONITORING TOOL")
    print("=" * 80)
    
    # Quick health check first
    monitor.check_sync_health()
    
    # Ask user what to do
    print(f"\n🤔 What would you like to do?")
    print("1. Just check current status")
    print("2. Trigger sync and monitor progress")
    print("3. Full sync test (trigger + monitor)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print(f"\n📊 Current status already shown above")
            
        elif choice == "2" or choice == "3":
            result = monitor.monitor_sync_progress()
            
            if result and result.get("success"):
                print(f"\n✅ SYNC MONITORING SUCCESS")
            else:
                print(f"\n❌ SYNC MONITORING FAILED")
                if result:
                    print(f"Error: {result.get('error', 'Unknown')}")
        else:
            print(f"Invalid choice: {choice}")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 