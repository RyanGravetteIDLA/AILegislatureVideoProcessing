#!/bin/bash

# Deployment script for Cloud Run with Firebase Admin SDK service account

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
SERVICE_NAME="media-portal-backend"
SERVICE_ACCOUNT="firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"

echo "Deploying to Cloud Run with the following settings:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo ""

# Copy service account JSON to credentials directory if it doesn't exist
if [ ! -d "./credentials" ]; then
  mkdir -p "./credentials"
fi

if [ ! -f "./credentials/legislativevideoreviewswithai-80ed70b021b5.json" ] && [ -f "/Users/ryangravette/Downloads/legislativevideoreviewswithai-firebase-adminsdk-fbsvc-f12bbdca43.json" ]; then
  echo "Copying service account JSON to credentials directory..."
  cp "/Users/ryangravette/Downloads/legislativevideoreviewswithai-firebase-adminsdk-fbsvc-f12bbdca43.json" "./credentials/legislativevideoreviewswithai-80ed70b021b5.json"
fi

# Build and deploy the service
echo "Building and deploying the test API service..."

# Deploy the simplified test API first
gcloud run deploy "media-portal-test" \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account="$SERVICE_ACCOUNT" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

if [ $? -eq 0 ]; then
  echo "Test API deployment successful! Now deploying the main service..."
  
  # Restore the original Dockerfile for the main deployment
  # We need to back up our current test Dockerfile first
  mv Dockerfile Dockerfile.test.bak
  
  # Create a minimal but functional main API Dockerfile
  cat > Dockerfile << EOF
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY src/ ./src/
COPY credentials/ ./credentials/

# Create necessary directories
RUN mkdir -p data/logs data/temp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV GOOGLE_CLOUD_PROJECT=legislativevideoreviewswithai
ENV GCS_BUCKET_NAME=legislativevideoreviewswithai.firebasestorage.app
ENV USE_CLOUD_STORAGE=true
ENV PREFER_CLOUD_STORAGE=true

# Expose the port for Cloud Run
EXPOSE 8080

# Command to run when container starts
CMD ["uvicorn", "src.api_firestore:app", "--host", "0.0.0.0", "--port", "\${PORT:-8080}"]
EOF

  # Deploy the main API service
  gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --service-account="$SERVICE_ACCOUNT" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCS_BUCKET_NAME=legislativevideoreviewswithai.firebasestorage.app,USE_CLOUD_STORAGE=true,PREFER_CLOUD_STORAGE=true"
else
  echo "Test API deployment failed. Fix issues before deploying the main service."
fi

if [ $? -eq 0 ]; then
  echo "\nDeployment successful!"
  echo "Service URL: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app"
  echo "API URL: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api"
  echo "Health check: https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/health"
else
  echo "\nDeployment failed."
fi