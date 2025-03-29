# Cloud Function Deployment Guide

## Overview

This document describes the deployment of the Idaho Legislature Media Portal API using Google Cloud Functions instead of Cloud Run. We shifted to this approach after encountering persistent issues with container deployments.

## Architecture

- **Backend**: Google Cloud Function (Python 3.9, Flask)
- **Database**: Firebase Firestore
- **Storage**: Google Cloud Storage
- **Frontend**: Vue.js hosted on Firebase Hosting

## Deployment URLs

- **Frontend**: https://legislativevideoreviewswithai.web.app
- **API**: https://media-portal-api-6alz6huq6a-uw.a.run.app
- **Alternative API URL**: https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api
- **Diagnostic Page**: https://legislativevideoreviewswithai.web.app/diagnostic.html

## API Endpoints

- `/` or `/api` - Root endpoint with API information
- `/api/health` - Health check endpoint
- `/api/videos` - List of available videos
- More endpoints to be added (audio, transcripts, etc.)

## Deployment Process

### Backend (Cloud Function)

1. Create a `main.py` file with Flask-based API implementation
2. Create a `requirements.txt` file with necessary dependencies
3. Deploy using gcloud CLI:

```bash
gcloud functions deploy media-portal-api \
  --gen2 \
  --region=us-west1 \
  --runtime=python39 \
  --entry-point=api_handler \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256Mi \
  --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=legislativevideoreviewswithai
```

Or use the simplified deployment script:

```bash
./deploy_simple_function.sh
```

### Frontend

1. Update environment variables in `.env.production`:

```
VITE_API_URL=https://media-portal-api-6alz6huq6a-uw.a.run.app/api
VITE_FILE_SERVER_URL=https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app
```

2. Build and deploy to Firebase Hosting:

```bash
cd frontend
./deploy_to_firebase.sh
```

## Troubleshooting

If you encounter issues with the API connection:

1. Check the diagnostic page at https://legislativevideoreviewswithai.web.app/diagnostic.html
2. Verify that the API is running by visiting the health check endpoint
3. Check Cloud Function logs in the Google Cloud Console
4. Ensure CORS is properly configured for Firebase Hosting domains

## Why Cloud Functions Instead of Cloud Run?

We opted to use Cloud Functions instead of Cloud Run for several reasons:

1. **Simplicity**: Cloud Functions require less configuration and have fewer moving parts
2. **Startup Time**: Cloud Functions initialize faster than containerized applications
3. **Zero Maintenance**: No need to manage container images or deployment pipelines
4. **Cost Efficiency**: Cloud Functions only charge for actual execution time
5. **Troubleshooting**: Easier to diagnose and fix issues with Cloud Functions

## Future Improvements

1. Add additional API endpoints for audio and transcripts
2. Implement pagination and filtering for media listings
3. Add authentication for admin functions
4. Set up CI/CD for automatic deployments
5. Implement caching for frequent API requests