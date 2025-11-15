#!/bin/bash
# AWS ECS Deployment Script 
# Usage: ./deploy-aws.sh [AWS_REGION] [ECR_REPO_NAME]

set -e

AWS_REGION=${1:-"us-east-1"}
ECR_REPO=${2:-"trading-bot"}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "🚀 Deploying Trading Bot to AWS ECS..."
echo "Region: $AWS_REGION"
echo "ECR Repo: $ECR_REPO"

# Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION || true

# Build and push Docker image
echo "🐳 Building and pushing Docker image..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $IMAGE_URI
docker build -t $ECR_REPO .
docker tag $ECR_REPO:latest $IMAGE_URI:latest
docker push $IMAGE_URI:latest

# Update task definition with correct image URI
sed "s|ACCOUNT_ID|$AWS_ACCOUNT_ID|g; s|REGION|$AWS_REGION|g" cloud/aws-ecs-task.json > /tmp/task-def.json

# Register task definition
echo "📋 Registering ECS task definition..."
aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-def.json \
    --region $AWS_REGION

# Create EventBridge rule for every 4 hours
echo "⏰ Creating EventBridge scheduler..."
aws events put-rule \
    --name trading-bot-schedule \
    --schedule-expression "rate(4 hours)" \
    --region $AWS_REGION

# Create ECS target for the rule
aws events put-targets \
    --rule trading-bot-schedule \
    --targets "Id=1,Arn=arn:aws:ecs:${AWS_REGION}:${AWS_ACCOUNT_ID}:cluster/default,RoleArn=arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsEventsRole,EcsParameters={TaskDefinitionArn=arn:aws:ecs:${AWS_REGION}:${AWS_ACCOUNT_ID}:task-definition/trading-bot:1,LaunchType=FARGATE,NetworkConfiguration={awsvpcConfiguration={Subnets=[subnet-12345],SecurityGroups=[sg-12345],AssignPublicIp=ENABLED}}}" \
    --region $AWS_REGION

echo "✅ Deployment complete!"
echo "📊 Monitor logs: aws logs describe-log-groups --log-group-name-prefix '/ecs/trading-bot' --region $AWS_REGION"