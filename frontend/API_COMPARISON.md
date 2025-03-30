# API vs. Direct Firestore Comparison

## Current Data Flow Architecture

The frontend application currently accesses data through an API that connects to Firestore:

```
Frontend (Vue.js + Pinia) → API Layer → Firestore Database
```

## Data Field Comparison

Our investigation revealed that the API returns a simplified subset of fields compared to what's available in Firestore:

### Fields Available in API Response:
- `category`
- `date`
- `description`
- `duration`
- `id`
- `thumbnail`
- `title`
- `url`
- `year`

### Additional Fields Available in Firestore:
- `created_at`
- `file_name`
- `gcs_path`
- `last_modified`
- `media_type`
- `original_path`
- `processed`
- `related_audio_id`
- `related_audio_path`
- `related_audio_url`
- `related_transcript_id`
- `related_transcript_path`
- `related_transcript_url`
- `session_id`
- `session_name`
- `updated_at`
- `uploaded`

## Key Missing Data That Would Be Valuable

The most important missing data that would be valuable to have in the frontend are:

1. **Related Media IDs and Paths**:
   - `related_audio_id`
   - `related_audio_path`
   - `related_transcript_id`
   - `related_transcript_path`

   These fields would allow the frontend to directly access related media without having to make complex relationship queries.

2. **Session Information**:
   - `session_id`
   - `session_name`

   This information provides better context about the legislative session.

3. **Media Processing Status**:
   - `processed`
   - `uploaded`

   These fields could be useful for showing processing status in the UI.

## Options for Enhancement

### Option 1: Enhance the API Endpoints

Modify the existing API endpoints to include the additional fields from Firestore. This would require changes to:

- The API response models in the Cloud Functions codebase
- The data conversion functions to include additional fields

This is the recommended approach as it maintains the security benefits of the API while providing more complete data.

### Option 2: Create New Enhanced API Endpoints

Add new endpoint versions that return the enhanced data while keeping the original endpoints for backward compatibility:

- `/api/videos/enhanced`
- `/api/videos/enhanced/{video_id}`

This would allow for a gradual transition to the enhanced data model.

### Option 3: Direct Firestore Access

Implement direct Firestore access in the frontend for specific needs where the complete data is required. This approach comes with security considerations but could be useful for admin features.

## Implementation Example

We've created an example implementation showing how the API endpoints could be enhanced to include all Firestore fields while maintaining the existing API structure and security model.

## Recommendation

We recommend implementing **Option 1 or Option 2** to enhance the API with additional Firestore fields while maintaining the current architecture. 

The specific fields that would provide the most value are:
- Related media IDs and paths
- Session information
- Media processing status

This enhancement would provide the frontend with richer data without compromising the security benefits of the current API-based approach.