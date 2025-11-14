#!/usr/bin/env python3
"""
Quick Start Script for Auto Job Application Bot
Easy setup and launch script for new users
"""

import os
import sys
import subprocess
import json
import asyncio
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    banner = """
🤖 AUTO JOB APPLICATION BOT 🤖
═══════════════════════════════════════
Automated job search and application system
Find and apply to relevant jobs while you sleep!
═══════════════════════════════════════
"""
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    
    requirements = [
        "selenium",
        "beautifulsoup4", 
        "requests",
        "streamlit",
        "plotly",
        "python-dotenv",
        "aiohttp",
        "webdriver-manager"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def download_chromedriver():
    """Download ChromeDriver if needed"""
    print("\n🌐 Setting up ChromeDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Test ChromeDriver
        driver_path = ChromeDriverManager().install()
        print(f"✅ ChromeDriver installed at: {driver_path}")
        return True
        
    except Exception as e:
        print(f"❌ ChromeDriver setup failed: {e}")
        return False

def create_config_interactive():
    """Create configuration through interactive prompts"""
    print("\n⚙️ Setting up your job preferences...")
    print("(Press Enter to use default values shown in brackets)")
    
    # Personal info
    full_name = input("Full Name [John Doe]: ").strip() or "John Doe"
    email = input("Email address [john.doe@example.com]: ").strip() or "john.doe@example.com"
    phone = input("Phone number [+1-555-0123]: ").strip() or "+1-555-0123"
    location = input("Your location [Remote]: ").strip() or "Remote"
    
    print("\n💼 Job Preferences:")
    
    # Job roles
    print("Target job roles (separate with commas):")
    roles_input = input("[Software Engineer, Python Developer, Backend Developer]: ").strip()
    target_roles = [r.strip() for r in roles_input.split(',')] if roles_input else [
        "Software Engineer", "Python Developer", "Backend Developer"
    ]
    
    # Locations
    print("Preferred locations (separate with commas):")
    locations_input = input("[Remote, New York NY, San Francisco CA]: ").strip()
    preferred_locations = [l.strip() for l in locations_input.split(',')] if locations_input else [
        "Remote", "New York, NY", "San Francisco, CA"
    ]
    
    # Salary
    try:
        salary_min = int(input("Minimum salary [80000]: ").strip() or "80000")
        salary_max = int(input("Maximum salary [150000]: ").strip() or "150000")
    except ValueError:
        salary_min, salary_max = 80000, 150000
    
    print("\n🛠️ Technical Skills:")
    skills_input = input("Technical skills (separate with commas) [Python, JavaScript, AWS, Docker]: ").strip()
    technical_skills = [s.strip() for s in skills_input.split(',')] if skills_input else [
        "Python", "JavaScript", "AWS", "Docker"
    ]
    
    print("\n🎯 Keywords:")
    must_have_input = input("Must-have keywords [Python, Backend, API]: ").strip()
    must_have = [k.strip() for k in must_have_input.split(',')] if must_have_input else [
        "Python", "Backend", "API"
    ]
    
    nice_to_have_input = input("Nice-to-have keywords [AWS, Docker, React]: ").strip()
    nice_to_have = [k.strip() for k in nice_to_have_input.split(',')] if nice_to_have_input else [
        "AWS", "Docker", "React"
    ]
    
    avoid_input = input("Keywords to avoid [PHP, WordPress, Sales]: ").strip()
    avoid_keywords = [k.strip() for k in avoid_input.split(',')] if avoid_input else [
        "PHP", "WordPress", "Sales"
    ]
    
    print("\n🤖 Bot Settings:")
    auto_apply = input("Enable auto-apply? (y/N): ").strip().lower() == 'y'
    
    try:
        max_applications = int(input("Max applications per day [10]: ").strip() or "10")
        min_match_score = float(input("Minimum match score (0.0-1.0) [0.7]: ").strip() or "0.7")
    except ValueError:
        max_applications = 10
        min_match_score = 0.7
    
    # Create config
    config = {
        "user_profile": {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": location,
            "target_roles": target_roles,
            "preferred_locations": preferred_locations,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "job_types": ["full-time", "remote"],
            "experience_level": ["mid", "senior"],
            "technical_skills": technical_skills,
            "soft_skills": ["Communication", "Problem Solving", "Leadership"],
            "keywords_must_have": must_have,
            "keywords_nice_to_have": nice_to_have,
            "keywords_avoid": avoid_keywords,
            "auto_apply_enabled": auto_apply,
            "max_applications_per_day": max_applications,
            "min_match_score": min_match_score,
            "cover_letter_template": "Dear Hiring Manager,\n\nI am excited to apply for the {title} position at {company}...",
            "resume_path": "resume.pdf",
            "email_notifications": True,
            "daily_report": True
        },
        "linkedin_credentials": {
            "email": "",
            "password": ""
        }
    }
    
    return config

def save_config(config):
    """Save configuration to file"""
    try:
        with open("job_bot_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved to job_bot_config.json")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def test_installation():
    """Test if everything is working"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        import selenium
        import requests
        import pandas
        import streamlit
        print("✅ All packages imported successfully")
        
        # Test ChromeDriver
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.get("https://httpbin.org/ip")
        driver.quit()
        print("✅ ChromeDriver working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def show_next_steps():
    """Show next steps to user"""
    print("\n🎉 AUTO JOB BOT SETUP COMPLETE! 🎉")
    print("\n📋 What to do next:")
    print("\n1. 🔐 OPTIONAL: Add LinkedIn credentials to job_bot_config.json for LinkedIn job applications")
    print("   Edit the 'linkedin_credentials' section with your email and password")
    
    print("\n2. 📄 OPTIONAL: Add your resume PDF file as 'resume.pdf' in this directory")
    
    print("\n3. 🚀 Run the bot using one of these methods:")
    print("   • Interactive mode:  python auto_job_bot.py")
    print("   • Web dashboard:     streamlit run job_bot_dashboard.py")
    print("   • Single search:     python -c 'import asyncio; from auto_job_bot import AutoJobBot; bot = AutoJobBot(); asyncio.run(bot.initialize()); asyncio.run(bot.run_daily_cycle())'")
    
    print("\n4. 📊 Monitor results:")
    print("   • Check job_database.json for found jobs")
    print("   • Check job_bot.log for activity logs")
    print("   • Use the web dashboard for real-time monitoring")
    
    print("\n⚠️  IMPORTANT SAFETY TIPS:")
    print("   • Start with auto_apply_enabled: false to review jobs manually")
    print("   • Test with a small max_applications_per_day value (5-10)")
    print("   • Review and customize your keywords and preferences")
    print("   • Keep your LinkedIn/job site credentials secure")
    
    print("\n🆘 Need help? Check the README.md or logs for troubleshooting")

def main():
    """Main setup function"""
    print_banner()
    
    # Step 1: Check Python version
    check_python_version()
    
    # Step 2: Install requirements
    if not install_requirements():
        print("\n❌ Failed to install required packages. Please check your internet connection and try again.")
        return
    
    # Step 3: Setup ChromeDriver
    if not download_chromedriver():
        print("\n❌ ChromeDriver setup failed. You may need to install Chrome browser.")
        return
    
    # Step 4: Create configuration
    config = create_config_interactive()
    
    if not save_config(config):
        print("\n❌ Failed to save configuration")
        return
    
    # Step 5: Test installation
    if not test_installation():
        print("\n❌ Installation test failed")
        return
    
    # Step 6: Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()