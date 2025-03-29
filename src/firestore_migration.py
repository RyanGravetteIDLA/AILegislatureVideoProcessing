#!/usr/bin/env python3
"""
Firestore Migration Module for Idaho Legislative Media Portal.

This script handles the migration of data from SQLite to Firestore,
and uploads associated media files to Google Cloud Storage.

The migration process consists of:
1. Reading all records from the SQLite database
2. Uploading associated media files to GCS
3. Creating corresponding Firestore documents
4. Validating the migration

Usage:
    python firestore_migration.py [--dry-run] [--limit NUM]
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Add project root to path for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Local imports
from google.cloud import firestore
from src.transcript_db import get_all_transcripts, init_db as init_sqlite_db
from src.cloud_storage import GoogleCloudStorage, get_default_gcs_client


# Configure logging
logs_dir = os.path.join(base_dir, "data", "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "firestore_migration.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("firestore_migration")


def get_firebase_project_id():
    """
    Get the Firebase project ID from environment or configuration.

    Returns:
        str: Firebase project ID
    """
    # First try to read from environment variable
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        # Try to get from application default credentials
        try:
            import google.auth

            _, project_id = google.auth.default()
        except Exception as e:
            logger.warning(f"Could not get project ID from default credentials: {e}")

    # Fallback to hardcoded value (from our migration plan)
    if not project_id:
        project_id = "legislativevideoreviewswithai"
        logger.warning(f"Using fallback project ID: {project_id}")

    return project_id


def init_firestore_client():
    """
    Initialize the Firestore client.

    Returns:
        google.cloud.firestore.Client: Firestore client instance
    """
    project_id = get_firebase_project_id()
    logger.info(f"Initializing Firestore client for project: {project_id}")

    try:
        db = firestore.Client(project=project_id)
        return db
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}")
        raise


def validate_gcs_path(path):
    """
    Ensure GCS path is properly formatted.

    Args:
        path (str): Path to validate

    Returns:
        str: Properly formatted GCS path
    """
    if not path:
        return None

    # Remove gs:// prefix if present as we'll store just the relative path
    if path.startswith("gs://"):
        # Extract bucket name and blob path
        parts = path[5:].split("/", 1)
        if len(parts) > 1:
            # Return just the blob path without bucket name
            return parts[1]
        return ""

    return path


def get_mime_type(file_path):
    """
    Determine MIME type of a file.

    Args:
        file_path (str): Path to the file

    Returns:
        str: MIME type or None if not determinable
    """
    import mimetypes

    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def create_firestore_document(db, transcript, gcs_client, dry_run=False):
    """
    Create a Firestore document for a transcript and upload the file to GCS.

    Args:
        db (firestore.Client): Firestore client
        transcript (Transcript): SQLite transcript record
        gcs_client (GoogleCloudStorage): GCS client
        dry_run (bool): If True, don't actually write to Firestore/GCS

    Returns:
        tuple: (dict, str) - Document data and document ID
    """
    # Determine media type based on file extension
    file_ext = os.path.splitext(transcript.file_path)[1].lower()

    if file_ext in [".mp4", ".avi", ".mov"]:
        media_type = "video"
        collection = "videos"
    elif file_ext in [".mp3", ".wav", ".m4a"]:
        media_type = "audio"
        collection = "audio"
    elif file_ext in [".txt", ".pdf", ".docx", ".md"]:
        media_type = "transcript"
        collection = "transcripts"
    else:
        media_type = "unknown"
        collection = "other"

    # Generate consistent document ID (Use something unique but deterministic)
    # This ensures we can re-run the migration without creating duplicates
    doc_id = f"{transcript.year}_{transcript.category}_{transcript.session_name}_{media_type}"
    # Clean ID to make it Firestore-friendly
    doc_id = (
        doc_id.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    )

    # Prepare the remote path for GCS
    remote_path = f"{media_type}/{transcript.year}/{transcript.category}/{os.path.basename(transcript.file_path)}"

    # Upload file to GCS if it exists
    gcs_path = None
    if os.path.exists(transcript.file_path):
        if not dry_run:
            gcs_result = gcs_client.upload_file(transcript.file_path, remote_path)
            gcs_path = validate_gcs_path(gcs_result)
            logger.info(f"Uploaded {transcript.file_path} to GCS: {gcs_path}")
        else:
            logger.info(
                f"[DRY RUN] Would upload {transcript.file_path} to GCS as {remote_path}"
            )
            gcs_path = remote_path
    else:
        logger.warning(f"File not found for upload: {transcript.file_path}")

    # Create document data
    doc_data = {
        # Core metadata from SQLite
        "year": transcript.year,
        "category": transcript.category,
        "session_name": transcript.session_name,
        "file_name": transcript.file_name,
        "original_path": transcript.file_path,  # Keep for reference
        # Media type and status
        "media_type": media_type,
        "processed": transcript.processed,
        "uploaded": True if gcs_path else False,
        # GCS references
        "gcs_path": gcs_path,
        # Additional metadata
        "file_size": transcript.file_size,
        "mime_type": get_mime_type(transcript.file_path),
        "last_modified": transcript.last_modified,
        "error_message": transcript.error_message,
        # Timestamps
        "created_at": transcript.created_at,
        "updated_at": (
            transcript.updated_at if transcript.updated_at else transcript.created_at
        ),
        "migrated_at": datetime.now(),
    }

    # Filter out None values for cleaner documents
    doc_data = {k: v for k, v in doc_data.items() if v is not None}

    # Add the document to Firestore
    if not dry_run:
        doc_ref = db.collection(collection).document(doc_id)
        doc_ref.set(doc_data)
        logger.info(f"Created Firestore document: {collection}/{doc_id}")
    else:
        logger.info(f"[DRY RUN] Would create Firestore document: {collection}/{doc_id}")

    return doc_data, doc_id


def migrate_sqlite_to_firestore(limit=None, dry_run=False):
    """
    Migrate all records from SQLite to Firestore.

    Args:
        limit (int, optional): Maximum number of records to migrate
        dry_run (bool): If True, don't actually write to Firestore/GCS

    Returns:
        dict: Migration statistics
    """
    # Initialize SQLite DB
    init_sqlite_db()

    # Get all transcript records
    transcripts = get_all_transcripts()
    logger.info(f"Found {len(transcripts)} transcripts in SQLite database")

    # Limit if specified
    if limit and limit > 0:
        transcripts = transcripts[:limit]
        logger.info(f"Limiting migration to {limit} records")

    # Initialize Firestore client
    try:
        db = init_firestore_client()
    except Exception as e:
        logger.error(f"Failed to initialize Firestore: {e}")
        return {"success": False, "error": str(e)}

    # Initialize GCS client
    try:
        gcs_client = get_default_gcs_client()
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        return {"success": False, "error": str(e)}

    # Migration statistics
    stats = {
        "total": len(transcripts),
        "migrated": 0,
        "videos": 0,
        "audio": 0,
        "transcripts": 0,
        "other": 0,
        "errors": 0,
        "dry_run": dry_run,
        "success": True,
    }

    # Process each transcript
    for transcript in tqdm(transcripts, desc="Migrating records"):
        try:
            # Create Firestore document
            doc_data, doc_id = create_firestore_document(
                db, transcript, gcs_client, dry_run
            )

            # Update statistics
            stats["migrated"] += 1
            media_type = doc_data.get("media_type", "unknown")
            if media_type == "video":
                stats["videos"] += 1
            elif media_type == "audio":
                stats["audio"] += 1
            elif media_type == "transcript":
                stats["transcripts"] += 1
            else:
                stats["other"] += 1

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            logger.error(f"Error migrating transcript {transcript.file_path}: {e}")
            logger.error(f"Detailed error: {error_detail}")
            stats["errors"] += 1

    # Log migration summary
    logger.info(
        f"Migration complete: {stats['migrated']} of {stats['total']} records migrated"
    )
    logger.info(f"  Videos: {stats['videos']}")
    logger.info(f"  Audio: {stats['audio']}")
    logger.info(f"  Transcripts: {stats['transcripts']}")
    logger.info(f"  Other: {stats['other']}")
    logger.info(f"  Errors: {stats['errors']}")

    if dry_run:
        logger.info("This was a dry run. No changes were made to Firestore or GCS.")

    return stats


def validate_migration(limit=None):
    """
    Validate that the migration was successful by comparing SQLite and Firestore.

    Args:
        limit (int, optional): Maximum number of records to validate

    Returns:
        dict: Validation statistics
    """
    # Initialize SQLite DB
    init_sqlite_db()

    # Get all transcript records
    transcripts = get_all_transcripts()
    if limit and limit > 0:
        transcripts = transcripts[:limit]

    # Initialize Firestore client
    db = init_firestore_client()

    # Validation statistics
    stats = {
        "total_sqlite": len(transcripts),
        "total_firestore": 0,
        "matches": 0,
        "mismatches": 0,
        "missing": 0,
    }

    # Count documents in each collection
    videos_count = len(list(db.collection("videos").limit(1000).stream()))
    audio_count = len(list(db.collection("audio").limit(1000).stream()))
    transcripts_count = len(list(db.collection("transcripts").limit(1000).stream()))
    other_count = len(list(db.collection("other").limit(1000).stream()))

    stats["total_firestore"] = (
        videos_count + audio_count + transcripts_count + other_count
    )

    logger.info(f"Found {stats['total_sqlite']} records in SQLite")
    logger.info(f"Found {stats['total_firestore']} documents in Firestore")
    logger.info(f"  Videos: {videos_count}")
    logger.info(f"  Audio: {audio_count}")
    logger.info(f"  Transcripts: {transcripts_count}")
    logger.info(f"  Other: {other_count}")

    return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Migrate SQLite database to Firestore")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without writing to Firestore/GCS",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of records to process"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate migration after completion"
    )
    parser.add_argument(
        "--credentials", help="Path to service account JSON credentials file"
    )

    args = parser.parse_args()

    # Set service account credentials if provided
    if args.credentials:
        if os.path.exists(args.credentials):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials
            print(f"Using service account credentials from: {args.credentials}")
        else:
            print(f"ERROR: Credentials file not found: {args.credentials}")
            print(
                "Please provide a valid path to service account credentials JSON file."
            )
            return

    # Perform migration
    try:
        stats = migrate_sqlite_to_firestore(limit=args.limit, dry_run=args.dry_run)

        # Validate if requested and not a dry run
        if args.validate and not args.dry_run and stats.get("success", False):
            validation = validate_migration(limit=args.limit)

        # Output summary
        if stats.get("success", False):
            print("\nMigration Summary:")
            print(f"Total Records: {stats['total']}")
            print(f"Successfully Migrated: {stats['migrated']}")
            print(f"  Videos: {stats['videos']}")
            print(f"  Audio: {stats['audio']}")
            print(f"  Transcripts: {stats['transcripts']}")
            print(f"  Other: {stats['other']}")
            print(f"Errors: {stats['errors']}")

            if args.dry_run:
                print("\nThis was a dry run. No changes were made to Firestore or GCS.")
        else:
            print("\nMigration Failed:")
            print(f"Error: {stats.get('error', 'Unknown error')}")
            print("\nTo fix authentication issues, please:")
            print(
                "1. Ensure you have a service account with Firestore and Storage permissions"
            )
            print("2. Download service account credentials JSON file")
            print("3. Run migration with: --credentials=/path/to/credentials.json")
            print("4. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    except Exception as e:
        print(f"\nMigration failed with error: {e}")
        print("\nPlease ensure you have proper authentication set up for Google Cloud.")
        print("See: https://cloud.google.com/docs/authentication/external/set-up-adc")


if __name__ == "__main__":
    main()
