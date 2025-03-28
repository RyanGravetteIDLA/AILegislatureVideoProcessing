# Claude.md - Configuration and Information File

## Service Accounts

The application uses the following service account for Firebase/Firestore authentication:

- Project ID: legislativevideoreviewswithai
- Service Account: firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
- Credentials File: credentials/legislativevideoreviewswithai-80ed70b021b5.json

## Environment Variables

Key environment variables used by the application:

- GOOGLE_CLOUD_PROJECT: legislativevideoreviewswithai
- GOOGLE_APPLICATION_CREDENTIALS: path to the service account JSON file
- GCS_BUCKET_NAME: Default bucket for Cloud Storage
- USE_CLOUD_STORAGE: Whether to use Cloud Storage (true/false)
- PREFER_CLOUD_STORAGE: Whether to prefer Cloud Storage over local storage (true/false)

## Deployment Commands

Use these commands when deploying to Cloud Run:

```bash
# Deploy to Cloud Run with the correct service account
gcloud run deploy media-portal-backend \
  --source . \
  --region=us-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
```

## Local Testing

To test locally, make sure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials/legislativevideoreviewswithai-80ed70b021b5.json"
```

## Troubleshooting Authentication Issues

If you're experiencing authentication issues with Google Cloud services:

1. Check that your service account email in the JSON file matches the actual service account in GCP
2. Verify the service account has the proper IAM roles:
   - roles/datastore.user for Firestore
   - roles/storage.admin for Cloud Storage
3. Make sure GOOGLE_APPLICATION_CREDENTIALS points to the correct JSON file
4. When deployed to Cloud Run, ensure the service account is correctly specified with the --service-account flag