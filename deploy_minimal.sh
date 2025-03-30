#!/bin/bash

# Ultra-minimal deployment script for Cloud Run

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
SERVICE_NAME="minimal-api"
SERVICE_ACCOUNT="firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"

echo "Deploying minimal API to Cloud Run with the following settings:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo ""

# Use the minimal Dockerfile
if [ -f "./Dockerfile.minimal" ]; then
  cp Dockerfile.minimal Dockerfile
  echo "Using minimal Flask Dockerfile"
fi

# Build and deploy the service using Google Cloud Build
echo "Building and deploying the minimal API..."

# Deploy using Cloud Build and Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

if [ $? -eq 0 ]; then
  echo "Container build successful! Deploying to Cloud Run..."
  
  gcloud run deploy "$SERVICE_NAME" \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --service-account="$SERVICE_ACCOUNT" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
  
  if [ $? -eq 0 ]; then
    echo "Minimal API deployment successful!"
    echo "Service URL: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app"
    
    # Test the API
    echo "Testing the API..."
    curl -s "https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/health"
    echo ""
  else
    echo "Minimal API deployment failed."
  fi
else
  echo "Container build failed."
fi