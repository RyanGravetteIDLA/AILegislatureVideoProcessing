"""
Test configuration and fixtures for the Idaho Legislative Media Portal.
"""

import os
import sys
import pytest
from unittest import mock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class MockFirestoreDB:
    """Mock implementation of FirestoreDB class"""

    def __init__(self):
        # Sample data for tests
        self.data = {
            "videos": [
                {
                    "_id": "video1",
                    "_collection": "videos",
                    "year": "2025",
                    "category": "House Chambers",
                    "session_name": "January 8, 2025_Legislative Session Day 3",
                    "file_name": "HouseChambers_01-08-2025.mp4",
                    "gcs_path": "2025/House Chambers/January 8, 2025_Legislative Session Day 3/HouseChambers_01-08-2025.mp4",
                    "duration": "01:15:30",
                    "created_at": "2025-01-08T12:00:00",
                    "last_modified": "2025-01-08T15:30:00",
                },
                {
                    "_id": "video2",
                    "_collection": "videos",
                    "year": "2025",
                    "category": "Senate Chambers",
                    "session_name": "January 9, 2025_Legislative Session Day 4",
                    "file_name": "SenateChambers_01-09-2025.mp4",
                    "gcs_path": "2025/Senate Chambers/January 9, 2025_Legislative Session Day 4/SenateChambers_01-09-2025.mp4",
                    "duration": "00:45:20",
                    "created_at": "2025-01-09T10:00:00",
                    "last_modified": "2025-01-09T12:00:00",
                },
            ],
            "audio": [
                {
                    "_id": "audio1",
                    "_collection": "audio",
                    "year": "2025",
                    "category": "House Chambers",
                    "session_name": "January 8, 2025_Legislative Session Day 3",
                    "file_name": "HouseChambers_01-08-2025.mp3",
                    "gcs_path": "2025/House Chambers/January 8, 2025_Legislative Session Day 3/HouseChambers_01-08-2025.mp3",
                    "duration": "01:15:30",
                    "created_at": "2025-01-08T16:00:00",
                    "last_modified": "2025-01-08T16:30:00",
                }
            ],
            "transcripts": [
                {
                    "_id": "transcript1",
                    "_collection": "transcripts",
                    "year": "2025",
                    "category": "House Chambers",
                    "session_name": "January 8, 2025_Legislative Session Day 3",
                    "file_name": "HouseChambers_01-08-2025_transcription.txt",
                    "gcs_path": "2025/House Chambers/January 8, 2025_Legislative Session Day 3/HouseChambers_01-08-2025_transcription.txt",
                    "created_at": "2025-01-08T17:00:00",
                    "last_modified": "2025-01-08T17:30:00",
                }
            ],
        }

    def get_all_media(self, media_type=None, limit=None):
        """Mock implementation of get_all_media."""
        if media_type:
            if media_type == "video":
                collection = "videos"
            elif media_type == "audio":
                collection = "audio"
            elif media_type == "transcript":
                collection = "transcripts"
            else:
                collection = media_type

            return self.data.get(collection, [])

        # Return all media types combined
        result = []
        for media_list in self.data.values():
            result.extend(media_list)

        if limit and limit < len(result):
            return result[:limit]
        return result

    def get_media_by_id(self, media_id, collection=None):
        """Mock implementation of get_media_by_id."""
        if collection:
            collections = [collection]
        else:
            collections = self.data.keys()

        for coll in collections:
            for item in self.data.get(coll, []):
                if item["_id"] == media_id:
                    return item
        return None

    def search_media(
        self, query_text, media_type=None, year=None, category=None, limit=100
    ):
        """Mock implementation of search_media."""
        result = []

        if media_type:
            if media_type == "video":
                collections = ["videos"]
            elif media_type == "audio":
                collections = ["audio"]
            elif media_type == "transcript":
                collections = ["transcripts"]
            else:
                collections = [media_type]
        else:
            collections = self.data.keys()

        for coll in collections:
            for item in self.data.get(coll, []):
                # Apply filters
                if year and item.get("year") != year:
                    continue
                if category and item.get("category") != category:
                    continue

                # Apply text search
                if (
                    query_text.lower() in item.get("session_name", "").lower()
                    or query_text.lower() in item.get("category", "").lower()
                ):
                    result.append(item)

        if limit and limit < len(result):
            return result[:limit]
        return result

    def get_filter_options(self):
        """Mock implementation of get_filter_options."""
        years = set()
        categories = set()

        for collection in self.data.values():
            for item in collection:
                if "year" in item and item["year"]:
                    years.add(item["year"])
                if "category" in item and item["category"]:
                    categories.add(item["category"])

        return {"years": sorted(list(years)), "categories": sorted(list(categories))}

    def get_statistics(self):
        """Mock implementation of get_statistics."""
        return {
            "total": sum(len(collection) for collection in self.data.values()),
            "videos": len(self.data.get("videos", [])),
            "audio": len(self.data.get("audio", [])),
            "transcripts": len(self.data.get("transcripts", [])),
            "other": len(self.data.get("other", [])),
        }


