#!/usr/bin/env python3
"""
Reengagement Analytics Report Generator
=====================================

This script calls the working reengagement API endpoints to generate
comprehensive analytics insights and reports.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import argparse
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalyticsConfig:
    """Configuration for analytics report generation"""
    base_url: str
    organization_id: str
    output_dir: str = "analytics/reports"
    timeout: int = 30

class ReengagementAnalytics:
    """Main analytics class for reengagement data"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.data = {}
        self.report = {
            "generated_at": datetime.now().isoformat(),
            "organization_id": config.organization_id,
            "summary": {},
            "insights": {},
            "recommendations": []
        }
    
    async def fetch_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        """Fetch data from a single endpoint"""
        url = f"{self.config.base_url}{endpoint}"
        try:
            async with session.get(url, timeout=self.config.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✓ Successfully fetched {endpoint}")
                    return data
                else:
                    logger.error(f"✗ Failed to fetch {endpoint}: {response.status}")
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"✗ Error fetching {endpoint}: {e}")
            return {"error": str(e)}
    
    async def collect_data(self):
        """Collect data from all working endpoints"""
        endpoints = [
            "/api/v1/reengagement/health",
            f"/api/v1/reengagement/{self.config.organization_id}/risk-metrics",
            f"/api/v1/reengagement/{self.config.organization_id}/prioritized",
            f"/api/v1/reengagement/{self.config.organization_id}/dashboard-summary",
            f"/api/v1/reengagement/{self.config.organization_id}/performance"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_endpoint(session, endpoint) for endpoint in endpoints]
            results = await asyncio.gather(*tasks)
            
            # Map results to endpoint names
            endpoint_names = [
                "health",
                "risk_metrics", 
                "prioritized",
                "dashboard_summary",
                "performance"
            ]
            
            for name, result in zip(endpoint_names, results):
                self.data[name] = result
        
        logger.info(f"Data collection complete. Collected {len(self.data)} endpoint responses.")
    
    def analyze_risk_distribution(self) -> Dict:
        """Analyze risk distribution from risk metrics"""
        risk_data = self.data.get("risk_metrics", {})
        
        if "summary" not in risk_data:
            return {"error": "No risk metrics data available"}
        
        summary = risk_data["summary"]
        risk_dist = summary.get("risk_distribution", {})
        engagement_dist = summary.get("engagement_distribution", {})
        
        total_patients = summary.get("total_patients", 0)
        
        analysis = {
            "total_patients": total_patients,
            "risk_breakdown": {
                "high_risk": {
                    "count": risk_dist.get("high", 0),
                    "percentage": round((risk_dist.get("high", 0) / total_patients * 100), 2) if total_patients > 0 else 0
                },
                "medium_risk": {
                    "count": risk_dist.get("medium", 0),
                    "percentage": round((risk_dist.get("medium", 0) / total_patients * 100), 2) if total_patients > 0 else 0
                },
                "low_risk": {
                    "count": risk_dist.get("low", 0),
                    "percentage": round((risk_dist.get("low", 0) / total_patients * 100), 2) if total_patients > 0 else 0
                }
            },
            "engagement_breakdown": {
                "active": {
                    "count": engagement_dist.get("active", 0),
                    "percentage": round((engagement_dist.get("active", 0) / total_patients * 100), 2) if total_patients > 0 else 0
                },
                "dormant": {
                    "count": engagement_dist.get("dormant", 0),
                    "percentage": round((engagement_dist.get("dormant", 0) / total_patients * 100), 2) if total_patients > 0 else 0
                },
                "stale": {
                    "count": engagement_dist.get("stale", 0),
                    "percentage": round((engagement_dist.get("stale", 0) / total_patients * 100), 2) if total_patients > 0 else 0
                }
            }
        }
        
        return analysis
    
    def generate_insights(self):
        """Generate insights from collected data"""
        insights = {}
        
        # Risk Distribution Insights
        risk_analysis = self.analyze_risk_distribution()
        if "error" not in risk_analysis:
            insights["risk_insights"] = {
                "high_risk_percentage": risk_analysis["risk_breakdown"]["high_risk"]["percentage"],
                "dormant_percentage": risk_analysis["engagement_breakdown"]["dormant"]["percentage"],
                "total_at_risk": risk_analysis["engagement_breakdown"]["dormant"]["count"] + risk_analysis["engagement_breakdown"]["stale"]["count"]
            }
        
        self.report["insights"] = insights
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        risk_analysis = self.analyze_risk_distribution()
        if "error" not in risk_analysis:
            high_risk_pct = risk_analysis["risk_breakdown"]["high_risk"]["percentage"]
            dormant_pct = risk_analysis["engagement_breakdown"]["dormant"]["percentage"]
            
            if high_risk_pct > 20:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Risk Management",
                    "recommendation": f"Immediate attention needed: {high_risk_pct}% of patients are high-risk",
                    "action": "Implement targeted reengagement campaigns for high-risk patients"
                })
            
            if dormant_pct > 15:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Engagement",
                    "recommendation": f"High dormancy rate: {dormant_pct}% of patients are dormant",
                    "action": "Develop win-back campaigns for dormant patients"
                })
        
        self.report["recommendations"] = recommendations
    
    def create_summary_report(self):
        """Create executive summary"""
        summary = {
            "api_health": "healthy" if self.data.get("health", {}).get("status") == "healthy" else "unhealthy",
            "data_freshness": self.data.get("risk_metrics", {}).get("timestamp", "unknown"),
            "total_patients_analyzed": self.data.get("risk_metrics", {}).get("summary", {}).get("total_patients", 0),
            "endpoints_tested": len([k for k, v in self.data.items() if "error" not in v]),
            "critical_actions_needed": len([r for r in self.report.get("recommendations", []) if r.get("priority") == "URGENT"]),
            "key_metrics": {
                "high_risk_patients": self.data.get("risk_metrics", {}).get("summary", {}).get("risk_distribution", {}).get("high", 0),
                "dormant_patients": self.data.get("risk_metrics", {}).get("summary", {}).get("engagement_distribution", {}).get("dormant", 0),
                "urgent_priority_patients": self.data.get("risk_metrics", {}).get("summary", {}).get("action_priorities", {}).get("urgent", 0)
            }
        }
        
        self.report["summary"] = summary
    
    def save_report(self):
        """Save the analytics report"""
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detailed_filename = f"{self.config.output_dir}/reengagement_analytics_{timestamp}.json"
        
        with open(detailed_filename, 'w') as f:
            json.dump({
                "report": self.report,
                "raw_data": self.data,
                "analysis": {
                    "risk_distribution": self.analyze_risk_distribution()
                }
            }, f, indent=2)
        
        logger.info(f"Report saved: {detailed_filename}")
        return detailed_filename
    
    def print_summary(self):
        """Print executive summary to console"""
        print("\n" + "="*80)
        print("REENGAGEMENT ANALYTICS REPORT - EXECUTIVE SUMMARY")
        print("="*80)
        
        summary = self.report.get("summary", {})
        
        print(f"📊 Organization ID: {self.config.organization_id}")
        print(f"🕐 Generated: {self.report['generated_at']}")
        print(f"🏥 API Health: {summary.get('api_health', 'unknown')}")
        print(f"👥 Total Patients: {summary.get('total_patients_analyzed', 0)}")
        print(f"🔗 Endpoints Tested: {summary.get('endpoints_tested', 0)}")
        
        print("\n📈 KEY METRICS:")
        key_metrics = summary.get("key_metrics", {})
        print(f"  🔴 High Risk Patients: {key_metrics.get('high_risk_patients', 0)}")
        print(f"  😴 Dormant Patients: {key_metrics.get('dormant_patients', 0)}")
        print(f"  🚨 Urgent Priority Patients: {key_metrics.get('urgent_priority_patients', 0)}")
        
        print("\n🎯 RECOMMENDATIONS:")
        recommendations = self.report.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                priority_emoji = "🚨" if rec.get("priority") == "URGENT" else "⚠️" if rec.get("priority") == "HIGH" else "📝"
                print(f"  {priority_emoji} {rec.get('recommendation', 'No recommendation')}")
        else:
            print("  ✅ No critical recommendations at this time")
        
        print("\n" + "="*80)
    
    async def run_analysis(self):
        """Run the complete analytics pipeline"""
        logger.info("Starting reengagement analytics report generation...")
        
        # Step 1: Collect data
        await self.collect_data()
        
        # Step 2: Generate insights
        self.generate_insights()
        
        # Step 3: Generate recommendations
        self.generate_recommendations()
        
        # Step 4: Create summary
        self.create_summary_report()
        
        # Step 5: Save and display results
        detailed_file = self.save_report()
        self.print_summary()
        
        logger.info("Analytics report generation complete!")
        return detailed_file

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate reengagement analytics report")
    parser.add_argument("--organization-id", required=True, help="Organization ID to analyze")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--output-dir", default="analytics/reports", help="Output directory for reports")
    
    args = parser.parse_args()
    
    config = AnalyticsConfig(
        base_url=args.base_url,
        organization_id=args.organization_id,
        output_dir=args.output_dir
    )
    
    analytics = ReengagementAnalytics(config)
    await analytics.run_analysis()

if __name__ == "__main__":
    asyncio.run(main()) 