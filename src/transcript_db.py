#!/usr/bin/env python3
"""
Compatibility module for transcript_db that uses Firestore instead of SQLite.
Maintains the same interface as transcript_db.py but uses Firestore as the backend.
"""

import os
import logging
from datetime import datetime
from dataclasses import dataclass

# Local imports
from firestore_db import get_firestore_db, FirestoreDB

# Set up directory paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logs_dir = os.path.join(base_dir, "data", "logs")

# Create directories if they don't exist
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "transcript_db_firestore.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("transcript_db_firestore")


@dataclass
class Transcript:
    """Compatibility class for SQLite Transcript model."""

    id: str
    year: str
    category: str
    session_name: str
    file_name: str
    file_path: str
    file_size: float = None
    last_modified: datetime = None
    processed: bool = False
    uploaded: bool = False
    upload_path: str = None
    upload_date: datetime = None
    error_message: str = None
    created_at: datetime = None
    updated_at: datetime = None


def init_db():
    """Initialize the database (no-op for Firestore)."""
    logger.info("Using Firestore database (compatibility mode)")
    return True


def firestore_doc_to_transcript(doc_data):
    """Convert a Firestore document to a Transcript object."""
    return Transcript(
        id=doc_data.get("_id", ""),
        year=doc_data.get("year", ""),
        category=doc_data.get("category", ""),
        session_name=doc_data.get("session_name", ""),
        file_name=doc_data.get("file_name", ""),
        file_path=doc_data.get("original_path", "") or doc_data.get("file_path", ""),
        file_size=doc_data.get("file_size"),
        last_modified=doc_data.get("last_modified"),
        processed=doc_data.get("processed", False),
        uploaded=doc_data.get("uploaded", False),
        upload_path=doc_data.get("upload_path"),
        upload_date=doc_data.get("upload_date"),
        error_message=doc_data.get("error_message"),
        created_at=doc_data.get("created_at", datetime.now()),
        updated_at=doc_data.get(
            "updated_at", doc_data.get("created_at", datetime.now())
        ),
    )


def get_transcript_by_path(file_path):
    """Get a transcript record by its file path."""
    db = get_firestore_db()
    try:
        # Search in all collections
        for collection in ["transcripts", "audio", "videos", "other"]:
            docs = list(
                db.client.collection(collection)
                .where("original_path", "==", file_path)
                .limit(1)
                .stream()
            )

            if docs:
                doc = docs[0]
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                doc_data["_collection"] = collection
                return firestore_doc_to_transcript(doc_data)
    except Exception as e:
        logger.error(f"Error getting transcript by path {file_path}: {e}")

    return None


def add_transcript(
    year,
    category,
    session_name,
    file_name,
    file_path,
    file_size=None,
    last_modified=None,
):
    """Add a new transcript to the database."""
    db = get_firestore_db()
    try:
        # Check if transcript already exists
        existing = get_transcript_by_path(file_path)
        if existing:
            logger.debug(f"Transcript already exists: {file_path}")
            return existing

        # Determine media type based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()

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

        # Generate consistent document ID
        doc_id = f"{year}_{category}_{session_name}_{media_type}_{os.path.basename(file_path)}"
        # Clean ID to make it Firestore-friendly
        doc_id = (
            doc_id.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
        )

        # Create document data
        doc_data = {
            "year": year,
            "category": category,
            "session_name": session_name,
            "file_name": file_name,
            "original_path": file_path,
            "file_path": file_path,  # For compatibility
            "file_size": file_size,
            "last_modified": last_modified,
            "processed": False,
            "uploaded": False,
            "media_type": media_type,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Add the document to Firestore
        doc_ref = db.client.collection(collection).document(doc_id)
        doc_ref.set(doc_data)
        logger.info(f"Added new transcript to Firestore: {file_path}")

        # Add ID for return
        doc_data["_id"] = doc_id
        doc_data["_collection"] = collection

        return firestore_doc_to_transcript(doc_data)

    except Exception as e:
        logger.error(f"Error adding transcript {file_path}: {e}")
        raise


def update_transcript_status(
    file_path, processed=None, uploaded=None, upload_path=None, error_message=None
):
    """Update the status of a transcript."""
    db = get_firestore_db()
    try:
        # Find the transcript by file path
        transcript = get_transcript_by_path(file_path)
        if not transcript:
            logger.warning(f"Transcript not found for update: {file_path}")
            return None

        # Prepare update data
        update_data = {}

        if processed is not None:
            update_data["processed"] = processed

        if uploaded is not None:
            update_data["uploaded"] = uploaded
            if uploaded:
                update_data["upload_date"] = datetime.now()

        if upload_path is not None:
            update_data["upload_path"] = upload_path

        if error_message is not None:
            update_data["error_message"] = error_message

        # Add updated timestamp
        update_data["updated_at"] = datetime.now()

        # Determine collection
        if hasattr(transcript, "_collection") and transcript._collection:
            collection = transcript._collection
        else:
            # Determine collection based on file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in [".mp4", ".avi", ".mov"]:
                collection = "videos"
            elif file_ext in [".mp3", ".wav", ".m4a"]:
                collection = "audio"
            elif file_ext in [".txt", ".pdf", ".docx", ".md"]:
                collection = "transcripts"
            else:
                collection = "other"

        # Update the document in Firestore
        if hasattr(transcript, "id") and transcript.id:
            doc_ref = db.client.collection(collection).document(transcript.id)
            doc_ref.update(update_data)
            logger.info(f"Updated transcript status in Firestore: {file_path}")

            # Update the transcript object for return
            for key, value in update_data.items():
                setattr(transcript, key, value)

            return transcript
        else:
            logger.warning(f"Could not update transcript, no ID found: {file_path}")
            return None

    except Exception as e:
        logger.error(f"Error updating transcript {file_path}: {e}")
        raise


def get_unprocessed_transcripts():
    """Get all transcripts that haven't been processed yet."""
    db = get_firestore_db()
    results = []

    try:
        # Get unprocessed docs from each collection
        for collection in ["transcripts", "audio", "videos", "other"]:
            docs = list(
                db.client.collection(collection)
                .where("processed", "==", False)
                .stream()
            )

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                doc_data["_collection"] = collection
                results.append(firestore_doc_to_transcript(doc_data))

    except Exception as e:
        logger.error(f"Error getting unprocessed transcripts: {e}")

    return results


def get_processed_not_uploaded_transcripts():
    """Get all transcripts that have been processed but not uploaded."""
    db = get_firestore_db()
    results = []

    try:
        # Get processed but not uploaded docs from each collection
        for collection in ["transcripts", "audio", "videos", "other"]:
            docs = list(
                db.client.collection(collection)
                .where("processed", "==", True)
                .where("uploaded", "==", False)
                .stream()
            )

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                doc_data["_collection"] = collection
                results.append(firestore_doc_to_transcript(doc_data))

    except Exception as e:
        logger.error(f"Error getting processed not uploaded transcripts: {e}")

    return results


def get_all_transcripts():
    """Get all transcript records."""
    db = get_firestore_db()
    results = []

    try:
        # Get all docs from each collection
        for collection in ["transcripts", "audio", "videos", "other"]:
            docs = list(db.client.collection(collection).stream())

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                doc_data["_collection"] = collection
                results.append(firestore_doc_to_transcript(doc_data))

    except Exception as e:
        logger.error(f"Error getting all transcripts: {e}")

    return results


# Initialize the database when this module is imported
init_db()

if __name__ == "__main__":
    # Test the module
    print("Testing transcript_db_firestore compatibility module")
    print(f"Found {len(get_all_transcripts())} transcripts in Firestore")
