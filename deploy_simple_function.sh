#!/bin/bash

# Deploy a minimal Cloud Function for Idaho Legislature Media Portal API

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
FUNCTION_NAME="media-portal-api"
SERVICE_ACCOUNT="firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"

echo "Deploying Minimal Cloud Function with the following settings:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Function Name: $FUNCTION_NAME"
echo "  Service Account: $SERVICE_ACCOUNT"
echo ""

# Create a temporary directory for minimal deployment
mkdir -p temp_function
cp main.py temp_function/
cp requirements.txt temp_function/

# Move to the temporary directory for deployment
cd temp_function

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
  
  # Test the function
  echo "Testing the function..."
  curl -s "$FUNCTION_URL/api/health"
  echo ""
else
  echo "Function deployment failed."
fi

# Clean up
cd ..
rm -rf temp_function