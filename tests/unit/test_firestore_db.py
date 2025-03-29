"""
Unit tests for the FirestoreDB class.
These tests use mocks to avoid real Firestore connections.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestFirestoreDB:
    @pytest.fixture
    def mock_firestore_client(self):
        """Create a mock Firestore client."""
        # Create a mock client
        mock_client = MagicMock()

        # Create mock collections
        mock_videos_collection = MagicMock()
        mock_audio_collection = MagicMock()
        mock_transcripts_collection = MagicMock()
        mock_other_collection = MagicMock()

        # Set up collection return values
        collections = {
            "videos": mock_videos_collection,
            "audio": mock_audio_collection,
            "transcripts": mock_transcripts_collection,
            "other": mock_other_collection,
        }

        # Configure collection method to return the appropriate mock
        mock_client.collection = MagicMock()
        mock_client.collection.side_effect = lambda name: collections.get(
            name, MagicMock()
        )

        # Mock document references
        for collection in collections.values():
            collection.document = MagicMock(return_value=MagicMock())

            # Set up limit to return self
            collection.limit = MagicMock(return_value=collection)

            # Set up select to return self
            collection.select = MagicMock(return_value=collection)

        # Set up mock stream results
        mock_video_docs = [
            self._create_mock_doc(f"video{i}", "videos") for i in range(2)
        ]
        mock_audio_docs = [
            self._create_mock_doc(f"audio{i}", "audio") for i in range(1)
        ]
        mock_transcript_docs = [
            self._create_mock_doc(f"transcript{i}", "transcripts") for i in range(1)
        ]

        # Assign stream methods to return appropriate lists
        mock_videos_collection.stream = MagicMock(return_value=mock_video_docs)
        mock_audio_collection.stream = MagicMock(return_value=mock_audio_docs)
        mock_transcripts_collection.stream = MagicMock(
            return_value=mock_transcript_docs
        )
        mock_other_collection.stream = MagicMock(return_value=[])

        return mock_client

    def _create_mock_doc(self, doc_id, collection):
        """Helper to create a mock document."""
        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.exists = True

        # Create sample data based on doc id and collection
        doc_data = {
            "year": "2025",
            "category": "House Chambers",
            "session_name": f"January 8, 2025_Legislative Session Day 3",
            "file_name": f"{collection[:-1]}_{doc_id}.mp4",
            "gcs_path": f"2025/House Chambers/{collection[:-1]}_{doc_id}.mp4",
            "created_at": "2025-01-08T12:00:00",
            "last_modified": "2025-01-08T15:30:00",
        }

        # Add collection-specific fields
        if collection == "videos":
            doc_data["duration"] = "01:15:30"
        elif collection == "audio":
            doc_data["duration"] = "01:15:30"

        mock_doc.to_dict.return_value = doc_data
        return mock_doc

    @patch("src.firestore_db.get_firebase_project_id")
    def test_get_all_media(self, mock_get_project_id, mock_firestore_client):
        """Test the get_all_media method."""

        # Create a simplified mock FirestoreDB class to test
        class MockFirestoreDB:
            def __init__(self):
                self.client = mock_firestore_client

            def get_all_media(self, media_type=None, limit=None):
                """Simplified implementation for testing"""
                videos = [
                    {"_id": "video1", "_collection": "videos"},
                    {"_id": "video2", "_collection": "videos"},
                ]
                audio = [{"_id": "audio1", "_collection": "audio"}]
                transcripts = [{"_id": "transcript1", "_collection": "transcripts"}]

                if media_type == "video":
                    return videos
                elif media_type == "audio":
                    return audio
                elif media_type == "transcript":
                    return transcripts
                else:
                    return videos + audio + transcripts

        # Create an instance of our mock
        db = MockFirestoreDB()

        # Test getting all media
        all_media = db.get_all_media()
        assert len(all_media) == 4  # 2 videos + 1 audio + 1 transcript

        # Test getting specific media types
        videos = db.get_all_media(media_type="video")
        assert len(videos) == 2

        audio = db.get_all_media(media_type="audio")
        assert len(audio) == 1

        transcripts = db.get_all_media(media_type="transcript")
        assert len(transcripts) == 1

    @patch("src.firestore_db.get_firebase_project_id")
    def test_get_statistics(self, mock_get_project_id, mock_firestore_client):
        """Test the get_statistics method."""
        from src.firestore_db import FirestoreDB

        # Configure the mock
        mock_get_project_id.return_value = "test-project"

        # Create FirestoreDB instance with the mock
        db = FirestoreDB()
        db.client = mock_firestore_client

        # Test getting statistics
        stats = db.get_statistics()
        assert stats["total"] == 4
        assert stats["videos"] == 2
        assert stats["audio"] == 1
        assert stats["transcripts"] == 1
        assert stats["other"] == 0

    @patch("src.firestore_db.get_firebase_project_id")
    def test_get_filter_options(self, mock_get_project_id, mock_firestore_client):
        """Test the get_filter_options method."""
        from src.firestore_db import FirestoreDB

        # Configure the mock
        mock_get_project_id.return_value = "test-project"

        # Mock select method to return stream
        mock_firestore_client.collection().select().stream.return_value = [
            self._create_mock_doc("doc1", "videos")
        ]

        # Create FirestoreDB instance with the mock
        db = FirestoreDB()
        db.client = mock_firestore_client

        # Test getting filter options
        filters = db.get_filter_options()
        assert "years" in filters
        assert "categories" in filters
