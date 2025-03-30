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
logger = setup_logging("video_service")


def get_all_videos(year=None, category=None, search=None, limit=100, with_related=True):
    """
    Get all videos with optional filtering and related media

    Args:
        year: Filter by year
        category: Filter by category
        search: Search term
        limit: Maximum number of results
        with_related: Whether to include related media information

    Returns:
        List of videos as dictionaries
    """
    logger.info(
        f"Getting videos with filters - year: {year}, category: {category}, search: {search}"
    )

    try:
        # Get database client
        db = get_db_client()

        # Start with videos collection reference
        videos_ref = db.collection("videos")

        # Apply filters if provided
        if year:
            videos_ref = videos_ref.where("year", "==", year)

        if category:
            videos_ref = videos_ref.where("category", "==", category)

        # Apply limit
        videos_ref = videos_ref.limit(limit)

        # Get documents
        video_docs = list(videos_ref.stream())

        # If no results and search term is provided, do a client-side search
        if search and not video_docs:
            all_videos = db.collection("videos").limit(limit).stream()
            video_docs = []

            search_lower = search.lower()
            for doc in all_videos:
                data = doc.to_dict()
                session_name = data.get("session_name", "").lower()
                category_val = data.get("category", "").lower()

                if search_lower in session_name or search_lower in category_val:
                    video_docs.append(doc)

        # Convert to VideoItem objects
        videos = []
        for doc in video_docs:
            try:
                video_data = doc.to_dict()
                
                # If with_related is True, and relations aren't already present, look for related media
                if with_related and not (video_data.get("related_audio_id") or video_data.get("related_transcript_id")):
                    session_id = video_data.get("session_id")
                    if session_id:
                        # Find related audio by session_id
                        try:
                            audio_query = db.collection("audio").where("session_id", "==", session_id).limit(1)
                            audio_docs = list(audio_query.stream())
                            if audio_docs:
                                audio_doc = audio_docs[0]
                                video_data["related_audio_id"] = audio_doc.id
                                video_data["related_audio_path"] = audio_doc.get("gcs_path")
                                logger.info(f"Found related audio {audio_doc.id} for video {doc.id}")
                        except Exception as e:
                            logger.warning(f"Error finding related audio for video {doc.id}: {e}")
                        
                        # Find related transcript by session_id
                        try:
                            transcript_query = db.collection("transcripts").where("session_id", "==", session_id).limit(1)
                            transcript_docs = list(transcript_query.stream())
                            if transcript_docs:
                                transcript_doc = transcript_docs[0]
                                video_data["related_transcript_id"] = transcript_doc.id
                                video_data["related_transcript_path"] = transcript_doc.get("gcs_path")
                                logger.info(f"Found related transcript {transcript_doc.id} for video {doc.id}")
                        except Exception as e:
                            logger.warning(f"Error finding related transcript for video {doc.id}: {e}")
                
                video_item = VideoItem.from_firestore(doc.id, video_data)
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


