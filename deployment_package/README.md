# 📦 Deployment Package Instructions

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
