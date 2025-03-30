# Firebase Cloud Functions API Architecture

## Overview

The Idaho Legislative Media Portal's API is implemented using Firebase Cloud Functions, providing a serverless architecture that scales automatically based on demand. This document outlines the Cloud Functions implementation, including its architecture, API endpoints, code organization, and integration with Firestore.

The API serves as the backend for the Idaho Legislative Media Portal, providing access to videos, audio recordings, and transcripts of legislative sessions. It follows RESTful principles and uses a microservices pattern to organize different aspects of functionality.

## Architecture

### Serverless Implementation

The API is implemented as a single Cloud Function (`api_handler`) that routes requests to specialized services based on the URL path. This approach offers several benefits:

1. **Simplified Deployment**: Single function deployment with automatic routing
2. **Efficient Resource Usage**: On-demand execution with automatic scaling
3. **Reduced Maintenance**: No server infrastructure to maintain
4. **Cost-Effective**: Pay only for actual usage

### Architecture Layers

The implementation follows a layered architecture:

1. **Entry Point**: `main.py` with `api_handler` function
2. **Gateway**: `gateway_service.py` for request routing
3. **Services**: Specialized services for different resource types
4. **Models**: Type-specific data models
5. **Database Access**: Firestore database interface

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────┐
│ api_handler │────►│ gateway_service  │────►│ resource_service │────►│  Firestore │
└─────────────┘     └──────────────────┘     └─────────────────┘     └────────────┘
                           │                        │
                           ▼                        ▼
                    ┌──────────────┐        ┌───────────────┐
                    │ common utils │        │ data models   │
                    └──────────────┘        └───────────────┘
```

## API Endpoints

### Root and Health Endpoints

- **API Info**: `GET /api` or `GET /`
  - Returns information about the API and available endpoints
  - Implementation: `gateway_service.py`

- **Health Check**: `GET /api/health`
  - Checks if the API is operational
  - Implementation: `health_service.py`

### Media Endpoints

- **Videos**
  - `GET /api/videos` - List all videos with optional filtering
  - `GET /api/videos/{id}` - Get a specific video by ID
  - `GET /api/videos/{id}/transcripts` - Get transcripts related to a video
  - Implementation: `video_service.py`

- **Audio**
  - `GET /api/audio` - List all audio files with optional filtering
  - `GET /api/audio/{id}` - Get a specific audio file by ID
  - `GET /api/audio/{id}/transcripts` - Get transcripts related to an audio file
  - Implementation: `audio_service.py`

- **Transcripts**
  - `GET /api/transcripts` - List all transcripts with optional filtering
  - `GET /api/transcripts/{id}` - Get a specific transcript by ID
  - Implementation: `transcript_service.py`

### Metadata Endpoints

- **Statistics**: `GET /api/stats`
  - Returns counts of videos, audio files, and transcripts
  - Implementation: `stats_service.py`

- **Filters**: `GET /api/filters`
  - Returns available filter options (years and categories)
  - Implementation: `stats_service.py`

### Query Parameters

All list endpoints support the following query parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `year` | Filter by year | `?year=2025` |
| `category` | Filter by category | `?category=House%20Chambers` |
| `search` | Text search across fields | `?search=budget` |
| `limit` | Maximum number of results | `?limit=20` |

## Code Organization

### Directory Structure

The Cloud Functions code is organized in a hierarchical structure:

```
src/cloud_functions/
├── main.py                # Entry point for Cloud Function
├── services/              # Service implementations
│   ├── gateway_service.py # Request routing service
│   ├── health_service.py  # Health check service
│   ├── video_service.py   # Video resource service
│   ├── audio_service.py   # Audio resource service
│   ├── transcript_service.py # Transcript resource service
│   └── stats_service.py   # Statistics service
├── models/               # Data models
│   ├── video.py          # Video data model
│   ├── audio.py          # Audio data model
│   └── transcript.py     # Transcript data model
└── common/               # Shared utilities
    ├── utils.py          # Common utilities
    └── db_service.py     # Database service
```

### Entry Point (`main.py`)

The `api_handler` function in `main.py` serves as the entry point for all API requests:

```python
def api_handler(request):
    """
    Main Cloud Function entry point for API requests.
    Routes all requests through the gateway service.
    """
    # Add timestamp to request object for easier access
    request.timestamp = datetime.now().isoformat()

    # Log the request
    logger.info(f"Received request: {request.method} {request.path}")

    # Route the request through the gateway
    return route_request(request)
```

### Gateway Service (`gateway_service.py`)

The gateway service analyzes the request path and routes to the appropriate service handler:

```python
def route_request(request):
    """Main routing function for API gateway"""
    # Handle OPTIONS request (CORS preflight)
    if request.method == "OPTIONS":
        return create_options_response()
        
    # Parse the request path
    path = parse_request_path(request)
    path_parts = path.strip("/").split("/")
    
    # Route to the appropriate service based on the path
    if not path_parts or path_parts[0] == "" or path_parts[0] == "api":
        return handle_info_request(request)
    
    # Extract the actual endpoint (after "api" if present)
    endpoint = path_parts[0] if path_parts[0] != "api" else path_parts[1] if len(path_parts) > 1 else ""
    
    # Route to appropriate handler
    if endpoint == "health":
        return handle_health_request(request)
    elif endpoint == "videos":
        # ... route to video service
    # ... other routing logic
```

## Data Models

The API uses dataclasses to define models for different resource types:

### Video Model (`models/video.py`)

```python
@dataclass
class VideoItem:
    """Model for video items"""
    id: str
    title: str
    year: str
    category: str
    url: str
    description: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[str] = None
    thumbnail: Optional[str] = None

    @classmethod
    def from_firestore(cls, doc_id, doc_data):
        """Create a VideoItem from Firestore document data"""
        # ... conversion logic
