#!/bin/bash

# Try to find the credentials file in multiple locations
CREDENTIALS_PATHS=(
  "/Users/ryangravette/pullLegislature/PullLegislature2/credentials/legislativevideoreviewswithai-80ed70b021b5.json"
  "/Users/ryangravette/Downloads/legislativevideoreviewswithai-firebase-adminsdk-fbsvc-f12bbdca43.json"
)

# Find the first available credentials file
for path in "${CREDENTIALS_PATHS[@]}"; do
  if [ -f "$path" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="$path"
    echo "Environment variable GOOGLE_APPLICATION_CREDENTIALS is set to $GOOGLE_APPLICATION_CREDENTIALS"
    break
  fi
done

# Check if credentials were found
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "ERROR: No credentials file found. Please make sure one of these files exists:"
  for path in "${CREDENTIALS_PATHS[@]}"; do
    echo "  - $path"
  done
  echo "You can download a new credentials file from the Firebase console."
fi

# Set environment variables for cloud storage
export GCS_BUCKET_NAME="legislativevideoreviewswithai.firebasestorage.app"
export USE_CLOUD_STORAGE="true"
export PREFER_CLOUD_STORAGE="true"
export GOOGLE_CLOUD_PROJECT="legislativevideoreviewswithai"

echo "Environment variables for cloud services set:"
echo "  - GCS_BUCKET_NAME=$GCS_BUCKET_NAME"
echo "  - USE_CLOUD_STORAGE=$USE_CLOUD_STORAGE"
echo "  - PREFER_CLOUD_STORAGE=$PREFER_CLOUD_STORAGE"
echo "  - GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"