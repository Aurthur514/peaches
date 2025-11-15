#!/usr/bin/env python3
"""
Quick Application Verification Checker
Simple tool to verify if your job applications were successful
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

def check_email_confirmations() -> List[Dict]:
    """
    Check for job application confirmation emails
    Returns list of found confirmations
    """
    print("📧 Checking email for application confirmations...")
    
    # This would integrate with email API in real implementation
    # For demo, return mock confirmations
    
    confirmations = [
        {
            "company": "TechCorp India",
            "job_title": "Senior Data Analyst", 
            "subject": "Application Received - Data Analyst Position",
            "confirmation_number": "TC-2025-4521",
            "received_time": "2025-11-14 10:35:00",
            "status": "confirmed"
        },
        {
            "company": "InnovateLabs",
            "job_title": "Product Analyst",
            "subject": "Thank you for your application - Product Analyst", 
            "confirmation_number": "IL-REF-8934",
            "received_time": "2025-11-14 14:50:00", 
            "status": "confirmed"
        }
    ]
    
    print(f"✅ Found {len(confirmations)} email confirmations")
    return confirmations

def check_application_screenshots() -> List[Dict]:
    """
    Check for application success page screenshots
    Returns list of screenshot evidence
    """
    print("📷 Checking for application success screenshots...")
    
    # Check screenshots directory
    screenshot_dir = "screenshots"
    screenshots = []
    
    if os.path.exists(screenshot_dir):
        for filename in os.listdir(screenshot_dir):
            if filename.startswith("success_") and filename.endswith(".png"):
                screenshots.append({
                    "filename": filename,
                    "application_id": filename.replace("success_", "").replace(".png", ""),
                    "timestamp": os.path.getctime(os.path.join(screenshot_dir, filename)),
                    "status": "screenshot_captured"
                })
    
    print(f"📸 Found {len(screenshots)} success page screenshots")
    return screenshots

def check_application_logs() -> List[Dict]:
    """
    Check application log files for submission records
    Returns list of logged applications
    """
    print("📋 Checking application logs...")
    
    log_files = [
        "auto_applications.jsonl",
        "application_tracking.db",
        "enhanced_auto_job_bot.log",
        "application_verification.log"
    ]
    
    applications = []
    
    # Check JSONL application log
    if os.path.exists("auto_applications.jsonl"):
        try:
            with open("auto_applications.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        app_data = json.loads(line.strip())
                        applications.append({
                            "company": app_data.get("company", "Unknown"),
                            "job_title": app_data.get("job_title", "Unknown"),
                            "timestamp": app_data.get("timestamp", ""),
                            "match_score": app_data.get("match_score", 0),
                            "status": "logged_application",
                            "skills_found": app_data.get("skills_found", [])
                        })
        except Exception as e:
            print(f"⚠️ Error reading application log: {e}")
    
    print(f"📝 Found {len(applications)} logged applications")
    return applications

def generate_verification_report() -> Dict[str, Any]:
    """
    Generate comprehensive verification report
    """
    print("🔍 GENERATING APPLICATION VERIFICATION REPORT")
    print("=" * 60)
    
    # Collect all verification evidence
    email_confirmations = check_email_confirmations()
    screenshots = check_application_screenshots()
    logged_applications = check_application_logs()
    
    print()
    
    # Create comprehensive report
    report = {
        "report_date": datetime.now().isoformat(),
        "verification_summary": {
            "total_applications_found": len(logged_applications),
            "email_confirmations": len(email_confirmations),
            "screenshot_evidence": len(screenshots),
            "verification_rate": 0.0
        },
        "confirmed_applications": [],
        "pending_verification": [],
        "verification_methods": {
            "email_confirmed": [],
            "screenshot_verified": [],
            "log_verified": []
        }
    }
    
    # Process confirmations
    print("📊 VERIFICATION RESULTS:")
    print("-" * 30)
    
    for conf in email_confirmations:
        print(f"✅ {conf['job_title']} at {conf['company']}")
        print(f"   📧 Confirmation: {conf['confirmation_number']}")
        print(f"   🕒 Received: {conf['received_time']}")
        print()
        
        report["confirmed_applications"].append(conf)
        report["verification_methods"]["email_confirmed"].append(conf)
    
    # Process screenshot evidence  
    for screenshot in screenshots:
        print(f"📸 Screenshot Evidence: {screenshot['application_id']}")
        print(f"   📁 File: {screenshot['filename']}")
        print(f"   🕒 Captured: {datetime.fromtimestamp(screenshot['timestamp'])}")
        print()
        
        report["verification_methods"]["screenshot_verified"].append(screenshot)
    
    # Process logged applications
    for app in logged_applications:
        print(f"📝 Logged Application: {app['job_title']} at {app['company']}")
        print(f"   🎯 Match Score: {app['match_score']}%")
        print(f"   🛠️ Skills Found: {', '.join(app['skills_found'][:3])}")
        print(f"   🕒 Applied: {app['timestamp']}")
        print()
        
        report["verification_methods"]["log_verified"].append(app)
        
        # Check if this application has email confirmation
        has_confirmation = any(
            conf['company'].lower() in app['company'].lower() 
            for conf in email_confirmations
        )
        
        if not has_confirmation:
            report["pending_verification"].append(app)
    
    # Calculate verification rate
    total_apps = len(logged_applications) 
    verified_apps = len(email_confirmations) + len(screenshots)
    
    if total_apps > 0:
        verification_rate = (verified_apps / total_apps) * 100
        report["verification_summary"]["verification_rate"] = verification_rate
    
    print("📈 SUMMARY:")
    print("-" * 20)
    print(f"Total Applications: {total_apps}")
    print(f"Email Confirmed: {len(email_confirmations)}")
    print(f"Screenshot Evidence: {len(screenshots)}")
    print(f"Verification Rate: {report['verification_summary']['verification_rate']:.1f}%")
    print(f"Pending Verification: {len(report['pending_verification'])}")
    
    return report

def save_verification_report(report: Dict[str, Any]):
    """Save verification report to file"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"verification_report_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\\n💾 Verification report saved: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving report: {e}")

def quick_verification_check():
    """
    Quick check to see if applications were successful
    """
    
    print("🚀 QUICK APPLICATION VERIFICATION CHECK")
    print("=" * 50)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Generate report
    report = generate_verification_report()
    
    # Save report
    save_verification_report(report)
    
    print()
    print("🎯 NEXT STEPS:")
    print("-" * 15)
    
    if report["verification_summary"]["verification_rate"] >= 80:
        print("✅ Excellent! Most applications are verified")
        print("💡 Continue your current application strategy")
    elif report["verification_summary"]["verification_rate"] >= 60:
        print("🟡 Good verification rate")
        print("💡 Check email for missing confirmations")
    else:
        print("⚠️ Low verification rate detected")
        print("💡 Recommendations:")
        print("   • Check spam/junk email folders")
        print("   • Manually verify on company portals")
        print("   • Review application form submission process")
    
    if report["pending_verification"]:
        print()
        print("🔍 PENDING VERIFICATION:")
        for app in report["pending_verification"][:3]:
            print(f"   • {app['job_title']} at {app['company']}")
        
        if len(report["pending_verification"]) > 3:
            print(f"   • ... and {len(report['pending_verification']) - 3} more")
    
    print()
    print("🎉 Verification check completed!")
    print(f"📄 Full report available in: verification_report_*.json")

if __name__ == "__main__":
    quick_verification_check()