```

Similar model classes exist for AudioItem and TranscriptItem, each with their own fields and Firestore conversion logic.

## Firestore Integration

### Database Access

The database service (`common/db_service.py`) provides unified access to Firestore:

```python
def get_db_interface_instance():
    """Get or initialize the database interface"""
    global _db_interface
    
    if _db_interface is None:
        try:
            _db_interface = get_db_interface()
            logger.info("Database interface initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database interface: {e}")
            raise
    
    return _db_interface
```

For backward compatibility, there's also a raw Firestore client accessor:

```python
def get_db_client():
    """Legacy function: Get the Firestore client directly"""
    db = get_db_interface_instance()
    
    # Access the raw Firestore client through the implementation
    if hasattr(db.db_implementation, 'client'):
        return db.db_implementation.client
    
    # Fallback to creating a new client
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'legislativevideoreviewswithai')
    from google.cloud import firestore
    return firestore.Client(project=project_id)
```

### Firestore Queries

Each service implements specific queries to retrieve data from Firestore:

```python
# Example from video_service.py
def get_all_videos(year=None, category=None, search=None, limit=100):
    """Get all videos with optional filtering"""
    try:
        # Get database client
        db = get_db_client()

        # Start with videos collection reference
        videos_ref = db.collection("videos")

        # Apply filters if provided
        if year:
            videos_ref = videos_ref.where("year", "==", year)

        if category:
            videos_ref = videos_ref.where("category", "==", category)

        # Apply limit
        videos_ref = videos_ref.limit(limit)

        # Get documents
        video_docs = list(videos_ref.stream())
        
        # ... additional processing
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        # Return mock data as fallback
        return get_mock_videos()
```

## Error Handling and Utilities

### Response Formatting

The API uses standardized response formatting through utility functions:

```python
def create_response(data, status_code=200):
    """Create a standardized API response"""
    return jsonify(data), status_code, get_cors_headers()

def create_error_response(message, status_code=400):
    """Create a standardized error response"""
    return (
        jsonify(
            {"error": True, "message": message, "timestamp": datetime.now().isoformat()}
        ),
        status_code,
        get_cors_headers(),
    )
```

### CORS Support

CORS headers are added to all responses:

```python
def get_cors_headers():
    """Get CORS headers for API responses"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }
```

### Fallback Mock Data

Each service provides mock data for testing and fallback when database access fails:

```python
def get_mock_videos():
    """Return mock videos for testing"""
    return [
        {
            "id": "mock1",
            "title": "House Chambers - Morning Session",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-15",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/videos/mock1.mp4",
        },
        # ... more mock items
    ]
```

## Deployment

### Deployment Configuration

The Firebase Cloud Functions API is deployed with the following configuration:

- **Region**: us-west1
- **Memory**: 256 MB (default)
- **Timeout**: 60 seconds (default)
- **Runtime**: Python 3.9
- **Entry Point**: `api_handler`

### Deployment Command

```bash
gcloud functions deploy media-portal-api \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-west1 \
  --entry-point api_handler \
  --source src/cloud_functions
```

## Monitoring and Logs

Cloud Functions logs can be viewed in the Firebase Console or Google Cloud Console:

- Firebase Console: Functions > media-portal-api > Logs
- Google Cloud Console: Logging > Logs Explorer > Filter for `resource.type="cloud_function"`

Key metrics to monitor:
- Execution time
- Memory usage
- Error rates
- Number of invocations

## Security Considerations

The Firebase Cloud Functions API implements several security measures:

1. **Authentication**: Currently public access (allow-unauthenticated), but could be restricted in the future
2. **CORS**: Configured to allow cross-origin requests for web client access
3. **Rate Limiting**: Automatic Firebase rate limiting prevents abuse
4. **Secure Data Access**: Restricted to read-only operations on the database

## Testing the API

### Endpoint Testing

Example requests to test the API:

```bash
# Health check
curl https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api/health

# List videos
curl https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api/videos

# Get video by ID
curl https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api/videos/DOCUMENT_ID

# Filter videos
curl https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api/videos?year=2025&category=House%20Chambers
```

### Response Format

All API responses follow this general structure:

```json
{
  "data": [...],  // Array for list endpoints, object for single-item endpoints
  "total": 42,    // For list endpoints, the total count of items
  "filters": {    // Applied filters, if any
    "year": "2025",
    "category": "House Chambers"
  },
  "metadata": {   // Additional information
    "timestamp": "2025-03-29T12:34:56.789Z",
    "version": "1.0"
  }
}
```

## Future Enhancements

Potential enhancements to the Firebase Functions API:

1. **Authentication**: Add Firebase Authentication for protected endpoints
2. **Pagination**: Implement cursor-based pagination for large result sets
3. **Advanced Search**: Add full-text search capabilities
4. **Caching**: Implement response caching for improved performance
5. **Webhook Events**: Add webhook triggers for new content
6. **Media Upload**: Add endpoints for uploading new media files

## Conclusion

The Firebase Cloud Functions implementation provides a robust, scalable API for the Idaho Legislative Media Portal. Its microservices architecture ensures maintainability and extensibility, while the serverless model eliminates infrastructure management concerns.

---

## Additional Resources

- [Firebase Cloud Functions Documentation](https://firebase.google.com/docs/functions)
- [Firebase Console](https://console.firebase.google.com/project/legislativevideoreviewswithai)
- [Google Cloud Functions Dashboard](https://console.cloud.google.com/functions)