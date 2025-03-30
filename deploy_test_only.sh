#!/bin/bash

# Deployment script for test API only

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
SERVICE_NAME="media-portal-test"
SERVICE_ACCOUNT="firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"

echo "Deploying test API to Cloud Run with the following settings:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo ""

# Copy service account JSON to credentials directory if it doesn't exist
if [ ! -d "./credentials" ]; then
  mkdir -p "./credentials"
fi

# Use the test Dockerfile
if [ -f "./Dockerfile.test" ]; then
  cp Dockerfile.test Dockerfile
  echo "Using test Dockerfile"
fi

# Build and deploy the service
echo "Building and deploying the test API service..."

# Deploy the test API
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account="$SERVICE_ACCOUNT" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

if [ $? -eq 0 ]; then
  echo "Test API deployment successful!"
  echo "Service URL: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app"
  echo "API URL: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/health"
  
  # Test the API
  echo "Testing the API..."
  curl -s "https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/health"
  echo ""
else
  echo "Test API deployment failed."
fi