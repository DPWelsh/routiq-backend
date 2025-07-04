#!/usr/bin/env python3
"""
Demo script showing how to use the reengagement analytics module
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from analytics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.reengagement_analytics import ReengagementAnalytics, AnalyticsConfig

async def demo_analytics():
    """Demo function showing basic usage"""
    
    print("🚀 Reengagement Analytics Demo")
    print("=" * 50)
    
    # Example configuration - replace with your actual values
    demo_config = AnalyticsConfig(
        base_url="http://localhost:8000",
        organization_id="your-org-id-here",  # Replace with actual org ID
        output_dir="analytics/demo_reports"
    )
    
    print(f"📊 Configuration:")
    print(f"  Base URL: {demo_config.base_url}")
    print(f"  Organization ID: {demo_config.organization_id}")
    print(f"  Output Directory: {demo_config.output_dir}")
    print()
    
    # Create analytics instance
    analytics = ReengagementAnalytics(demo_config)
    
    # Run the analysis
    try:
        report_file = await analytics.run_analysis()
        print(f"\n✅ Demo completed successfully!")
        print(f"📄 Report saved to: {report_file}")
        
        # Show some example data access
        print("\n🔍 Example Data Access:")
        print("Raw data keys:", list(analytics.data.keys()))
        if analytics.data.get("health"):
            print("API Health:", analytics.data["health"].get("status"))
        
        if analytics.data.get("risk_metrics"):
            total_patients = analytics.data["risk_metrics"].get("summary", {}).get("total_patients", 0)
            print(f"Total Patients: {total_patients}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nThis is expected if:")
        print("  - The API server is not running")
        print("  - The organization ID doesn't exist")
        print("  - The endpoints are not accessible")
        print("\nTo fix this:")
        print("  1. Start your API server")
        print("  2. Replace 'your-org-id-here' with a valid organization ID")
        print("  3. Ensure the reengagement endpoints are working")

if __name__ == "__main__":
    asyncio.run(demo_analytics()) 