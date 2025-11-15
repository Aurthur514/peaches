#!/bin/bash
# Google Cloud Platform Deployment Script
# Usage: ./deploy-gcp.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/trading-bot"

echo "🚀 Deploying Trading Bot to Google Cloud..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Create secrets (run once)
echo "🔐 Creating secrets..."
gcloud secrets create trading-secrets --data-file=.env --project=$PROJECT_ID || true

# Deploy Cloud Run Job
echo "☁️ Deploying Cloud Run Job..."
gcloud run jobs replace cloud/gcloud-run-job.yaml \
    --region=$REGION \
    --project=$PROJECT_ID

# Create Cloud Scheduler job for every 4 hours
echo "⏰ Creating scheduler..."
gcloud scheduler jobs create http trading-bot-scheduler \
    --schedule="0 */4 * * *" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/trading-bot:run" \
    --http-method=POST \
    --oauth-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
    --project=$PROJECT_ID || true

echo "✅ Deployment complete!"
echo "📊 Monitor logs: gcloud logging read 'resource.type=cloud_run_job' --project=$PROJECT_ID"