"""
Video service for the Idaho Legislature Media Portal API.
Provides access to video data.
"""

# Handle both direct import and relative import
try:
    from ..common.utils import setup_logging, create_response, create_error_response
    from ..common.db_service import get_db_client, get_mock_videos
    from ..models.video import VideoItem
except ImportError:
    from common.utils import setup_logging, create_response, create_error_response
    from common.db_service import get_db_client, get_mock_videos
    from models.video import VideoItem

# Set up logging
logger = setup_logging('video_service')

def get_all_videos(year=None, category=None, search=None, limit=100):
    """
    Get all videos with optional filtering
    
    Args:
        year: Filter by year
        category: Filter by category
        search: Search term
        limit: Maximum number of results
        
    Returns:
        List of videos as dictionaries
    """
    logger.info(f"Getting videos with filters - year: {year}, category: {category}, search: {search}")
    
    try:
        # Get database client
        db = get_db_client()
        
        # Start with videos collection reference
        videos_ref = db.collection('videos')
        
        # Apply filters if provided
        if year:
            videos_ref = videos_ref.where('year', '==', year)
        
        if category:
            videos_ref = videos_ref.where('category', '==', category)
        
        # Apply limit
        videos_ref = videos_ref.limit(limit)
        
        # Get documents
        video_docs = list(videos_ref.stream())
        
        # If no results and search term is provided, do a client-side search
        if search and not video_docs:
            all_videos = db.collection('videos').limit(limit).stream()
            video_docs = []
            
            search_lower = search.lower()
            for doc in all_videos:
                data = doc.to_dict()
                session_name = data.get('session_name', '').lower()
                category_val = data.get('category', '').lower()
                
                if (search_lower in session_name or search_lower in category_val):
                    video_docs.append(doc)
        
        # Convert to VideoItem objects
        videos = []
        for doc in video_docs:
            try:
                video_item = VideoItem.from_firestore(doc.id, doc.to_dict())
                videos.append(video_item.to_dict())
            except Exception as e:
                logger.error(f"Error processing video document {doc.id}: {e}")
        
        # If no videos found, return mock data
        if not videos:
            logger.info("No videos found in Firestore, returning mock data")
            return get_mock_videos()
            
        return videos
        
    except Exception as e:
        logger.error(f"Error retrieving videos: {e}")
        # Fall back to mock data
        return get_mock_videos()

def get_video_by_id(video_id):
    """
    Get a specific video by ID
    
    Args:
        video_id: The video ID
        
    Returns:
        Video as a dictionary or None if not found
    """
    logger.info(f"Getting video with ID: {video_id}")
    
    try:
        # Get database client
        db = get_db_client()
        
        # Get document
        doc_ref = db.collection('videos').document(video_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"Video not found: {video_id}")
            return None
        
        # Convert to VideoItem
        video_item = VideoItem.from_firestore(doc.id, doc.to_dict())
        return video_item.to_dict()
        
    except Exception as e:
        logger.error(f"Error retrieving video {video_id}: {e}")
        return None

def handle_videos_request(request=None):
    """
    Handle request for all videos
    
    Args:
        request: The HTTP request
        
    Returns:
        JSON response with videos
    """
    # Extract query parameters if request is provided
    year = request.args.get('year') if request and hasattr(request, 'args') else None
    category = request.args.get('category') if request and hasattr(request, 'args') else None
    search = request.args.get('search') if request and hasattr(request, 'args') else None
    
    # Get videos
    videos = get_all_videos(year, category, search)
    
    # Return response
    return create_response(videos)

def handle_video_request(video_id):
    """
    Handle request for a specific video
    
    Args:
        video_id: The video ID
        
    Returns:
        JSON response with video or error
    """
    # Get video
    video = get_video_by_id(video_id)
    
    # Return response
    if video:
        return create_response(video)
    else:
        return create_error_response("Video not found", 404)