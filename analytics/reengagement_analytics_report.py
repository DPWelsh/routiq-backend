#!/usr/bin/env python3
"""
Reengagement Analytics Report Generator
=====================================

This script calls the working reengagement API endpoints to generate
comprehensive analytics insights and reports.

Working Endpoints:
- GET /api/v1/reengagement/health
- GET /api/v1/reengagement/{organization_id}/risk-metrics
- GET /api/v1/reengagement/{organization_id}/prioritized
- GET /api/v1/reengagement/{organization_id}/dashboard-summary
- GET /api/v1/reengagement/{organization_id}/patient/{patient_id}/details
- GET /api/v1/reengagement/{organization_id}/performance

Usage:
    python reengagement_analytics_report.py --organization-id <org_id> --base-url <url>
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import pandas as pd
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
    
    async def fetch_patient_details(self, session: aiohttp.ClientSession, patient_ids: List[str]) -> Dict:
        """Fetch detailed information for high-priority patients"""
        patient_details = {}
        
        # Limit to top 10 patients to avoid overwhelming the API
        top_patients = patient_ids[:10]
        
        for patient_id in top_patients:
            endpoint = f"/api/v1/reengagement/{self.config.organization_id}/patient/{patient_id}/details"
            result = await self.fetch_endpoint(session, endpoint)
            if "error" not in result:
                patient_details[patient_id] = result
        
        return patient_details
    
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
    
    def analyze_prioritized_patients(self) -> Dict:
        """Analyze prioritized patient data"""
        prioritized_data = self.data.get("prioritized", {})
        
        if "patients" not in prioritized_data:
            return {"error": "No prioritized patient data available"}
        
        patients = prioritized_data["patients"]
        
        # Analyze by priority levels
        priority_analysis = {}
        for priority in [1, 2, 3, 4, 5]:
            priority_patients = [p for p in patients if p.get("action_priority") == priority]
            priority_analysis[f"priority_{priority}"] = {
                "count": len(priority_patients),
                "avg_lifetime_value": round(sum(p.get("lifetime_value_aud", 0) for p in priority_patients) / len(priority_patients), 2) if priority_patients else 0,
                "avg_days_since_contact": round(sum(p.get("days_since_last_contact", 0) for p in priority_patients if p.get("days_since_last_contact")) / len([p for p in priority_patients if p.get("days_since_last_contact")]), 1) if [p for p in priority_patients if p.get("days_since_last_contact")] else 0
            }
        
        # Top value patients
        top_value_patients = sorted(patients, key=lambda x: x.get("lifetime_value_aud", 0), reverse=True)[:5]
        
        return {
            "total_prioritized": len(patients),
            "priority_breakdown": priority_analysis,
            "top_value_patients": [
                {
                    "patient_id": p.get("patient_id"),
                    "patient_name": p.get("patient_name"),
                    "lifetime_value_aud": p.get("lifetime_value_aud", 0),
                    "risk_level": p.get("risk_level"),
                    "action_priority": p.get("action_priority")
                }
                for p in top_value_patients
            ]
        }
    
    def analyze_performance_metrics(self) -> Dict:
        """Analyze performance metrics"""
        performance_data = self.data.get("performance", {})
        
        if "performance_metrics" not in performance_data:
            return {"error": "No performance metrics data available"}
        
        metrics = performance_data["performance_metrics"]
        
        # Extract key metrics
        engagement_health = metrics.get("engagement_health", {})
        risk_assessment = metrics.get("risk_assessment", {})
        contact_metrics = metrics.get("contact_metrics", {})
        financial_metrics = metrics.get("financial_metrics", {})
        
        return {
            "engagement_performance": {
                "total_patients": metrics.get("total_patients", 0),
                "engagement_rate": engagement_health.get("engagement_rate_percent", 0),
                "active_patients": engagement_health.get("currently_active", 0),
                "at_risk_patients": engagement_health.get("currently_dormant", 0) + engagement_health.get("currently_stale", 0)
            },
            "risk_performance": {
                "high_risk_count": risk_assessment.get("high_risk", 0),
                "critical_risk_count": risk_assessment.get("critical_risk", 0),
                "urgent_actions_needed": risk_assessment.get("urgent_actions_needed", 0),
                "total_high_priority": risk_assessment.get("total_high_priority", 0)
            },
            "contact_performance": {
                "avg_contact_success_score": contact_metrics.get("avg_contact_success_score", 0),
                "avg_days_since_contact": contact_metrics.get("avg_days_since_contact", 0),
                "contact_rate_percent": contact_metrics.get("contact_rate_percent", 0)
            },
            "financial_performance": {
                "total_lifetime_value_aud": financial_metrics.get("total_lifetime_value_aud", 0),
                "avg_lifetime_value_aud": financial_metrics.get("avg_lifetime_value_aud", 0)
            }
        }
    
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
        
        # Priority Insights
        priority_analysis = self.analyze_prioritized_patients()
        if "error" not in priority_analysis:
            insights["priority_insights"] = {
                "urgent_priority_count": priority_analysis["priority_breakdown"]["priority_1"]["count"],
                "high_value_at_risk": len([p for p in priority_analysis["top_value_patients"] if p["action_priority"] <= 2]),
                "avg_value_urgent": priority_analysis["priority_breakdown"]["priority_1"]["avg_lifetime_value"]
            }
        
        # Performance Insights
        performance_analysis = self.analyze_performance_metrics()
        if "error" not in performance_analysis:
            insights["performance_insights"] = {
                "engagement_rate": performance_analysis["engagement_performance"]["engagement_rate"],
                "contact_success_rate": performance_analysis["contact_performance"]["contact_rate_percent"],
                "financial_at_risk": performance_analysis["financial_performance"]["total_lifetime_value_aud"] * 0.3  # Estimate 30% of dormant/stale value at risk
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
        
        # Priority-based recommendations
        priority_analysis = self.analyze_prioritized_patients()
        if "error" not in priority_analysis:
            urgent_count = priority_analysis["priority_breakdown"]["priority_1"]["count"]
            
            if urgent_count > 0:
                recommendations.append({
                    "priority": "URGENT",
                    "category": "Action Required",
                    "recommendation": f"{urgent_count} patients require immediate attention",
                    "action": "Contact priority 1 patients within 24 hours"
                })
        
        # Performance-based recommendations
        performance_analysis = self.analyze_performance_metrics()
        if "error" not in performance_analysis:
            engagement_rate = performance_analysis["engagement_performance"]["engagement_rate"]
            contact_rate = performance_analysis["contact_performance"]["contact_rate_percent"]
            
            if engagement_rate < 50:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Engagement Strategy",
                    "recommendation": f"Low engagement rate: {engagement_rate}%",
                    "action": "Review and optimize engagement strategies"
                })
            
            if contact_rate < 30:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Contact Strategy",
                    "recommendation": f"Low contact success rate: {contact_rate}%",
                    "action": "Analyze contact methods and timing for optimization"
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
                    "risk_distribution": self.analyze_risk_distribution(),
                    "prioritized_patients": self.analyze_prioritized_patients(),
                    "performance_metrics": self.analyze_performance_metrics()
                }
            }, f, indent=2)
        
        # Save executive summary
        summary_filename = f"{self.config.output_dir}/executive_summary_{timestamp}.json"
        with open(summary_filename, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        logger.info(f"Reports saved:")
        logger.info(f"  - Detailed: {detailed_filename}")
        logger.info(f"  - Summary: {summary_filename}")
        
        return detailed_filename, summary_filename
    
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
        detailed_file, summary_file = self.save_report()
        self.print_summary()
        
        logger.info("Analytics report generation complete!")
        return detailed_file, summary_file

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