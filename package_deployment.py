import os
import zipfile
import json
from pathlib import Path

def create_deployment_package():
    """Create a complete deployment package that can be uploaded to any cloud platform"""
    
    print("🚀 Creating deployment package...")
    
    # Files to include in deployment
    files_to_include = [
        "coinswitch_futures_live_bot.py",
        "config.py", 
        "health_monitor.py",
        "requirements.txt",
        "Dockerfile",
        ".env",
        "CLOUD_DEPLOYMENT.md",
        "QUICK_DEPLOY.md"
    ]
    
    # Create deployment folder
    deploy_dir = Path("deployment_package")
    deploy_dir.mkdir(exist_ok=True)
    
    # Copy essential files
    for file_name in files_to_include:
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(deploy_dir / file_name, 'w', encoding='utf-8') as dst:
                dst.write(content)
            print(f"✅ Copied {file_name}")
        else:
            print(f"❌ Missing {file_name}")
    
    # Create simplified run script
    run_script = '''#!/usr/bin/env python3
"""Simple entry point for cloud deployment"""
import os
import sys

# Set up environment
if not os.getenv('CS_API_KEY'):
    print("ERROR: Missing CS_API_KEY environment variable")
    sys.exit(1)

# Import and run the trading bot
try:
    from coinswitch_futures_live_bot import main
    print("Starting CoinSwitch Futures Trading Bot...")
    main()
except Exception as e:
    print(f"ERROR: Error running bot: {e}")
    sys.exit(1)
'''
    
    with open(deploy_dir / "run_bot.py", 'w', encoding='utf-8') as f:
        f.write(run_script)
    print("✅ Created run_bot.py")
    
    # Create railway.toml for Railway deployment
    railway_config = '''[build]
builder = "DOCKERFILE"

[deploy]
startCommand = "python run_bot.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
CS_API_KEY = { required = true }
CS_API_SECRET_HEX = { required = true }
CS_DRY_RUN = { default = "false" }
CS_WALLET_BALANCE = { default = "1000" }
CS_MAX_SYMBOLS = { default = "50" }
'''
    
    with open(deploy_dir / "railway.toml", 'w') as f:
        f.write(railway_config)
    print("✅ Created railway.toml")
    
    # Create render.yaml for Render deployment
    render_config = '''services:
  - type: worker
    name: coinswitch-futures-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python run_bot.py
    envVars:
      - key: CS_API_KEY
        sync: false
      - key: CS_API_SECRET_HEX  
        sync: false
      - key: CS_DRY_RUN
        value: "false"
      - key: CS_WALLET_BALANCE
        value: "1000"
      - key: CS_MAX_SYMBOLS
        value: "50"
'''
    
    with open(deploy_dir / "render.yaml", 'w') as f:
        f.write(render_config)
    print("✅ Created render.yaml")
    
    # Create deployment instructions
    instructions = '''# 📦 Deployment Package Instructions

This package contains everything needed to deploy your CoinSwitch futures trading bot.

## 🚀 Quick Deploy Options:

### Option 1: Railway.app (Recommended)
1. Upload this entire folder to GitHub
2. Connect Railway to your GitHub repo
3. Add environment variables in Railway dashboard
4. Deploy automatically!

### Option 2: Render.com 
1. Upload folder to GitHub
2. Create new Web Service on Render
3. Set environment variables
4. Deploy!

### Option 3: Google Cloud Run
1. Zip this entire folder
2. Upload to Cloud Run
3. Set environment variables
4. Deploy!

## 🔧 Required Environment Variables:

```
CS_API_KEY=2510b7d179a4134bd995430551a6f9f33689a004fc8b026b9dfb389c7a6385b8
CS_API_SECRET_HEX=fbdedec8ecb377672aa69ea7732d458c351e7e5d5a44b2a4b28514d906322fe1
CS_DRY_RUN=false
CS_WALLET_BALANCE=1000
CS_MAX_SYMBOLS=50
```

## 📁 Package Contents:

- `coinswitch_futures_live_bot.py` - Main trading bot
- `run_bot.py` - Simple entry point
- `requirements.txt` - Python dependencies  
- `Dockerfile` - Container configuration
- `railway.toml` - Railway platform config
- `render.yaml` - Render platform config
- `.env` - Environment variables (for local testing)
- Configuration and documentation files

## ⚡ Ready to Deploy!

Your bot will automatically:
- 🎯 Scan 50 futures symbols every run
- 💰 Place live trades with TP/SL orders
- 🧠 Learn and adapt strategies
- 📊 Log all trades to database

**Set up scheduling after deployment to run every 4 hours!**
'''
    
    with open(deploy_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(instructions)
    print("✅ Created README.md")
    
    # Create zip package
    zip_path = "coinswitch_bot_deployment.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in deploy_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Created {zip_path}")
    
    # Summary
    print(f"""
SUCCESS: Deployment package ready!

Package contents:
   - Folder: deployment_package/
   - Archive: {zip_path}

Quick deploy options:
   1. Upload deployment_package/ to GitHub -> Railway/Render
   2. Upload {zip_path} to Google Cloud Run
   3. Extract and upload to any cloud platform

Don't forget to:
   - Set environment variables on your platform
   - Configure scheduling (every 4 hours)
   - Monitor the first few runs

Your bot is ready for live trading!
""")

if __name__ == "__main__":
    create_deployment_package()