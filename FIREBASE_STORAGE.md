# Firebase Storage Architecture

## Overview

The Idaho Legislative Media Portal uses Firebase Storage (built on Google Cloud Storage) as its primary storage solution for media files including videos, audio recordings, and transcripts. This document outlines the storage structure, file organization patterns, naming conventions, access mechanisms, and integration with Firestore.

## Storage Configuration

### Primary Storage Bucket

- **Main bucket name**: `legislativevideoreviewswithai.appspot.com`
- **Fallback bucket names**:
  - `legislativevideoreviewswithai.firebasestorage.app`
  - `idaho-legislature-media`
- **Service Account**: `firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com`

### Configuration Parameters

The system uses several configuration parameters to control storage behavior:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `USE_CLOUD_STORAGE` | Whether to use cloud storage at all | `True` |
| `CLOUD_STORAGE_PUBLIC` | Whether files should be publicly accessible | `False` |
| `PREFER_CLOUD_STORAGE` | Whether to prefer cloud storage over local files | `True` |

These parameters can be configured through:
- Environment variables
- The secrets manager (`src/secrets_manager.py`)
- Application configuration (`src/config.py`)

## File Organization Structure

### Hierarchical Path Pattern

Files in Firebase Storage are organized using a hierarchical structure that mirrors the local file organization:

```
{year}/{category}/{session_name}/{filename}
```

For example:
```
2025/House Chambers/January 9, 2025_Legislative Session Day 4/HouseChambers01-09-2025.mp4
```

### Media Type Specific Patterns

The system handles three primary types of media files:

1. **Videos**:
   - File extensions: `.mp4`
   - Example path: `2025/House Chambers/January 24, 2025_Legislative Session Day 19/1_HouseChambers01-24-2025.mp4`

2. **Audio**:
   - File extensions: `.mp3`, `.wav`
   - Typically stored in an `audio` subdirectory
   - Example path: `2025/House Chambers/January 24, 2025_Legislative Session Day 19/audio/1_HouseChambers01-24-2025.mp3`

3. **Transcripts**:
   - File extensions: `.txt` (with naming pattern: `*_transcription.txt`)
   - Typically stored alongside their corresponding audio files
   - Example path: `2025/House Chambers/January 24, 2025_Legislative Session Day 19/audio/1_HouseChambers01-24-2025_transcription.txt`

### Fallback Organization

If a standard hierarchical structure can't be determined, files may use a simplified organization:

```
{media_type}/{year}/Unsorted/{filename}
```

For example: `video/2025/Unsorted/HouseChambers01-09-2025.mp4`

## Storage Operations

### File Upload Process

Files are uploaded to Firebase Storage using the `GoogleCloudStorage` class in `src/cloud_storage.py`:

```python
def upload_file(self, local_path, remote_path=None, make_public=False, content_type=None):
    """Upload a file to Google Cloud Storage and return its URL/path"""
    # Determine remote path if not provided
    if not remote_path:
        remote_path = os.path.basename(local_path)
    
    # Create a blob in the bucket
    blob = self.bucket.blob(remote_path)
    
    # Set content type if provided
    if content_type:
        blob.content_type = content_type
    
    # Upload the file
    blob.upload_from_filename(local_path)
    
    # Make public if requested
    if make_public:
        blob.make_public()
        return blob.public_url
    else:
        return f"gs://{self.bucket_name}/{remote_path}"
```

### Batch Upload Process

For bulk uploads, the system uses `scripts/upload_media_to_cloud.py` which:

1. Scans local directories for media files using glob patterns
2. Categorizes files by media type based on file extensions
3. Preserves the original directory structure in cloud storage
4. Updates Firestore database with upload status and cloud paths
5. Creates relationships between related media items

## File Serving Mechanisms

The system uses multiple strategies to serve files from Firebase Storage:

### 1. Direct Public URLs

When `CLOUD_STORAGE_PUBLIC` is enabled, files are made publicly accessible with direct URLs:

```python
blob = gcs_client.bucket.blob(gcs_path)
public_url = blob.public_url
# Format: https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/{path}
```

### 2. Signed URLs

For non-public files, the system generates time-limited signed URLs:

```python
signed_url = gcs_client.get_signed_url(gcs_path, expiration=3600)
# Provides temporary authenticated access for 1 hour
```

### 3. API-Based Access

