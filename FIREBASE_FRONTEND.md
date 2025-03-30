# Firebase Frontend Architecture

## Overview

The Idaho Legislative Media Portal frontend is a modern Single Page Application (SPA) built with Vue.js 3 and deployed to Firebase Hosting. This document outlines the frontend architecture, component organization, state management, routing, Firebase integration, and deployment process.

## Technology Stack

- **Framework**: Vue.js 3 (Composition API)
- **Build Tool**: Vite.js
- **State Management**: Pinia
- **Routing**: Vue Router
- **HTTP Client**: Axios
- **Hosting**: Firebase Hosting
- **CSS Framework**: Custom styling with utility classes

## Directory Structure

```
frontend/
├── public/              # Static files that are copied to dist directly
├── src/                 # Application source code
│   ├── assets/          # Static assets (images, icons, etc.)
│   │   ├── icons/       # Application icons
│   │   └── ...
│   ├── components/      # Reusable Vue components
│   │   ├── layout/      # Layout components
│   │   ├── media/       # Media-related components
│   │   └── ui/          # UI components
│   ├── router/          # Vue Router configuration
│   ├── stores/          # Pinia state management stores
│   ├── views/           # Page components
│   ├── App.vue          # Root component
│   ├── main.js          # Application entry point
│   └── style.css        # Global CSS styles
├── .env                 # Environment variables for development
├── .env.production      # Environment variables for production
├── .firebaserc          # Firebase project configuration
├── firebase.json        # Firebase hosting configuration
├── index.html           # HTML entry point
├── package.json         # Dependencies and scripts
├── vite.config.js       # Vite configuration
└── deploy_to_firebase.sh # Deployment script
```

## Application Entry Point

The main entry point (`main.js`) initializes the Vue application with router and state management:

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

## Component Organization

The application follows a hierarchical component structure:

### Layout Components

Layout components provide the overall structure of the application:

```
/components/layout/
├── AppHeader.vue   # Global navigation header
├── AppFooter.vue   # Global footer
└── AppLayout.vue   # Main layout wrapper
```

The `AppLayout.vue` component serves as a wrapper for all pages:

```vue
<template>
  <div class="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
    <AppHeader />
    
    <main id="main-content" class="flex-grow" role="main">
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <!-- Page content -->
        <slot></slot>
      </div>
    </main>
    
    <AppFooter />
  </div>
</template>
```

### View Components

View components represent different pages of the application:

```
/views/
├── Home.vue       # Landing page with statistics and quick access
├── Videos.vue     # Main media browsing page
└── Admin.vue      # Admin dashboard (placeholder)
```

## Routing

