# Frontend Microservices Integration

This document details the updates made to the frontend to integrate with the new microservices API architecture.

## Overview

The frontend has been updated to work with the new microservices architecture, which provides a more modular and maintainable backend. The key endpoints used by the frontend are:

- `/api` - General API information
- `/api/health` - Health check endpoint
- `/api/videos` - Access to video content
- `/api/audio` - Access to audio content
- `/api/transcripts` - Access to transcript content
- `/api/stats` - Statistics about media collections
- `/api/filters` - Filter options for years and categories

## Changes Made

### 1. Media Store Updates

The `mediaStore.js` file has been updated to:

- Fetch filter options from the central `/api/filters` endpoint
- Improve error handling for API requests
- Enhanced fallback to mock data when API is unavailable
- Added better logging for debugging API interactions
- Improved ID handling in `getItemById` to handle both string and numeric IDs

### 2. Home Page Updates

The Home page (`Home.vue`) has been updated to:

- Use the `/api/stats` endpoint to display accurate media counts
- Improve error handling and fallback to mock data
- Add better API URL normalization

### 3. Diagnostic Page 

A new diagnostic page has been added at `/diagnostic` to:

- Test connectivity with all API endpoints
- Display response data from each endpoint
- Show real-time status of API connections
- Help diagnose any integration issues

### 4. Navigation Updates

The AppFooter component has been updated to include a link to the new diagnostic page.

## API Integration Details

### Filter Options

The frontend now fetches available years and categories from the `/api/filters` endpoint, ensuring consistent filtering across all media types.

```javascript
// Example of fetching filter options
const filtersResponse = await api.get('/filters', { timeout: 10000 })
if (filtersResponse.data && filtersResponse.data.years && filtersResponse.data.categories) {
  this.years = filtersResponse.data.years
  this.categories = filtersResponse.data.categories
}
```

### Statistics

The homepage now uses the `/api/stats` endpoint to show accurate counts of videos, audio files, and transcripts.

```javascript
// Example of fetching statistics
const response = await axiosInstance.get('/stats')
if (response.data) {
  stats.value = response.data
}
```

### Media Fetching

All media fetching functions have been updated to work with the new API structure, with improved error handling and fallback mechanisms.

```javascript
// Example of fetching videos
const response = await api.get('/videos', { timeout: 15000 })
if (response.data && Array.isArray(response.data)) {
  this.videos = response.data
}
```

## Testing

The new diagnostic page provides a comprehensive way to test all API endpoints. It should be used when:

1. Deploying to a new environment
2. After making changes to the backend API
3. Troubleshooting connectivity issues
4. Verifying that all services are operational

To access the diagnostic page, navigate to `/diagnostic` in the browser.

## Future Improvements

1. Add pagination support for large collections
2. Implement caching for frequently accessed data
3. Add advanced filtering and search capabilities
4. Support for related media lookup (e.g., finding transcripts related to a video)
5. Implement real-time updates through WebSockets or polling