#!/usr/bin/env python3
"""
Comprehensive Data Analysis - Validate Synced Data Quality
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Set the database URL first
os.environ['DATABASE_URL'] = 'postgresql://postgres.eilaqdyxkohzoqryhobm:RH2jd!!0t2m2025@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

def analyze_synced_data():
    """Comprehensive analysis of synced data"""
    print("📊 COMPREHENSIVE DATA ANALYSIS")
    print("=" * 60)
    
    org_id = 'org_2xwHiNrj68eaRUlX10anlXGvzX7'
    
    # 1. Overall Data Health
    print("1️⃣ OVERALL DATA HEALTH")
    print("-" * 30)
    
    overall = db.execute_query("""
        SELECT 
            COUNT(*) as total_contacts,
            COUNT(*) FILTER (WHERE contact_type = 'cliniko_patient') as cliniko_patients,
            COUNT(*) FILTER (WHERE phone IS NOT NULL) as contacts_with_phone,
            COUNT(*) FILTER (WHERE email IS NOT NULL) as contacts_with_email,
            COUNT(*) FILTER (WHERE name IS NOT NULL) as contacts_with_name
        FROM contacts 
        WHERE organization_id = %s
    """, (org_id,))
    
    if overall:
        data = overall[0]
        print(f"📋 Total Contacts: {data['total_contacts']}")
        print(f"🏥 Cliniko Patients: {data['cliniko_patients']}")
        print(f"📞 With Phone: {data['contacts_with_phone']} ({data['contacts_with_phone']/data['total_contacts']*100:.1f}%)")
        print(f"📧 With Email: {data['contacts_with_email']} ({data['contacts_with_email']/data['total_contacts']*100:.1f}%)")
        print(f"👤 With Name: {data['contacts_with_name']} ({data['contacts_with_name']/data['total_contacts']*100:.1f}%)")
    
    # 2. Active Patients Analysis
    print(f"\n2️⃣ ACTIVE PATIENTS ANALYSIS")
    print("-" * 30)
    
    active_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_active,
            AVG(recent_appointment_count) as avg_recent_appts,
            AVG(upcoming_appointment_count) as avg_upcoming_appts,
            AVG(total_appointment_count) as avg_total_appts,
            COUNT(*) FILTER (WHERE next_appointment_time IS NOT NULL) as with_next_appt,
            COUNT(*) FILTER (WHERE next_appointment_type IS NOT NULL) as with_appt_type,
            COUNT(*) FILTER (WHERE primary_appointment_type IS NOT NULL) as with_primary_type,
            COUNT(*) FILTER (WHERE treatment_notes IS NOT NULL AND treatment_notes != '') as with_notes
        FROM active_patients 
        WHERE organization_id = %s
    """, (org_id,))
    
    if active_stats:
        data = active_stats[0]
        print(f"👥 Total Active Patients: {data['total_active']}")
        print(f"📊 Avg Recent Appointments: {data['avg_recent_appts']:.1f}")
        print(f"📅 Avg Upcoming Appointments: {data['avg_upcoming_appts']:.1f}")
        print(f"📈 Avg Total Appointments: {data['avg_total_appts']:.1f}")
        print(f"🕐 With Next Appointment: {data['with_next_appt']} ({data['with_next_appt']/data['total_active']*100:.1f}%)")
        print(f"🏷️  With Appointment Type: {data['with_appt_type']} ({data['with_appt_type']/data['total_active']*100:.1f}%)")
        print(f"🎯 With Primary Type: {data['with_primary_type']} ({data['with_primary_type']/data['total_active']*100:.1f}%)")
        print(f"📝 With Treatment Notes: {data['with_notes']} ({data['with_notes']/data['total_active']*100:.1f}%)")
    
    # 3. Appointment Type Distribution
    print(f"\n3️⃣ APPOINTMENT TYPE DISTRIBUTION")
    print("-" * 30)
    
    appt_types = db.execute_query("""
        SELECT 
            primary_appointment_type,
            COUNT(*) as patient_count
        FROM active_patients 
        WHERE organization_id = %s 
        AND primary_appointment_type IS NOT NULL
        GROUP BY primary_appointment_type
        ORDER BY patient_count DESC
    """, (org_id,))
    
    if appt_types:
        print("📋 Primary Appointment Types:")
        for appt in appt_types:
            print(f"   • {appt['primary_appointment_type']}: {appt['patient_count']} patients")
    else:
        print("⚠️  No appointment type data found")
    
    # 4. Patient Activity Patterns
    print(f"\n4️⃣ PATIENT ACTIVITY PATTERNS")
    print("-" * 30)
    
    activity = db.execute_query("""
        SELECT 
            CASE 
                WHEN recent_appointment_count > 0 AND upcoming_appointment_count > 0 THEN 'Active (Recent + Upcoming)'
                WHEN recent_appointment_count > 0 AND upcoming_appointment_count = 0 THEN 'Recently Active'
                WHEN recent_appointment_count = 0 AND upcoming_appointment_count > 0 THEN 'Scheduled Only'
                ELSE 'Inactive'
            END as activity_status,
            COUNT(*) as patient_count
        FROM active_patients 
        WHERE organization_id = %s
        GROUP BY 1
        ORDER BY patient_count DESC
    """, (org_id,))
    
    if activity:
        print("📊 Patient Activity Status:")
        for status in activity:
            print(f"   • {status['activity_status']}: {status['patient_count']} patients")
    
    # 5. Data Quality Issues
    print(f"\n5️⃣ DATA QUALITY ANALYSIS")
    print("-" * 30)
    
    quality_issues = []
    
    # Check for missing contact links
    missing_contacts = db.execute_query("""
        SELECT COUNT(*) as count
        FROM active_patients ap
        LEFT JOIN contacts c ON c.id = ap.contact_id
        WHERE ap.organization_id = %s AND c.id IS NULL
    """, (org_id,))
    
    if missing_contacts and missing_contacts[0]['count'] > 0:
        quality_issues.append(f"❌ {missing_contacts[0]['count']} active patients with missing contact records")
    
    # Check for patients with no appointment data
    no_appts = db.execute_query("""
        SELECT COUNT(*) as count
        FROM active_patients 
        WHERE organization_id = %s 
        AND total_appointment_count = 0
    """, (org_id,))
    
    if no_appts and no_appts[0]['count'] > 0:
        quality_issues.append(f"⚠️  {no_appts[0]['count']} active patients with no appointment history")
    
    # Check for very old last appointments
    old_appts = db.execute_query("""
        SELECT COUNT(*) as count
        FROM active_patients 
        WHERE organization_id = %s 
        AND last_appointment_date < NOW() - INTERVAL '6 months'
    """, (org_id,))
    
    if old_appts and old_appts[0]['count'] > 0:
        quality_issues.append(f"⚠️  {old_appts[0]['count']} patients with last appointment > 6 months ago")
    
    if quality_issues:
        print("🔍 Data Quality Issues Found:")
        for issue in quality_issues:
            print(f"   {issue}")
    else:
        print("✅ No major data quality issues detected")
    
    # 6. Sample Patient Records
    print(f"\n6️⃣ SAMPLE PATIENT RECORDS")
    print("-" * 30)
    
    samples = db.execute_query("""
        SELECT 
            c.name,
            c.phone,
            ap.recent_appointment_count,
            ap.upcoming_appointment_count,
            ap.total_appointment_count,
            ap.last_appointment_date,
            ap.next_appointment_time,
            ap.next_appointment_type,
            ap.primary_appointment_type,
            CASE WHEN ap.treatment_notes IS NOT NULL AND ap.treatment_notes != '' 
                 THEN LEFT(ap.treatment_notes, 50) || '...'
                 ELSE 'No notes'
            END as notes_preview
        FROM active_patients ap
        JOIN contacts c ON c.id = ap.contact_id
        WHERE ap.organization_id = %s
        ORDER BY ap.total_appointment_count DESC, ap.updated_at DESC
        LIMIT 3
    """, (org_id,))
    
    if samples:
        print("👥 Top Active Patients (by appointment count):")
        for i, patient in enumerate(samples, 1):
            print(f"\n{i}. {patient['name']} ({patient['phone']})")
            print(f"   📊 Appointments: {patient['recent_appointment_count']} recent, {patient['upcoming_appointment_count']} upcoming, {patient['total_appointment_count']} total")
            print(f"   🕐 Last: {patient['last_appointment_date']}")
            print(f"   📅 Next: {patient['next_appointment_time']} ({patient['next_appointment_type'] or 'None'})")
            print(f"   🏷️  Primary Type: {patient['primary_appointment_type'] or 'Unknown'}")
            print(f"   📝 Notes: {patient['notes_preview']}")
    
    # 7. Sync Performance
    print(f"\n7️⃣ SYNC PERFORMANCE")
    print("-" * 30)
    
    sync_perf = db.execute_query("""
        SELECT 
            started_at,
            completed_at,
            records_processed,
            records_success,
            records_failed,
            EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
        FROM sync_logs 
        WHERE source_system = 'cliniko' 
        AND organization_id = %s
        ORDER BY started_at DESC 
        LIMIT 1
    """, (org_id,))
    
    if sync_perf:
        sync = sync_perf[0]
        duration = float(sync['duration_seconds'])
        print(f"🕐 Last Sync: {sync['started_at']}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📊 Processed: {sync['records_processed']} patients")
        print(f"✅ Success: {sync['records_success']} active patients")
        print(f"❌ Failed: {sync['records_failed']} records")
        print(f"🚀 Performance: {sync['records_processed']/duration:.1f} patients/second")
        
        # Data freshness
        hours_old = (datetime.now() - sync['started_at'].replace(tzinfo=None)).total_seconds() / 3600
        print(f"🔄 Data Age: {hours_old:.1f} hours old")
        
        if hours_old < 1:
            print("✅ Data is very fresh (< 1 hour)")
        elif hours_old < 24:
            print("✅ Data is fresh (< 24 hours)")
        else:
            print("⚠️  Data is getting stale (> 24 hours)")
    
    # 8. Recommendations
    print(f"\n8️⃣ RECOMMENDATIONS")
    print("-" * 30)
    
    recommendations = []
    
    if active_stats and active_stats[0]['with_notes'] < active_stats[0]['total_active'] * 0.5:
        recommendations.append("📝 Consider encouraging more detailed treatment notes in Cliniko")
    
    if active_stats and active_stats[0]['with_next_appt'] < active_stats[0]['total_active'] * 0.3:
        recommendations.append("📅 Many patients don't have upcoming appointments scheduled")
    
    if sync_perf and (datetime.now() - sync_perf[0]['started_at'].replace(tzinfo=None)).total_seconds() > 86400:
        recommendations.append("🔄 Enable automatic sync scheduler (ENABLE_SYNC_SCHEDULER=true)")
    else:
        recommendations.append("✅ Consider enabling automatic sync scheduler for regular updates")
    
    recommendations.append("📊 Set up monitoring alerts for sync failures")
    recommendations.append("🎯 Create patient engagement workflows for inactive patients")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print(f"\n🎉 DATA ANALYSIS COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        analyze_synced_data()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc() 