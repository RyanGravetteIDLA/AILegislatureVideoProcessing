#!/bin/bash
# Script to deploy Firebase Cloud Functions with proper environment setup

echo "Deploying Firebase Cloud Functions..."

# Set up environment
export GOOGLE_APPLICATION_CREDENTIALS="credentials/legislativevideoreviewswithai-80ed70b021b5.json"
export GCS_BUCKET_NAME="legislativevideoreviewswithai.appspot.com"
export GOOGLE_CLOUD_PROJECT="legislativevideoreviewswithai"

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "Firebase CLI not found. Please install it with 'npm install -g firebase-tools'."
    exit 1
fi

# Check if user is logged in
LOGGED_IN=$(firebase projects:list 2>&1 | grep -c "legislativevideoreviewswithai")
if [ $LOGGED_IN -eq 0 ]; then
    echo "You need to login to Firebase first. Run 'firebase login'."
    firebase login
fi

# Deploy functions with error handling
echo "Deploying functions to project: $GOOGLE_CLOUD_PROJECT"
firebase use $GOOGLE_CLOUD_PROJECT

# Deploy functions with increased timeout
echo "Deploying functions with increased timeout..."
firebase deploy --only functions --project $GOOGLE_CLOUD_PROJECT --debug

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Functions deployed successfully!"
else
    echo "❌ Function deployment failed. Please check the logs above."
    echo "You may need to deploy from the Firebase console or Google Cloud console."
fi

echo "Deployment script completed."