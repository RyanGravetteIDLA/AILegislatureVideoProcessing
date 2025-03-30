# Idaho Legislative Media Portal Frontend

This is the Vue.js frontend for the Idaho Legislative Media Portal, which provides access to legislative session videos, audio recordings, and transcripts.

## Configuration for Firebase Hosting

The frontend has been configured for deployment to Firebase Hosting with the following:

1. Environment Variables
   - Development: Using `http://localhost:5000/api` for local development
   - Production: Using Firebase Cloud Functions URL for API access

2. Firebase Configuration Files
   - `firebase.json` - Configures hosting settings with SPA rewrites
   - `.firebaserc` - Specifies the GCP project ID

3. Deployment Documentation
   - See `FIREBASE_DEPLOYMENT.md` for detailed deployment instructions

## Project Structure

- `src/` - Source code
  - `components/` - Vue components
  - `views/` - Page views
  - `stores/` - Pinia state management
  - `router/` - Vue Router configuration
  - `assets/` - Static assets

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Integration

The frontend connects to the Firebase Cloud Functions backend. It uses environment variables to determine the API endpoint:

- `VITE_API_URL` - Base URL for API requests
- `VITE_FILE_SERVER_URL` - URL for serving media files

The Pinia store (`src/stores/mediaStore.js`) handles all API requests and state management for media items.

## Deployment

Refer to `FIREBASE_DEPLOYMENT.md` for complete deployment instructions.
