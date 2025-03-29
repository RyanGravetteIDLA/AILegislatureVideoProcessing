# Google Cloud Run Deployment Guide

This guide outlines the steps to deploy the Idaho Legislature Media Portal to Google Cloud Run.

## Prerequisites

1. Google Cloud Platform account
2. Google Cloud SDK installed and configured
3. Docker installed
4. Service account with necessary permissions

## Step 1: Setup Google Cloud Project

1. Create a new Google Cloud Project (or use an existing one):

```bash
gcloud projects create [PROJECT_ID] --name="Idaho Legislature Media Portal"
gcloud config set project [PROJECT_ID]
```

2. Enable required APIs:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Step 2: Configure Service Account

The application uses Firebase Admin SDK service account for authentication:

```bash
# If you haven't uploaded your service account key to the project
gcloud secrets create firebase-credentials --data-file=credentials/legislativevideoreviewswithai-80ed70b021b5.json

# Grant permissions to the service account
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

## Step 3: Deploy the backend to Cloud Run

Deploy the backend to Cloud Run:

```bash
gcloud run deploy media-portal-backend \
  --source . \
  --region=us-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
```

Note: The `--service-account` flag specifies which service account Cloud Run should use for authentication. This should match the service account email in your JSON credentials file.

## Step 4: Deploy Frontend to Firebase Hosting

1. Build and deploy the Frontend:

```bash
# Update environment variables for production
cd frontend
echo "VITE_API_URL=https://media-portal-backend-[PROJECT_ID].us-west1.run.app/api" > .env.production
echo "VITE_FILE_SERVER_URL=https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app" >> .env.production

# Build frontend
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

## Step 5: Set up environment variables

The Cloud Run service needs several environment variables configured in order to properly authenticate with Google Cloud services:

```bash
# Example values - replace with your actual values
gcloud run services update media-portal-backend \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=legislativevideoreviewswithai,GCS_BUCKET_NAME=legislativevideoreviewswithai.firebasestorage.app,USE_CLOUD_STORAGE=true,PREFER_CLOUD_STORAGE=true" \
  --region=us-west1
```

### Updating the Service Account

If you need to update the service account:

```bash
# Update environment variables with the correct service account email
gcloud run services update media-portal-backend \
  --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com \
  --region=us-west1
```

## Step 6: Set Up Cloud Storage for Media Files

By default, the application uses the Firebase Storage bucket associated with your project. You can verify the bucket name in the Firebase Console under Storage.

```bash
# If you need to create a custom bucket, use:
gsutil mb -l us-west1 gs://custom-bucket-name
```

## Step 7: Set Up Scheduled Jobs

1. Create a Cloud Scheduler job for daily ingestion:

```bash
gcloud scheduler jobs create http daily-media-ingestion \
  --schedule="0 4 * * *" \
  --uri="https://media-portal-backend-[PROJECT_ID].us-west1.run.app/api/admin/ingest" \
  --http-method=POST \
  --message-body='{"recent_only": true, "days": 1}' \
  --headers="Content-Type=application/json" \
  --time-zone="America/Boise"
```

## Testing the Deployment

1. Test the API:
   - Visit `https://media-portal-backend-[PROJECT_ID].us-west1.run.app/api/health`

2. Test the Frontend:
   - Visit your Firebase Hosting URL (`https://legislativevideoreviewswithai.web.app`)

## Local Testing

To test locally, make sure the environment variables are set:

```bash
# Use the script to set all required environment variables
source set_credentials.sh

# Start the server
python src/server.py
```