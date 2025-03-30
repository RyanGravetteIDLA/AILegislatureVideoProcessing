"""
API module for serving media data to the frontend application.
Provides RESTful endpoints for videos, audio, and transcripts.

This module implements a FastAPI application that serves structured data about 
Idaho Legislature media content, including videos, audio recordings, and transcripts.
It connects to the Firestore database via the firestore_db module and provides
filtering capabilities by year, category, and search terms.

Key features:
- RESTful API design with JSON responses
- Filtering and search capabilities
- Error handling and logging
- CORS support for frontend integration
- Health check endpoint for monitoring
"""

import os
import logging
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local imports - use Firestore instead of SQLite
from firestore_db import get_firestore_db, FirestoreDB

# Configure logging
# Create logs directory if it doesn't exist
logs_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs"
)
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "api.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Idaho Legislature Media API",
    description="API for accessing Idaho Legislature media content",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://legislativevideoreviewswithai.web.app",
        "https://legislativevideoreviewswithai.firebaseapp.com",
        "http://localhost:5173",
        "http://localhost:4173",
    ],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database dependency
def get_db():
    return get_firestore_db()


# Data models for API responses
class MediaBase(BaseModel):
    """
    Base model for all media types with common properties.

    Attributes:
        id: Unique identifier for the media item
        title: Title of the media, typically includes category and session name
        description: Optional detailed description of the content
        year: Legislative year the media belongs to
        category: Category of the media (e.g., House Chambers, Committee)
        date: Optional date when the media was recorded/modified
    """

    id: str  # Using string IDs for Firestore documents
    title: str
    description: Optional[str] = None
    year: str
    category: str
    date: Optional[str] = None

    class Config:
        orm_mode = True


class VideoItem(MediaBase):
    """
    Model for video items, extends MediaBase with video-specific properties.

    Attributes:
        duration: Duration of the video in HH:MM:SS format
        thumbnail: Optional URL to a thumbnail image
        url: URL where the video can be accessed
    """

    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    url: str


class AudioItem(MediaBase):
    """
    Model for audio items, extends MediaBase with audio-specific properties.

    Attributes:
        duration: Duration of the audio in HH:MM:SS format
        url: URL where the audio can be accessed
    """

    duration: Optional[str] = None
    url: str


class TranscriptItem(MediaBase):
    """
    Model for transcript items, extends MediaBase.

    Attributes:
        url: URL where the transcript can be accessed
    """

    url: str


# Helper functions
def format_date(timestamp) -> Optional[str]:
    """Format a datetime object to ISO date string."""
    if timestamp:
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%Y-%m-%d")
        elif isinstance(timestamp, str):
            return timestamp[:10]  # Extract YYYY-MM-DD part
    return None


