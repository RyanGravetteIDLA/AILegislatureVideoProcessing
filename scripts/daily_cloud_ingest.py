#!/usr/bin/env python3
"""
Daily script to scan for new files and upload them to Cloud Storage.
Designed to be triggered by Cloud Scheduler via the API endpoint.
"""

import os
import sys
import time
import logging
import json
import re
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Disable googleapiclient discovery cache warning
os.environ["GOOGLE_DISCOVERY_URL"] = ""
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

# Import scan_transcripts to update the database
try:
    # First try absolute imports
    try:
        from src.firestore_db import get_firestore_db
        from src.cloud_storage import GoogleCloudStorage, get_default_gcs_client
    except ImportError:
        # Fall back to relative imports
        from firestore_db import get_firestore_db
        from cloud_storage import GoogleCloudStorage, get_default_gcs_client

    # For these we need to use a conditional approach
    try:
        from scripts.scan_transcripts import scan_transcripts
    except ImportError:
        try:
            from scan_transcripts import scan_transcripts
        except ImportError:
            # Define a dummy function if not available
            def scan_transcripts():
                print("scan_transcripts function not available")
                return {"found": 0}

    try:
        from scripts.downloader import download_committee_videos
    except ImportError:
        try:
            from downloader import download_committee_videos
        except ImportError:
            # Define a dummy function if not available
            def download_committee_videos(days_to_download=1):
                print("download_committee_videos function not available")
                return {"attempted": 0, "success": 0, "skipped": 0, "error": 0}

except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging
log_dir = os.path.join("data", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f'daily_cloud_ingest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger("daily_cloud_ingest")

# Constants
DOWNLOADS_DIR = os.path.join("data", "downloads")

# Media patterns
MEDIA_PATTERNS = {
    "video": ["mp4", "avi", "mov"],
    "audio": ["mp3", "wav", "m4a"],
    "transcript": ["txt"],
}


def find_media_files(base_dir=DOWNLOADS_DIR, media_type=None, days=1, recent_only=True):
    """
    Find all media files of a specific type, optionally filtering for recent files.

    Args:
        base_dir: Base directory to search in
        media_type: Type of media to find ('video', 'audio', 'transcript', or None for all)
        days: Number of days to look back for recent files
        recent_only: Only include files modified in the last X days

    Returns:
        list: List of file paths
    """
    result_files = []

    # File extensions for the given media type
    if media_type and media_type in MEDIA_PATTERNS:
        extensions = MEDIA_PATTERNS[media_type]
    else:
        # Use all extensions if no specific type
        extensions = []
        for type_exts in MEDIA_PATTERNS.values():
            extensions.extend(type_exts)

    # Calculate cutoff date if filtering by recency
    cutoff_date = datetime.now() - timedelta(days=days) if recent_only else None

    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)

            # Check if extension matches
            ext = os.path.splitext(file)[1].lower().lstrip(".")
            if ext not in extensions:
                continue

            # Check if file is recent enough
            if cutoff_date:
                try:
                    mtime = os.path.getmtime(file_path)
                    file_date = datetime.fromtimestamp(mtime)
                    if file_date < cutoff_date:
                        continue
                except OSError:
                    # Skip files with permission issues
                    continue

            result_files.append(file_path)

    # Sort files by modification time (newest first)
    result_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    logger.info(
        f"Found {len(result_files)} {media_type or 'media'} files"
        f"{' modified in the last ' + str(days) + ' days' if recent_only else ''}"
    )

    return result_files


def get_gcs_path(local_path, base_dir=DOWNLOADS_DIR):
    """
    Convert local path to GCS path, preserving directory structure.

    Args:
        local_path: Local file path
        base_dir: Base directory to strip from path

    Returns:
        str: GCS path
    """
    # Make paths absolute for reliable path manipulation
    local_path = os.path.abspath(local_path)
    base_dir = os.path.abspath(base_dir)

    # Strip base directory and ensure proper separators
    relative_path = local_path[len(base_dir) :].lstrip(os.sep)

    # Convert Windows backslashes to forward slashes if needed
    if os.sep != "/":
        relative_path = relative_path.replace(os.sep, "/")

    return relative_path


