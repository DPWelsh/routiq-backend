#!/usr/bin/env python3
"""
Sample Analytics Runner with Mock Data
=====================================

This script demonstrates the analytics module using mock data 
when the API is not available for testing.
"""

import asyncio
import json
import os
from datetime import datetime
from reengagement_analytics import ReengagementAnalytics, AnalyticsConfig

# Mock data for testing when API is not available
MOCK_DATA = {
    "health": {
        "status": "healthy",
        "service": "reengagement_api",
        "timestamp": datetime.now().isoformat()
    },
    "risk_metrics": {
        "organization_id": "test-org-123",
        "summary": {
            "total_patients": 1250,
            "risk_distribution": {
                "high": 85,
                "medium": 425,
                "low": 740
            },
            "engagement_distribution": {
                "active": 680,
                "dormant": 320,
                "stale": 250
            },
            "action_priorities": {
                "urgent": 25,
                "important": 95,
                "medium": 310,
                "low": 820
            }
        },
        "timestamp": datetime.now().isoformat()
    },
    "prioritized": {
        "organization_id": "test-org-123",
        "patients": [
            {
                "patient_id": "p1",
                "patient_name": "John Doe",
                "email": "john@example.com",
                "risk_level": "high",
                "action_priority": 1,
                "lifetime_value_aud": 2500,
                "days_since_last_contact": 45
            },
            {
                "patient_id": "p2", 
                "patient_name": "Jane Smith",
                "email": "jane@example.com",
                "risk_level": "medium",
                "action_priority": 2,
                "lifetime_value_aud": 1800,
                "days_since_last_contact": 32
            }
        ],
        "result_count": 2
    },
    "dashboard_summary": {
        "organization_id": "test-org-123",
        "summary_metrics": {
            "total_patients": 1250,
            "engagement_breakdown": {
                "active": 680,
                "dormant": 320,
                "stale": 250
            },
            "financial_metrics": {
                "total_lifetime_value_aud": 1875000,
                "avg_lifetime_value_aud": 1500
            }
        }
    },
    "performance": {
        "organization_id": "test-org-123",
        "performance_metrics": {
            "total_patients": 1250,
            "engagement_health": {
                "currently_active": 680,
                "currently_dormant": 320,
                "currently_stale": 250,
                "engagement_rate_percent": 54.4
            },
            "contact_performance": {
                "avg_contact_success_score": 3.2,
                "avg_days_since_contact": 28.5,
                "contact_rate_percent": 42.3
            }
        }
    }
}

class MockAnalytics(ReengagementAnalytics):
    """Analytics class with mock data for testing"""
    
    async def collect_data(self):
        """Override to use mock data instead of API calls"""
        print("📊 Using mock data for testing...")
        self.data = MOCK_DATA.copy()
        
        # Add some variation to make it more realistic
        for key, value in self.data.items():
            if isinstance(value, dict) and "timestamp" not in value:
                value["timestamp"] = datetime.now().isoformat()
        
        print(f"✅ Mock data loaded. Available endpoints: {list(self.data.keys())}")

async def run_sample_analysis():
    """Run sample analysis with mock data"""
    
    print("🧪 Running Sample Reengagement Analytics")
    print("=" * 60)
    print("This demo uses mock data to show how the analytics work")
    print("when the API is not available for testing.")
    print()
    
    # Create configuration
    config = AnalyticsConfig(
        base_url="http://mock-api",
        organization_id="test-org-123",
        output_dir="analytics/sample_reports"
    )
    
    # Create mock analytics instance
    analytics = MockAnalytics(config)
    
    # Run analysis
    try:
        report_file = await analytics.run_analysis()
        
        print(f"\n🎉 Sample analysis completed!")
        print(f"📄 Report saved to: {report_file}")
        
        # Show some additional insights
        print("\n📈 Additional Insights:")
        
        # Calculate some extra metrics
        total_patients = analytics.data["risk_metrics"]["summary"]["total_patients"]
        high_risk = analytics.data["risk_metrics"]["summary"]["risk_distribution"]["high"]
        dormant = analytics.data["risk_metrics"]["summary"]["engagement_distribution"]["dormant"]
        
        print(f"  🔍 Patient Risk Analysis:")
        print(f"    • Total Patients: {total_patients:,}")
        print(f"    • High Risk: {high_risk} ({high_risk/total_patients*100:.1f}%)")
        print(f"    • Dormant: {dormant} ({dormant/total_patients*100:.1f}%)")
        
        # Financial insights
        total_value = analytics.data["dashboard_summary"]["summary_metrics"]["financial_metrics"]["total_lifetime_value_aud"]
        avg_value = analytics.data["dashboard_summary"]["summary_metrics"]["financial_metrics"]["avg_lifetime_value_aud"]
        
        print(f"  💰 Financial Analysis:")
        print(f"    • Total Lifetime Value: ${total_value:,.2f} AUD")
        print(f"    • Average Patient Value: ${avg_value:,.2f} AUD")
        print(f"    • At-Risk Value: ${(dormant * avg_value):,.2f} AUD")
        
        # Show report content preview
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                
            print(f"\n📋 Report Preview:")
            print(f"  • Report Type: {type(report_data).__name__}")
            print(f"  • Sections: {list(report_data.keys())}")
            print(f"  • Insights Generated: {len(report_data.get('report', {}).get('insights', {}))}")
            print(f"  • Recommendations: {len(report_data.get('report', {}).get('recommendations', []))}")
    
    except Exception as e:
        print(f"❌ Sample analysis failed: {e}")
        import traceback
        traceback.print_exc()

def compare_with_real_api():
    """Instructions for comparing with real API data"""
    print("\n🔄 To Compare with Real API Data:")
    print("=" * 50)
    print("1. Start your API server:")
    print("   python src/main.py")
    print()
    print("2. Test endpoints:")
    print("   python analytics/test_endpoints.py --organization-id your-real-org-id")
    print()
    print("3. Run real analytics:")
    print("   python analytics/reengagement_analytics.py --organization-id your-real-org-id")
    print()
    print("4. Compare results with this mock data analysis")

if __name__ == "__main__":
    asyncio.run(run_sample_analysis())
    compare_with_real_api() 