def firestore_to_model(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Firestore document to API response model.

    This function maps data from the Firestore document to the format expected by the API.

    Args:
        doc_data: A dictionary containing Firestore document data

    Returns:
        Dict containing all fields needed for the API response models
    """
    # Create a title from category and session name
    session_title = f"{doc_data.get('category', 'Unknown')} - {doc_data.get('session_name', 'Unknown')}"

    # Construct base data common to all media types
    base_data = {
        "id": doc_data.get("_id", ""),
        "title": session_title,
        "description": f"Legislative Session {doc_data.get('year', 'Unknown')}",
        "year": doc_data.get("year", "Unknown"),
        "category": doc_data.get("category", "Unknown"),
        "date": format_date(
            doc_data.get("last_modified") or doc_data.get("created_at")
        ),
    }

    # Construct file URL
    gcs_path = doc_data.get("gcs_path", "")
    if gcs_path:
        # This URL pattern will be resolved by our file server component
        base_url = f"/api/files/gcs/{gcs_path}"
    else:
        # Fallback to original path if available
        base_url = f"/api/files/{doc_data.get('year', 'unknown')}/{doc_data.get('category', 'unknown')}/{doc_data.get('file_name', 'unknown')}"

    return {
        **base_data,
        "url": base_url,
        "duration": doc_data.get(
            "duration", "00:00:00"
        ),  # Placeholder or actual duration if available
    }


# API Routes
@app.get("/api/videos", response_model=List[VideoItem])
def get_videos(
    db: FirestoreDB = Depends(get_db),
    year: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get a list of available videos.

    This endpoint returns all available video files, with optional filtering capabilities.
    Videos can be filtered by legislative year, category (like "House Chambers"),
    or by a text search that matches against session name or category.

    Args:
        db: Firestore database client
        year: Optional filter for specific legislative year
        category: Optional filter for specific category
        search: Optional text search term

    Returns:
        List of VideoItem objects with metadata and access URLs

    Raises:
        HTTPException: If there's an error retrieving or processing the videos
    """
    try:
        if search:
            # Use search function if search term provided
            docs = db.search_media(
                search, media_type="video", year=year, category=category
            )
        else:
            # Get all videos and filter manually
            docs = db.get_all_media(media_type="video")

            # Apply filters manually
            if year:
                docs = [d for d in docs if d.get("year") == year]
            if category:
                docs = [d for d in docs if d.get("category") == category]

        # Convert to response models
        return [VideoItem(**firestore_to_model(doc)) for doc in docs]

    except Exception as e:
        logger.error(f"Error retrieving videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos/{video_id}", response_model=VideoItem)
def get_video(video_id: str, db: FirestoreDB = Depends(get_db)):
    """Get a specific video by ID."""
    try:
        doc = db.get_media_by_id(video_id, collection="videos")

        if not doc:
            raise HTTPException(status_code=404, detail="Video not found")

        return VideoItem(**firestore_to_model(doc))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio", response_model=List[AudioItem])
def get_audio_files(
    db: FirestoreDB = Depends(get_db),
    year: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get a list of available audio files.
    Optionally filter by year, category, or search term.
    """
    try:
        if search:
            # Use search function if search term provided
            docs = db.search_media(
                search, media_type="audio", year=year, category=category
            )
        else:
            # Get all audio files and filter manually
            docs = db.get_all_media(media_type="audio")

            # Apply filters manually
            if year:
                docs = [d for d in docs if d.get("year") == year]
            if category:
                docs = [d for d in docs if d.get("category") == category]

        # Convert to response models
        return [AudioItem(**firestore_to_model(doc)) for doc in docs]

    except Exception as e:
        logger.error(f"Error retrieving audio files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/{audio_id}", response_model=AudioItem)
def get_audio(audio_id: str, db: FirestoreDB = Depends(get_db)):
    """Get a specific audio file by ID."""
    try:
        doc = db.get_media_by_id(audio_id, collection="audio")

        if not doc:
            raise HTTPException(status_code=404, detail="Audio file not found")

        return AudioItem(**firestore_to_model(doc))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audio {audio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transcripts", response_model=List[TranscriptItem])
def get_transcripts(
    db: FirestoreDB = Depends(get_db),
    year: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get a list of available transcripts.
    Optionally filter by year, category, or search term.
    """
    try:
        if search:
            # Use search function if search term provided
            docs = db.search_media(
                search, media_type="transcript", year=year, category=category
            )
        else:
            # Get all transcripts and filter manually
            docs = db.get_all_media(media_type="transcript")

            # Apply filters manually
            if year:
                docs = [d for d in docs if d.get("year") == year]
            if category:
                docs = [d for d in docs if d.get("category") == category]

        # Convert to response models
        return [TranscriptItem(**firestore_to_model(doc)) for doc in docs]

    except Exception as e:
        logger.error(f"Error retrieving transcripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transcripts/{transcript_id}", response_model=TranscriptItem)
def get_transcript(transcript_id: str, db: FirestoreDB = Depends(get_db)):
    """Get a specific transcript by ID."""
    try:
        doc = db.get_media_by_id(transcript_id, collection="transcripts")

        if not doc:
            raise HTTPException(status_code=404, detail="Transcript not found")

        return TranscriptItem(**firestore_to_model(doc))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcript {transcript_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/filters")
def get_filter_options(db: FirestoreDB = Depends(get_db)):
    """Get available filter options (years and categories)."""
    try:
        return db.get_filter_options()

    except Exception as e:
        logger.error(f"Error retrieving filter options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
def get_statistics(db: FirestoreDB = Depends(get_db)):
    """
    Get statistics about the available media.

    This endpoint provides count statistics for the different types of media files
    available in the system. This is useful for dashboard displays, monitoring,
    and general system status reporting.

    Args:
        db: Firestore database client

    Returns:
        Dictionary containing counts of videos, audio files, transcripts, and total items

    Raises:
        HTTPException: If there's an error retrieving or calculating the statistics
    """
    try:
        return db.get_statistics()

    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Add a health check endpoint
@app.get("/api/health")
def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "firestore",
    }


@app.get("/api/version")
def api_version():
    """API version information."""
    return {
        "version": "2.0.0",
        "database": "firestore",
        "gcp_project": os.environ.get("GOOGLE_CLOUD_PROJECT", "unknown"),
    }


if __name__ == "__main__":
    import uvicorn

    # Start the server
    uvicorn.run("api:app", host="0.0.0.0", port=5000, reload=True)
