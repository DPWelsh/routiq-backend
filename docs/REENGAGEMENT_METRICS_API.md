# 🎯 Reengagement Platform API Requirements
## Strategic Backend Endpoints for Patient Retention & Recovery

**From: Frontend Product Team**  
**To: Backend Development Team**  
**Priority: HIGH - Critical for platform success**

---

## 📊 **Executive Summary**

Our current patient stats are **generic and not actionable** for a reengagement platform. We need **risk-based, action-oriented metrics** that help staff prioritize patient outreach and measure reengagement success.

### **Current Problem:**
- "36 active patients" → Meaningless for reengagement
- "100% activity rate" → False metric
- No risk stratification or prioritization

### **Solution:**
Transform into **actionable reengagement dashboard** with risk alerts and performance tracking.

---

## 🚨 **Priority 1: Risk & Alert Metrics**

### **Endpoint 1: Patient Risk Assessment**
```http
GET /api/v1/reengagement/{org_id}/risk-metrics
```

**Required Response:**
```json
{
  "organization_id": "org_xxx",
  "risk_summary": {
    "critical_risk": 12,        // 45+ days no contact
    "high_risk": 8,             // 30-44 days no contact  
    "medium_risk": 15,          // 14-29 days no contact
    "low_risk": 23,             // 7-13 days no contact
    "engaged": 45               // Recent contact
  },
  "alerts": {
    "missed_appointments_14d": 7,
    "failed_communications": 3,
    "overdue_followups": 12,
    "no_future_appointments": 18
  },
  "immediate_actions_required": 15,
  "last_updated": "2025-06-30T08:00:00Z"
}
```

---

## 📈 **Priority 2: Performance Metrics**

### **Endpoint 2: Reengagement Performance**
```http
GET /api/v1/reengagement/{org_id}/performance
```

**Required Response:**
```json
{
  "timeframe": "last_30_days",
  "reengagement_metrics": {
    "outreach_attempts": 145,
    "successful_contacts": 89,
    "contact_success_rate": 61.4,
    "appointments_scheduled": 67,
    "conversion_rate": 75.3,
    "avg_days_to_reengage": 8.5
  },
  "communication_channels": {
    "sms": {
      "sent": 95,
      "delivered": 87,
      "responded": 52,
      "response_rate": 59.8
    },
    "email": {
      "sent": 78,
      "opened": 45,
      "responded": 23,
      "response_rate": 51.1
    },
    "phone": {
      "attempted": 34,
      "connected": 28,
      "appointment_booked": 21,
      "conversion_rate": 75.0
    }
  },
  "benchmark_comparison": {
    "industry_avg_contact_rate": 55.0,
    "industry_avg_conversion": 68.0,
    "our_performance": "above_average"
  }
}
```

---

## 📋 **Priority 3: Actionable Patient List**

### **Endpoint 3: Risk-Prioritized Patient List**
```http
GET /api/v1/reengagement/{org_id}/patients/prioritized
```

**Query Parameters:**
- `risk_level`: critical|high|medium|low|all
- `action_required`: missed_appt|overdue_followup|failed_contact|no_future_appt
- `limit`: number of records
- `sort_by`: risk_score|days_since_contact|next_action_date

**Required Response:**
```json
{
  "patients": [
    {
      "id": "patient_123",
      "name": "John Smith",
      "phone": "+1234567890",
      "email": "john.smith@email.com",
      "risk_level": "critical",
      "risk_score": 85,
      "days_since_last_contact": 47,
      "last_appointment_date": "2025-05-14",
      "next_scheduled_appointment": null,
      "recommended_action": "immediate_phone_call",
      "action_priority": 1,
      "communication_preferences": ["sms", "phone"],
      "best_contact_time": "morning",
      "previous_response_rate": 78.5,
      "total_lifetime_appointments": 12,
      "missed_appointments_last_90d": 2,
      "reengagement_history": [
        {
          "date": "2025-06-15",
          "method": "sms", 
          "success": false,
          "reason": "no_response"
        }
      ],
      "health_conditions": ["chronic_pain", "physiotherapy"],
      "referral_source": "gp_referral",
      "last_treatment_outcome": "improved"
    }
  ],
  "summary": {
    "total_at_risk": 35,
    "immediate_action_required": 12,
    "avg_days_since_contact": 23.4,
    "success_rate_prediction": 67.2
  }
}
```

---

## 📊 **Priority 4: Trending & Analytics**

### **Endpoint 4: Reengagement Trends**
```http
GET /api/v1/reengagement/{org_id}/trends
```

**Query Parameters:**
- `period`: 7d|30d|90d|6m|1y
- `metrics`: risk_levels|success_rates|channel_performance

**Required Response:**
```json
{
  "period": "30d",
  "daily_trends": [
    {
      "date": "2025-06-01",
      "new_at_risk": 3,
      "reengaged_successfully": 7,
      "outreach_attempts": 15,
      "appointments_scheduled": 5
    }
  ],
  "channel_performance_trends": {
    "sms": { "success_rate_trend": "improving", "change_pct": 12.3 },
    "email": { "success_rate_trend": "stable", "change_pct": -2.1 },
    "phone": { "success_rate_trend": "declining", "change_pct": -8.7 }
  },
  "risk_distribution_changes": {
    "critical_trend": "decreasing",
    "high_trend": "stable", 
    "overall_improvement": true
  }
}
```

---

## 🎯 **Frontend Dashboard Design**

### **Proposed New Stats Cards:**
1. **🚨 Immediate Action Required** (12 patients)
2. **📞 This Week's Target** (25 patients to contact)  
3. **✅ Reengagement Success Rate** (67.2%)
4. **📈 Trend** (↗️ 8% improvement vs last month)

### **Risk-Based Patient List:**
- **Critical (Red)**: 45+ days, immediate phone call required
- **High (Orange)**: 30-44 days, SMS + follow-up needed
- **Medium (Yellow)**: 14-29 days, automated check-in
- **Low (Green)**: 7-13 days, routine monitoring

---

## 🔧 **Implementation Priority**

### **Phase 1 (Week 1-2):**
- ✅ Patient Risk Assessment endpoint
- ✅ Basic risk-prioritized patient list
- ✅ Frontend dashboard with risk metrics

### **Phase 2 (Week 3-4):**
- ✅ Performance metrics endpoint
- ✅ Communication channel tracking
- ✅ Advanced filtering and actions

### **Phase 3 (Week 5-6):**
- ✅ Trending analytics
- ✅ Benchmark comparisons  
- ✅ Automated alert system

---

## 📋 **Success Metrics**

**We'll measure success by:**
1. **Staff Efficiency**: Reduced time to identify at-risk patients (target: 50% reduction)
2. **Reengagement Rate**: Improved contact → appointment conversion (target: >70%)
3. **Patient Retention**: Reduced critical risk patients (target: <5% of total)
4. **Revenue Impact**: Increased appointment bookings from outreach (target: +25%)

---

## 🚀 **Why This Matters**

This isn't just about better metrics - it's about **transforming patient care**:
- **Proactive vs Reactive**: Catch patients before they're lost
- **Data-Driven Outreach**: Target the right patients with the right message
- **Measurable ROI**: Track which reengagement strategies actually work
- **Staff Productivity**: Clear priorities instead of guessing who to contact

**Bottom Line**: Turn patient data into patient retention. 