"""
Database service for the Idaho Legislature Media Portal API.
Provides access to Firestore database.
"""

import os
from google.cloud import firestore
from .utils import setup_logging

# Set up logging
logger = setup_logging("db_service")

# Singleton database client
_db_client = None


def get_db_client():
    """
    Get or initialize the Firestore client

    Returns:
        The Firestore client instance
    """
    global _db_client

    if _db_client is None:
        project_id = os.environ.get(
            "GOOGLE_CLOUD_PROJECT", "legislativevideoreviewswithai"
        )
        logger.info(f"Initializing Firestore client for project: {project_id}")

        try:
            _db_client = firestore.Client(project=project_id)
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

    return _db_client


# Mock data for testing when Firestore is not available
def get_mock_videos():
    """
    Return mock videos for testing

    Returns:
        List of mock video objects
    """
    return [
        {
            "id": "mock1",
            "title": "House Chambers - Morning Session",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-15",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/mock1.mp4",
        },
        {
            "id": "mock2",
            "title": "Senate Chambers - Afternoon Session",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-16",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/mock2.mp4",
        },
    ]


def get_mock_audio():
    """
    Return mock audio for testing

    Returns:
        List of mock audio objects
    """
    return [
        {
            "id": "mock_audio1",
            "title": "House Floor - Budget Discussion",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-18",
            "duration": "01:24:30",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/audio/mock1.mp3",
        },
        {
            "id": "mock_audio2",
            "title": "Senate Committee - Education",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-19",
            "duration": "00:45:12",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/audio/mock2.mp3",
        },
        {
            "id": "mock_audio3",
            "title": "House Floor - Healthcare Debate",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-20",
            "duration": "02:15:45",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/audio/mock3.mp3",
        },
        {
            "id": "mock_audio4",
            "title": "Senate Floor - Education Funding",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-21",
            "duration": "01:30:00",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/audio/mock4.mp3",
        },
        {
            "id": "mock_audio5",
            "title": "Joint Session - State of the State",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Joint Session",
            "date": "2025-01-07",
            "duration": "01:15:30",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/audio/mock5.mp3",
        },
    ]


def get_mock_transcripts():
    """
    Return mock transcripts for testing

    Returns:
        List of mock transcript objects
    """
    return [
        {
            "id": "mock_transcript1",
            "title": "House Floor - Budget Discussion",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-18",
            "content": "Speaker: I'd like to call the meeting to order. Today we'll be discussing the budget proposal for the upcoming fiscal year...",
            "related_video_id": "mock1",
            "related_audio_id": "mock_audio1",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/transcripts/mock1.txt",
        },
        {
            "id": "mock_transcript2",
            "title": "Senate Committee - Education",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-19",
            "content": "Chair: Welcome to the Senate Education Committee. Today we're discussing the proposed changes to the state's education funding formula...",
            "related_video_id": "mock2",
            "related_audio_id": "mock_audio2",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/transcripts/mock2.txt",
        },
        {
            "id": "mock_transcript3",
            "title": "House Floor - Healthcare Debate",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-20",
            "content": "Speaker: The House will now consider HB101, relating to healthcare reform. The chair recognizes the representative from District 14...",
            "related_video_id": "mock3",
            "related_audio_id": "mock_audio3",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/transcripts/mock3.txt",
        },
        {
            "id": "mock_transcript4",
            "title": "Senate Floor - Education Funding",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-21",
            "content": "President: The Senate will now consider SB42, relating to education funding. The chair recognizes the senator from District 7...",
            "related_video_id": "mock4",
            "related_audio_id": "mock_audio4",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/transcripts/mock4.txt",
        },
        {
            "id": "mock_transcript5",
            "title": "Joint Session - State of the State",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Joint Session",
            "date": "2025-01-07",
            "content": "Governor: Mr. President, Mr. Speaker, members of the legislature, and my fellow Idahoans. It is my privilege to address you today on the state of our great state...",
            "related_video_id": "mock5",
            "related_audio_id": "mock_audio5",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com/transcripts/mock5.txt",
        },
    ]
