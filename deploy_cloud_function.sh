#!/bin/bash
# Script to deploy the Firebase Cloud Function with corrected package structure

echo "Deploying Fixed Firebase Cloud Function..."

# Set up environment variables
export GOOGLE_APPLICATION_CREDENTIALS="credentials/legislativevideoreviewswithai-80ed70b021b5.json"
export GCS_BUCKET_NAME="legislativevideoreviewswithai.appspot.com"
export GOOGLE_CLOUD_PROJECT="legislativevideoreviewswithai"

# Navigate to functions directory
cd "$(dirname "$0")/functions"
echo "Working in $(pwd)"

# Deploy the function using gcloud for more control
echo "Deploying Cloud Function using gcloud..."
gcloud functions deploy media_portal_api \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=media_portal_api \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256MB \
  --project=$GOOGLE_CLOUD_PROJECT

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Cloud Function deployed successfully!"
    
    # Get the function URL
    FUNCTION_URL=$(gcloud functions describe media_portal_api --gen2 --region=us-central1 --format="value(serviceConfig.uri)")
    echo "Function URL: $FUNCTION_URL"
    
    # Test the function
    echo "Testing the function..."
    curl -s "$FUNCTION_URL/health" | jq .
else
    echo "❌ Function deployment failed. Please check the logs above."
fi

echo "Deployment script completed."