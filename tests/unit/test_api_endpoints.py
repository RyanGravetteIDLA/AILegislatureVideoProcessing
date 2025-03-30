"""
Unit tests for the API endpoints in api_firestore.py.
These tests use a mock Firestore DB to avoid real DB connections.
"""

import pytest


def test_health_check(mock_db_app):
    """Test the health check endpoint."""
    response = mock_db_app.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["database"] == "firestore"


def test_api_version(mock_db_app):
    """Test the API version endpoint."""
    response = mock_db_app.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0"
    assert data["database"] == "firestore"


def test_get_videos(mock_db_app):
    """Test the get_videos endpoint."""
    response = mock_db_app.get("/api/videos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Check fields
    video = data[0]
    assert "id" in video
    assert "title" in video
    assert "description" in video
    assert "year" in video
    assert "category" in video
    assert "url" in video


def test_get_videos_with_filter(mock_db_app):
    """Test the get_videos endpoint with filters."""
    # Test filtering by year
    response = mock_db_app.get("/api/videos?year=2025")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test filtering by category
    response = mock_db_app.get("/api/videos?category=House%20Chambers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "House Chambers"


def test_get_video_by_id(mock_db_app):
    """Test the get_video_by_id endpoint."""
    # Valid video ID
    response = mock_db_app.get("/api/videos/video1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "video1"

    # Invalid video ID
    response = mock_db_app.get("/api/videos/nonexistent")
    assert response.status_code == 404


def test_get_audio_files(mock_db_app):
    """Test the get_audio_files endpoint."""
    response = mock_db_app.get("/api/audio")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    # Check fields
    audio = data[0]
    assert "id" in audio
    assert "title" in audio
    assert "description" in audio
    assert "year" in audio
    assert "category" in audio
    assert "url" in audio


def test_get_audio_by_id(mock_db_app):
    """Test the get_audio_by_id endpoint."""
    # Valid audio ID
    response = mock_db_app.get("/api/audio/audio1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "audio1"

    # Invalid audio ID
    response = mock_db_app.get("/api/audio/nonexistent")
    assert response.status_code == 404


def test_get_transcripts(mock_db_app):
    """Test the get_transcripts endpoint."""
    response = mock_db_app.get("/api/transcripts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    # Check fields
    transcript = data[0]
    assert "id" in transcript
    assert "title" in transcript
    assert "description" in transcript
    assert "year" in transcript
    assert "category" in transcript
    assert "url" in transcript


def test_get_transcript_by_id(mock_db_app):
    """Test the get_transcript_by_id endpoint."""
    # Valid transcript ID
    response = mock_db_app.get("/api/transcripts/transcript1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "transcript1"

    # Invalid transcript ID
    response = mock_db_app.get("/api/transcripts/nonexistent")
    assert response.status_code == 404


def test_get_filter_options(mock_db_app):
    """Test the get_filter_options endpoint."""
    response = mock_db_app.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    assert "years" in data
    assert "categories" in data
    assert "2025" in data["years"]
    assert "House Chambers" in data["categories"]
    assert "Senate Chambers" in data["categories"]


def test_get_statistics(mock_db_app):
    """Test the get_statistics endpoint."""
    response = mock_db_app.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert data["videos"] == 2
    assert data["audio"] == 1
    assert data["transcripts"] == 1
    assert data["other"] == 0
