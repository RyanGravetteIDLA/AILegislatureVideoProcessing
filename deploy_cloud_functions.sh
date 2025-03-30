#!/bin/bash
# Script to deploy the cloud functions backend

echo "Deploying the Cloud Functions backend..."

# Set project ID and location
PROJECT_ID="legislativevideoreviewswithai"
REGION="us-west1"
FUNCTION_NAME="idaho-legislature-api"
ENTRY_POINT="api_handler"
SOURCE_DIR="/Users/ryangravette/pullLegislature/PullLegislature2/src/cloud_functions"

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy the cloud_functions directory content to the temp directory
if [ -d "$SOURCE_DIR" ]; then
    echo "Copying files from $SOURCE_DIR to $TEMP_DIR"
    cp -r "$SOURCE_DIR"/* "$TEMP_DIR"
    
    # Verify main.py exists
    if [ ! -f "$TEMP_DIR/main.py" ]; then
        echo "ERROR: main.py not found in source directory"
        ls -la "$SOURCE_DIR"
        exit 1
    fi
else
    echo "Source directory not found: $SOURCE_DIR"
    exit 1
fi

# Create requirements.txt
cat > "$TEMP_DIR/requirements.txt" << EOL
firebase-admin==6.2.0
google-cloud-firestore==2.11.1
google-cloud-storage==2.9.0
flask==2.3.3
Flask-Cors==4.0.0
requests==2.31.0
EOL

echo "Deploying from $TEMP_DIR to Cloud Functions..."

# Deploy the function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python310 \
  --region=$REGION \
  --source="$TEMP_DIR" \
  --entry-point=$ENTRY_POINT \
  --trigger-http \
  --allow-unauthenticated \
  --project=$PROJECT_ID

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Deployment complete!"

# Test the deployment
echo "Testing the deployed function..."
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(url)")
echo "Function URL: $FUNCTION_URL"

echo "Testing audio endpoint..."
curl -s $FUNCTION_URL/audio | head -30

echo "Testing transcripts endpoint..."
curl -s $FUNCTION_URL/transcripts | head -30