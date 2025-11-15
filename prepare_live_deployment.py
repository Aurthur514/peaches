#!/usr/bin/env python3
"""
Production Deployment Script for Auto Job Bot
Prepares and validates the system for live deployment
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path

def check_requirements():
    """Check if all required files and dependencies are ready"""
    print("🔍 Checking deployment requirements...")
    
    required_files = [
        'enhanced_job_bot_dashboard.py',
        'auto_job_bot.py', 
        'enhanced_job_scrapers_v2.py',
        'job_bot_config.json',
        'requirements_production.txt',
        'Procfile',
        'render.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def validate_config():
    """Validate job bot configuration"""
    print("🔧 Validating configuration...")
    
    try:
        with open('job_bot_config.json', 'r') as f:
            config = json.load(f)
        
        required_sections = ['user_profile', 'linkedin_credentials']
        for section in required_sections:
            if section not in config:
                print(f"⚠️  Missing config section: {section}")
        
        user_profile = config.get('user_profile', {})
        required_fields = ['full_name', 'email', 'target_roles', 'location']
        
        for field in required_fields:
            if field not in user_profile or not user_profile[field]:
                print(f"⚠️  Missing or empty field: {field}")
        
        print("✅ Configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def prepare_production_config():
    """Create production-ready configuration"""
    print("⚙️ Preparing production configuration...")
    
    try:
        with open('job_bot_config.json', 'r') as f:
            config = json.load(f)
        
        # Remove sensitive local paths
        if 'resume_path' in config.get('user_profile', {}):
            config['user_profile']['resume_path'] = 'resume.pdf'
        
        # Set production defaults
        config['user_profile']['email_notifications'] = True
        config['user_profile']['daily_report'] = True
        
        # Clear LinkedIn credentials for security (will be set via environment variables)
        config['linkedin_credentials'] = {
            "email": "",
            "password": ""
        }
        
        with open('job_bot_config_production.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Production configuration created")
        return True
        
    except Exception as e:
        print(f"❌ Production config creation failed: {e}")
        return False

def create_deployment_package():
    """Create deployment package"""
    print("📦 Creating deployment package...")
    
    deployment_files = [
        'enhanced_job_bot_dashboard.py',
        'auto_job_bot.py',
        'enhanced_job_scrapers_v2.py', 
        'job_bot_config_production.json',
        'requirements_production.txt',
        'Procfile',
        'render.yaml',
        'LIVE_DEPLOYMENT.md'
    ]
    
    # Create deployment directory
    deploy_dir = Path('deployment_live')
    deploy_dir.mkdir(exist_ok=True)
    
    # Copy files to deployment directory
    import shutil
    for file in deployment_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir / file)
            print(f"✅ Copied {file}")
        else:
            print(f"⚠️  File not found: {file}")
    
    # Rename production config
    prod_config = deploy_dir / 'job_bot_config_production.json'
    final_config = deploy_dir / 'job_bot_config.json' 
    
    if prod_config.exists():
        if final_config.exists():
            final_config.unlink()  # Remove existing file first
        prod_config.rename(final_config)
    
    print(f"✅ Deployment package created in {deploy_dir}")
    return True

def run_final_tests():
    """Run final tests before deployment"""
    print("🧪 Running final tests...")
    
    try:
        # Test imports
        sys.path.insert(0, '.')
        
        print("Testing dashboard import...")
        import enhanced_job_bot_dashboard
        print("✅ Dashboard import successful")
        
        print("Testing auto job bot import...")
        import auto_job_bot
        print("✅ Auto job bot import successful")
        
        print("Testing scrapers import...")
        import enhanced_job_scrapers_v2
        print("✅ Scrapers import successful")
        
        print("✅ All tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def generate_deployment_instructions():
    """Generate deployment instructions"""
    print("📋 Generating deployment instructions...")
    
    instructions = """
🚀 AUTO JOB BOT - LIVE DEPLOYMENT INSTRUCTIONS

Your Auto Job Bot is ready for live deployment!

OPTION 1 - RENDER (RECOMMENDED):
1. Go to https://render.com
2. Connect your GitHub account
3. Fork this repository to your GitHub
4. Create a new Web Service
5. Select this repository
6. Use these settings:
   - Build Command: pip install -r requirements_production.txt
   - Start Command: streamlit run enhanced_job_bot_dashboard.py --server.port $PORT --server.address 0.0.0.0

OPTION 2 - RAILWAY:
1. Go to https://railway.app  
2. Connect your GitHub account
3. Deploy from this repository
4. Railway will auto-detect the configuration

OPTION 3 - HEROKU:
1. Install Heroku CLI
2. Run: heroku create your-job-bot-name
3. Run: git push heroku main

ENVIRONMENT VARIABLES (Optional):
- LINKEDIN_EMAIL: your_email@gmail.com
- LINKEDIN_PASSWORD: your_password
- SECRET_KEY: random_secret_key

Your live dashboard will be available at your deployment URL!

🎉 Once deployed, your Auto Job Bot will run 24/7 finding job opportunities!
"""
    
    with open('deployment_instructions.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ Deployment instructions created")

def main():
    """Main deployment preparation function"""
    print("🚀" * 20)
    print("AUTO JOB BOT - LIVE DEPLOYMENT PREPARATION")
    print("🚀" * 20)
    print()
    
    steps = [
        ("Checking requirements", check_requirements),
        ("Validating configuration", validate_config),
        ("Preparing production config", prepare_production_config),
        ("Creating deployment package", create_deployment_package),
        ("Running final tests", run_final_tests),
        ("Generating instructions", generate_deployment_instructions)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"STEP: {step_name}")
        print(f"{'='*50}")
        
        try:
            success = step_func()
            if not success:
                print(f"❌ Step failed: {step_name}")
                return False
        except Exception as e:
            print(f"❌ Step error: {step_name} - {e}")
            return False
    
    print("\n" + "🎉" * 50)
    print("AUTO JOB BOT IS READY FOR LIVE DEPLOYMENT!")
    print("🎉" * 50)
    print()
    print("📁 Deployment files created in: deployment_live/")
    print("📋 Instructions available in: deployment_instructions.txt")
    print()
    print("🚀 Your enhanced Auto Job Bot is ready to go live!")
    print("   Visit https://render.com or https://railway.app to deploy")
    print()
    
    return True

if __name__ == "__main__":
    main()