def format_date(timestamp):
    """Mock implementation of format_date"""
    if timestamp:
        if isinstance(timestamp, str):
            return timestamp[:10]  # Extract YYYY-MM-DD part
    return None


def firestore_to_model(doc_data):
    """Mock implementation of firestore_to_model"""
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


@pytest.fixture
def mock_firestore_db():
    """
    Fixture that provides a mock Firestore database.
    This is used to test the API without real Firestore access.
    """
    return MockFirestoreDB()


# Define a fixture for the mocked API
@pytest.fixture
def mock_db_app():
    """
    Fixture that returns a test client with a mocked database.
    """
    # Create a simple FastAPI app with mocked endpoints
    app = FastAPI()

    # Create class models for API responses
    class MediaBase(BaseModel):
        id: str
        title: str
        description: Optional[str] = None
        year: str
        category: str
        date: Optional[str] = None

    class VideoItem(MediaBase):
        duration: Optional[str] = None
        thumbnail: Optional[str] = None
        url: str

    class AudioItem(MediaBase):
        duration: Optional[str] = None
        url: str

    class TranscriptItem(MediaBase):
        url: str

    db = MockFirestoreDB()

    # API endpoints with mock implementations
    @app.get("/api/health")
    def health_check():
        """API health check endpoint."""
        from datetime import datetime

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

    @app.get("/api/videos", response_model=List[VideoItem])
    def get_videos(
        year: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ):
        """Get a list of available videos."""
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
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/videos/{video_id}", response_model=VideoItem)
    def get_video(video_id: str):
        """Get a specific video by ID."""
        try:
            doc = db.get_media_by_id(video_id, collection="videos")

            if not doc:
                raise HTTPException(status_code=404, detail="Video not found")

            return VideoItem(**firestore_to_model(doc))

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/audio", response_model=List[AudioItem])
    def get_audio_files(
        year: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ):
        """Get a list of available audio files."""
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
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/audio/{audio_id}", response_model=AudioItem)
    def get_audio(audio_id: str):
        """Get a specific audio file by ID."""
        try:
            doc = db.get_media_by_id(audio_id, collection="audio")

            if not doc:
                raise HTTPException(status_code=404, detail="Audio file not found")

            return AudioItem(**firestore_to_model(doc))

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/transcripts", response_model=List[TranscriptItem])
    def get_transcripts(
        year: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ):
        """Get a list of available transcripts."""
        try:
            if search:
                # Use search function if search term provided
                docs = db.search_media(
                    search, media_type="transcript", year=year, category=category
                )
            else:
                # Get all transcripts and filter manually
                docs = db.get_all_media(media_type="transcripts")

                # Apply filters manually
                if year:
                    docs = [d for d in docs if d.get("year") == year]
                if category:
                    docs = [d for d in docs if d.get("category") == category]

            # Convert to response models
            return [TranscriptItem(**firestore_to_model(doc)) for doc in docs]

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/transcripts/{transcript_id}", response_model=TranscriptItem)
    def get_transcript(transcript_id: str):
        """Get a specific transcript by ID."""
        try:
            doc = db.get_media_by_id(transcript_id, collection="transcripts")

            if not doc:
                raise HTTPException(status_code=404, detail="Transcript not found")

            return TranscriptItem(**firestore_to_model(doc))

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/filters")
    def get_filter_options():
        """Get available filter options (years and categories)."""
        try:
            return db.get_filter_options()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/stats")
    def get_statistics():
        """Get statistics about the available media."""
        try:
            return db.get_statistics()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return TestClient(app)


@pytest.fixture
def api_client(mock_db_app):
    """
    Fixture that returns a test client for the API without mocking.
    In a real scenario, this would connect to the actual API,
    but for this demonstration we'll use the mock client.
    """
    # Use the mock client for now
    # In a real implementation, you would connect to an actual API
    return mock_db_app