def upload_to_cloud_storage(
    files, media_type, gcs_client=None, batch_size=5, rate_limit=1, skip_existing=True
):
    """
    Upload files to Cloud Storage.

    Args:
        files: List of file paths to upload
        media_type: Type of media ('video', 'audio', 'transcript')
        gcs_client: GoogleCloudStorage client instance
        batch_size: Number of files to process in each batch
        rate_limit: Sleep time between uploads (seconds)
        skip_existing: Skip files that already exist in Cloud Storage

    Returns:
        dict: Statistics about the upload process
    """
    if not files:
        logger.info(f"No {media_type} files to upload")
        return {"total": 0, "success": 0, "skipped": 0, "error": 0}

    # Initialize GCS client if not provided
    if gcs_client is None:
        try:
            gcs_client = get_default_gcs_client()
            logger.info(f"Using GCS bucket: {gcs_client.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            return {
                "total": len(files),
                "success": 0,
                "skipped": 0,
                "error": len(files),
            }

    # Stats tracking
    stats = {
        "total": len(files),
        "success": 0,
        "skipped": 0,
        "error": 0,
        "uploaded_files": [],
    }

    # Process files in batches
    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        logger.info(
            f"Processing batch {i//batch_size + 1}/{(len(files)-1)//batch_size + 1} ({len(batch)} files)"
        )

        for file_path in batch:
            # Get GCS path
            remote_path = get_gcs_path(file_path)

            try:
                # Check if file already exists in Cloud Storage
                if skip_existing:
                    blob = gcs_client.bucket.blob(remote_path)
                    if blob.exists():
                        logger.info(
                            f"File already exists in Cloud Storage, skipping: {remote_path}"
                        )
                        stats["skipped"] += 1
                        continue

                # Upload the file
                result = gcs_client.upload_file(
                    file_path, remote_path, make_public=False
                )

                if result:
                    stats["success"] += 1
                    stats["uploaded_files"].append(result)
                    logger.info(f"Successfully uploaded: {remote_path}")

                    # Create a Firestore document for this file
                    create_firestore_document(file_path, remote_path, media_type)
                else:
                    stats["error"] += 1
                    logger.error(f"Failed to upload: {file_path}")

            except Exception as e:
                stats["error"] += 1
                logger.error(f"Error uploading {file_path}: {e}")

            # Rate limiting
            if rate_limit > 0:
                time.sleep(rate_limit)

    # Log summary
    success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
    logger.info(
        f"{media_type.capitalize()} upload complete. "
        f"Success: {stats['success']} ({success_rate:.1f}%), "
        f"Skipped: {stats['skipped']}, Errors: {stats['error']}"
    )

    return stats


def create_firestore_document(file_path, gcs_path, media_type):
    """
    Create a Firestore document for an uploaded file.

    Args:
        file_path: Local file path
        gcs_path: GCS path of the uploaded file
        media_type: Type of media ('video', 'audio', 'transcript')

    Returns:
        bool: True if document was created, False otherwise
    """
    try:
        # Get Firestore DB client
        db = get_firestore_db()

        # Extract metadata from file path
        path_parts = os.path.normpath(file_path).split(os.sep)

        # Expected structure: data/downloads/YEAR/CATEGORY/[SESSION]/FILENAME
        # Find year and category in the path
        year = None
        category = None
        session_name = None
        file_name = os.path.basename(file_path)

        # Look for year (4-digit number) and category in path
        for i, part in enumerate(path_parts):
            if part.isdigit() and len(part) == 4:
                year = part
                if i + 1 < len(path_parts):
                    category = path_parts[i + 1]
                if i + 2 < len(path_parts) and not path_parts[i + 2].endswith(
                    (".mp4", ".mp3", ".wav", ".txt")
                ):
                    session_name = path_parts[i + 2]
                break

        # Fallback: Extract from filename if not found in path
        if not year or not category:
            parts = file_name.split("_")
            if len(parts) >= 2:
                # Look for year in filename parts
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        year = part
                        break

                # Try to extract category from filename
                if parts[0].isdigit() and len(parts) >= 2:
                    category = parts[1]

        # Use current year if still not found
        if not year:
            year = str(datetime.now().year)

        # Use default category if not found
        if not category:
            category = "Unknown"

        # Try to extract date from filename or path
        date = None
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        date_match = re.search(date_pattern, file_name) or re.search(
            date_pattern, file_path
        )
        if date_match:
            date = date_match.group(1)

        # Prepare document data
        data = {
            "file_name": file_name,
            "original_path": file_path,
            "gcs_path": gcs_path,
            "year": year,
            "category": category,
            "session_name": session_name or f"{category} {year}",
            "media_type": media_type,
            "processed": True,
            "uploaded": True,
            "created_at": datetime.now(),
            "last_modified": datetime.now(),
        }

        # Add date if available
        if date:
            data["date"] = date

        # Determine collection based on media type
        if media_type == "video":
            collection = "videos"
        elif media_type == "audio":
            collection = "audio"
        elif media_type == "transcript":
            collection = "transcripts"
        else:
            collection = "other"

        # Add the document to Firestore - this will handle relationships automatically
        success, doc_id = db.add_media(data, collection)

        if success:
            logger.info(f"Created Firestore document in '{collection}': {doc_id}")
            return True
        else:
            logger.error(f"Failed to create Firestore document for {file_path}")
            return False

    except Exception as e:
        logger.error(f"Error creating Firestore document for {file_path}: {e}")
        return False


