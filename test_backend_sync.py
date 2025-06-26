#!/usr/bin/env python3
"""
Comprehensive Backend Sync Tests
Tests all sync functionality including stale sync cleanup and timeout handling
"""

import requests
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://routiq-backend-prod.up.railway.app"
ORGANIZATION_ID = "org_2xwHiNrj68eaRUlX10anlXGvzX7"
TIMEOUT = 30

class BackendSyncTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.org_id = ORGANIZATION_ID
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any]):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        
        if details.get("message"):
            print(f"   {details['message']}")
    
    def test_stale_sync_cleanup(self) -> bool:
        """Test the stale sync cleanup endpoint"""
        try:
            response = requests.post(f"{self.base_url}/api/v1/sync/cleanup", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Stale Sync Cleanup", "PASS", {
                    "message": f"Cleaned up {data.get('cleaned_syncs', 0)} stale syncs",
                    "response": data
                })
                return True
            else:
                self.log_test("Stale Sync Cleanup", "FAIL", {
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_test("Stale Sync Cleanup", "FAIL", {
                "message": f"Exception: {str(e)}"
            })
            return False
    
    def test_dashboard_with_cleanup(self) -> bool:
        """Test dashboard endpoint with automatic cleanup"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/sync/dashboard/{self.org_id}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                current_sync = data.get('current_sync')
                patient_stats = data.get('patient_stats', {})
                
                self.log_test("Dashboard with Auto-Cleanup", "PASS", {
                    "message": f"Total patients: {patient_stats.get('total_patients', 0)}, Active: {patient_stats.get('active_patients', 0)}",
                    "has_current_sync": current_sync is not None,
                    "current_sync_status": current_sync.get('status') if current_sync else None
                })
                return True
            else:
                self.log_test("Dashboard with Auto-Cleanup", "FAIL", {
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_test("Dashboard with Auto-Cleanup", "FAIL", {
                "message": f"Exception: {str(e)}"
            })
            return False
    
    def test_duplicate_sync_prevention(self) -> bool:
        """Test that duplicate syncs are prevented"""
        try:
            # Start first sync
            response1 = requests.post(f"{self.base_url}/api/v1/sync/start/{self.org_id}?sync_mode=active", timeout=TIMEOUT)
            
            if response1.status_code != 200:
                self.log_test("Duplicate Sync Prevention", "FAIL", {
                    "message": f"Failed to start first sync: HTTP {response1.status_code}"
                })
                return False
            
            sync1_data = response1.json()
            sync1_id = sync1_data.get("sync_id")
            
            # Wait a moment
            time.sleep(2)
            
            # Try to start second sync
            response2 = requests.post(f"{self.base_url}/api/v1/sync/start/{self.org_id}?sync_mode=full", timeout=TIMEOUT)
            
            if response2.status_code == 200:
                sync2_data = response2.json()
                
                if "already in progress" in sync2_data.get("message", ""):
                    self.log_test("Duplicate Sync Prevention", "PASS", {
                        "message": "Successfully prevented duplicate sync",
                        "first_sync": sync1_id,
                        "second_response": sync2_data.get("message")
                    })
                    return True
                else:
                    self.log_test("Duplicate Sync Prevention", "FAIL", {
                        "message": "Did not prevent duplicate sync",
                        "first_sync": sync1_id,
                        "second_sync": sync2_data.get("sync_id")
                    })
                    return False
            else:
                self.log_test("Duplicate Sync Prevention", "FAIL", {
                    "message": f"Second sync request failed: HTTP {response2.status_code}"
                })
                return False
                
        except Exception as e:
            self.log_test("Duplicate Sync Prevention", "FAIL", {
                "message": f"Exception: {str(e)}"
            })
            return False
    
    def test_sync_history(self) -> bool:
        """Test sync history endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/sync/history/{self.org_id}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                recent_syncs = data.get('recent_syncs', [])
                
                self.log_test("Sync History", "PASS", {
                    "message": f"Found {len(recent_syncs)} recent syncs",
                    "total_syncs": data.get('total_syncs', 0),
                    "successful_syncs": data.get('successful_syncs', 0),
                    "failed_syncs": data.get('failed_syncs', 0)
                })
                return True
            else:
                self.log_test("Sync History", "FAIL", {
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_test("Sync History", "FAIL", {
                "message": f"Exception: {str(e)}"
            })
            return False
    
    def monitor_sync_progress(self, max_wait_seconds: int = 120) -> bool:
        """Monitor sync progress for a limited time"""
        try:
            # Get current sync from dashboard
            dashboard_response = requests.get(f"{self.base_url}/api/v1/sync/dashboard/{self.org_id}", timeout=TIMEOUT)
            
            if dashboard_response.status_code != 200:
                self.log_test("Sync Progress Monitoring", "FAIL", {
                    "message": "Could not get dashboard data"
                })
                return False
            
            dashboard_data = dashboard_response.json()
            current_sync = dashboard_data.get('current_sync')
            
            if not current_sync:
                self.log_test("Sync Progress Monitoring", "WARN", {
                    "message": "No current sync to monitor"
                })
                return True
            
            sync_id = current_sync.get('sync_id')
            start_time = time.time()
            last_step = None
            
            print(f"   Monitoring sync: {sync_id}")
            
            while time.time() - start_time < max_wait_seconds:
                # Check dashboard (which includes cleanup)
                response = requests.get(f"{self.base_url}/api/v1/sync/dashboard/{self.org_id}", timeout=TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    sync = data.get('current_sync')
                    
                    if not sync:
                        self.log_test("Sync Progress Monitoring", "PASS", {
                            "message": "Sync completed (no longer in current_sync)",
                            "duration_seconds": int(time.time() - start_time)
                        })
                        return True
                    
                    status = sync.get('status')
                    step = sync.get('current_step')
                    progress = sync.get('progress_percentage', 0)
                    
                    if step != last_step:
                        print(f"   {progress}% - {status}: {step}")
                        last_step = step
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        self.log_test("Sync Progress Monitoring", "PASS", {
                            "message": f"Sync finished with status: {status}",
                            "duration_seconds": int(time.time() - start_time),
                            "final_progress": progress
                        })
                        return True
                
                time.sleep(5)  # Check every 5 seconds
            
            # Timeout reached
            self.log_test("Sync Progress Monitoring", "WARN", {
                "message": f"Monitoring timed out after {max_wait_seconds} seconds",
                "last_status": current_sync.get('status'),
                "last_step": current_sync.get('current_step')
            })
            return False
            
        except Exception as e:
            self.log_test("Sync Progress Monitoring", "FAIL", {
                "message": f"Exception: {str(e)}"
            })
            return False
    
    def test_force_cancel(self, sync_id: str) -> bool:
        """Test force cancel functionality"""
        try:
            response = requests.delete(f"{self.base_url}/api/v1/sync/force-cancel/{sync_id}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Force Cancel Sync", "PASS", {
                    "message": f"Successfully cancelled sync: {sync_id}",
                    "response": data.get("message")
                })
                return True
            elif response.status_code == 404:
                self.log_test("Force Cancel Sync", "PASS", {
                    "message": f"Sync not found (may have already completed): {sync_id}"
                })
                return True
            else:
                self.log_test("Force Cancel Sync", "FAIL", {
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_test("Force Cancel Sync", "FAIL", {
                "message": f"Exception: {str(e)}"
            })
            return False
    
    def run_all_tests(self):
        """Run all backend sync tests"""
        print("🧪 COMPREHENSIVE BACKEND SYNC TESTS")
        print("=" * 60)
        print(f"Backend: {self.base_url}")
        print(f"Organization: {self.org_id}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Test 1: Stale sync cleanup
        self.test_stale_sync_cleanup()
        time.sleep(1)
        
        # Test 2: Dashboard with auto-cleanup
        self.test_dashboard_with_cleanup()
        time.sleep(1)
        
        # Test 3: Sync history
        self.test_sync_history()
        time.sleep(1)
        
        # Test 4: Duplicate sync prevention
        self.test_duplicate_sync_prevention()
        time.sleep(2)
        
        # Test 5: Monitor sync progress
        print("\n📊 Monitoring sync progress...")
        self.monitor_sync_progress(max_wait_seconds=60)
        
        # Test 6: Force cancel if still running
        dashboard_response = requests.get(f"{self.base_url}/api/v1/sync/dashboard/{self.org_id}", timeout=TIMEOUT)
        if dashboard_response.status_code == 200:
            current_sync = dashboard_response.json().get('current_sync')
            if current_sync and current_sync.get('status') in ['running', 'starting']:
                print("\n🛑 Testing force cancel on running sync...")
                self.test_force_cancel(current_sync.get('sync_id'))
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        
        pass_count = len([r for r in self.test_results if r['status'] == 'PASS'])
        fail_count = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warn_count = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"✅ Passed: {pass_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"⚠️  Warnings: {warn_count}")
        print(f"📊 Total: {len(self.test_results)}")
        
        if fail_count == 0:
            print("\n🎉 All critical tests passed!")
        else:
            print(f"\n⚠️  {fail_count} tests failed - check logs above")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backend_sync_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total": len(self.test_results),
                    "passed": pass_count,
                    "failed": fail_count,
                    "warnings": warn_count
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        
        return fail_count == 0

if __name__ == "__main__":
    tester = BackendSyncTester()
    success = tester.run_all_tests()
    exit(0 if success else 1) 