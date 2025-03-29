#!/usr/bin/env python3
"""
Media Ingestion Script with Relationship Management

This script ingests media files (videos, audio, transcripts) into the
Idaho Legislature Media Portal system with proper relationship management.

Features:
- Consistent file naming and organization
- Explicit relationship tracking between media types
- Session-based grouping for related media
- Direct URL references for improved performance
"""

import os
import re
import hashlib
import datetime
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import storage as gcs_storage

# Initialize Firebase with explicit credentials
try:
    firebase_admin.get_app()
except ValueError:
    # Get credentials path from environment variable or use default path
    cred_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        "credentials/legislativevideoreviewswithai-80ed70b021b5.json",
    )
    print(f"Using credentials file: {cred_path}")

    if not os.path.exists(cred_path):
        print(f"WARNING: Credentials file {cred_path} not found!")
        print("Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("to point to your Firebase service account JSON file.")
        exit(1)

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(
        cred,
        {
            "projectId": "legislativevideoreviewswithai",
            "storageBucket": "legislativevideoreviewswithai.appspot.com",
        },
    )

# Initialize clients
db = firestore.client()
firebase_bucket = storage.bucket()
gcs_client = gcs_storage.Client.from_service_account_json(cred_path)

# File type mappings
FILE_TYPES = {
    ".mp4": "video",
    ".mp3": "audio",
    ".pdf": "transcript",
    ".txt": "transcript",
}

# Storage constants
STORAGE_URL = "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com"

# Legacy paths dictionary to track files that might exist in non-standard locations
LEGACY_PATHS = {
    "audio": [
        "audio",  # Standard location
        "audio/House Chambers",  # Legacy location
        "audio/Senate Chambers",  # Legacy location
    ],
    "transcript": [
        "transcript",  # Standard location
        "transcript/2025/House Chambers",  # Legacy location
        "transcript/2025/Senate Chambers",  # Legacy location
    ],
    "video": [
        "video",  # Standard location
        "video/2025/House Chambers",  # Legacy location
        "video/2025/Senate Chambers",  # Legacy location
    ],
}


def extract_metadata(file_path):
    """
    Extract metadata from a file path or name.
    Returns a dictionary with year, chamber, date, and session day if available.
    """
    file_path = str(file_path)
    filename = os.path.basename(file_path)

    metadata = {"year": None, "chamber": None, "date": None, "session_day": None}

    # Try to extract year
    year_match = re.search(r"20\d{2}", file_path)
    if year_match:
        metadata["year"] = year_match.group(0)

    # Try to extract chamber
    if "house" in file_path.lower():
        metadata["chamber"] = "House Chambers"
    elif "senate" in file_path.lower():
        metadata["chamber"] = "Senate Chambers"

    # Try to extract date (format: MM-DD-YYYY)
    date_match = re.search(r"(\d{2}-\d{2}-\d{4})", file_path)
    if date_match:
        metadata["date"] = date_match.group(1)

        # Try to convert to YYYY-MM-DD format for consistency
        try:
            month, day, year = metadata["date"].split("-")
            metadata["date"] = f"{year}-{month}-{day}"
        except:
            pass

    # Try to extract session day
    day_match = re.search(r"day[_\s]?(\d+)", file_path, re.IGNORECASE)
    if day_match:
        metadata["session_day"] = day_match.group(1)

    # If we have a date but no year, extract year from date
    if metadata["date"] and not metadata["year"]:
        try:
            metadata["year"] = metadata["date"].split("-")[0]
        except:
            pass

    # Set defaults for missing values
    if not metadata["year"]:
        current_year = datetime.datetime.now().year
        metadata["year"] = str(current_year)

    if not metadata["chamber"]:
        metadata["chamber"] = "House Chambers"  # Default

    if not metadata["session_day"]:
        metadata["session_day"] = "1"  # Default to day 1

    return metadata


def generate_session_id(metadata):
    """Generate a unique session ID from metadata."""
    components = [
        metadata["year"],
        metadata["chamber"].replace(" ", "_"),
        f"Day{metadata['session_day']}",
    ]

    if metadata["date"]:
        components.insert(0, metadata["date"])

    session_string = "_".join(components)
    session_hash = hashlib.md5(session_string.encode()).hexdigest()[:8]

    return f"{metadata['year']}_{metadata['chamber'].replace(' ', '_')}_Day{metadata['session_day']}_{session_hash}"


def get_consistent_filename(metadata, file_type):
    """Generate a consistent filename based on metadata and file type."""
    # Format: YYYY-MM-DD_Chamber_DayN.ext
    date_part = metadata["date"] if metadata["date"] else f"{metadata['year']}-01-01"
    chamber_part = metadata["chamber"].replace(" ", "")

    extensions = {
        "video": ".mp4",
        "audio": ".mp3",
        "transcript": ".pdf",  # Default to PDF for transcripts
    }

    return f"{date_part}_{chamber_part}_Day{metadata['session_day']}{extensions[file_type]}"


def get_storage_path(metadata, file_type, filename):
    """Generate a consistent storage path based on metadata."""
    # Format: media_type/year/chamber/day/filename
    return f"{file_type}/{metadata['year']}/{metadata['chamber']}/{metadata['session_day']}/{filename}"


def upload_file_to_storage(local_path, storage_path):
    """Upload a file to Firebase Storage."""
    blob = firebase_bucket.blob(storage_path)

    # Set appropriate content type
    content_types = {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }
    ext = os.path.splitext(local_path)[1].lower()
    if ext in content_types:
        blob.content_type = content_types[ext]

    # Upload the file
    blob.upload_from_filename(local_path)

    # Make public and get URL
    blob.make_public()
    return blob.public_url


def process_media_file(file_path, session_data=None, dry_run=False, skip_videos=True):
    """
    Process a media file and add it to the database with relationship management.

    Args:
        file_path: Path to the media file
        session_data: Optional dictionary of existing session data
        dry_run: If True, don't actually upload or create documents
        skip_videos: If True, skip processing video files (assumes they're already in the system)

    Returns:
        Dictionary with file information including ID and session ID
    """
    file_path = Path(file_path)

    # Skip invalid files
    if not file_path.is_file():
        print(f"Skipping non-file: {file_path}")
        return None

    # Determine file type
    ext = file_path.suffix.lower()
    if ext not in FILE_TYPES:
        print(f"Skipping unsupported file type: {file_path}")
        return None

    file_type = FILE_TYPES[ext]

    # Skip video files if requested
    if skip_videos and file_type == "video":
        print(f"Skipping video file (will use existing): {file_path}")
        return None

    # Extract metadata
    metadata = extract_metadata(file_path)

    # Generate session ID
    session_id = generate_session_id(metadata)

    # Generate consistent filename
    new_filename = get_consistent_filename(metadata, file_type)

    # Generate storage path
    storage_path = get_storage_path(metadata, file_type, new_filename)

    # Generate public URL
    public_url = f"{STORAGE_URL}/{storage_path}"

    print(f"Processing {file_type}: {file_path}")
    print(f"  Metadata: {metadata}")
    print(f"  Session ID: {session_id}")
    print(f"  Storage path: {storage_path}")

    if dry_run:
        print("  [DRY RUN] Skipping upload and database creation")
        return {
            "file_path": str(file_path),
            "file_type": file_type,
            "metadata": metadata,
            "session_id": session_id,
            "storage_path": storage_path,
            "public_url": public_url,
        }

    # Upload file to storage
    try:
        print(f"  Uploading to: {storage_path}")
        upload_file_to_storage(str(file_path), storage_path)
        print("  Upload complete")
    except Exception as e:
        print(f"  Error uploading file: {e}")
        return None

    # Generate document data
    doc_data = {
        "type": file_type,
        "title": f"{metadata['chamber']} - Session Day {metadata['session_day']}",
        "description": f"Legislative Session Day {metadata['session_day']}",
        "year": metadata["year"],
        "chamber": metadata["chamber"],
        "session_day": metadata["session_day"],
        "date": metadata["date"],
        "path": storage_path,
        "url": public_url,
        "session_id": session_id,
        "filename": new_filename,
        "original_filename": file_path.name,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        # Initialize relationship fields
        "related_media": {},
        "related_urls": {},
    }

    # Add to Firestore
    collection_name = f"{file_type}s"  # videos, audio, transcripts
    try:
        print(f"  Adding to {collection_name} collection")
        doc_ref = db.collection(collection_name).add(doc_data)
        doc_id = doc_ref[1].id
        print(f"  Added document with ID: {doc_id}")
    except Exception as e:
        print(f"  Error adding document to Firestore: {e}")
        return None

    return {
        "id": doc_id,
        "file_path": str(file_path),
        "file_type": file_type,
        "metadata": metadata,
        "session_id": session_id,
        "storage_path": storage_path,
        "public_url": public_url,
        "doc_ref": doc_ref[1],
    }


def update_relationships(session_data):
    """
    Update relationship information for all media in a session.

    Args:
        session_data: Dictionary mapping file types to document info
    """
    if not session_data:
        return

    print(
        f"Updating relationships for session: {next(iter(session_data.values()))['session_id']}"
    )

    # Build relationship maps
    related_media = {}
    related_urls = {}

    for file_type, doc_info in session_data.items():
        related_media[file_type] = doc_info["id"]
        related_urls[file_type] = doc_info["public_url"]

    # Update each document with relationship info
    for file_type, doc_info in session_data.items():
        try:
            # Create copies of relationship maps excluding self-references
            doc_related_media = {
                k: v for k, v in related_media.items() if k != file_type
            }
            doc_related_urls = {k: v for k, v in related_urls.items() if k != file_type}

            print(
                f"  Updating {file_type} document {doc_info['id']} with relationships"
            )
            doc_info["doc_ref"].update(
                {
                    "related_media": doc_related_media,
                    "related_urls": doc_related_urls,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            # For convenience, also add direct reference fields
            updates = {}
            for rel_type, rel_id in doc_related_media.items():
                updates[f"related_{rel_type}_id"] = rel_id
                updates[f"related_{rel_type}_url"] = doc_related_urls[rel_type]

            if updates:
                doc_info["doc_ref"].update(updates)

            print(f"  Successfully updated relationships for {file_type}")
        except Exception as e:
            print(f"  Error updating relationships for {file_type}: {e}")


def process_directory(directory_path, dry_run=False, skip_videos=True):
    """
    Process all media files in a directory.

    Args:
        directory_path: Path to directory containing media files
        dry_run: If True, don't actually upload or create documents
        skip_videos: If True, skip processing video files (assumes they're already in the system)
    """
    directory_path = Path(directory_path)
    if not directory_path.is_dir():
        print(f"Error: {directory_path} is not a directory")
        return

    print(f"Processing directory: {directory_path}")

    # Find all media files
    media_files = []
    for ext in FILE_TYPES.keys():
        media_files.extend(directory_path.glob(f"**/*{ext}"))

    if not media_files:
        print("No media files found")
        return

    print(f"Found {len(media_files)} media files")

    # Group files by potential session
    sessions = {}

    for file_path in media_files:
        # Extract file info
        metadata = extract_metadata(file_path)
        session_id = generate_session_id(metadata)

        # Determine file type
        ext = file_path.suffix.lower()
        file_type = FILE_TYPES.get(ext)

        if not file_type:
            continue

        # Group by session
        if session_id not in sessions:
            sessions[session_id] = {}

        sessions[session_id][file_type] = file_path

    print(f"Files grouped into {len(sessions)} sessions")

    # Process each session
    for session_id, session_files in sessions.items():
        print(f"\nProcessing session: {session_id}")
        print(f"  Files: {session_files}")

        session_data = {}

        # Process each file in the session
        for file_type, file_path in session_files.items():
            doc_info = process_media_file(
                file_path, dry_run=dry_run, skip_videos=skip_videos
            )
            if doc_info:
                session_data[file_type] = doc_info

        # Update relationships if we have multiple media types
        if len(session_data) > 1 and not dry_run:
            update_relationships(session_data)


def main():
    """Main function to ingest media."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest media files with relationship management"
    )
    parser.add_argument("directory", help="Directory containing media files to process")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (no uploads or database changes)",
    )
    parser.add_argument(
        "--include-videos",
        action="store_true",
        help="Include video files in processing (default is to skip videos)",
    )
    args = parser.parse_args()

    skip_videos = not args.include_videos

    if skip_videos:
        print("NOTE: Skipping video files (will use existing videos)")
        print("Add --include-videos flag if you want to process video files too")
    else:
        print("NOTE: Including video files in processing (will create new videos)")

    process_directory(args.directory, dry_run=args.dry_run, skip_videos=skip_videos)


if __name__ == "__main__":
    main()
