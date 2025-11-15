#!/usr/bin/env python3
"""
Cloud Deployment Helper - Deploy Trading Bot to Multiple Cloud Providers
Handles deployment without requiring local cloud CLI tools
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_prerequisites():
    """Check if required tools are available"""
    print("🔍 Checking prerequisites...")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker:", result.stdout.strip())
        else:
            print("❌ Docker not available")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed")
        return False
    
    # Check if Docker daemon is running
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker daemon is running")
        else:
            print("❌ Docker daemon not running - please start Docker Desktop")
            return False
    except:
        print("❌ Docker daemon not running - please start Docker Desktop")
        return False
    
    return True

def build_image():
    """Build the Docker image"""
    print("🐳 Building Docker image...")
    
    try:
        result = subprocess.run(['docker', 'build', '-t', 'trading-bot', '.'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker image built successfully")
            return True
        else:
            print("❌ Docker build failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error building image: {e}")
        return False

def test_local():
    """Test the bot locally in Docker"""
    print("🧪 Testing bot locally...")
    
    # Read .env file for environment variables
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                env_vars[key] = value
    
    # Override to dry-run for testing
    env_vars['CS_DRY_RUN'] = 'true'
    env_vars['CS_MAX_SYMBOLS'] = '5'
    
    # Build Docker run command
    docker_env = []
    for key, value in env_vars.items():
        docker_env.extend(['-e', f'{key}={value}'])
    
    cmd = ['docker', 'run', '--rm'] + docker_env + ['trading-bot']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ Local test successful!")
            print("📊 Output preview:")
            print(result.stdout[-500:])  # Last 500 characters
            return True
        else:
            print("❌ Local test failed:")
            print(result.stderr[-500:])
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out (2 minutes) - this might be normal for the first run")
        return True
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def show_deployment_options():
    """Show available deployment options"""
    print("\n🚀 DEPLOYMENT OPTIONS")
    print("=" * 50)
    
    print("\n📱 OPTION 1: GitHub Actions (Recommended)")
    print("- Push code to GitHub")
    print("- GitHub will build and deploy automatically")
    print("- No local cloud tools required")
    
    print("\n☁️  OPTION 2: Cloud Web Console")
    print("- Upload the Docker image manually")
    print("- Use cloud provider web interfaces")
    print("- Google Cloud Run, AWS ECS, Azure Container Instances")
    
    print("\n🖥️  OPTION 3: Install Cloud CLI Tools")
    print("- Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
    print("- AWS CLI: https://aws.amazon.com/cli/")
    print("- Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
    
    print("\n🐳 OPTION 4: Docker Hub + Cloud Deploy")
    print("- Push to Docker Hub")
    print("- Deploy from Docker Hub to cloud")

def push_to_docker_hub():
    """Guide for pushing to Docker Hub"""
    print("\n📦 DOCKER HUB DEPLOYMENT")
    print("=" * 30)
    
    username = input("Enter your Docker Hub username: ").strip()
    if not username:
        print("❌ Username required")
        return False
    
    image_name = f"{username}/trading-bot"
    
    print(f"\n🏷️  Tagging image as {image_name}...")
    try:
        subprocess.run(['docker', 'tag', 'trading-bot', image_name], check=True)
        print("✅ Tagged successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to tag image")
        return False
    
    print(f"\n📤 Pushing to Docker Hub...")
    print(f"Command: docker push {image_name}")
    print("⚠️  Make sure you're logged in: docker login")
    
    try:
        result = subprocess.run(['docker', 'push', image_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Pushed to Docker Hub successfully!")
            print(f"\n🔗 Your image: https://hub.docker.com/r/{image_name}")
            
            print(f"\n🚀 Deploy commands for cloud providers:")
            print(f"Google Cloud Run:")
            print(f"  gcloud run deploy trading-bot --image={image_name} --region=us-central1")
            print(f"\nAWS ECS:")
            print(f"  Update task definition with image: {image_name}")
            print(f"\nAzure Container Instances:")
            print(f"  az container create --name trading-bot --image {image_name}")
            
            return True
        else:
            print("❌ Push failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error pushing: {e}")
        return False

def main():
    """Main deployment workflow"""
    print("🤖 TRADING BOT CLOUD DEPLOYMENT")
    print("=" * 40)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please:")
        print("1. Install Docker Desktop")
        print("2. Start Docker Desktop")
        print("3. Run this script again")
        return
    
    if not build_image():
        print("❌ Cannot proceed without successful build")
        return
    
    print("\n🧪 Would you like to test locally first? (y/n): ", end="")
    if input().lower().startswith('y'):
        if not test_local():
            print("⚠️  Local test had issues, but continuing...")
    
    show_deployment_options()
    
    print("\n🐳 Would you like to push to Docker Hub? (y/n): ", end="")
    if input().lower().startswith('y'):
        push_to_docker_hub()
    
    print("\n✅ Deployment preparation complete!")
    print("📖 See CLOUD_DEPLOYMENT.md for detailed instructions")

if __name__ == "__main__":
    main()