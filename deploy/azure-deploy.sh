#!/bin/bash
# Azure Deployment Script for QuantLib Pro
# Deploys to Azure Container Instances or Azure App Service

set -e

echo " QuantLib Pro - Azure Deployment Script"
echo "=========================================="

# Configuration
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-quantlib-pro-rg}"
LOCATION="${AZURE_LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-quantlibproacr}"
APP_NAME="${APP_NAME:-quantlib-pro}"
SERVICE_PLAN="${SERVICE_PLAN:-quantlib-plan}"
IMAGE_NAME="$ACR_NAME.azurecr.io/quantlib-pro:latest"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo " Azure CLI not found. Please install it first."
    exit 1
fi

echo " Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  ACR: $ACR_NAME"
echo "  App Name: $APP_NAME"
echo ""

# Step 1: Login to Azure (if not already logged in)
echo " Step 1: Checking Azure login..."
az account show &> /dev/null || az login

echo " Azure login confirmed"

# Step 2: Create Resource Group
echo ""
echo " Step 2: Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none 2>/dev/null || echo "Resource group already exists"

echo " Resource group ready"

# Step 3: Create Azure Container Registry
echo ""
echo "  Step 3: Creating Azure Container Registry..."
az acr check-name --name $ACR_NAME --output none 2>/dev/null

az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --location $LOCATION \
    --admin-enabled true \
    --output none 2>/dev/null || echo "ACR already exists"

echo " ACR ready"

# Step 4: Build and push Docker image
echo ""
echo " Step 4: Building and pushing Docker image to ACR..."
az acr build \
    --registry $ACR_NAME \
    --image quantlib-pro:latest \
    --file Dockerfile \
    .

echo " Image pushed to ACR"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Step 5: Choose deployment method
echo ""
echo " Step 5: Deployment Method Selection"
echo "  1) Azure App Service (Recommended for production)"
echo "  2) Azure Container Instances (Simpler, lower cost)"
echo ""
read -p "Select deployment method (1 or 2) [default: 1]: " DEPLOY_METHOD
DEPLOY_METHOD=${DEPLOY_METHOD:-1}

if [ "$DEPLOY_METHOD" == "1" ]; then
    # Deploy to Azure App Service
    echo ""
    echo " Deploying to Azure App Service..."
    
    # Create App Service Plan
    az appservice plan create \
        --name $SERVICE_PLAN \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --is-linux \
        --sku B2 \
        --output none 2>/dev/null || echo "App Service Plan already exists"
    
    # Create or update web app
    az webapp create \
        --resource-group $RESOURCE_GROUP \
        --plan $SERVICE_PLAN \
        --name $APP_NAME \
        --deployment-container-image-name $IMAGE_NAME \
        --output none 2>/dev/null || \
    az webapp config container set \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --docker-custom-image-name $IMAGE_NAME \
        --docker-registry-server-url https://$ACR_NAME.azurecr.io \
        --docker-registry-server-user $ACR_USERNAME \
        --docker-registry-server-password $ACR_PASSWORD \
        --output none
    
    # Configure app settings
    az webapp config appsettings set \
        --resource-group $RESOURCE_GROUP \
        --name $APP_NAME \
        --settings \
            APP_ENV=production \
            STREAMLIT_SERVER_PORT=8501 \
            WEBSITES_PORT=8501 \
        --output none
    
    # Enable container logging
    az webapp log config \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --docker-container-logging filesystem \
        --output none
    
    # Get URL
    APP_URL="https://${APP_NAME}.azurewebsites.net"
    
    echo " Deployed to App Service"
    
else
    # Deploy to Azure Container Instances
    echo ""
    echo " Deploying to Azure Container Instances..."
    
    az container create \
        --resource-group $RESOURCE_GROUP \
        --name $APP_NAME \
        --image $IMAGE_NAME \
        --registry-login-server $ACR_NAME.azurecr.io \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --dns-name-label $APP_NAME \
        --ports 8501 \
        --cpu 2 \
        --memory 4 \
        --environment-variables \
            APP_ENV=production \
            STREAMLIT_SERVER_PORT=8501 \
        --output none
    
    # Get FQDN
    APP_URL=$(az container show \
        --resource-group $RESOURCE_GROUP \
        --name $APP_NAME \
        --query ipAddress.fqdn \
        --output tsv)
    APP_URL="http://${APP_URL}:8501"
    
    echo " Deployed to Container Instances"
fi

# Step 6: Configure monitoring (Application Insights)
echo ""
echo " Step 6: Setting up Application Insights..."
APPINSIGHTS_NAME="${APP_NAME}-insights"

az monitor app-insights component create \
    --app $APPINSIGHTS_NAME \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --application-type web \
    --output none 2>/dev/null || echo "Application Insights already exists"

INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app $APPINSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query instrumentationKey \
    --output tsv)

if [ "$DEPLOY_METHOD" == "1" ]; then
    az webapp config appsettings set \
        --resource-group $RESOURCE_GROUP \
        --name $APP_NAME \
        --settings \
            APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY \
        --output none
fi

echo " Monitoring configured"

# Step 7: Setup custom domain (optional)
echo ""
echo " Optional: Custom Domain Setup"
if [ "$DEPLOY_METHOD" == "1" ]; then
    echo "  To map a custom domain:"
    echo "  az webapp config hostname add --webapp-name $APP_NAME --resource-group $RESOURCE_GROUP --hostname YOUR-DOMAIN.com"
    echo "  az webapp config ssl bind --certificate-thumbprint THUMBPRINT --ssl-type SNI --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi
echo ""

# Step 8: Health check
echo " Step 8: Running health check..."
sleep 20
if curl -f -s "${APP_URL}/_stcore/health" > /dev/null 2>&1; then
    echo " Health check passed"
else
    echo "  Health check pending (service may still be starting)"
fi

echo ""
echo " Deployment Complete!"
echo "=========================================="
echo " Application URL: $APP_URL"
echo ""
echo " Monitoring:"
if [ "$DEPLOY_METHOD" == "1" ]; then
    echo "  Logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "  App Insights: https://portal.azure.com/#resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Insights/components/$APPINSIGHTS_NAME"
else
    echo "  Logs: az container logs --name $APP_NAME --resource-group $RESOURCE_GROUP --follow"
    echo "  Metrics: az container show --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi
echo ""
echo " Useful Commands:"
if [ "$DEPLOY_METHOD" == "1" ]; then
    echo "  Restart: az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "  Scale: az appservice plan update --name $SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku P1V2"
    echo "  Delete: az webapp delete --name $APP_NAME --resource-group $RESOURCE_GROUP"
else
    echo "  Restart: az container restart --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "  Delete: az container delete --name $APP_NAME --resource-group $RESOURCE_GROUP --yes"
fi
echo ""
echo " Tips:"
echo "  - Enable Azure CDN for global content delivery"
echo "  - Setup Azure Front Door for load balancing"
echo "  - Configure auto-scaling rules"
echo "  - Enable Azure Backup for data protection"
echo ""
