# Deployment Instructions for Idaho Legislature Media Portal

This document provides step-by-step instructions for deploying the Idaho Legislature Media Portal, including both the microservices backend and the Vue.js frontend.

## Backend Deployment

The backend uses a microservices architecture deployed to Google Cloud Functions.

### Prerequisites

1. Google Cloud SDK installed and configured
2. Firebase CLI installed (for frontend deployment)
3. Node.js and npm installed
4. Python 3.10+ installed

### Step 1: Deploy the Microservices Backend

Run the provided deployment script to deploy the microservices to Google Cloud Functions:

```bash
chmod +x update_microservices.sh
./update_microservices.sh
```

This script will:
1. Create a deployment package with all required files
2. Deploy to Google Cloud Functions
3. Test all endpoints to verify correct operation

### Step 2: Verify Backend Deployment

Verify the deployment by testing the various endpoints:

```bash
export API_URL="https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/idaho-legislature-api"

# Test health endpoint
curl $API_URL/health | jq .

# Test videos endpoint
curl $API_URL/videos | jq .

# Test stats endpoint
curl $API_URL/stats | jq .

# Test filters endpoint
curl $API_URL/filters | jq .
```

## Frontend Deployment

The frontend is a Vue.js application that can be deployed to Firebase Hosting.

### Step 1: Configure Environment Variables

Update the `.env.production` file with the correct API endpoint:

```
VITE_API_URL=https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/idaho-legislature-api
VITE_FILE_SERVER_URL=https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com
```

### Step 2: Deploy to Firebase Hosting

Run the provided deployment script:

```bash
cd frontend
chmod +x deploy_to_firebase.sh
./deploy_to_firebase.sh
```

This script will:
1. Set up the production environment variables
2. Build the project for production
3. Initialize Firebase if needed
4. Deploy to Firebase Hosting

### Step 3: Verify Frontend Deployment

1. Open https://legislativevideoreviewswithai.web.app in your browser
2. Navigate to the diagnostic page at https://legislativevideoreviewswithai.web.app/diagnostic to verify all API connections are working

## Local Development

### Backend

To run the backend locally:

```bash
# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the local server
python run_server.py
```

### Frontend

To run the frontend locally:

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Troubleshooting

### Backend Issues

1. **Deployment Failures**:
   - Check the Cloud Function logs in the Google Cloud Console
   - Verify service account permissions

2. **API Connection Issues**:
   - Ensure CORS is properly configured
   - Check that the function URL is correct
   - Verify the function is publicly accessible

### Frontend Issues

1. **API Connection Problems**:
   - Use the diagnostic page to check API connections
   - Verify environment variables are correctly set
   - Check browser console for error messages

2. **Deployment Failures**:
   - Ensure Firebase CLI is authenticated
   - Verify the project ID is correct
   - Check that the build process completed successfully

## Monitoring and Maintenance

- **Backend Logs**: Monitor logs in Google Cloud Console
- **Frontend Analytics**: Set up Firebase Analytics for frontend monitoring
- **Automated Testing**: Consider implementing automated tests for continuous integration

For additional support, refer to the project documentation or contact the system administrator.