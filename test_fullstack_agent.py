#!/usr/bin/env python3
"""
Quick test script for the Fullstack Job Agent
Tests configuration and basic functionality without applying to jobs
"""

import json
import os
from pathlib import Path

def test_config():
    """Test configuration file"""
    print("🔍 Testing Configuration...")
    
    config_file = Path('profile.json')
    
    if not config_file.exists():
        print("❌ profile.json not found!")
        print("📝 Copy fullstack_config_example.json to profile.json and update it")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Check required fields
    required = [
        'first_name', 'last_name', 'email', 'phone',
        'linkedin_email', 'linkedin_password',
        'skills', 'master_resume_path'
    ]
    
    missing = []
    for field in required:
        if field not in config:
            missing.append(field)
        elif isinstance(config[field], str) and 'YOUR_' in config[field].upper():
            missing.append(f"{field} (needs value)")
    
    if missing:
        print(f"❌ Missing or incomplete fields: {', '.join(missing)}")
        return False
    
    print(f"✅ Configuration valid")
    print(f"   Name: {config['first_name']} {config['last_name']}")
    print(f"   Email: {config['email']}")
    print(f"   Skills: {len(config.get('skills', []))} listed")
    print(f"   Match threshold: {config.get('min_match_score', 0.3):.0%}")
    
    # Check resume
    resume_path = config.get('master_resume_path', '')
    if not resume_path or not os.path.exists(resume_path):
        print(f"⚠️  Resume not found at: {resume_path}")
    else:
        print(f"✅ Resume found: {resume_path}")
    
    # Check Gemini
    if not config.get('gemini_key') or 'YOUR_' in config.get('gemini_key', '').upper():
        print("⚠️  Gemini API key not set (resume tailoring disabled)")
        print("   Get free key: https://makersuite.google.com/app/apikey")
    else:
        print("✅ Gemini API key configured")
    
    return True


def test_dependencies():
    """Test required dependencies"""
    print("\n🔍 Testing Dependencies...")
    
    deps = {
        'selenium': 'selenium',
        'google.generativeai': 'google-generativeai',
        'docx': 'python-docx'
    }
    
    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Run: pip install {package}")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def test_tech_stack_extraction():
    """Test tech stack extraction"""
    print("\n🔍 Testing Tech Stack Extraction...")
    
    sample_desc = """
    We're looking for a Fullstack Developer with expertise in:
    - React and TypeScript for frontend
    - Node.js and Express for backend
    - PostgreSQL database
    - AWS cloud services
    - Docker and Kubernetes
    """
    
    # Import the agent
    try:
        from fullstack_job_agent import FullstackJobAgent
        
        config = {'skills': ['React', 'Node.js', 'Python', 'PostgreSQL', 'AWS', 'Docker']}
        agent = FullstackJobAgent(config)
        
        techs = agent.extract_tech_stack(sample_desc)
        print(f"✅ Extracted {len(techs)} technologies:")
        print(f"   {', '.join(techs[:10])}")
        
        match_score = agent.calculate_match_score(techs, config['skills'])
        print(f"✅ Match score: {match_score:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🧪 FULLSTACK JOB AGENT - QUICK TEST                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Test dependencies
    results.append(("Dependencies", test_dependencies()))
    
    # Test config
    results.append(("Configuration", test_config()))
    
    # Test tech extraction
    results.append(("Tech Stack Matching", test_tech_stack_extraction()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("\n🚀 Ready to run:")
        print("   python fullstack_job_agent.py --dry-run --max 10")
    else:
        print("\n⚠️  Some tests failed. Fix issues above before running agent.")
    
    return all_passed


if __name__ == "__main__":
    main()