The application provides a file server component (`src/file_server.py`) that proxies access to storage:

```
/api/files/gcs/{path}  # References a file directly in Cloud Storage
/api/files/{year}/{category}/{filename}  # File path pattern
```

This abstraction allows the system to:
- Determine the best serving method dynamically
- Handle authentication and permissions
- Provide fallback to local files when needed
- Optimize for different file types and sizes

## Firebase Storage and Firestore Integration

### Document References

Files in Firebase Storage are referenced in Firestore documents with these key fields:

| Field | Description | Example |
|-------|-------------|---------|
| `gcs_path` | Path within the storage bucket | `2025/House Chambers/January 24, 2025_Legislative Session Day 19/1_HouseChambers01-24-2025.mp4` |
| `url` | Access URL (may be generated) | `/api/files/gcs/2025/House Chambers/January 24, 2025_Legislative Session Day 19/1_HouseChambers01-24-2025.mp4` |
| `uploaded` | Whether file has been uploaded to cloud | `true` |
| `media_type` | Type of media | `video`, `audio`, or `transcript` |

### Relationship Management

Media files are linked in a bidirectional relationship model:

1. **Video documents** contain:
   - `related_audio_id`: Reference to corresponding audio document
   - `related_audio_path`: Cloud path to audio file
   - `related_transcript_id`: Reference to transcript document
   - `related_transcript_path`: Cloud path to transcript file

2. **Audio documents** contain:
   - `related_video_id`: Reference to video document
   - `related_transcript_id`: Reference to transcript document

3. **Transcript documents** contain:
   - `related_video_id`: Reference to video document
   - `related_audio_id`: Reference to audio document

All related documents share the same `session_id` for grouping.

## Utility Functions

The system includes several utility functions for working with Firebase Storage:

### Access and Authentication

- `get_default_gcs_client()`: Initializes a client with proper credentials
- `get_signed_url(path, expiration=3600)`: Creates temporary access URLs

### Path Management

- `get_cloud_path(local_path)`: Converts local paths to their Firebase Storage equivalent
- `generate_standard_path(media_type, year, category, session, filename)`: Creates standardized paths

### Search and Verification

- `search_cloud_storage(pattern)`: Searches for files matching a pattern
- `check_file_exists(path)`: Verifies if a file exists in storage
- `list_files(prefix)`: Lists files under a specific path prefix

## Storage Statistics (As of Latest Test)

Based on current usage patterns:

- All media is from the year **2025**
- Two main categories: **House Chambers** and **Senate Chambers**
- Videos, audio, and transcripts are nearly 1:1:1 in terms of document count
- All files using **session_id** for grouping related media

## Best Practices

### 1. Use the Correct Upload Pattern

- Always preserve the original hierarchical structure when uploading
- Use batch uploading for multiple files to maintain consistency
- Update Firestore documents with proper references after upload

### 2. File Serving

- Use the file server API rather than direct storage URLs when possible
- This provides flexibility to change storage backends without breaking clients
- Handle CORS configurations for web access (see `frontend/update_cors.py`)

### 3. Storage Security

- Avoid making files public unless necessary
- Use signed URLs with appropriate expiration times
- Leverage Firebase Security Rules for fine-grained access control

### 4. Optimization

- Use content-specific storage classes for different types of media
- Consider implementing a CDN for frequently accessed files
- Implement caching mechanisms for popular content

## Testing and Validation

To verify the Firebase Storage configuration and test file operations:

```python
from src.cloud_storage import get_default_gcs_client

# Initialize client
gcs = get_default_gcs_client()

# List files in the bucket
files = list(gcs.bucket.list_blobs(prefix="2025/"))

# Check specific file existence
blob = gcs.bucket.blob("2025/House Chambers/January 24, 2025_Legislative Session Day 19/1_HouseChambers01-24-2025.mp4")
exists = blob.exists()

# Generate a signed URL
signed_url = gcs.get_signed_url("2025/House Chambers/January 24, 2025_Legislative Session Day 19/1_HouseChambers01-24-2025.mp4")
```

---

## Additional Resources

- [Firebase Storage Documentation](https://firebase.google.com/docs/storage)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Firebase Console - Storage](https://console.firebase.google.com/project/legislativevideoreviewswithai/storage)
- [Google Cloud Console - Storage Browser](https://console.cloud.google.com/storage/browser/legislativevideoreviewswithai.appspot.com)