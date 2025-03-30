#!/bin/bash
# Script to deploy the Firebase Cloud Function with corrected package structure

echo "Deploying Fixed Firebase Cloud Function..."

# Set up environment variables
export GOOGLE_APPLICATION_CREDENTIALS="credentials/legislativevideoreviewswithai-80ed70b021b5.json"
export GCS_BUCKET_NAME="legislativevideoreviewswithai.appspot.com"
export GOOGLE_CLOUD_PROJECT="legislativevideoreviewswithai"

# Check if firebase-tools is installed
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

# Navigate to functions directory
cd "$(dirname "$0")/functions"
echo "Working in $(pwd)"

# Ensure virtual environment is set up
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Deploy the function using Firebase CLI
echo "Deploying Cloud Function using Firebase CLI..."
firebase use legislativevideoreviewswithai
firebase deploy --only functions

# Deactivate the virtual environment
deactivate

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Cloud Function deployed successfully!"
    
    # Test the function
    echo "Testing the function..."
    FUNCTION_URL="https://us-central1-legislativevideoreviewswithai.cloudfunctions.net/media_portal_api"
    curl -s "$FUNCTION_URL/health" || echo "Function is not yet accessible. It may take a few minutes to fully deploy."
else
    echo "❌ Function deployment failed. Please check the logs above."
fi

echo "Deployment script completed."