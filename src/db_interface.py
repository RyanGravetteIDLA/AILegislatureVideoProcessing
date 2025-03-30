#!/usr/bin/env python3
"""
Unified database interface for the Idaho Legislature Media Portal.
Provides a standardized API for accessing and modifying database records,
regardless of the underlying database implementation (Firestore, SQLite, etc.).
"""

import os
import logging
import importlib
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any

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
        logging.FileHandler(os.path.join(logs_dir, "db_interface.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("db_interface")

# Determine database type from environment variable
DB_TYPE = os.environ.get("DB_TYPE", "firestore").lower()
logger.info(f"Using database type: {DB_TYPE}")


@dataclass
class MediaItem:
    """Standard media item model for all database implementations."""

    id: str
    media_type: str  # video, audio, transcript, other
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
    
    # Relationship fields
    related_video_id: str = None
    related_audio_id: str = None
    related_transcript_id: str = None


class DatabaseInterface:
    """Unified database interface that delegates to the appropriate implementation."""

    def __init__(self):
        """Initialize the database interface."""
        self.db_implementation = None
        
        try:
            if DB_TYPE == "firestore":
                # Import Firestore implementation
                from firestore_db import get_firestore_db
                self.db_implementation = get_firestore_db()
                logger.info("Using Firestore database implementation")
            elif DB_TYPE == "sqlite":
                # Import SQLite implementation (use local import to avoid dependency)
                import transcript_db_sqlite
                self.db_implementation = transcript_db_sqlite
                logger.info("Using SQLite database implementation")
            else:
                # Default to Firestore
                from firestore_db import get_firestore_db
                self.db_implementation = get_firestore_db()
                logger.info(f"Unknown database type '{DB_TYPE}', defaulting to Firestore")
        except Exception as e:
            logger.error(f"Error initializing database interface: {e}")
            raise

    def get_media_by_path(self, file_path: str) -> Optional[MediaItem]:
        """Get a media item by its file path."""
        try:
            if DB_TYPE == "firestore":
                # Using Firestore implementation
                for collection in ["transcripts", "audio", "videos", "other"]:
                    docs = list(
                        self.db_implementation.client.collection(collection)
                        .where("original_path", "==", file_path)
                        .limit(1)
                        .stream()
                    )

                    if docs:
                        doc = docs[0]
                        doc_data = doc.to_dict()
                        doc_data["id"] = doc.id
                        doc_data["media_type"] = doc_data.get("media_type", collection.rstrip("s"))
                        return self._convert_to_media_item(doc_data)
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                transcript = session.query(self.db_implementation.Transcript).filter_by(file_path=file_path).first()
                
                if transcript:
                    return self._convert_sqlite_to_media_item(transcript)
                    
                session.close()
                
            return None
        except Exception as e:
            logger.error(f"Error getting media by path {file_path}: {e}")
            return None

    def add_media_item(
        self,
        media_type: str,
        year: str,
        category: str,
        session_name: str,
        file_name: str,
        file_path: str,
        file_size: Optional[float] = None,
        last_modified: Optional[datetime] = None,
    ) -> Optional[MediaItem]:
        """Add a new media item to the database."""
        try:
            # Check if media item already exists
            existing = self.get_media_by_path(file_path)
            if existing:
                logger.debug(f"Media item already exists: {file_path}")
                return existing

            if DB_TYPE == "firestore":
                # Using Firestore implementation
                # Determine collection based on media type
                if media_type == "video":
                    collection = "videos"
                elif media_type == "audio":
                    collection = "audio"
                elif media_type == "transcript":
                    collection = "transcripts"
                else:
                    collection = "other"

                # Generate consistent document ID
                doc_id = f"{year}_{category}_{session_name}_{media_type}_{os.path.basename(file_path)}"
                # Clean ID to make it Firestore-friendly
                doc_id = (
                    doc_id.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
                )

                # Create document data
                doc_data = {
                    "media_type": media_type,
                    "year": year,
                    "category": category,
                    "session_name": session_name,
                    "file_name": file_name,
                    "original_path": file_path,
                    "file_path": file_path,
                    "file_size": file_size,
                    "last_modified": last_modified,
                    "processed": False,
                    "uploaded": False,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }

                # Add the document to Firestore
                doc_ref = self.db_implementation.client.collection(collection).document(doc_id)
                doc_ref.set(doc_data)
                logger.info(f"Added new {media_type} to Firestore: {file_path}")

                # Add ID for return
                doc_data["id"] = doc_id
                
                return self._convert_to_media_item(doc_data)
                
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                
                new_transcript = self.db_implementation.Transcript(
                    year=year,
                    category=category,
                    session_name=session_name,
                    file_name=file_name,
                    file_path=file_path,
                    file_size=file_size,
                    last_modified=last_modified,
                    processed=False,
                    uploaded=False,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                
                session.add(new_transcript)
                session.commit()
                
                result = self._convert_sqlite_to_media_item(new_transcript)
                session.close()
                
                return result

        except Exception as e:
            logger.error(f"Error adding media item {file_path}: {e}")
            return None

    def update_media_status(
        self,
        file_path: str,
        processed: Optional[bool] = None,
        uploaded: Optional[bool] = None,
        upload_path: Optional[str] = None,
        error_message: Optional[str] = None,
        related_video_id: Optional[str] = None,
        related_audio_id: Optional[str] = None,
        related_transcript_id: Optional[str] = None,
    ) -> Optional[MediaItem]:
        """Update the status of a media item."""
        try:
            # Find the media item by file path
            media_item = self.get_media_by_path(file_path)
            if not media_item:
                logger.warning(f"Media item not found for update: {file_path}")
                return None

            if DB_TYPE == "firestore":
                # Determine collection based on media type
                if media_item.media_type == "video":
                    collection = "videos"
                elif media_item.media_type == "audio":
                    collection = "audio"
                elif media_item.media_type == "transcript":
                    collection = "transcripts"
                else:
                    collection = "other"

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
                    
                # Handle relationship fields
                if related_video_id is not None:
                    update_data["related_video_id"] = related_video_id
                    
                if related_audio_id is not None:
                    update_data["related_audio_id"] = related_audio_id
                    
                if related_transcript_id is not None:
                    update_data["related_transcript_id"] = related_transcript_id

                # Add updated timestamp
                update_data["updated_at"] = datetime.now()

                # Update the document in Firestore
                doc_ref = self.db_implementation.client.collection(collection).document(media_item.id)
                doc_ref.update(update_data)
                logger.info(f"Updated {media_item.media_type} status in Firestore: {file_path}")

                # Update the media item object for return
                for key, value in update_data.items():
                    setattr(media_item, key, value)

                return media_item
                
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                transcript = session.query(self.db_implementation.Transcript).filter_by(file_path=file_path).first()
                
                if transcript:
                    if processed is not None:
                        transcript.processed = processed
                        
                    if uploaded is not None:
                        transcript.uploaded = uploaded
                        if uploaded:
                            transcript.upload_date = datetime.now()
                            
                    if upload_path is not None:
                        transcript.upload_path = upload_path
                        
                    if error_message is not None:
                        transcript.error_message = error_message
                        
                    # Update the timestamp
                    transcript.updated_at = datetime.now()
                    
                    session.commit()
                    result = self._convert_sqlite_to_media_item(transcript)
                    session.close()
                    
                    return result
                    
                session.close()
                return None

        except Exception as e:
            logger.error(f"Error updating media status {file_path}: {e}")
            return None

    def get_unprocessed_items(self, media_type: Optional[str] = None) -> List[MediaItem]:
        """Get all media items that haven't been processed yet."""
        results = []

        try:
            if DB_TYPE == "firestore":
                collections = []
                
                if media_type == "video":
                    collections = ["videos"]
                elif media_type == "audio":
                    collections = ["audio"]
                elif media_type == "transcript":
                    collections = ["transcripts"]
                else:
                    # If no media type specified, search all collections
                    collections = ["transcripts", "audio", "videos", "other"]

                # Get unprocessed docs from each collection
                for collection in collections:
                    docs = list(
                        self.db_implementation.client.collection(collection)
                        .where("processed", "==", False)
                        .stream()
                    )

                    for doc in docs:
                        doc_data = doc.to_dict()
                        doc_data["id"] = doc.id
                        doc_data["media_type"] = doc_data.get("media_type", collection.rstrip("s"))
                        results.append(self._convert_to_media_item(doc_data))
                        
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                
                query = session.query(self.db_implementation.Transcript).filter_by(processed=False)
                transcripts = query.all()
                
                for transcript in transcripts:
                    results.append(self._convert_sqlite_to_media_item(transcript))
                    
                session.close()

        except Exception as e:
            logger.error(f"Error getting unprocessed media items: {e}")

        return results

    def get_processed_not_uploaded_items(self, media_type: Optional[str] = None) -> List[MediaItem]:
        """Get all media items that have been processed but not uploaded."""
        results = []

        try:
            if DB_TYPE == "firestore":
                collections = []
                
                if media_type == "video":
                    collections = ["videos"]
                elif media_type == "audio":
                    collections = ["audio"]
                elif media_type == "transcript":
                    collections = ["transcripts"]
                else:
                    # If no media type specified, search all collections
                    collections = ["transcripts", "audio", "videos", "other"]

                # Get processed but not uploaded docs from each collection
                for collection in collections:
                    docs = list(
                        self.db_implementation.client.collection(collection)
                        .where("processed", "==", True)
                        .where("uploaded", "==", False)
                        .stream()
                    )

                    for doc in docs:
                        doc_data = doc.to_dict()
                        doc_data["id"] = doc.id
                        doc_data["media_type"] = doc_data.get("media_type", collection.rstrip("s"))
                        results.append(self._convert_to_media_item(doc_data))
                        
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                
                query = session.query(self.db_implementation.Transcript).filter_by(processed=True, uploaded=False)
                transcripts = query.all()
                
                for transcript in transcripts:
                    results.append(self._convert_sqlite_to_media_item(transcript))
                    
                session.close()

        except Exception as e:
            logger.error(f"Error getting processed not uploaded media items: {e}")

        return results

    def get_all_items(self, media_type: Optional[str] = None) -> List[MediaItem]:
        """Get all media items."""
        results = []

        try:
            if DB_TYPE == "firestore":
                collections = []
                
                if media_type == "video":
                    collections = ["videos"]
                elif media_type == "audio":
                    collections = ["audio"]
                elif media_type == "transcript":
                    collections = ["transcripts"]
                else:
                    # If no media type specified, search all collections
                    collections = ["transcripts", "audio", "videos", "other"]

                # Get all docs from each collection
                for collection in collections:
                    docs = list(self.db_implementation.client.collection(collection).stream())

                    for doc in docs:
                        doc_data = doc.to_dict()
                        doc_data["id"] = doc.id
                        doc_data["media_type"] = doc_data.get("media_type", collection.rstrip("s"))
                        results.append(self._convert_to_media_item(doc_data))
                        
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                
                query = session.query(self.db_implementation.Transcript)
                transcripts = query.all()
                
                for transcript in transcripts:
                    results.append(self._convert_sqlite_to_media_item(transcript))
                    
                session.close()

        except Exception as e:
            logger.error(f"Error getting all media items: {e}")

        return results
        
    def get_items_by_year_category(self, year: str, category: str, media_type: Optional[str] = None) -> List[MediaItem]:
        """Get media items by year and category."""
        results = []

        try:
            if DB_TYPE == "firestore":
                collections = []
                
                if media_type == "video":
                    collections = ["videos"]
                elif media_type == "audio":
                    collections = ["audio"]
                elif media_type == "transcript":
                    collections = ["transcripts"]
                else:
                    # If no media type specified, search all collections
                    collections = ["transcripts", "audio", "videos", "other"]

                # Get docs from each collection
                for collection in collections:
                    docs = list(
                        self.db_implementation.client.collection(collection)
                        .where("year", "==", year)
                        .where("category", "==", category)
                        .stream()
                    )

                    for doc in docs:
                        doc_data = doc.to_dict()
                        doc_data["id"] = doc.id
                        doc_data["media_type"] = doc_data.get("media_type", collection.rstrip("s"))
                        results.append(self._convert_to_media_item(doc_data))
                        
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                
                query = session.query(self.db_implementation.Transcript).filter_by(year=year, category=category)
                transcripts = query.all()
                
                for transcript in transcripts:
                    results.append(self._convert_sqlite_to_media_item(transcript))
                    
                session.close()

        except Exception as e:
            logger.error(f"Error getting media items by year ({year}) and category ({category}): {e}")

        return results
        
    def get_item_by_id(self, item_id: str, media_type: Optional[str] = None) -> Optional[MediaItem]:
        """Get a media item by its ID."""
        try:
            if DB_TYPE == "firestore":
                collections = []
                
                if media_type == "video":
                    collections = ["videos"]
                elif media_type == "audio":
                    collections = ["audio"]
                elif media_type == "transcript":
                    collections = ["transcripts"]
                else:
                    # If no media type specified, search all collections
                    collections = ["transcripts", "audio", "videos", "other"]

                # Search for the item in the specified collections
                for collection in collections:
                    try:
                        doc = self.db_implementation.client.collection(collection).document(item_id).get()
                        if doc.exists:
                            doc_data = doc.to_dict()
                            doc_data["id"] = doc.id
                            doc_data["media_type"] = doc_data.get("media_type", collection.rstrip("s"))
                            return self._convert_to_media_item(doc_data)
                    except Exception as e:
                        logger.warning(f"Error checking {collection} for item ID {item_id}: {e}")
                
                return None
                
            elif DB_TYPE == "sqlite":
                # Using SQLite implementation
                session = self.db_implementation.Session()
                
                transcript = session.query(self.db_implementation.Transcript).filter_by(id=item_id).first()
                
                if transcript:
                    result = self._convert_sqlite_to_media_item(transcript)
                    session.close()
                    return result
                    
                session.close()
                return None

        except Exception as e:
            logger.error(f"Error getting media item by ID {item_id}: {e}")
            return None

    def _convert_to_media_item(self, doc_data: Dict[str, Any]) -> MediaItem:
        """Convert a Firestore document to a MediaItem object."""
        return MediaItem(
            id=doc_data.get("id", ""),
            media_type=doc_data.get("media_type", "unknown"),
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
            related_video_id=doc_data.get("related_video_id"),
            related_audio_id=doc_data.get("related_audio_id"),
            related_transcript_id=doc_data.get("related_transcript_id"),
            created_at=doc_data.get("created_at", datetime.now()),
            updated_at=doc_data.get("updated_at", doc_data.get("created_at", datetime.now())),
        )
        
    def _convert_sqlite_to_media_item(self, transcript) -> MediaItem:
        """Convert a SQLite Transcript object to a MediaItem object."""
        # Determine media type based on file extension
        file_ext = os.path.splitext(transcript.file_path)[1].lower() if transcript.file_path else ""
        if file_ext in [".mp4", ".avi", ".mov"]:
            media_type = "video"
        elif file_ext in [".mp3", ".wav", ".m4a"]:
            media_type = "audio"
        elif file_ext in [".txt", ".pdf", ".docx", ".md"]:
            media_type = "transcript"
        else:
            media_type = "unknown"
            
        return MediaItem(
            id=str(transcript.id),
            media_type=media_type,
            year=transcript.year,
            category=transcript.category,
            session_name=transcript.session_name,
            file_name=transcript.file_name,
            file_path=transcript.file_path,
            file_size=transcript.file_size,
            last_modified=transcript.last_modified,
            processed=transcript.processed,
            uploaded=transcript.uploaded,
            upload_path=transcript.upload_path,
            upload_date=transcript.upload_date,
            error_message=transcript.error_message,
            related_video_id=getattr(transcript, "related_video_id", None),
            related_audio_id=getattr(transcript, "related_audio_id", None),
            related_transcript_id=getattr(transcript, "related_transcript_id", None),
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
        )


# Create a singleton instance
_db_interface = None

def get_db_interface() -> DatabaseInterface:
    """Get the database interface singleton."""
    global _db_interface
    if _db_interface is None:
        _db_interface = DatabaseInterface()
    return _db_interface


# Initialize the database interface when this module is imported
db_interface = get_db_interface()

if __name__ == "__main__":
    # Test the module
    print("Testing unified database interface")
    db = get_db_interface()
    all_items = db.get_all_items()
    print(f"Found {len(all_items)} total items in the database")
    
    # Count by media type
    videos = [item for item in all_items if item.media_type == "video"]
    audio = [item for item in all_items if item.media_type == "audio"]
    transcripts = [item for item in all_items if item.media_type == "transcript"]
    others = [item for item in all_items if item.media_type == "unknown" or item.media_type == "other"]
    
    print(f"Videos: {len(videos)}")
    print(f"Audio: {len(audio)}")
    print(f"Transcripts: {len(transcripts)}")
    print(f"Other: {len(others)}")