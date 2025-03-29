#!/bin/bash

# Ultra-simple deployment script for Cloud Run

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
SERVICE_NAME="media-portal-simple"
SERVICE_ACCOUNT="firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"

echo "Deploying simple test server to Cloud Run with the following settings:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo ""

# Use the simple Dockerfile
if [ -f "./Dockerfile.simple" ]; then
  cp Dockerfile.simple Dockerfile
  echo "Using simple Flask Dockerfile"
fi

# Build and deploy the service
echo "Building and deploying the simple server..."

# Deploy the simple server
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --service-account="$SERVICE_ACCOUNT"

if [ $? -eq 0 ]; then
  echo "Simple server deployment successful!"
  echo "Service URL: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app"
  echo "Health check: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/health"
  
  # Test the API
  echo "Testing the server..."
  curl -s "https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/health"
  echo ""
else
  echo "Simple server deployment failed."
fi