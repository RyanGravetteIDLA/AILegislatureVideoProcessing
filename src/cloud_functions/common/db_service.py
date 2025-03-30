"""
Database service for the Idaho Legislature Media Portal API.
Provides access to unified database interface.
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the unified database interface
try:
    from db_interface import get_db_interface, MediaItem
except ImportError:
    # Fallback to relative import
    from ...db_interface import get_db_interface, MediaItem

from .utils import setup_logging

# Set up logging
logger = setup_logging("db_service")

# Singleton database interface
_db_interface = None


def get_db_interface_instance():
    """
    Get or initialize the database interface
    
    Returns:
        The database interface instance
    """
    global _db_interface
    
    if _db_interface is None:
        try:
            _db_interface = get_db_interface()
            logger.info("Database interface initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database interface: {e}")
            raise
    
    return _db_interface


# For backward compatibility with code that expects Firestore directly
def get_db_client():
    """
    Legacy function: Get the Firestore client directly
    
    Returns:
        The Firestore client instance
    """
    db = get_db_interface_instance()
    
    # Access the raw Firestore client through the implementation
    if hasattr(db.db_implementation, 'client'):
        return db.db_implementation.client
    
    # Fallback to creating a new client
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'legislativevideoreviewswithai')
    from google.cloud import firestore
    return firestore.Client(project=project_id)


# Mock data for testing when database is not available
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


# Enhanced functions that use the unified database interface
def get_videos_from_db(year=None, category=None, search=None):
    """
    Get videos from the database with optional filters
    
    Args:
        year: Optional filter by year
        category: Optional filter by category
        search: Optional search term
        
    Returns:
        List of video objects
    """
    try:
        db = get_db_interface_instance()
        all_items = db.get_all_items(media_type="video")
        
        # Apply filters
        filtered_items = []
        for item in all_items:
            # Skip non-video items (shouldn't happen with media_type filter)
            if item.media_type != "video":
                continue
                
            # Apply year filter
            if year and item.year != year:
                continue
                
            # Apply category filter
            if category and item.category != category:
                continue
                
            # Apply search filter
            if search:
                search_term = search.lower()
                title = item.file_name.lower()
                session = item.session_name.lower()
                
                if search_term not in title and search_term not in session:
                    continue
                    
            # Item passed all filters, add to result
            filtered_items.append(item)
            
        return filtered_items
    except Exception as e:
        logger.error(f"Error getting videos from database: {e}")
        # Return mock data if database access fails
        return get_mock_videos()


def get_audio_from_db(year=None, category=None, search=None):
    """
    Get audio from the database with optional filters
    
    Args:
        year: Optional filter by year
        category: Optional filter by category
        search: Optional search term
        
    Returns:
        List of audio objects
    """
    try:
        db = get_db_interface_instance()
        all_items = db.get_all_items(media_type="audio")
        
        # Apply filters
        filtered_items = []
        for item in all_items:
            # Skip non-audio items (shouldn't happen with media_type filter)
            if item.media_type != "audio":
                continue
                
            # Apply year filter
            if year and item.year != year:
                continue
                
            # Apply category filter
            if category and item.category != category:
                continue
                
            # Apply search filter
            if search:
                search_term = search.lower()
                title = item.file_name.lower()
                session = item.session_name.lower()
                
                if search_term not in title and search_term not in session:
                    continue
                    
            # Item passed all filters, add to result
            filtered_items.append(item)
            
        return filtered_items
    except Exception as e:
        logger.error(f"Error getting audio from database: {e}")
        # Return mock data if database access fails
        return get_mock_audio()


def get_transcripts_from_db(year=None, category=None, search=None):
    """
    Get transcripts from the database with optional filters
    
    Args:
        year: Optional filter by year
        category: Optional filter by category
        search: Optional search term
        
    Returns:
        List of transcript objects
    """
    try:
        db = get_db_interface_instance()
        all_items = db.get_all_items(media_type="transcript")
        
        # Apply filters
        filtered_items = []
        for item in all_items:
            # Skip non-transcript items (shouldn't happen with media_type filter)
            if item.media_type != "transcript":
                continue
                
            # Apply year filter
            if year and item.year != year:
                continue
                
            # Apply category filter
            if category and item.category != category:
                continue
                
            # Apply search filter
            if search:
                search_term = search.lower()
                title = item.file_name.lower()
                session = item.session_name.lower()
                
                if search_term not in title and search_term not in session:
                    continue
                    
            # Item passed all filters, add to result
            filtered_items.append(item)
            
        return filtered_items
    except Exception as e:
        logger.error(f"Error getting transcripts from database: {e}")
        # Return mock data if database access fails
        return get_mock_transcripts()


def get_filter_options():
    """
    Get available filter options for the API
    
    Returns:
        Dictionary with years and categories
    """
    try:
        db = get_db_interface_instance()
        all_items = db.get_all_items()
        
        # Extract unique years and categories
        years = set()
        categories = set()
        
        for item in all_items:
            if item.year:
                years.add(item.year)
            if item.category:
                categories.add(item.category)
                
        return {
            "years": sorted(list(years)),
            "categories": sorted(list(categories))
        }
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        # Return some mock options if database access fails
        return {
            "years": ["2023", "2024", "2025"],
            "categories": ["House Chambers", "Senate Chambers", "Joint Session"]
        }