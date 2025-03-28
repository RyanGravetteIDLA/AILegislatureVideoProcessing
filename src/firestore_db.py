#!/usr/bin/env python3
"""
Firestore database module for accessing media data.
Replacement for the transcript_db.py module, using Firestore instead of SQLite.
"""

import os
import sys
import logging
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Add project root to path for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Set up directory paths
logs_dir = os.path.join(base_dir, 'data', 'logs')

# Create directories if they don't exist
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'firestore_db.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('firestore_db')


def get_firebase_project_id():
    """
    Get the Firebase project ID from environment or configuration.
    
    Returns:
        str: Firebase project ID
    """
    # First try to read from environment variable
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        # Try to get from application default credentials
        try:
            import google.auth
            _, project_id = google.auth.default()
        except Exception as e:
            logger.warning(f"Could not get project ID from default credentials: {e}")
    
    # Fallback to hardcoded value (from our migration plan)
    if not project_id:
        project_id = 'legislativevideoreviewswithai'
        logger.warning(f"Using fallback project ID: {project_id}")
        
    # Set the environment variable for the service account if needed
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  'credentials', 'legislativevideoreviewswithai-80ed70b021b5.json')
        if os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to {credentials_path}")
    
    return project_id


class FirestoreDB:
    """
    Firestore database client for accessing media data.
    Serves as a replacement for the SQLite-based transcript_db module.
    """
    
    def __init__(self, project_id=None):
        """
        Initialize the Firestore client.
        
        Args:
            project_id (str, optional): Firebase project ID. If None, tries to get from environment.
        """
        self.project_id = project_id or get_firebase_project_id()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Firestore client."""
        try:
            self.client = firestore.Client(project=self.project_id)
            logger.info(f"Initialized Firestore client for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    def get_all_media(self, media_type=None, limit=None):
        """
        Get all media records from Firestore.
        
        Args:
            media_type (str, optional): Filter by media type ('video', 'audio', 'transcript')
            limit (int, optional): Maximum number of records to return
            
        Returns:
            list: List of Firestore document snapshots
        """
        results = []
        collections = []
        
        # Determine which collections to query
        if media_type == 'video':
            collections = ['videos']
        elif media_type == 'audio':
            collections = ['audio']
        elif media_type == 'transcript':
            collections = ['transcripts']
        else:
            collections = ['videos', 'audio', 'transcripts', 'other']
        
        # Query each collection
        for collection in collections:
            query = self.client.collection(collection)
            if limit:
                query = query.limit(limit)
            
            # Execute query and add results
            docs = list(query.stream())
            for doc in docs:
                # Add collection name and document ID to the data
                data = doc.to_dict()
                data['_collection'] = collection
                data['_id'] = doc.id
                results.append(data)
        
        return results
    
    def get_media_by_id(self, media_id, collection=None):
        """
        Get a specific media record by ID.
        
        Args:
            media_id (str): Document ID
            collection (str, optional): Collection name. If None, searches all collections.
            
        Returns:
            dict: Document data or None if not found
        """
        if collection:
            collections = [collection]
        else:
            collections = ['videos', 'audio', 'transcripts', 'other']
        
        for coll in collections:
            doc_ref = self.client.collection(coll).document(media_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                data['_collection'] = coll
                data['_id'] = doc.id
                return data
        
        return None
    
    def search_media(self, query_text, media_type=None, year=None, category=None, limit=100):
        """
        Search for media records by text, year, category, etc.
        
        Args:
            query_text (str): Text to search for in session_name or category
            media_type (str, optional): Filter by media type
            year (str, optional): Filter by year
            category (str, optional): Filter by category
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of matching document data
        """
        results = []
        collections = []
        
        # Determine which collections to query
        if media_type == 'video':
            collections = ['videos']
        elif media_type == 'audio':
            collections = ['audio']
        elif media_type == 'transcript':
            collections = ['transcripts']
        else:
            collections = ['videos', 'audio', 'transcripts', 'other']
        
        # Query each collection
        for collection in collections:
            query = self.client.collection(collection)
            
            # Apply filters
            if year:
                query = query.where(filter=FieldFilter("year", "==", year))
            if category:
                query = query.where(filter=FieldFilter("category", "==", category))
            
            # Execute query and add results
            docs = list(query.limit(limit).stream())
            
            # Filter by query text manually (since Firestore doesn't support full-text search)
            for doc in docs:
                data = doc.to_dict()
                session_name = data.get('session_name', '').lower()
                category_name = data.get('category', '').lower()
                
                if (query_text.lower() in session_name or 
                    query_text.lower() in category_name):
                    # Add collection name and document ID to the data
                    data['_collection'] = collection
                    data['_id'] = doc.id
                    results.append(data)
        
        return results[:limit]
    
    def get_filter_options(self):
        """
        Get available filter options (years and categories).
        
        Returns:
            dict: Dictionary with years and categories
        """
        years = set()
        categories = set()
        
        collections = ['videos', 'audio', 'transcripts', 'other']
        
        for collection in collections:
            # Get years
            year_query = self.client.collection(collection).select(['year'])
            for doc in year_query.stream():
                data = doc.to_dict()
                if 'year' in data and data['year']:
                    years.add(data['year'])
            
            # Get categories
            category_query = self.client.collection(collection).select(['category'])
            for doc in category_query.stream():
                data = doc.to_dict()
                if 'category' in data and data['category']:
                    categories.add(data['category'])
        
        return {
            'years': sorted(list(years)),
            'categories': sorted(list(categories))
        }
    
    def get_statistics(self):
        """
        Get statistics about the available media.
        
        Returns:
            dict: Dictionary with media counts
        """
        video_count = len(list(self.client.collection('videos').limit(1000).stream()))
        audio_count = len(list(self.client.collection('audio').limit(1000).stream()))
        transcript_count = len(list(self.client.collection('transcripts').limit(1000).stream()))
        other_count = len(list(self.client.collection('other').limit(1000).stream()))
        
        return {
            'total': video_count + audio_count + transcript_count + other_count,
            'videos': video_count,
            'audio': audio_count,
            'transcripts': transcript_count,
            'other': other_count
        }
    
    def add_media(self, data, collection):
        """
        Add a new media record to Firestore.
        
        Args:
            data (dict): Media data
            collection (str): Collection name ('videos', 'audio', 'transcripts', 'other')
            
        Returns:
            tuple: (bool, str) - Success status and document ID
        """
        if collection not in ['videos', 'audio', 'transcripts', 'other']:
            logger.error(f"Invalid collection: {collection}")
            return False, None
        
        # Add timestamps
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        
        try:
            # Add the document
            doc_ref = self.client.collection(collection).document()
            doc_ref.set(data)
            logger.info(f"Added new {collection} record: {doc_ref.id}")
            return True, doc_ref.id
        
        except Exception as e:
            logger.error(f"Error adding {collection} record: {e}")
            return False, None
    
    def update_media(self, doc_id, data, collection):
        """
        Update an existing media record in Firestore.
        
        Args:
            doc_id (str): Document ID
            data (dict): Updated data
            collection (str): Collection name
            
        Returns:
            bool: Success status
        """
        if collection not in ['videos', 'audio', 'transcripts', 'other']:
            logger.error(f"Invalid collection: {collection}")
            return False
        
        try:
            # Update timestamps
            data['updated_at'] = datetime.now()
            
            # Update the document
            doc_ref = self.client.collection(collection).document(doc_id)
            doc_ref.update(data)
            logger.info(f"Updated {collection} record: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating {collection} record {doc_id}: {e}")
            return False
    
    def delete_media(self, doc_id, collection):
        """
        Delete a media record from Firestore.
        
        Args:
            doc_id (str): Document ID
            collection (str): Collection name
            
        Returns:
            bool: Success status
        """
        if collection not in ['videos', 'audio', 'transcripts', 'other']:
            logger.error(f"Invalid collection: {collection}")
            return False
        
        try:
            # Delete the document
            doc_ref = self.client.collection(collection).document(doc_id)
            doc_ref.delete()
            logger.info(f"Deleted {collection} record: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting {collection} record {doc_id}: {e}")
            return False
    
    def get_unprocessed_media(self, media_type=None):
        """
        Get media records that haven't been processed yet.
        
        Args:
            media_type (str, optional): Filter by media type
            
        Returns:
            list: List of unprocessed media records
        """
        results = []
        collections = []
        
        # Determine which collections to query
        if media_type == 'video':
            collections = ['videos']
        elif media_type == 'audio':
            collections = ['audio']
        elif media_type == 'transcript':
            collections = ['transcripts']
        else:
            collections = ['videos', 'audio', 'transcripts', 'other']
        
        # Query each collection
        for collection in collections:
            query = self.client.collection(collection).where(
                filter=FieldFilter("processed", "==", False)
            )
            
            # Execute query and add results
            docs = list(query.stream())
            for doc in docs:
                data = doc.to_dict()
                data['_collection'] = collection
                data['_id'] = doc.id
                results.append(data)
        
        return results


# Create a singleton instance
_firestore_db_instance = None

def get_firestore_db():
    """
    Get the Firestore DB instance (singleton pattern).
    
    Returns:
        FirestoreDB: Firestore database client instance
    """
    global _firestore_db_instance
    if _firestore_db_instance is None:
        _firestore_db_instance = FirestoreDB()
    return _firestore_db_instance


if __name__ == "__main__":
    # Example usage
    db = get_firestore_db()
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Media Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Videos: {stats['videos']}")
    print(f"  Audio: {stats['audio']}")
    print(f"  Transcripts: {stats['transcripts']}")
    print(f"  Other: {stats['other']}")
    
    # Get filter options
    filters = db.get_filter_options()
    print(f"\nFilter Options:")
    print(f"  Years: {filters['years']}")
    print(f"  Categories: {filters['categories']}")