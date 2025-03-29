"""
Stats service for the Idaho Legislature Media Portal API.
Provides statistics and filter options.
"""

# Handle both direct import and relative import
try:
    from ..common.utils import setup_logging, create_response, create_error_response
    from ..common.db_service import get_db_client
except ImportError:
    from common.utils import setup_logging, create_response, create_error_response
    from common.db_service import get_db_client

# Set up logging
logger = setup_logging('stats_service')

def get_collection_count(db, collection_name, limit=1000):
    """
    Get the count of documents in a collection
    
    Args:
        db: Firestore client
        collection_name: Name of the collection
        limit: Maximum number of documents to count
        
    Returns:
        int: Number of documents in the collection
    """
    try:
        # Get collection reference
        collection_ref = db.collection(collection_name)
        
        # Count documents
        docs = list(collection_ref.limit(limit).stream())
        return len(docs)
    except Exception as e:
        logger.error(f"Error counting documents in {collection_name}: {e}")
        return 0

def get_media_stats():
    """
    Get statistics about media collections
    
    Returns:
        dict: Statistics about media collections
    """
    logger.info("Getting media statistics")
    
    try:
        # Get database client
        db = get_db_client()
        
        # Count documents in each collection
        video_count = get_collection_count(db, 'videos')
        audio_count = get_collection_count(db, 'audio')
        transcript_count = get_collection_count(db, 'transcripts')
        
        # Calculate total
        total_count = video_count + audio_count + transcript_count
        
        # Return statistics
        return {
            'total': total_count,
            'videos': video_count,
            'audio': audio_count,
            'transcripts': transcript_count
        }
    except Exception as e:
        logger.error(f"Error getting media statistics: {e}")
        return {
            'total': 0,
            'videos': 0,
            'audio': 0,
            'transcripts': 0
        }

def get_filter_options():
    """
    Get available filter options (years and categories)
    
    Returns:
        dict: Years and categories available for filtering
    """
    logger.info("Getting filter options")
    
    try:
        # Get database client
        db = get_db_client()
        
        years = set()
        categories = set()
        
        # Get years and categories from videos collection
        videos_ref = db.collection('videos')
        for doc in videos_ref.stream():
            data = doc.to_dict()
            if 'year' in data and data['year']:
                years.add(data['year'])
            if 'category' in data and data['category']:
                categories.add(data['category'])
        
        # Return filter options
        return {
            'years': sorted(list(years)),
            'categories': sorted(list(categories))
        }
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return {
            'years': [],
            'categories': []
        }

def handle_stats_request():
    """
    Handle request for media statistics
    
    Returns:
        JSON response with statistics
    """
    logger.info("Stats endpoint called")
    
    # Get statistics
    stats = get_media_stats()
    
    # Return response
    return create_response(stats)

def handle_filters_request():
    """
    Handle request for filter options
    
    Returns:
        JSON response with filter options
    """
    logger.info("Filters endpoint called")
    
    # Get filter options
    filters = get_filter_options()
    
    # Return response
    return create_response(filters)