#!/usr/bin/env python3
"""
Cliniko Analytics - Phase 1: Data Discovery & Organization Setup
Implements Step 1 (Identify Active Organizations) and Step 2 (Check Sync Status)
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse

class ClinikoPhase1Discovery:
    """Phase 1: Organization Discovery and Sync Status Analysis"""
    
    def __init__(self, base_url: str = None):
        """Initialize the discovery client"""
        self.base_url = base_url or os.getenv("TEST_SERVER_URL", "https://routiq-backend-prod.up.railway.app")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Cliniko-Analytics-Phase1/1.0"
        }
        self.timeout = 30
        
        # Real organization IDs from Clerk (not slugs!)
        self.organizations = {
            "org_2xwHiNrj68eaRUlX10anlXGvzX7": "Surf Rehab",
            "org_2y2Dl9fJlSWcKwREa0BTOJDvfQB": "danoz-personal"
        }
    
    def step1_identify_active_organizations(self) -> List[Dict[str, Any]]:
        """
        Step 1: Identify Active Organizations
        Tests multiple organization IDs to find which ones have active data
        """
        print("🔍 PHASE 1 - STEP 1: Identifying Active Organizations")
        print("=" * 60)
        
        active_organizations = []
        
        for org_id, org_name in self.organizations.items():
            print(f"Testing organization: {org_name} ({org_id})")
            
            org_data = {
                "organization_id": org_id,
                "organization_name": org_name,
                "status": "inactive",
                "total_contacts": 0,
                "active_patients": 0,
                "upcoming_appointments": 0,
                "last_sync_time": None
            }
            
            # Test Cliniko status endpoint (this is what works!)
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/cliniko/status/{org_id}",
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    org_data.update({
                        "status": "active",
                        "total_contacts": data.get("total_contacts", 0),
                        "active_patients": data.get("active_patients", 0), 
                        "upcoming_appointments": data.get("upcoming_appointments", 0),
                        "last_sync_time": data.get("last_sync_time")
                    })
                    print(f"  ✅ Contacts: {org_data['total_contacts']}")
                    print(f"  ✅ Active Patients: {org_data['active_patients']}")
                    print(f"  ✅ Upcoming Appointments: {org_data['upcoming_appointments']}")
                    print(f"  ✅ Last Sync: {org_data['last_sync_time']}")
                else:
                    print(f"  ❌ Status endpoint: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error getting status: {e}")
            
            active_organizations.append(org_data)
            print()  # Empty line for readability
        
        print(f"📊 STEP 1 RESULTS: Found {len(active_organizations)} organizations with data")
        return active_organizations
    
    def step2_check_sync_status(self, active_organizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step 2: Check Sync Status
        Verifies data freshness and sync health for active organizations
        """
        print("\n🔄 PHASE 1 - STEP 2: Checking Sync Status")
        print("=" * 60)
        
        sync_reports = []
        
        for org_data in active_organizations:
            org_id = org_data["organization_id"]
            print(f"Checking sync status for: {org_id}")
            
            sync_report = {
                "organization_id": org_id,
                "sync_status": "unknown",
                "last_sync_time": None,
                "last_sync_ago_minutes": None,
                "sync_health": "unknown",
                "total_synced_records": 0,
                "last_error": None,
                "sync_frequency": None,
                "recommendation": "unknown"
            }
            
            try:
                # Check sync status
                status_response = requests.get(
                    f"{self.base_url}/api/v1/cliniko/status/{org_id}",
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    # Extract sync information
                    last_sync = status_data.get("last_sync_time")
                    if last_sync:
                        try:
                            last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                            sync_report["last_sync_time"] = last_sync
                            
                            # Calculate time since last sync
                            now = datetime.now(last_sync_dt.tzinfo)
                            minutes_ago = (now - last_sync_dt).total_seconds() / 60
                            sync_report["last_sync_ago_minutes"] = round(minutes_ago, 1)
                            
                            # Determine sync health
                            if minutes_ago < 60:  # Less than 1 hour
                                sync_report["sync_health"] = "excellent"
                                sync_report["recommendation"] = "Data is fresh"
                            elif minutes_ago < 24 * 60:  # Less than 1 day
                                sync_report["sync_health"] = "good"
                                sync_report["recommendation"] = "Data is recent"
                            elif minutes_ago < 7 * 24 * 60:  # Less than 1 week
                                sync_report["sync_health"] = "stale"
                                sync_report["recommendation"] = "Consider triggering sync"
                            else:
                                sync_report["sync_health"] = "very_stale"
                                sync_report["recommendation"] = "Urgent: Trigger sync immediately"
                            
                            print(f"  ✅ Last synced: {minutes_ago:.1f} minutes ago ({sync_report['sync_health']})")
                            
                        except Exception as e:
                            print(f"  ⚠️  Could not parse sync time: {e}")
                    
                    # Extract other status info
                    sync_report["sync_status"] = status_data.get("status", "unknown")
                    sync_report["total_synced_records"] = status_data.get("total_records", 0)
                    sync_report["last_error"] = status_data.get("last_error")
                    
                elif status_response.status_code == 404:
                    print(f"  ❌ Sync status not available")
                    sync_report["sync_status"] = "not_configured"
                    sync_report["recommendation"] = "Set up Cliniko sync"
                else:
                    print(f"  ⚠️  Status check failed: HTTP {status_response.status_code}")
                    sync_report["sync_status"] = "error"
                    
            except Exception as e:
                print(f"  ❌ Error checking sync status: {e}")
                sync_report["sync_status"] = "error"
                sync_report["last_error"] = str(e)
            
            sync_reports.append(sync_report)
            print()
        
        print(f"📊 STEP 2 RESULTS: Analyzed sync status for {len(sync_reports)} organizations")
        return sync_reports
    
    def generate_phase1_report(self, active_organizations: List[Dict[str, Any]], 
                             sync_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive Phase 1 report"""
        
        # Combine organization and sync data
        combined_data = []
        for org in active_organizations:
            org_id = org["organization_id"]
            sync_data = next((s for s in sync_reports if s["organization_id"] == org_id), {})
            
            combined_record = {**org, **sync_data}
            combined_data.append(combined_record)
        
        # Generate summary statistics
        summary = {
            "total_organizations_tested": len(self.organizations),
            "active_organizations_found": len(active_organizations),
            "organizations_with_contacts": sum(1 for org in active_organizations if org["total_contacts"] > 0),
            "organizations_with_patients": sum(1 for org in active_organizations if org["active_patients"] > 0),
            "total_contacts_found": sum(org["total_contacts"] for org in active_organizations),
            "total_patients_found": sum(org["active_patients"] for org in active_organizations),
            "sync_health_distribution": {},
            "recommendations": []
        }
        
        # Analyze sync health
        sync_health_counts = {}
        for sync in sync_reports:
            health = sync.get("sync_health", "unknown")
            sync_health_counts[health] = sync_health_counts.get(health, 0) + 1
        
        summary["sync_health_distribution"] = sync_health_counts
        
        # Generate recommendations
        stale_orgs = [s for s in sync_reports if s.get("sync_health") in ["stale", "very_stale"]]
        if stale_orgs:
            summary["recommendations"].append(f"Trigger sync for {len(stale_orgs)} organizations with stale data")
        
        no_sync_orgs = [s for s in sync_reports if s.get("sync_status") == "not_configured"]
        if no_sync_orgs:
            summary["recommendations"].append(f"Configure Cliniko sync for {len(no_sync_orgs)} organizations")
        
        return {
            "summary": summary,
            "organizations": combined_data,
            "timestamp": datetime.now().isoformat()
        }
    
    def run_phase1_discovery(self) -> Dict[str, Any]:
        """Run complete Phase 1 discovery process"""
        print("🚀 STARTING CLINIKO ANALYTICS - PHASE 1")
        print("Data Discovery & Organization Setup")
        print("=" * 80)
        
        # Step 1: Identify active organizations
        active_organizations = self.step1_identify_active_organizations()
        
        if not active_organizations:
            print("❌ No active organizations found. Exiting Phase 1.")
            return {"error": "No active organizations found"}
        
        # Step 2: Check sync status
        sync_reports = self.step2_check_sync_status(active_organizations)
        
        # Generate comprehensive report
        report = self.generate_phase1_report(active_organizations, sync_reports)
        
        # Print summary
        print("\n📋 PHASE 1 SUMMARY REPORT")
        print("=" * 80)
        summary = report["summary"]
        print(f"Organizations tested: {summary['total_organizations_tested']}")
        print(f"Active organizations found: {summary['active_organizations_found']}")
        print(f"Total contacts discovered: {summary['total_contacts_found']}")
        print(f"Total patients discovered: {summary['total_patients_found']}")
        
        print(f"\nSync Health Distribution:")
        for health, count in summary["sync_health_distribution"].items():
            print(f"  {health}: {count} organizations")
        
        if summary["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"  • {rec}")
        
        print(f"\n✅ Phase 1 Complete! Ready for Phase 2 (Patient Data Collection)")
        
        return report


def main():
    """Main function for Phase 1 discovery"""
    parser = argparse.ArgumentParser(description="Cliniko Analytics - Phase 1: Organization Discovery")
    parser.add_argument("--server", default="https://routiq-backend-prod.up.railway.app", 
                       help="API server URL")
    parser.add_argument("--output", help="Output JSON file for results")
    
    args = parser.parse_args()
    
    # Run Phase 1 discovery
    discovery = ClinikoPhase1Discovery(args.server)
    report = discovery.run_phase1_discovery()
    
    # Save results if output file specified
    if args.output and "error" not in report:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main() 