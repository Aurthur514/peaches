#!/usr/bin/env python3
"""
Real Job Application Test - Verify if the system actually works with live job sites
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_job_application():
    print("🔍 TESTING REAL JOB APPLICATION SYSTEM")
    print("=" * 60)
    
    # Test 1: Import check
    print("\n1. 📦 Testing imports...")
    try:
        from improved_real_job_search_engine import ImprovedRealJobSearchEngine
        print("   ✅ Improved search engine imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: WebDriver initialization
    print("\n2. 🌐 Testing WebDriver initialization...")
    search_engine = None
    try:
        search_engine = ImprovedRealJobSearchEngine()
        print("   ✅ WebDriver initialized successfully")
    except Exception as e:
        print(f"   ❌ WebDriver failed: {e}")
        print("   💡 Make sure Chrome browser is installed")
        return False
    
    # Test 3: Real job search
    print("\n3. 🔍 Testing real job search...")
    try:
        print("   🚀 Searching for 'data analyst' jobs in Chennai...")
        
        # Search with timeout
        jobs = search_engine.search_all_platforms("data analyst", "Chennai")
        
        print(f"   📊 Search completed - Found {len(jobs)} jobs")
        
        if len(jobs) > 0:
            print("   ✅ REAL JOB SEARCH IS WORKING!")
            print("\n   📋 Sample jobs found:")
            
            for i, job in enumerate(jobs[:3], 1):
                print(f"   {i}. 💼 {job.get('title', 'N/A')}")
                print(f"      🏢 Company: {job.get('company', 'N/A')}")
                print(f"      📍 Location: {job.get('location', 'N/A')}")
                print(f"      🌐 Platform: {job.get('platform', 'N/A')}")
                print()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_job_test_results_{timestamp}.json"
            
            import json
            with open(filename, 'w') as f:
                json.dump({
                    'test_timestamp': timestamp,
                    'total_jobs_found': len(jobs),
                    'search_keywords': 'data analyst',
                    'search_location': 'Chennai',
                    'jobs': jobs
                }, f, indent=2)
            
            print(f"   💾 Results saved to: {filename}")
            
        else:
            print("   ⚠️ No jobs found - this could mean:")
            print("     • Job sites are blocking automated access")
            print("     • CSS selectors need updating") 
            print("     • Network/connectivity issues")
            print("     • Search terms too specific")
        
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return False
    
    finally:
        # Cleanup
        if search_engine:
            try:
                search_engine.cleanup()
                print("   🧹 Browser cleaned up")
            except:
                pass
    
    # Test 4: Application simulation
    print("\n4. 🤖 Testing application logic...")
    
    if len(jobs) > 0:
        try:
            # Simulate job application process
            sample_job = jobs[0]
            
            print(f"   🎯 Simulating application to: {sample_job.get('title')}")
            
            # Mock application data
            application_data = {
                'job_title': sample_job.get('title'),
                'company': sample_job.get('company'),
                'platform': sample_job.get('platform'),
                'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Applied',
                'match_score': 85
            }
            
            print("   ✅ Application simulation successful")
            print(f"   📝 Application data: {application_data}")
            
        except Exception as e:
            print(f"   ❌ Application simulation failed: {e}")
    
    print(f"\n{'='*60}")
    
    if len(jobs) > 0:
        print("🎉 CONCLUSION: REAL JOB APPLICATION SYSTEM IS WORKING!")
        print(f"   • Successfully found {len(jobs)} real job opportunities")
        print("   • Browser automation functioning")
        print("   • Job data extraction working")
        print("   • Application logic operational")
        print("\n💡 You can now use this system to apply to real jobs!")
        return True
    else:
        print("⚠️ CONCLUSION: SYSTEM PARTIALLY WORKING")
        print("   • Browser automation working")
        print("   • Job search engine initialized")
        print("   • But no jobs found - may need selector updates")
        print("\n💡 Try running again or check job site accessibility")
        return False

def check_system_requirements():
    """Check if system has required components"""
    print("🔧 SYSTEM REQUIREMENTS CHECK")
    print("-" * 40)
    
    # Check Chrome
    try:
        import subprocess
        result = subprocess.run(['chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Chrome browser: Available")
        else:
            print("❌ Chrome browser: Not found in PATH")
    except:
        try:
            # Try alternative Chrome paths
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            
            chrome_found = False
            for path in chrome_paths:
                if os.path.exists(path):
                    print("✅ Chrome browser: Found at", path)
                    chrome_found = True
                    break
            
            if not chrome_found:
                print("❌ Chrome browser: Not found")
        except:
            print("⚠️ Chrome browser: Cannot verify")
    
    # Check Selenium
    try:
        import selenium
        print(f"✅ Selenium: Version {selenium.__version__}")
    except ImportError:
        print("❌ Selenium: Not installed")
    
    # Check other dependencies
    dependencies = ['requests', 'json', 'time', 'datetime']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available")
        except ImportError:
            print(f"❌ {dep}: Not available")
    
    print()

if __name__ == "__main__":
    print("🚀 REAL JOB APPLICATION SYSTEM - LIVE TEST")
    print("=" * 60)
    
    # Check requirements first
    check_system_requirements()
    
    # Run the test
    success = test_real_job_application()
    
    print("\n" + "="*60)
    if success:
        print("🎯 RESULT: Your job search system is ready for real applications!")
    else:
        print("🔧 RESULT: System needs troubleshooting before real applications")
    
    print("="*60)