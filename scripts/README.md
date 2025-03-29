# Idaho Legislature Media Portal - Data Management Scripts

These scripts are used to manage the data for the Idaho Legislature Media Portal.

**IMPORTANT**: All scripts have been configured to preserve video (MP4) files while deleting audio and transcript files.

## Setup

Before running any of these scripts, make sure you have set up your service account credentials:

1. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your Firebase service account JSON file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials/legislativevideoreviewswithai-80ed70b021b5.json
```

2. Install the required Python dependencies:

```bash
pip install firebase-admin google-cloud-storage
```

## Scripts

### 1. Clear Legacy Files

This script specifically finds and deletes audio (.mp3) and transcript (.pdf, .txt) files stored in non-standard locations in Firebase Storage. It will preserve all video (.mp4) files.

```bash
# Dry run (shows what would be deleted without actually deleting anything)
./clear_legacy_files.py

# Execute deletion
./clear_legacy_files.py --execute
```

### 2. Clear All Data

This script deletes documents from the 'audio' and 'transcripts' Firestore collections and deletes all audio and transcript files from Firebase Storage. All video (.mp4) files and video collection entries will be preserved.

```bash
./clear_data.py
```

You will be prompted to confirm the deletion by typing `DELETE ALL DATA`.

### 3. Media Ingestion

This script uploads media files to Firebase Storage and adds their metadata to Firestore with proper relationship management. By default, it will skip video files and only process audio and transcript files, assuming videos are already in the system.

```bash
# Dry run (doesn't upload files or create documents)
./media_ingestion.py --dry-run /path/to/your/media/files

# Execute ingestion (audio and transcript files only)
./media_ingestion.py /path/to/your/media/files

# Include video files too (if you need to add new videos)
./media_ingestion.py --include-videos /path/to/your/media/files
```

## Process for Rebuilding the Data Structure

To rebuild the data structure with proper relationships while preserving video files:

1. Clear legacy audio and transcript files:
   ```bash
   ./clear_legacy_files.py --execute
   ```

2. Clear audio and transcript data (database and any remaining files):
   ```bash
   ./clear_data.py
   ```

3. Ingest audio and transcript files with proper relationships to existing videos:
   ```bash
   ./media_ingestion.py /path/to/your/media/files
   ```

The frontend has already been updated to work with the new data structure, using direct URL references for related media.

## Complete Workflow for Adding New Media

To download new media from the Idaho Legislature website and add it to the system:

1. Set up your environment:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/credentials/legislativevideoreviewswithai-80ed70b021b5.json
   ```

2. Download specific videos (with optional audio conversion):
   ```bash
   # Download a specific date's video and convert to audio
   python scripts/download_specific_date.py 2025 "House Chambers" "January 8" --output-dir data/downloads --convert-audio
   
   # Download all videos from a year/category
   python scripts/download_year_category.py 2025 "House Chambers" --output-dir data/downloads --convert-audio
   
   # Download only missing videos from a year/category
   python scripts/download_missing_videos.py --year 2025 --category "House Chambers" --output-dir data/downloads --convert-audio
   ```

3. Ingest the downloaded files into Firebase with proper relationship management:
   ```bash
   # Process only audio and transcript files (preserving existing videos)
   python scripts/media_ingestion.py data/downloads
   
   # Process all files including videos (if adding new videos)
   python scripts/media_ingestion.py --include-videos data/downloads
   ```

4. Ensure relationships are properly established:
   ```bash
   python scripts/update_media_relationships.py
   ```

5. Verify ingestion results in Firebase Firestore and Storage.

You can run this entire workflow or any individual step as needed. For a full automated daily ingest, you can also use:
```bash
# Run the daily cloud ingest process (includes downloading, processing, and uploading)
python scripts/daily_cloud_ingest.py
```