def daily_ingest(
    recent_only=True,
    days=1,
    rate_limit=1,
    skip_existing=True,
    batch_size=5,
    download_new=True,
):
    """
    Process daily media ingestion with Cloud Storage.

    Args:
        recent_only: Only upload files modified in the last X days
        days: Number of days to look back for recent files
        rate_limit: Sleep time between uploads (seconds)
        skip_existing: Skip files already in Cloud Storage
        batch_size: Number of files to process in each batch
        download_new: Whether to attempt downloading new videos first

    Returns:
        dict: Statistics about the ingestion process
    """
    start_time = time.time()
    logger.info(f"Starting daily cloud ingestion at {datetime.now()}")

    # Stats tracking
    stats = {
        "scan": {"found": 0},
        "download": {"attempted": 0, "success": 0, "skipped": 0, "error": 0},
        "video": {"total": 0, "success": 0, "skipped": 0, "error": 0},
        "audio": {"total": 0, "success": 0, "skipped": 0, "error": 0},
        "transcript": {"total": 0, "success": 0, "skipped": 0, "error": 0},
    }

    try:
        # Initialize GCS client
        gcs_client = get_default_gcs_client()

        # 1. Download new videos (optional)
        if download_new:
            try:
                logger.info("Step 1: Downloading new committee videos")
                download_stats = download_committee_videos(days_to_download=days)
                stats["download"] = download_stats
            except Exception as e:
                logger.error(f"Error downloading videos: {e}")
                stats["download"] = {
                    "attempted": 0,
                    "success": 0,
                    "skipped": 0,
                    "error": 1,
                }

        # 2. Scan for transcripts and update the database
        logger.info("Step 2: Scanning for transcripts and updating database")
        scan_results = scan_transcripts()
        stats["scan"] = scan_results

        # 3. Find and upload media files by type
        logger.info("Step 3: Finding and uploading media files")

        media_types = ["video", "audio", "transcript"]
        for media_type in media_types:
            # Find files of this type
            files = find_media_files(
                media_type=media_type, days=days, recent_only=recent_only
            )

            # Upload files to Cloud Storage
            if files:
                logger.info(f"Uploading {len(files)} {media_type} files")
                upload_stats = upload_to_cloud_storage(
                    files,
                    media_type=media_type,
                    gcs_client=gcs_client,
                    batch_size=batch_size,
                    rate_limit=rate_limit,
                    skip_existing=skip_existing,
                )

                # Update statistics
                stats[media_type] = upload_stats
            else:
                logger.info(f"No {media_type} files to upload")

        # 4. Log results
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        logger.info(
            f"Daily cloud ingestion completed in {int(minutes)} minutes, {int(seconds)} seconds"
        )
        logger.info("Ingestion statistics:")

        for media_type in media_types:
            media_stats = stats[media_type]
            success_rate = (
                media_stats["success"] / media_stats["total"] * 100
                if media_stats["total"] > 0
                else 0
            )
            logger.info(
                f"  {media_type.capitalize()}: {media_stats['success']}/{media_stats['total']} uploaded "
                f"({success_rate:.1f}%), {media_stats['skipped']} skipped, {media_stats['error']} errors"
            )

        return stats

    except Exception as e:
        logger.error(f"Error during daily cloud ingestion: {e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Daily script to ingest media to Cloud Storage"
    )

    parser.add_argument(
        "--recent-only", action="store_true", help="Only upload files modified recently"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to look back for recent files",
    )
    parser.add_argument(
        "--rate-limit", type=int, default=1, help="Sleep time between uploads (seconds)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Upload files even if they already exist in Cloud Storage",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of files to process in each batch",
    )
    parser.add_argument(
        "--no-download", action="store_true", help="Skip downloading new videos"
    )

    args = parser.parse_args()

    try:
        daily_ingest(
            recent_only=args.recent_only,
            days=args.days,
            rate_limit=args.rate_limit,
            skip_existing=not args.force,
            batch_size=args.batch_size,
            download_new=not args.no_download,
        )
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
