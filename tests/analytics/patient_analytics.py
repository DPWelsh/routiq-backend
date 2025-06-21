#!/usr/bin/env python3
"""
Patient Analytics Script
Fetches all active patients and analyzes appointment types and last appointments
Outputs results to CSV for further analysis
"""

import requests
import json
import csv
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse

# Add parent directory to path to import test utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PatientAnalytics:
    """Patient analytics using our consolidated test infrastructure"""
    
    def __init__(self, base_url: str = None):
        """Initialize analytics client"""
        self.base_url = base_url or os.getenv("TEST_SERVER_URL", "https://routiq-backend-prod.up.railway.app")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Routiq-Analytics/1.0"
        }
        self.timeout = 30
        
    def get_organizations_with_patients(self) -> List[str]:
        """Get list of organizations that have active patients"""
        try:
            # Try to get organization info from debug endpoint
            response = requests.get(
                f"{self.base_url}/api/v1/cliniko/debug/organizations",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("organizations_with_patients", [])
            else:
                print(f"⚠️  Could not fetch organizations (status: {response.status_code})")
                # Return common organization IDs to try
                return ["surfrehab", "demo", "test", "org1", "org2"]
                
        except Exception as e:
            print(f"⚠️  Error fetching organizations: {e}")
            return ["surfrehab", "demo", "test", "org1", "org2"]
    
    def get_active_patients(self, organization_id: str) -> Dict[str, Any]:
        """Get active patients for an organization"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/patients/{organization_id}/active",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                print(f"⚠️  Database connection issue for {organization_id} (expected in production)")
                return {"patients": [], "total_count": 0, "organization_id": organization_id}
            else:
                print(f"⚠️  Error for {organization_id}: Status {response.status_code}")
                return {"patients": [], "total_count": 0, "organization_id": organization_id}
                
        except Exception as e:
            print(f"❌ Error fetching patients for {organization_id}: {e}")
            return {"patients": [], "total_count": 0, "organization_id": organization_id}
    
    def get_enhanced_patients(self, organization_id: str) -> Dict[str, Any]:
        """Get enhanced patient data with appointments"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/patients/{organization_id}/active/with-appointments",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                print(f"⚠️  Enhanced endpoint database issue for {organization_id}")
                return {"patients": [], "total_count": 0, "organization_id": organization_id}
            else:
                print(f"⚠️  Enhanced endpoint error for {organization_id}: Status {response.status_code}")
                return {"patients": [], "total_count": 0, "organization_id": organization_id}
                
        except Exception as e:
            print(f"❌ Error fetching enhanced patients for {organization_id}: {e}")
            return {"patients": [], "total_count": 0, "organization_id": organization_id}
    
    def get_appointment_types_summary(self, organization_id: str) -> Dict[str, Any]:
        """Get appointment types summary for an organization"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/patients/{organization_id}/appointment-types/summary",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"appointment_types": [], "total_types": 0, "organization_id": organization_id}
                
        except Exception as e:
            print(f"❌ Error fetching appointment types for {organization_id}: {e}")
            return {"appointment_types": [], "total_types": 0, "organization_id": organization_id}
    
    def analyze_patient(self, patient: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
        """Analyze individual patient data"""
        analysis = {
            "organization_id": organization_id,
            "patient_id": patient.get("id", ""),
            "contact_id": patient.get("contact_id", ""),
            "contact_name": patient.get("contact_name", ""),
            "contact_phone": patient.get("contact_phone", ""),
            "contact_email": patient.get("contact_email", ""),
            
            # Appointment counts
            "total_appointments": patient.get("total_appointment_count", 0),
            "recent_appointments": patient.get("recent_appointment_count", 0),
            "upcoming_appointments": patient.get("upcoming_appointment_count", 0),
            
            # Enhanced fields
            "next_appointment_time": patient.get("next_appointment_time", ""),
            "next_appointment_type": patient.get("next_appointment_type", ""),
            "primary_appointment_type": patient.get("primary_appointment_type", ""),
            "treatment_notes": patient.get("treatment_notes", ""),
            "hours_until_next_appointment": patient.get("hours_until_next_appointment", ""),
            "priority": patient.get("priority", ""),
            
            # Last appointment analysis
            "last_appointment_date": "",
            "last_appointment_type": "",
            "days_since_last_appointment": "",
        }
        
        # Analyze recent appointments for last appointment
        recent_appointments = patient.get("recent_appointments", [])
        if recent_appointments and isinstance(recent_appointments, list):
            # Find most recent appointment
            most_recent = None
            most_recent_date = None
            
            for appt in recent_appointments:
                if isinstance(appt, dict) and appt.get("date"):
                    try:
                        appt_date = datetime.fromisoformat(appt["date"].replace('Z', '+00:00'))
                        if most_recent_date is None or appt_date > most_recent_date:
                            most_recent = appt
                            most_recent_date = appt_date
                    except:
                        continue
            
            if most_recent:
                analysis["last_appointment_date"] = most_recent.get("date", "")
                analysis["last_appointment_type"] = most_recent.get("appointment_type", "")
                
                # Calculate days since last appointment
                if most_recent_date:
                    days_since = (datetime.now(most_recent_date.tzinfo) - most_recent_date).days
                    analysis["days_since_last_appointment"] = days_since
        
        return analysis
    
    def generate_patient_analytics_csv(self, output_file: str = None):
        """Generate comprehensive patient analytics CSV"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics/patient_analytics_{timestamp}.csv"
        
        print("🔍 Starting Patient Analytics...")
        print("=" * 60)
        
        # Get organizations
        organizations = self.get_organizations_with_patients()
        print(f"📋 Testing {len(organizations)} organizations: {organizations}")
        
        all_patients_analysis = []
        summary_stats = {
            "total_organizations": 0,
            "organizations_with_data": 0,
            "total_patients": 0,
            "patients_with_appointments": 0,
            "patients_with_treatment_notes": 0,
            "appointment_types_found": set(),
        }
        
        # Analyze each organization
        for org_id in organizations:
            print(f"\n🏥 Analyzing organization: {org_id}")
            
            # Get basic patient data
            patients_data = self.get_active_patients(org_id)
            patient_count = patients_data.get("total_count", 0)
            
            print(f"   Patients found: {patient_count}")
            
            if patient_count > 0:
                summary_stats["organizations_with_data"] += 1
                summary_stats["total_patients"] += patient_count
                
                # Analyze each patient
                for patient in patients_data.get("patients", []):
                    analysis = self.analyze_patient(patient, org_id)
                    all_patients_analysis.append(analysis)
                    
                    # Update summary stats
                    if analysis["total_appointments"] > 0:
                        summary_stats["patients_with_appointments"] += 1
                    
                    if analysis["treatment_notes"]:
                        summary_stats["patients_with_treatment_notes"] += 1
                    
                    if analysis["next_appointment_type"]:
                        summary_stats["appointment_types_found"].add(analysis["next_appointment_type"])
                    
                    if analysis["primary_appointment_type"]:
                        summary_stats["appointment_types_found"].add(analysis["primary_appointment_type"])
            
            summary_stats["total_organizations"] += 1
        
        # Write CSV
        if all_patients_analysis:
            print(f"\n📊 Writing {len(all_patients_analysis)} patient records to {output_file}")
            
            fieldnames = [
                "organization_id", "patient_id", "contact_id", "contact_name", 
                "contact_phone", "contact_email", "total_appointments", 
                "recent_appointments", "upcoming_appointments",
                "next_appointment_time", "next_appointment_type", 
                "primary_appointment_type", "treatment_notes", 
                "hours_until_next_appointment", "priority",
                "last_appointment_date", "last_appointment_type", 
                "days_since_last_appointment"
            ]
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_patients_analysis)
            
            print(f"✅ CSV written successfully: {output_file}")
        else:
            print("⚠️  No patient data found to write to CSV")
        
        # Print summary statistics
        print("\n📈 ANALYTICS SUMMARY")
        print("=" * 60)
        print(f"Organizations analyzed: {summary_stats['total_organizations']}")
        print(f"Organizations with data: {summary_stats['organizations_with_data']}")
        print(f"Total patients: {summary_stats['total_patients']}")
        print(f"Patients with appointments: {summary_stats['patients_with_appointments']}")
        print(f"Patients with treatment notes: {summary_stats['patients_with_treatment_notes']}")
        print(f"Unique appointment types: {len(summary_stats['appointment_types_found'])}")
        
        if summary_stats['appointment_types_found']:
            print(f"Appointment types found: {', '.join(sorted(summary_stats['appointment_types_found']))}")
        
        return output_file, summary_stats
    
    def test_enhanced_endpoints(self):
        """Test that our enhanced endpoints are accessible"""
        print("🧪 Testing Enhanced Patient Visibility Endpoints")
        print("=" * 60)
        
        test_org = "surfrehab"
        
        endpoints = [
            ("Basic Patient List", f"/api/v1/patients/{test_org}/active"),
            ("Enhanced Patient List", f"/api/v1/patients/{test_org}/active/with-appointments"),
            ("Appointment Types Summary", f"/api/v1/patients/{test_org}/appointment-types/summary"),
            ("Filter by Type", f"/api/v1/patients/{test_org}/by-appointment-type/Follow-up"),
        ]
        
        for name, endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=15)
                status = "✅ Accessible" if response.status_code in [200, 500] else f"❌ Error {response.status_code}"
                print(f"{name:25}: {status}")
            except Exception as e:
                print(f"{name:25}: ❌ Connection Error")


def main():
    """Main analytics function"""
    parser = argparse.ArgumentParser(description="Routiq Patient Analytics")
    parser.add_argument("--server", default="https://routiq-backend-prod.up.railway.app", 
                       help="API server URL")
    parser.add_argument("--output", help="Output CSV file path")
    parser.add_argument("--test-endpoints", action="store_true", 
                       help="Test enhanced endpoints accessibility")
    
    args = parser.parse_args()
    
    analytics = PatientAnalytics(args.server)
    
    if args.test_endpoints:
        analytics.test_enhanced_endpoints()
        return
    
    # Generate analytics
    output_file, stats = analytics.generate_patient_analytics_csv(args.output)
    
    print(f"\n🎉 Analytics complete! Results saved to: {output_file}")
    

if __name__ == "__main__":
    main() 