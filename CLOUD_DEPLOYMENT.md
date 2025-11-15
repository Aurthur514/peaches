# Cloud Trading Bot Deployment Guide

Your futures trading bot is now ready for cloud deployment with scheduled execution! 🚀

## Quick Start Commands

### Option 1: Google Cloud Platform (Recommended)
```bash
# Set your project ID
export PROJECT_ID="your-gcp-project"

# Copy environment file and add your API keys
cp .env.example .env
# Edit .env with your CS_API_KEY and CS_API_SECRET_HEX

# Deploy (runs every 4 hours automatically)
chmod +x scripts/deploy-gcp.sh
./scripts/deploy-gcp.sh $PROJECT_ID us-central1
```

### Option 2: AWS ECS Fargate
```bash
# Configure AWS CLI first
aws configure

# Copy environment file and add your API keys  
cp .env.example .env
# Edit .env with your credentials

# Deploy (runs every 4 hours automatically)
chmod +x scripts/deploy-aws.sh
./scripts/deploy-aws.sh us-east-1
```

### Option 3: Azure Container Instances
```bash
# Login to Azure
az login

# Copy environment file and add your API keys
cp .env.example .env
# Edit .env with your credentials

# Deploy (runs every 4 hours automatically)
chmod +x scripts/deploy-azure.sh
./scripts/deploy-azure.sh
```

## Configuration

### Environment Variables
- `CS_API_KEY`: Your CoinSwitch API key
- `CS_API_SECRET_HEX`: Your 64-character hex private key
- `CS_DRY_RUN`: Set to `false` for live trading
- `CS_WALLET_BALANCE`: Override wallet balance (optional)
- `CS_MAX_SYMBOLS`: Limit symbols to scan (default: 50)

### Scheduling
- **Default**: Runs every 4 hours automatically
- **Custom**: Edit the cron/schedule expression in cloud configs
- **Manual**: Trigger runs via cloud console/CLI

## Monitoring

### Health Checks
```bash
# Check bot health locally
python health_monitor.py

# Monitor with alerts
python health_monitor.py --monitor
```

### Cloud Logging
- **GCP**: `gcloud logging read 'resource.type=cloud_run_job'`
- **AWS**: `aws logs describe-log-groups --log-group-name-prefix '/ecs/trading-bot'`
- **Azure**: `az container logs --resource-group trading-bot-rg --name trading-bot-group`

### Webhooks
Set `WEBHOOK_URL` environment variable for Slack/Discord notifications.

## Database Persistence

The bot creates these databases:
- `futures_trades.db`: Trade execution log
- `bot_learning.db`: Self-learning performance data

**Important**: Mount persistent volumes in production to retain learning data.

## Security

- API keys stored as cloud secrets (not in container)
- Read-only filesystem for container security
- Network isolation in cloud environments
- Regular security updates via automated rebuilds

## Costs

Estimated monthly costs (4-hour intervals):
- **GCP Cloud Run**: ~$5-10/month
- **AWS ECS Fargate**: ~$10-15/month  
- **Azure Container Instances**: ~$8-12/month

## Support

Check the logs for any issues. The bot includes comprehensive error handling and will retry failed operations automatically.

**Live trading is enabled** - ensure your API keys have trading permissions and sufficient balance! 💰