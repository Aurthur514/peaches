#!/bin/bash
# Azure Container Instance Deployment Script
# Usage: ./deploy-azure.sh [RESOURCE_GROUP] [REGISTRY_NAME]

set -e

RESOURCE_GROUP=${1:-"trading-bot-rg"}
REGISTRY_NAME=${2:-"tradingbotregistry"}
LOCATION="eastus"

echo "🚀 Deploying Trading Bot to Azure Container Instances..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Registry: $REGISTRY_NAME"

# Create resource group
echo "🏗️ Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry
echo "📦 Creating container registry..."
az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true

# Build and push image
echo "🐳 Building and pushing Docker image..."
az acr build --registry $REGISTRY_NAME --image trading-bot:latest .

# Get registry credentials
REGISTRY_SERVER="${REGISTRY_NAME}.azurecr.io"
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username --output tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value --output tsv)

# Deploy container instance
echo "☁️ Deploying container instance..."
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file cloud/azure-container-instance.json \
    --parameters containerImageName="${REGISTRY_SERVER}/trading-bot:latest" \
                 apiKey="${CS_API_KEY}" \
                 apiSecret="${CS_API_SECRET_HEX}"

# Create Logic App for scheduling (every 4 hours)
echo "⏰ Creating scheduler with Logic App..."
cat > /tmp/logic-app.json << EOF
{
  "definition": {
    "\$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "contentVersion": "1.0.0.0",
    "triggers": {
      "Recurrence": {
        "type": "Recurrence",
        "recurrence": {
          "frequency": "Hour",
          "interval": 4
        }
      }
    },
    "actions": {
      "HTTP": {
        "type": "Http",
        "inputs": {
          "method": "POST",
          "uri": "https://management.azure.com/subscriptions/[SUBSCRIPTION_ID]/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerInstance/containerGroups/trading-bot-group/restart",
          "headers": {
            "Authorization": "Bearer [ACCESS_TOKEN]"
          }
        }
      }
    }
  }
}
EOF

az logic workflow create \
    --resource-group $RESOURCE_GROUP \
    --name trading-bot-scheduler \
    --definition /tmp/logic-app.json

echo "✅ Deployment complete!"
echo "📊 Monitor logs: az container logs --resource-group $RESOURCE_GROUP --name trading-bot-group"