The application uses Vue Router for client-side routing:

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { title: 'Idaho Legislature Media Portal' }
  },
  {
    path: '/videos',
    name: 'videos',
    component: () => import('../views/Videos.vue'),
    meta: { title: 'Legislative Media' }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/Admin.vue'),
    meta: { title: 'Admin Dashboard', requiresAuth: true }
  },
  // Catch-all route for 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: Home,
    meta: { title: 'Page Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards for title updates and authentication
router.beforeEach((to, from, next) => {
  // Set document title
  document.title = `${to.meta.title || 'Home'} | Idaho Legislature Media`
  
  // Handle auth-required routes (placeholder for future implementation)
  if (to.meta.requiresAuth) {
    next()
  } else {
    next()
  }
})
```

Key features of the routing implementation:
- Clean URLs with HTML5 history mode
- Route-based code splitting for improved performance
- Page title management
- Scrolling behavior customization
- Authentication guards (placeholder for future implementation)

## State Management

The application uses Pinia for state management, with `mediaStore.js` as the primary store:

```javascript
// stores/mediaStore.js
import { defineStore } from 'pinia'
import axios from 'axios'

// Define the API base URL with fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Create an axios instance with common configuration
const api = axios.create({
  baseURL: NORMALIZED_API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Define the store
export const useMediaStore = defineStore('media', {
  state: () => ({
    videos: [],
    audio: [],
    transcripts: [],
    loading: false,
    error: null,
    // ... other state properties
  }),
  
  getters: {
    // Computed properties for derived data
  },
  
  actions: {
    // Async actions for API requests
    async fetchVideos() { /* ... */ },
    async fetchAudio() { /* ... */ },
    async fetchTranscripts() { /* ... */ },
    // ... other actions
  }
})
```

The store provides:
- Centralized state management for media items
- Asynchronous data fetching from the API
- Error handling and loading states
- Caching for performance optimization

## API Integration

The application connects to the Firebase Cloud Functions backend through environment variables:

```javascript
// In production (.env.production)
VITE_API_URL=https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api
VITE_FILE_SERVER_URL=https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com

// In development (.env)
VITE_API_URL=http://localhost:5000/api
VITE_FILE_SERVER_URL=http://localhost:5001
```

Axios is used for API communication with features like:
- Request/response interceptors for logging and error handling
- Timeout configuration for slow connections
- Base URL normalization
- URL transformation for correct file paths

## Firebase Integration

### Firebase Hosting Configuration

The `firebase.json` configuration file defines how the application is served:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=86400"
          }
        ]
      },
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      },
      {
        "source": "/",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "no-cache, no-store, must-revalidate"
          }
        ]
      }
    ],
    "trailingSlash": false,
    "cleanUrls": true,
    "frameworksBackend": {
      "region": "us-west1"
    }
  }
}
```

Key features of the Firebase hosting configuration:
- SPA routing with HTML5 history mode support
- Optimized caching policies for different file types
- Security headers for protection
- Clean URLs without trailing slashes
- Region configuration (us-west1)

### Firebase Project Configuration

The `.firebaserc` file specifies the Firebase project:

```json
{
  "projects": {
    "default": "legislativevideoreviewswithai"
  }
}
```

## Deployment Process

The application uses an automated deployment script (`deploy_to_firebase.sh`):

```bash
#!/bin/bash
# Deploy the frontend to Firebase Hosting

# Set environment variables for production
echo "Setting up production environment..."
cat > .env.production << EOL
VITE_API_URL=https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api
VITE_FILE_SERVER_URL=https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com
EOL

# Check if firebase-tools is installed
if ! command -v firebase &> /dev/null; then
    echo "Installing firebase-tools..."
    npm install -g firebase-tools
fi

# Build the project for production
echo "Building project for production..."
npm run build

# Initialize Firebase if not already initialized
if [ ! -f .firebaserc ]; then
    echo "Initializing Firebase..."
    firebase init hosting
    # ... create configuration files
fi

# Deploy to Firebase
echo "Deploying to Firebase..."
firebase deploy --only hosting

echo "Deployment complete!"
echo "Your application is live at: https://legislativevideoreviewswithai.web.app"
```

The deployment process:
1. Sets production environment variables
2. Installs Firebase tools if needed
3. Builds the production application with Vite
4. Initializes Firebase configuration if needed
5. Deploys to Firebase Hosting
6. Provides a confirmation message with the live URL

## Media Handling

The application handles multiple types of media:

### Media Types

- **Videos**: Legislative session videos in MP4 format
- **Audio**: Extracted audio from videos in MP3 format
- **Transcripts**: Text transcriptions of audio in TXT format

### Relationship Management

The application maintains relationships between media types:
- Each video can have related audio and transcript
- Each audio file can have related video and transcript
- Each transcript can have related video and audio

### URL Handling

The application normalizes URLs for different environments:

```javascript
// Helper function to ensure URLs are complete
const ensureCompleteUrl = (url) => {
  if (!url) return url
  
  // If the URL is already absolute, return it as is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  // If the URL starts with /api/files/, prefix it with the file server URL
  if (url.startsWith('/api/files/')) {
    const path = url.replace(/^\/api/, '')
    return `${FILE_SERVER_URL}${path}`
  }
  
  // Return the URL as is in other cases
  return url
}
```

## Performance Optimization

The application implements several performance optimizations:

1. **Route-based Code Splitting**: Components are loaded on demand
   ```javascript
   component: () => import('../views/Videos.vue')
   ```

2. **Cache Control Headers**: Different cache policies for different file types
   ```
   JS/CSS: 1 day (86400 seconds)
   Images: 1 year (31536000 seconds)
   HTML: No cache
   ```

3. **Lazy Loading of Components**: Components are loaded only when needed

4. **API Response Caching**: Responses are cached in the store

## User Interface Components

The application provides a modern user interface with:

- Responsive design for desktop and mobile
- Accessible navigation with keyboard support
- Dark mode support with CSS variables
- Loading and error states for better user experience

## Future Enhancements

The frontend architecture includes placeholders for future enhancements:

1. **Authentication**: The routing setup includes authentication guards
   ```javascript
   if (to.meta.requiresAuth) {
     // Authentication logic to be implemented
   }
   ```

2. **Admin Section**: Basic admin view is already in place

3. **Analytics Integration**: Comments in the code indicate where analytics tracking can be added
   ```javascript
   // Add analytics tracking here if needed
   console.log(`Route changed: ${from.path} → ${to.path}`)
   ```

## Conclusion

The Idaho Legislative Media Portal frontend employs a modern architecture with Vue.js 3 and Firebase Hosting. Its organization into components, views, and stores follows best practices for maintainability and scalability. The integration with Firebase Cloud Functions and Firebase Storage creates a cohesive ecosystem for serving media content.

The application is designed for easy deployment and maintenance, with automated scripts and careful configuration. It provides a user-friendly interface for accessing legislative media content while maintaining performance and accessibility.

---

## Additional Resources

- [Vue.js Documentation](https://vuejs.org/)
- [Firebase Hosting Documentation](https://firebase.google.com/docs/hosting)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue Router Documentation](https://router.vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)