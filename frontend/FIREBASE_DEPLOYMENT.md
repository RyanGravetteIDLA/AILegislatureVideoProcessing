# Firebase Hosting Deployment Instructions

This document provides step-by-step instructions for deploying the Idaho Legislative Media Portal frontend to Firebase Hosting.

## Prerequisites

1. Install Firebase CLI:
   ```bash
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```bash
   firebase login
   ```

## Configuration Files

The necessary configuration files have already been created:

- `firebase.json` - Configures hosting settings including rewrites for SPA support
- `.firebaserc` - Specifies the Firebase project ID
- `.env.production` - Contains the production API URL pointing to Cloud Run backend

## Build and Deploy

1. Build the Vue.js app:
   ```bash
   npm run build
   ```

2. Deploy to Firebase Hosting:
   ```bash
   firebase deploy --only hosting
   ```

## Deployed URLs

Once deployed, your app will be available at the following URLs:

- Default Firebase Hosting domain: `https://legislativevideoreviewswithai.web.app`
- Firebase Hosting subdomain: `https://legislativevideoreviewswithai.firebaseapp.com`

## Custom Domain (Optional)

To set up a custom domain:

1. In the Firebase console, go to Hosting > Add custom domain
2. Follow the instructions to add your domain
3. Update your DNS records as directed by Firebase
4. Wait for DNS propagation and SSL certificate provisioning

## Post-Deployment Verification

After deployment, verify the following:

1. The application loads correctly
2. Navigation works properly (check router)
3. API connections are working with the Cloud Run backend
4. Media files can be accessed from Cloud Storage

## Backend CORS Configuration

Before deploying to Firebase Hosting, update the backend CORS configuration to only allow requests from Firebase domains:

1. Run the provided script to update the backend CORS configuration:
   ```bash
   cd frontend
   ./update_cors.py
   ```

2. Deploy the updated backend to Cloud Run (this will be done in Step 4 of the migration plan)

## Troubleshooting

- If you encounter CORS issues, ensure that your Cloud Run backend has the appropriate CORS headers
- For routing issues, check that the Firebase rewrites are correctly configured in firebase.json
- If media files are not loading, verify the `VITE_FILE_SERVER_URL` environment variable

## Updating the Deployment

To deploy updates:

1. Make your changes to the codebase
2. Rebuild the app: `npm run build`
3. Deploy to Firebase: `firebase deploy --only hosting`