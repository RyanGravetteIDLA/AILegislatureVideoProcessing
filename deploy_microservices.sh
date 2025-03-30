#!/bin/bash

# Deploy microservices for Idaho Legislature Media Portal API

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
FUNCTION_NAME="media-portal-api"
SERVICE_ACCOUNT="firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"

echo "Deploying Cloud Function Microservices with the following settings:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Function Name: $FUNCTION_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo ""

# Clean up previous deployment if it exists
rm -rf deploy_cf
mkdir -p deploy_cf

# Create a flat structure for deployment
echo "Creating deployment structure..."
cp src/cloud_functions/main.py deploy_cf/
cp src/cloud_functions/requirements.txt deploy_cf/

# Create necessary directories
mkdir -p deploy_cf/services
mkdir -p deploy_cf/common
mkdir -p deploy_cf/models

# Copy files
cp src/cloud_functions/services/*.py deploy_cf/services/
cp src/cloud_functions/common/*.py deploy_cf/common/
cp src/cloud_functions/models/*.py deploy_cf/models/

# Create empty __init__.py files for Python packages
touch deploy_cf/__init__.py
touch deploy_cf/services/__init__.py
touch deploy_cf/common/__init__.py
touch deploy_cf/models/__init__.py

# Move to the deployment directory
cd deploy_cf

# Deploy the function
echo "Deploying Cloud Function..."

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --region=$REGION \
  --runtime=python39 \
  --entry-point=api_handler \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256Mi \
  --timeout=60s \
  --min-instances=0 \
  --max-instances=5 \
  --service-account=$SERVICE_ACCOUNT \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID

if [ $? -eq 0 ]; then
  echo "Function deployment successful!"
  
  # Get the function URL
  FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --gen2 --region=$REGION --format="value(serviceConfig.uri)")
  
  echo "Function URL: $FUNCTION_URL"
  echo "Health Check: $FUNCTION_URL/api/health"
  echo "Videos endpoint: $FUNCTION_URL/api/videos"
else
  echo "Function deployment failed."
fi

# Clean up
cd ..
rm -rf deploy_cf