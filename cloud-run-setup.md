# Google Cloud Run Deployment Guide

This guide outlines the steps to deploy the Idaho Legislature Media Portal to Google Cloud Run.

## Prerequisites

1. Google Cloud Platform account
2. Google Cloud SDK installed and configured
3. Docker installed
4. Service account with necessary permissions

## Setup Google Cloud Project

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

## Configure Environment Variables

1. Create environment variables in Secret Manager:

```bash
# Create secrets
gcloud secrets create api-env --data-file=.env
```

## Deploy API Service

1. Build and deploy the API service:

```bash
# Build the API container image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/legislature-api src/

# Deploy to Cloud Run
gcloud run deploy legislature-api \
  --image gcr.io/[PROJECT_ID]/legislature-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --set-secrets="/app/.env=api-env:latest" \
  --command="python" \
  --args="src/server.py,--api-only"
```

## Deploy File Server Service

1. Build and deploy the File Server service:

```bash
# Build the File Server container image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/legislature-files src/

# Deploy to Cloud Run
gcloud run deploy legislature-files \
  --image gcr.io/[PROJECT_ID]/legislature-files \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --set-secrets="/app/.env=api-env:latest" \
  --command="python" \
  --args="src/server.py,--file-only"
```

## Deploy Frontend

1. Build and deploy the Frontend:

```bash
# Update environment variables for production
cd frontend
echo "VITE_API_URL=https://legislature-api-[PROJECT_ID].run.app/api" > .env.production
echo "VITE_FILE_SERVER_URL=https://legislature-files-[PROJECT_ID].run.app/files" >> .env.production

# Build frontend
npm run build

# Build the Frontend container image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/legislature-frontend .

# Deploy to Cloud Run
gcloud run deploy legislature-frontend \
  --image gcr.io/[PROJECT_ID]/legislature-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

## Set Up Cloud Storage for Media Files

1. Create a Cloud Storage bucket for media files:

```bash
gsutil mb -l us-central1 gs://[PROJECT_ID]-legislature-media
```

2. Configure the bucket for public access (if applicable):

```bash
gsutil iam ch allUsers:objectViewer gs://[PROJECT_ID]-legislature-media
```

3. Update your `.env` file to use Cloud Storage instead of local files:

```
# Update this in the Secret Manager
MEDIA_STORAGE=gcs
GCS_BUCKET=[PROJECT_ID]-legislature-media
```

## Set Up Scheduled Jobs

1. Create a Cloud Scheduler job for regular updates:

```bash
gcloud scheduler jobs create http daily-transcript-updates \
  --schedule="0 2 * * *" \
  --uri="https://legislature-api-[PROJECT_ID].run.app/api/tasks/update-transcripts" \
  --http-method=POST \
  --oidc-service-account-email=[SERVICE_ACCOUNT_EMAIL]
```

## Monitoring and Logging

1. Set up Cloud Monitoring:

```bash
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

2. Set up alerts for service health:

```bash
gcloud alpha monitoring channels create --display-name="Admin Email" --type=email --config=email.address=[YOUR_EMAIL]
```

## Testing the Deployment

1. Test the API:
   - Visit `https://legislature-api-[PROJECT_ID].run.app/api/health`

2. Test the File Server:
   - Visit `https://legislature-files-[PROJECT_ID].run.app/health`

3. Test the Frontend:
   - Visit `https://legislature-frontend-[PROJECT_ID].run.app`

## Optimizing Costs

- Set concurrency and maximum instances to control scaling
- Configure memory and CPU appropriately for each service
- Use Cloud Storage lifecycle rules to manage old media files