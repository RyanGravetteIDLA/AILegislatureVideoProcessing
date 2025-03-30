#!/usr/bin/env python3
"""
Database migration utility for transitioning from legacy database interfaces
to the unified db_interface.py implementation.

This script helps migrate existing code by:
1. Providing compatibility layers for old function names
2. Offering utilities to convert between data formats
3. Validating data integrity across implementations
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("db_migration")

# Ensure we can import from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the new unified database interface
from db_interface import get_db_interface, MediaItem

# Global instance of the database interface
db = get_db_interface()

# Compatibility Functions for transcript_db.py and transcript_db_firestore.py

def get_transcript_by_path(file_path: str):
    """
    Legacy function: Get a transcript record by its file path.
    Maps to the new unified interface.
    """
    logger.debug(f"Legacy get_transcript_by_path call for {file_path}")
    media_item = db.get_media_by_path(file_path)
    return _media_item_to_transcript(media_item) if media_item else None


def add_transcript(
    year: str,
    category: str,
    session_name: str,
    file_name: str,
    file_path: str,
    file_size: Optional[float] = None,
    last_modified: Optional[datetime] = None,
):
    """
    Legacy function: Add a new transcript to the database.
    Maps to the new unified interface.
    """
    logger.debug(f"Legacy add_transcript call for {file_path}")
    
    # Determine media type based on file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in [".mp4", ".avi", ".mov"]:
        media_type = "video"
    elif file_ext in [".mp3", ".wav", ".m4a"]:
        media_type = "audio"
    elif file_ext in [".txt", ".pdf", ".docx", ".md"]:
        media_type = "transcript"
    else:
        media_type = "unknown"
    
    media_item = db.add_media_item(
        media_type=media_type,
        year=year,
        category=category,
        session_name=session_name,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        last_modified=last_modified,
    )
    
    return _media_item_to_transcript(media_item) if media_item else None


def update_transcript_status(
    file_path: str,
    processed: Optional[bool] = None,
    uploaded: Optional[bool] = None,
    upload_path: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """
    Legacy function: Update the status of a transcript.
    Maps to the new unified interface.
    """
    logger.debug(f"Legacy update_transcript_status call for {file_path}")
    media_item = db.update_media_status(
        file_path=file_path,
        processed=processed,
        uploaded=uploaded,
        upload_path=upload_path,
        error_message=error_message,
    )
    
    return _media_item_to_transcript(media_item) if media_item else None


def get_unprocessed_transcripts():
    """
    Legacy function: Get all transcripts that haven't been processed yet.
    Maps to the new unified interface.
    """
    logger.debug("Legacy get_unprocessed_transcripts call")
    media_items = db.get_unprocessed_items()
    return [_media_item_to_transcript(item) for item in media_items]


def get_processed_not_uploaded_transcripts():
    """
    Legacy function: Get all transcripts that have been processed but not uploaded.
    Maps to the new unified interface.
    """
    logger.debug("Legacy get_processed_not_uploaded_transcripts call")
    media_items = db.get_processed_not_uploaded_items()
    return [_media_item_to_transcript(item) for item in media_items]


def get_all_transcripts():
    """
    Legacy function: Get all transcript records.
    Maps to the new unified interface.
    """
    logger.debug("Legacy get_all_transcripts call")
    media_items = db.get_all_items()
    return [_media_item_to_transcript(item) for item in media_items]


def _media_item_to_transcript(media_item: MediaItem):
    """
    Convert a MediaItem to a legacy Transcript object format.
    This provides compatibility with code expecting the old format.
    """
    if not media_item:
        return None
    
    # Create a simple object with the expected attributes
    class LegacyTranscript:
        pass
    
    transcript = LegacyTranscript()
    transcript.id = media_item.id
    transcript.year = media_item.year
    transcript.category = media_item.category
    transcript.session_name = media_item.session_name
    transcript.file_name = media_item.file_name
    transcript.file_path = media_item.file_path
    transcript.file_size = media_item.file_size
    transcript.last_modified = media_item.last_modified
    transcript.processed = media_item.processed
    transcript.uploaded = media_item.uploaded
    transcript.upload_path = media_item.upload_path
    transcript.upload_date = media_item.upload_date
    transcript.error_message = media_item.error_message
    transcript.created_at = media_item.created_at
    transcript.updated_at = media_item.updated_at
    
    # Add the collection attribute for compatibility
    if media_item.media_type == "video":
        transcript._collection = "videos"
    elif media_item.media_type == "audio":
        transcript._collection = "audio"
    elif media_item.media_type == "transcript":
        transcript._collection = "transcripts"
    else:
        transcript._collection = "other"
    
    return transcript


def migrate_db():
    """
    Perform a full database migration from the old format to the new unified format.
    This is only needed if you're transitioning from SQLite to Firestore or vice versa.
    """
    # This implementation depends on the specific needs of the project
    # For now, just log that it was called
    logger.info("Database migration function called - implementation needed for specific migration")
    return "Migration not implemented - depends on specific requirements"


def validate_data_integrity():
    """
    Validate that data is consistent across implementations.
    This is useful when transitioning between database backends.
    """
    # This implementation depends on the specific needs of the project
    # For now, just log that it was called
    logger.info("Data integrity validation function called - implementation needed for specific validation")
    return "Validation not implemented - depends on specific requirements"


if __name__ == "__main__":
    print("Database Migration Utility")
    print("-" * 30)
    
    # Count items in the database
    all_items = db.get_all_items()
    print(f"Total media items in database: {len(all_items)}")
    
    # Count by media type
    videos = [item for item in all_items if item.media_type == "video"]
    audio = [item for item in all_items if item.media_type == "audio"]
    transcripts = [item for item in all_items if item.media_type == "transcript"]
    
    print(f"Videos: {len(videos)}")
    print(f"Audio: {len(audio)}")
    print(f"Transcripts: {len(transcripts)}")
    
    # Legacy compatibility test
    print("\nTesting legacy compatibility layer...")
    legacy_transcripts = get_all_transcripts()
    print(f"Legacy transcripts count: {len(legacy_transcripts)}")
    
    if len(legacy_transcripts) > 0:
        print("First legacy transcript:", legacy_transcripts[0].file_name)