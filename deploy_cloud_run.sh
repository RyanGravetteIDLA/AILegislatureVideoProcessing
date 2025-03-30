#!/bin/bash
# Script to build and deploy the backend to Cloud Run

# Configuration
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
SERVICE_NAME="media-portal-backend"
REPOSITORY="media-portal-repo"
IMAGE_NAME="media-backend"
IMAGE_TAG="v1"

# Full image path
IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Service account for Cloud Run
SERVICE_ACCOUNT="cloud-run-media-portal-service@${PROJECT_ID}.iam.gserviceaccount.com"

# Ensure the script exits on any error
set -e

echo "Starting deployment to Cloud Run..."
echo "Building Docker image: ${IMAGE_PATH}"

# Build the Docker image
docker build -t ${IMAGE_PATH} .

# Authenticate with Google Cloud
echo "Authenticating with Google Cloud..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Push the image to Artifact Registry
echo "Pushing Docker image to Artifact Registry..."
docker push ${IMAGE_PATH}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_PATH} \
  --platform managed \
  --region ${REGION} \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="GCS_BUCKET_NAME=${PROJECT_ID}.firebasestorage.app" \
  --set-env-vars="USE_CLOUD_STORAGE=true" \
  --set-env-vars="PREFER_CLOUD_STORAGE=true"

echo "Cloud Run deployment complete!"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"

# Check if the URL in .env.production needs to be updated
FRONTEND_ENV_FILE="./frontend/.env.production"
if [ -f "$FRONTEND_ENV_FILE" ]; then
    CURRENT_API_URL=$(grep "VITE_API_URL" "$FRONTEND_ENV_FILE" | cut -d'=' -f2)
    EXPECTED_API_URL="${SERVICE_URL}/api"
    
    if [ "$CURRENT_API_URL" != "$EXPECTED_API_URL" ]; then
        echo "WARNING: Frontend environment file has different API URL"
        echo "Current: $CURRENT_API_URL"
        echo "Expected: $EXPECTED_API_URL"
        echo ""
        echo "To update, edit $FRONTEND_ENV_FILE and change VITE_API_URL to: $EXPECTED_API_URL"
    else
        echo "Frontend environment file already has the correct API URL."
    fi
else
    echo "Frontend environment file not found at $FRONTEND_ENV_FILE"
fi