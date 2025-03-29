#!/bin/bash

# Deploy just the diagnostic page to Firebase Hosting

# Set default project ID
PROJECT_ID="legislativevideoreviewswithai"

echo "Deploying diagnostic page to Firebase Hosting..."

# Ensure we're in the frontend directory
cd "$(dirname "$0")"

# Deploy only the diagnostic.html file to Firebase Hosting
firebase deploy --only hosting

if [ $? -eq 0 ]; then
  echo "\nDeployment successful!"
  echo "Diagnostic page URL: https://legislativevideoreviewswithai.web.app/diagnostic.html"
else
  echo "\nDeployment failed."
fi