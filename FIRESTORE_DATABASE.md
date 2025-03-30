# Firestore Database Architecture

## Overview

The Idaho Legislative Media Portal uses Firestore as its primary database for storing and retrieving media metadata. Firestore is a flexible, scalable NoSQL database in the Firebase platform that enables real-time data synchronization and provides robust security features. This document outlines the database structure, collections, document schemas, relationships, and best practices for working with our Firestore implementation.

## Project Configuration

- **Project ID**: `legislativevideoreviewswithai`
- **Service Account**: `firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com`
- **Authentication**: Service account key JSON file required for admin-level access

## Collection Structure

The database is organized into four primary collections:

1. **videos**: Stores metadata for video files from legislative sessions (65 documents)
2. **audio**: Stores metadata for audio recordings extracted from videos (55 documents)
3. **transcripts**: Stores text transcriptions of audio recordings (53 documents)
4. **other**: Catchall for miscellaneous media types (0 documents, reserved for future use)

## Document Schema 

### Common Fields Across Collections

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `title` | string | Title of the media item | Yes |
| `description` | string | Description of the media content | No |
| `year` | string | Year the session took place | Yes |
| `category` | string | Category (e.g., "House Chambers", "Senate Chambers") | Yes |
| `date` | string | Session date (formatted as ISO string or YYYY-MM-DD) | No |
| `file_name` | string | Original file name | Yes |
| `session_name` | string | Name of the legislative session | No |
| `session_id` | string | Generated unique ID for grouping related media | Yes |
| `gcs_path` | string | Path to the file in Google Cloud Storage | Yes |
| `url` | string | Public URL for accessing the file | Yes |
| `original_path` | string | Original local file system path | No |
| `processed` | boolean | Whether the item has been processed | Yes |
| `uploaded` | boolean | Whether the item has been uploaded to cloud storage | Yes |
| `created_at` | timestamp | Creation timestamp in Firestore | Yes |
| `updated_at` | timestamp | Last update timestamp | Yes |

### Collection-Specific Fields

#### videos Collection

| Field | Type | Description |
|-------|------|-------------|
| `duration` | string | Video duration (formatted as HH:MM:SS) |
| `thumbnail` | string | URL to video thumbnail image |
| `related_audio_id` | string | ID reference to associated audio document |
| `related_audio_path` | string | GCS path to associated audio file |
| `related_audio_url` | string | URL to associated audio file |
| `related_transcript_id` | string | ID reference to associated transcript document |
| `related_transcript_path` | string | GCS path to associated transcript file |
| `related_transcript_url` | string | URL to associated transcript file |

#### audio Collection

| Field | Type | Description |
|-------|------|-------------|
| `duration` | string | Audio duration (formatted as HH:MM:SS) |
| `sample_rate` | number | Sample rate in Hz |
| `channels` | number | Number of audio channels |
| `related_video_id` | string | ID reference to associated video document |
| `related_video_path` | string | GCS path to associated video file |
| `related_video_url` | string | URL to associated video file |
| `related_transcript_id` | string | ID reference to associated transcript document |
| `related_transcript_path` | string | GCS path to associated transcript file |
| `related_transcript_url` | string | URL to associated transcript file |

#### transcripts Collection

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Full text content of the transcript |
| `language` | string | Language of the transcript (default: "en-US") |
| `word_count` | number | Total number of words in the transcript |
| `related_video_id` | string | ID reference to associated video document |
| `related_video_path` | string | GCS path to associated video file |
| `related_video_url` | string | URL to associated video file |
| `related_audio_id` | string | ID reference to associated audio document |
| `related_audio_path` | string | GCS path to associated audio file |
| `related_audio_url` | string | URL to associated audio file |

## Relationships

### Media Relationships Model

The database uses a **bidirectional relationship model** where:

1. Each media type references related media through ID fields
2. Related media paths and URLs are duplicated for faster access
3. A `session_id` field groups all media from a single legislative session

**Relationship Implementation Status**:
- 100% of transcripts have both `related_video_id` and `related_audio_id`
- 100% of audio documents have `related_video_id`
- Only ~3% of videos have `related_audio_id` and `related_transcript_id` populated
- The `session_id` field is present in 100% of documents across all collections

```
┌─────────┐     ┌────────┐     ┌────────────┐
│  video  │◄───►│  audio │◄───►│ transcript │
└─────────┘     └────────┘     └────────────┘
     │               │               │
     │               │               │
     └───────────────┼───────────────┘
                     ▼
                ┌──────────┐
                │session_id│
                └──────────┘
```

### Session ID Generation

The `session_id` is a critical field that groups related media items from the same legislative session. It is generated using:

1. A combination of year and category
2. Date information if available
3. Session number if available in the filename
4. A unique hash to ensure uniqueness

For example: `2025_House_Chambers_a1b2c3d4`

## Database Access

### Authentication and Initialization

The application uses a service account key for authentication with Firestore:

