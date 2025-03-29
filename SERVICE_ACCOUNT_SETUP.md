# Service Account Setup Guide

This guide explains how to set up the Firebase Admin SDK service account for the Idaho Legislature Media Portal.

## Option 1: Using the Automated Setup Script (Recommended)

We've created a script that automates the process of downloading and installing the service account key:

```bash
# Run the setup script
python scripts/setup_service_account.py
```

The script will:
1. Guide you to the Firebase console to download a new service account key
2. Install the key in the correct location
3. Set up environment variables for development
4. Test the authentication

## Option 2: Manual Setup

If you prefer to set up the service account manually, follow these steps:

### 1. Download the Service Account Key

1. Visit the [Firebase Console](https://console.firebase.google.com/project/legislativevideoreviewswithai/settings/serviceaccounts/adminsdk)
2. Select the "legislativevideoreviewswithai" project
3. Go to Project Settings > Service accounts
4. Click "Generate new private key"
5. Save the JSON file

### 2. Install the Service Account Key

1. Create a credentials directory if it doesn't exist:
   ```bash
   mkdir -p credentials
   ```

2. Copy the downloaded JSON file to the credentials directory:
   ```bash
   cp ~/Downloads/firebase-adminsdk-*.json credentials/legislativevideoreviewswithai-80ed70b021b5.json
   ```

### 3. Set Up Environment Variables

For local development, set the environment variable:

**On Mac/Linux:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/legislativevideoreviewswithai-80ed70b021b5.json"
```

**On Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$(Get-Location)\credentials\legislativevideoreviewswithai-80ed70b021b5.json"
```

### 4. Test Authentication

Test that authentication works:

```bash
python -c "from google.cloud import firestore; db = firestore.Client(); print('Firestore connection successful')"
```

## Cloud Deployment

When deploying to Cloud Run, use the service account directly:

```bash
gcloud run deploy media-portal-backend \
  --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com \
  ... other parameters ...
```

## Troubleshooting

If you encounter authentication issues:

1. **Invalid JWT Signature**: This means the private key doesn't match the service account email. Make sure you've downloaded a fresh key for the correct service account.

2. **Permission denied**: The service account exists but doesn't have the necessary permissions. Make sure it has:
   - `roles/datastore.user` for Firestore access
   - `roles/storage.admin` for Cloud Storage access

3. **File not found**: Make sure the path in GOOGLE_APPLICATION_CREDENTIALS points to a valid file.

4. **Environment variable not set**: Confirm the environment variable is set in your current shell:
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS  # Mac/Linux
   echo %GOOGLE_APPLICATION_CREDENTIALS% # Windows cmd
   echo $env:GOOGLE_APPLICATION_CREDENTIALS # Windows PowerShell
   ```