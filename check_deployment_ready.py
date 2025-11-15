#!/usr/bin/env python3
"""
Quick Live Deployment Checker
Verifies your Auto Job Bot is ready for cloud deployment
"""

import os
import json
import sys
from pathlib import Path

def check_deployment_readiness():
    """Check if Auto Job Bot is ready for live deployment"""
    
    print("🚀 AUTO JOB BOT - LIVE DEPLOYMENT CHECKER")
    print("=" * 60)
    print()
    
    checks_passed = 0
    total_checks = 8
    
    # Check 1: Required files exist
    print("1️⃣  Checking required files...")
    required_files = [
        "enhanced_job_bot_dashboard.py",
        "auto_job_bot.py", 
        "enhanced_job_scrapers_v2.py",
        "job_bot_config.json",
        "requirements_production.txt",
        "Procfile"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    if not missing_files:
        checks_passed += 1
        print("   🎉 All required files present!")
    else:
        print(f"   ⚠️  Missing files: {', '.join(missing_files)}")
    
    print()
    
    # Check 2: Configuration file
    print("2️⃣  Checking configuration...")
    try:
        with open('job_bot_config.json', 'r') as f:
            config = json.load(f)
        
        if 'user_profile' in config:
            profile = config['user_profile']
            print(f"   ✅ User: {profile.get('full_name', 'Unknown')}")
            print(f"   ✅ Email: {profile.get('email', 'Unknown')}")
            print(f"   ✅ Location: {profile.get('location', 'Unknown')}")
            checks_passed += 1
        else:
            print("   ❌ Invalid configuration structure")
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
    
    print()
    
    # Check 3: Production requirements
    print("3️⃣  Checking production requirements...")
    try:
        with open('requirements_production.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['streamlit', 'plotly', 'aiohttp', 'selenium', 'beautifulsoup4']
        found_packages = []
        
        for package in required_packages:
            if package in requirements:
                found_packages.append(package)
                print(f"   ✅ {package}")
        
        if len(found_packages) >= len(required_packages):
            checks_passed += 1
            
    except Exception as e:
        print(f"   ❌ Requirements check failed: {e}")
    
    print()
    
    # Check 4: Procfile
    print("4️⃣  Checking Procfile...")
    try:
        with open('Procfile', 'r') as f:
            procfile = f.read()
        
        if 'streamlit run enhanced_job_bot_dashboard.py' in procfile:
            print("   ✅ Procfile configured correctly")
            checks_passed += 1
        else:
            print("   ❌ Procfile misconfigured")
    except Exception as e:
        print(f"   ❌ Procfile error: {e}")
    
    print()
    
    # Check 5: Git status
    print("5️⃣  Checking Git repository...")
    if os.path.exists('.git'):
        print("   ✅ Git repository initialized")
        checks_passed += 1
    else:
        print("   ❌ Not a git repository")
    
    print()
    
    # Check 6: Python imports
    print("6️⃣  Checking Python imports...")
    try:
        import streamlit
        print(f"   ✅ Streamlit: {streamlit.__version__}")
        checks_passed += 1
    except ImportError:
        print("   ❌ Streamlit not installed")
    
    print()
    
    # Check 7: Dashboard file
    print("7️⃣  Checking dashboard integrity...")
    try:
        with open('enhanced_job_bot_dashboard.py', 'r', encoding='utf-8') as f:
            dashboard_code = f.read()
        
        if 'def main()' in dashboard_code and 'streamlit' in dashboard_code:
            print("   ✅ Dashboard code structure valid")
            checks_passed += 1
        else:
            print("   ❌ Dashboard code issues detected")
    except Exception as e:
        print(f"   ❌ Dashboard check failed: {e}")
    
    print()
    
    # Check 8: Port configuration
    print("8️⃣  Checking port configuration...")
    try:
        with open('Procfile', 'r') as f:
            procfile = f.read()
        
        if '--server.port=$PORT' in procfile:
            print("   ✅ Port configuration ready for cloud")
            checks_passed += 1
        else:
            print("   ❌ Port not configured for cloud deployment")
    except:
        print("   ❌ Could not verify port configuration")
    
    print()
    
    # Summary
    print("🎯 DEPLOYMENT READINESS SUMMARY")
    print("=" * 40)
    print(f"Checks passed: {checks_passed}/{total_checks}")
    
    if checks_passed == total_checks:
        print("🎉 EXCELLENT! Your Auto Job Bot is 100% ready for live deployment!")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Visit https://render.com and sign up")
        print("2. Connect your GitHub repository")
        print("3. Deploy as a Web Service")
        print("4. Use the configuration from GO_LIVE_GUIDE.md")
        print()
        print("💫 Your live URL will be: https://auto-job-bot-bharathan-m.onrender.com")
        
    elif checks_passed >= 6:
        print("⚡ GOOD! Your Auto Job Bot is mostly ready for deployment.")
        print("Address the remaining issues and you'll be ready to go live!")
        
    else:
        print("⚠️  Your Auto Job Bot needs some fixes before going live.")
        print("Please address the failed checks above.")
    
    print()
    print("📖 For detailed deployment instructions, see: GO_LIVE_GUIDE.md")
    
    return checks_passed == total_checks

if __name__ == "__main__":
    try:
        is_ready = check_deployment_readiness()
        sys.exit(0 if is_ready else 1)
    except Exception as e:
        print(f"❌ Deployment checker failed: {e}")
        sys.exit(1)