```python
# In firestore_db.py
def get_firebase_project_id():
    # Try environment variable first
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        # Try default credentials
        try:
            import google.auth
            _, project_id = google.auth.default()
        except Exception:
            # Fallback to hardcoded value
            project_id = "legislativevideoreviewswithai"
    
    return project_id
```

### Singleton Pattern for Database Access

All database access uses a singleton pattern to prevent multiple redundant connections:

```python
# Global singleton instance
_firestore_db_instance = None

def get_firestore_db():
    """Get the Firestore DB instance (singleton pattern)."""
    global _firestore_db_instance
    if _firestore_db_instance is None:
        _firestore_db_instance = FirestoreDB()
    return _firestore_db_instance
```

## Query Patterns

### Common Query Patterns

1. **Retrieving All Media of a Specific Type:**
   ```python
   videos = db.get_all_media(media_type="video")
   ```

2. **Filtering by Year and Category:**
   ```python
   videos = db.client.collection("videos") \
             .where(filter=FieldFilter("year", "==", "2025")) \
             .where(filter=FieldFilter("category", "==", "House Chambers")) \
             .stream()
   ```

3. **Document Lookup by ID:**
   ```python
   video = db.get_media_by_id("abc123", collection="videos")
   ```

4. **Text Search Across Multiple Fields:**
   ```python
   results = db.search_media("budget hearing", year="2025", media_type="transcript")
   ```

5. **Getting Related Media:**
   ```python
   related = db.get_related_media("abc123", collection="videos")
   ```

### Cloud Functions Database Access

The Cloud Functions implementation uses a database service layer that:

1. Initializes a standardized database interface
2. Supports fallback to mock data for testing
3. Provides data access methods for each microservice

Example:
```python
# Get database instance
db = get_db_interface_instance()

# Query videos with filtering
videos = db.get_all_media(media_type="video", 
                         filter_params={"year": "2025", "category": "House Chambers"})
```

## Best Practices

### 1. Use the Correct Access Pattern

- Always use the singleton instance via `get_firestore_db()` rather than creating new instances
- Prefer the unified database interface `get_db_interface()` for new code to ensure compatibility

### 2. Relationship Management

- When adding new media, use `find_matching_media()` to automatically detect relationships
- Always update bidirectional relationships using `update_relationship_references()`
- Run `update_all_relationships()` periodically to ensure relationship consistency

### 3. Error Handling

- Wrap Firestore operations in try/except blocks to handle potential errors
- Use the logging facilities to record database operation results
- Handle timeouts and retry strategies for critical operations

### 4. Performance Optimization

- Use `.select([])` to fetch only needed fields when retrieving large number of documents
- Apply appropriate query limits to prevent excessive data retrieval
- Create composite indexes for complex queries that combine multiple filters

## Microservices Architecture

The Cloud Functions implementation uses a dedicated service for each media type:

1. **Gateway Service**: Handles request routing and basic validation
2. **Video Service**: Manages video-related queries and operations
3. **Audio Service**: Manages audio-related queries and operations
4. **Transcript Service**: Manages transcript-related queries and operations
5. **Stats Service**: Provides statistics and filter options

Each service accesses the database through a unified interface with appropriate error handling and fallbacks.

## Testing Database Operations

A test script (`firebasemdcreationtests.py`) is available to validate the database structure and access patterns. This script:

1. Connects to Firestore and verifies collection structure
2. Samples documents from each collection
3. Analyzes field usage and relationship patterns
4. Generates schema information based on actual data
5. Produces statistics about the database

Run this script when making significant changes to database code:

```bash
python firebasemdcreationtests.py
```

## Backup and Recovery

Firestore data is automatically backed up through Google Cloud's standard backup mechanisms. For additional data protection:

1. **Export Collections**: Periodically export collections to Cloud Storage
   ```bash
   gcloud firestore export gs://legislativevideoreviewswithai.appspot.com/backups/$(date +%Y-%m-%d)
   ```

2. **Local Backup**: Maintain local JSON exports of critical data
   ```python
   # Export collection to JSON
   def export_collection_to_json(collection_name, output_file):
       db = get_firestore_db()
       docs = list(db.client.collection(collection_name).stream())
       data = [doc.to_dict() for doc in docs]
       with open(output_file, 'w') as f:
           json.dump(data, f, indent=2)
   ```

## Migration Tools

The `firestore_migration.py` module provides tools for migrating data from SQLite to Firestore. This includes:

1. Reading records from the SQLite database
2. Converting to the Firestore document format
3. Uploading associated media to Cloud Storage
4. Creating Firestore documents with proper relationships
5. Validating the migration was successful

---

## Available Filters and Categories

Based on the current database content:

### Years
- 2025

### Categories
- House Chambers
- Senate Chambers

## Additional Resources

- [Firebase Console](https://console.firebase.google.com/project/legislativevideoreviewswithai)
- [Google Cloud Storage Console](https://console.cloud.google.com/storage/browser/legislativevideoreviewswithai.appspot.com)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Cloud Functions Documentation](https://firebase.google.com/docs/functions)