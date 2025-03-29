# Deploying the Updated Backend without Docker

Since you're running in a VM that has challenges with Docker, here are alternative methods to deploy your updated backend to Cloud Run:

## Option 1: Deploy Directly with Google Cloud CLI

You can deploy directly using `gcloud` without Docker by using Cloud Build to build the container:

```bash
# Navigate to the project directory
cd /Users/ryangravette/pullLegislature/PullLegislature2

# Make sure you are authenticated
gcloud auth login

# Deploy directly from source
gcloud run deploy media-portal-backend \
  --source . \
  --region=us-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account=cloud-run-media-portal-service@legislativevideoreviewswithai.iam.gserviceaccount.com
```

## Option 2: Use Google Cloud Shell

If the direct deployment doesn't work, you can use Google Cloud Shell:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click on the Cloud Shell icon (>_) in the top right corner
3. In Cloud Shell, clone your repository or upload the files
4. Then run the deployment command:

```bash
# Clone repository (if needed)
git clone https://github.com/yourusername/your-repo.git

# Navigate to the project directory
cd your-repo

# Or upload the files using the Cloud Shell Upload feature

# Then deploy
gcloud run deploy media-portal-backend \
  --source . \
  --region=us-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account=cloud-run-media-portal-service@legislativevideoreviewswithai.iam.gserviceaccount.com
```

## Option 3: Continuous Deployment with Cloud Build

Set up continuous deployment with Cloud Build:

1. Go to [Cloud Build](https://console.cloud.google.com/cloud-build)
2. Connect your repository
3. Create a build trigger
4. Configure it to deploy to Cloud Run

## What's Been Fixed

The updated backend now correctly formats URLs for media files:

1. Previously, the API was returning only the Cloud Storage path (e.g., `videos/2023/house/video1.mp4`)
2. Now it returns a fully-formed URL (e.g., `https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/2023/house/video1.mp4`)

This should fix the videos page by ensuring that all media URLs are properly formatted for direct access.

## Testing After Deployment

Once deployed, verify the fix by:

1. Accessing the diagnostic page: https://legislativevideoreviewswithai.web.app/diagnostic.html
2. Testing the Videos API endpoint
3. Checking that the URLs in the response include the full Cloud Storage URL
4. Testing the videos page on the frontend

## Need More Help?

If you're still experiencing issues after deploying the updated backend, check the Cloud Run logs for any errors and make sure the service account has the proper permissions to access Cloud Storage.