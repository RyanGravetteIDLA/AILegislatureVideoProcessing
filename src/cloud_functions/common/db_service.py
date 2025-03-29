"""
Database service for the Idaho Legislature Media Portal API.
Provides access to Firestore database.
"""

import os
from google.cloud import firestore
from .utils import setup_logging

# Set up logging
logger = setup_logging('db_service')

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
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'legislativevideoreviewswithai')
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
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/mock1.mp4"
        },
        {
            "id": "mock2",
            "title": "Senate Chambers - Afternoon Session",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-16",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/mock2.mp4"
        }
    ]