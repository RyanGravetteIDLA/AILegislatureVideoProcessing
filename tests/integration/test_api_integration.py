"""
Integration tests for the API endpoints in api_firestore.py.
These tests connect to a real Firestore database.

NOTE: These tests will only run if you have proper Firestore credentials set up.
"""

import os
import pytest
import time


# Skip all tests in this module if no credentials are available
pytestmark = pytest.mark.skipif(
    not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    reason="Firestore credentials not available",
)


def test_health_check_integration(api_client):
    """Test the health check endpoint with a real API."""
    response = api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["database"] == "firestore"


def test_api_version_integration(api_client):
    """Test the API version endpoint with a real API."""
    response = api_client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0"
    assert data["database"] == "firestore"
    # Verify the project ID matches the expected value
    assert data["gcp_project"] in [
        "legislativevideoreviewswithai",
        os.environ.get("GOOGLE_CLOUD_PROJECT", "unknown"),
    ]


def test_get_videos_integration(api_client):
    """Test the get_videos endpoint with a real API."""
    response = api_client.get("/api/videos")
    assert response.status_code == 200
    data = response.json()

    # We may or may not have actual videos, but the response should be a list
    assert isinstance(data, list)

    # If we have videos, check their structure
    if data:
        video = data[0]
        assert "id" in video
        assert "title" in video
        assert "year" in video
        assert "category" in video
        assert "url" in video


def test_get_audio_integration(api_client):
    """Test the get_audio endpoint with a real API."""
    response = api_client.get("/api/audio")
    assert response.status_code == 200
    data = response.json()

    # We may or may not have actual audio files, but the response should be a list
    assert isinstance(data, list)

    # If we have audio files, check their structure
    if data:
        audio = data[0]
        assert "id" in audio
        assert "title" in audio
        assert "year" in audio
        assert "category" in audio
        assert "url" in audio


def test_get_transcripts_integration(api_client):
    """Test the get_transcripts endpoint with a real API."""
    response = api_client.get("/api/transcripts")
    assert response.status_code == 200
    data = response.json()

    # We may or may not have actual transcripts, but the response should be a list
    assert isinstance(data, list)

    # If we have transcripts, check their structure
    if data:
        transcript = data[0]
        assert "id" in transcript
        assert "title" in transcript
        assert "year" in transcript
        assert "category" in transcript
        assert "url" in transcript


def test_get_filters_integration(api_client):
    """Test the get_filters endpoint with a real API."""
    response = api_client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()

    # Response should contain years and categories
    assert "years" in data
    assert "categories" in data
    assert isinstance(data["years"], list)
    assert isinstance(data["categories"], list)


def test_get_stats_integration(api_client):
    """Test the get_stats endpoint with a real API."""
    response = api_client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()

    # Response should contain counts
    assert "total" in data
    assert "videos" in data
    assert "audio" in data
    assert "transcripts" in data

    # Total should equal the sum of the individual counts
    assert data["total"] == data["videos"] + data["audio"] + data[
        "transcripts"
    ] + data.get("other", 0)
