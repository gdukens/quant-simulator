#!/bin/bash
# GCP Deployment Script for QuantLib Pro
# Deploys to Google Cloud Run

set -e

echo "🚀 QuantLib Pro - GCP Deployment Script"
echo "========================================"

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-quantlib-pro}"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
MIN_INSTANCES="${MIN_INSTANCES:-1}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"
MEMORY="${MEMORY:-4Gi}"
CPU="${CPU:-2}"
TIMEOUT="${TIMEOUT:-300}"

# Check gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "❌ GCP_PROJECT_ID environment variable not set"
    echo "   Set it with: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Memory: $MEMORY"
echo "  CPU: $CPU"
echo ""

# Step 1: Set project
echo "🔧 Step 1: Setting up GCP project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo ""
echo "🔌 Step 2: Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project=$PROJECT_ID

echo "✅ APIs enabled"

# Step 3: Build Docker image using Cloud Build
echo ""
echo "🐳 Step 3: Building Docker image with Cloud Build..."
gcloud builds submit \
    --tag $IMAGE_NAME \
    --project=$PROJECT_ID \
    --timeout=20m

echo "✅ Image built and pushed to GCR"

# Step 4: Deploy to Cloud Run
echo ""
echo "🚢 Step 4: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --timeout $TIMEOUT \
    --min-instances $MIN_INSTANCES \
    --max-instances $MAX_INSTANCES \
    --port 8501 \
    --set-env-vars "APP_ENV=production,STREAMLIT_SERVER_PORT=8501" \
    --project=$PROJECT_ID

echo "✅ Service deployed"

# Step 5: Get service URL
echo ""
echo "🌐 Step 5: Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' \
    --project=$PROJECT_ID)

# Step 6: Setup custom domain (optional)
echo ""
echo "🔧 Optional: Custom Domain Setup"
echo "  To map a custom domain, run:"
echo "  gcloud run domain-mappings create --service $SERVICE_NAME --domain YOUR-DOMAIN.com --region $REGION"
echo ""

# Step 7: Setup Cloud SQL (optional)
echo "💾 Optional: Cloud SQL Setup"
echo "  To create a Cloud SQL instance for persistent storage:"
echo "  gcloud sql instances create quantlib-db --tier=db-f1-micro --region=$REGION"
echo ""

# Step 8: Health check
echo "🏥 Step 8: Running health check..."
sleep 10
if curl -f -s "${SERVICE_URL}/_stcore/health" > /dev/null; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed, but deployment completed"
fi

echo ""
echo "✅ Deployment Complete!"
echo "========================================"
echo "🌐 Application URL: $SERVICE_URL"
echo ""
echo "📊 Monitoring:"
echo "  Logs: gcloud run logs tail $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo "  Metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs: gcloud run logs tail $SERVICE_NAME --follow --region=$REGION"
echo "  Update service: gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --region=$REGION"
echo "  Scale service: gcloud run services update $SERVICE_NAME --max-instances 20 --region=$REGION"
echo "  Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo ""
echo "💡 Tips:"
echo "  - Enable VPC connector for private network access"
echo "  - Setup Cloud Armor for DDoS protection"
echo "  - Use Cloud CDN for static content caching"
echo "  - Configure Cloud Monitoring alerts"
echo ""
