# 🐳 Render.com Docker Image Deployment

Since you've connected GitHub, here's how to deploy your Docker image:

## 🚀 **Step-by-Step Docker Image Deployment:**

### **Step 1: Create New Service**
- In your Render dashboard, click **"New +"**
- Select **"Web Service"** (not Background Worker for Docker images)

### **Step 2: Choose Docker Image Source**
- Instead of connecting a repository, look for **"Deploy an existing image"**
- OR click **"Public Git Repository"** and enter: `aurthur514/trading-bot`
- OR look for **"Docker Image"** option in the deployment source

### **Step 3: Configure Docker Image**
- **Image URL:** `aurthur514/trading-bot:latest`
- **Service Name:** `coinswitch-futures-bot`
- **Region:** Choose closest to you
- **Instance Type:** Free tier

### **Step 4: Environment Variables**
Add these in the Environment section:
```
CS_API_KEY=2510b7d179a4134bd995430551a6f9f33689a004fc8b026b9dfb389c7a6385b8
CS_API_SECRET_HEX=fbdedec8ecb377672aa69ea7732d458c351e7e5d5a44b2a4b28514d906322fe1
CS_DRY_RUN=false
CS_WALLET_BALANCE=1000
CS_MAX_SYMBOLS=50
```

### **Step 5: Advanced Settings**
- **Auto-Deploy:** Disabled (since it's a one-time run)
- **Health Check Path:** Leave blank
- **Start Command:** `python run_bot.py`

## 🔄 **Alternative: Use Your GitHub Repo**

Since GitHub is connected, you can also:

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Trading bot ready for deployment"
   git push origin main
   ```

2. **Deploy from GitHub:**
   - Select your `peaches` repository
   - Render will automatically detect the Dockerfile
   - Add the same environment variables
   - Deploy!

## ⏰ **Set Up Scheduling**

After deployment, set up cron jobs:
1. Go to your service dashboard
2. Click **"Settings"** → **"Environment"**
3. Add cron job or use external scheduler

## 🎯 **What to Look For:**

In Render dashboard, you want:
- **"Deploy an existing image"** option, OR
- **"Docker"** as deployment method, OR  
- **"Container"** service type

**Your Docker image:** `aurthur514/trading-bot`

Need me to help with any specific step?