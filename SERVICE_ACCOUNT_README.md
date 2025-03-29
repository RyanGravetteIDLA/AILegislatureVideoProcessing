# Service Account Information

The application has been updated to use the Firebase Admin SDK service account for authentication:

- **Service Account Email**: firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
- **Credentials File**: credentials/legislativevideoreviewswithai-80ed70b021b5.json

## Running Locally

To run the application locally, use the provided script:

```bash
./start_local.sh
```

This script will:
1. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
2. Start the application server

## Manual Setup

If you prefer to set up manually:

```bash
# Set the credentials environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/legislativevideoreviewswithai-80ed70b021b5.json"

# Start the server
python src/server.py
```

## Cloud Run Deployment

When deploying to Cloud Run, use:

```bash
gcloud run deploy media-portal-backend \
  --source . \
  --region=us-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
```

For more detailed information, see the SERVICE_ACCOUNT_SETUP.md file.