def get_video_by_id(video_id, with_related=True):
    """
    Get a specific video by ID

    Args:
        video_id: The video ID
        with_related: Whether to include related media information

    Returns:
        Video as a dictionary or None if not found
    """
    logger.info(f"Getting video with ID: {video_id}")

    try:
        # Get database client
        db = get_db_client()

        # Get document
        doc_ref = db.collection("videos").document(video_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(f"Video not found: {video_id}")
            return None

        video_data = doc.to_dict()
        
        # If with_related is True, and relations aren't already present, look for related media
        if with_related and not (video_data.get("related_audio_id") or video_data.get("related_transcript_id")):
            session_id = video_data.get("session_id")
            if session_id:
                # Find related audio by session_id
                try:
                    audio_query = db.collection("audio").where("session_id", "==", session_id).limit(1)
                    audio_docs = list(audio_query.stream())
                    if audio_docs:
                        audio_doc = audio_docs[0]
                        video_data["related_audio_id"] = audio_doc.id
                        video_data["related_audio_path"] = audio_doc.get("gcs_path")
                        logger.info(f"Found related audio {audio_doc.id} for video {doc.id}")
                except Exception as e:
                    logger.warning(f"Error finding related audio for video {doc.id}: {e}")
                
                # Find related transcript by session_id
                try:
                    transcript_query = db.collection("transcripts").where("session_id", "==", session_id).limit(1)
                    transcript_docs = list(transcript_query.stream())
                    if transcript_docs:
                        transcript_doc = transcript_docs[0]
                        video_data["related_transcript_id"] = transcript_doc.id
                        video_data["related_transcript_path"] = transcript_doc.get("gcs_path")
                        logger.info(f"Found related transcript {transcript_doc.id} for video {doc.id}")
                except Exception as e:
                    logger.warning(f"Error finding related transcript for video {doc.id}: {e}")

        # Convert to VideoItem
        video_item = VideoItem.from_firestore(doc.id, video_data)
        return video_item.to_dict()

    except Exception as e:
        logger.error(f"Error retrieving video {video_id}: {e}")
        return None


def find_related_media_for_video(video_id):
    """
    Find related audio and transcript for a specific video

    Args:
        video_id: The video ID

    Returns:
        Dictionary with related media information
    """
    logger.info(f"Finding related media for video ID: {video_id}")
    
    result = {
        "audio": None,
        "transcript": None
    }
    
    try:
        # Get the video first
        video = get_video_by_id(video_id, with_related=False)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            return result
            
        # Get database client
        db = get_db_client()
        
        # Strategy 1: Try to use related_audio_id and related_transcript_id if present
        if video.get("related_audio_id"):
            try:
                audio_doc = db.collection("audio").document(video["related_audio_id"]).get()
                if audio_doc.exists:
                    result["audio"] = audio_doc.to_dict()
                    result["audio"]["id"] = audio_doc.id
                    logger.info(f"Found related audio {audio_doc.id} via related_audio_id")
            except Exception as e:
                logger.warning(f"Error retrieving related audio {video.get('related_audio_id')}: {e}")
                
        if video.get("related_transcript_id"):
            try:
                transcript_doc = db.collection("transcripts").document(video["related_transcript_id"]).get()
                if transcript_doc.exists:
                    result["transcript"] = transcript_doc.to_dict()
                    result["transcript"]["id"] = transcript_doc.id
                    logger.info(f"Found related transcript {transcript_doc.id} via related_transcript_id")
            except Exception as e:
                logger.warning(f"Error retrieving related transcript {video.get('related_transcript_id')}: {e}")
        
        # Strategy 2: Try to find related media by session_id
        if (not result["audio"] or not result["transcript"]) and video.get("session_id"):
            session_id = video["session_id"]
            logger.info(f"Looking for related media with session_id: {session_id}")
            
            # Find audio by session_id
            if not result["audio"]:
                try:
                    audio_query = db.collection("audio").where("session_id", "==", session_id).limit(1)
                    audio_docs = list(audio_query.stream())
                    if audio_docs:
                        audio_doc = audio_docs[0]
                        result["audio"] = audio_doc.to_dict()
                        result["audio"]["id"] = audio_doc.id
                        logger.info(f"Found related audio {audio_doc.id} via session_id")
                except Exception as e:
                    logger.warning(f"Error finding audio by session_id {session_id}: {e}")
            
            # Find transcript by session_id
            if not result["transcript"]:
                try:
                    transcript_query = db.collection("transcripts").where("session_id", "==", session_id).limit(1)
                    transcript_docs = list(transcript_query.stream())
                    if transcript_docs:
                        transcript_doc = transcript_docs[0]
                        result["transcript"] = transcript_doc.to_dict()
                        result["transcript"]["id"] = transcript_doc.id
                        logger.info(f"Found related transcript {transcript_doc.id} via session_id")
                except Exception as e:
                    logger.warning(f"Error finding transcript by session_id {session_id}: {e}")
        
        # Strategy 3: Try to find related media by matching year/category/date
        if not result["audio"] or not result["transcript"]:
            year = video.get("year")
            category = video.get("category")
            date = video.get("date")
            
            if year and category:
                logger.info(f"Looking for related media with year: {year}, category: {category}, date: {date}")
                
                # Find audio by year/category/date
                if not result["audio"] and date:
                    try:
                        audio_query = db.collection("audio").where("year", "==", year).where("category", "==", category)
                        audio_docs = list(audio_query.stream())
                        
                        # Filter by date if available
                        matching_audio = None
                        for doc in audio_docs:
                            doc_data = doc.to_dict()
                            doc_date = doc_data.get("date")
                            if doc_date and doc_date.startswith(date):
                                matching_audio = doc
                                break
                        
                        if matching_audio:
                            result["audio"] = matching_audio.to_dict()
                            result["audio"]["id"] = matching_audio.id
                            logger.info(f"Found related audio {matching_audio.id} via year/category/date")
                    except Exception as e:
                        logger.warning(f"Error finding audio by year/category/date: {e}")
                
                # Find transcript by year/category/date
                if not result["transcript"] and date:
                    try:
                        transcript_query = db.collection("transcripts").where("year", "==", year).where("category", "==", category)
                        transcript_docs = list(transcript_query.stream())
                        
                        # Filter by date if available
                        matching_transcript = None
                        for doc in transcript_docs:
                            doc_data = doc.to_dict()
                            doc_date = doc_data.get("date")
                            if doc_date and doc_date.startswith(date):
                                matching_transcript = doc
                                break
                        
                        if matching_transcript:
                            result["transcript"] = matching_transcript.to_dict()
                            result["transcript"]["id"] = matching_transcript.id
                            logger.info(f"Found related transcript {matching_transcript.id} via year/category/date")
                    except Exception as e:
                        logger.warning(f"Error finding transcript by year/category/date: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error finding related media for video {video_id}: {e}")
        return result


def handle_videos_request(request=None):
    """
    Handle request for all videos

    Args:
        request: The HTTP request

    Returns:
        JSON response with videos
    """
    # Extract query parameters if request is provided
    year = request.args.get("year") if request and hasattr(request, "args") else None
    category = (
        request.args.get("category") if request and hasattr(request, "args") else None
    )
    search = (
        request.args.get("search") if request and hasattr(request, "args") else None
    )
    with_related = (
        request.args.get("with_related", "true").lower() == "true"
        if request and hasattr(request, "args")
        else True
    )

    # Get videos
    videos = get_all_videos(year, category, search, with_related=with_related)

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


def handle_video_related_media_request(video_id):
    """
    Handle request for related media for a specific video

    Args:
        video_id: The video ID

    Returns:
        JSON response with related media or error
    """
    # Get related media
    related_media = find_related_media_for_video(video_id)

    # Return response
    return create_response(related_media)
