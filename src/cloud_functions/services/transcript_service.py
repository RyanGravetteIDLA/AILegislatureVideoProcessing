"""
Transcript service for the Idaho Legislature Media Portal API.
Provides access to transcript data.
"""

# Handle both direct import and relative import
try:
    from ..common.utils import setup_logging, create_response, create_error_response
    from ..common.db_service import get_db_client, get_mock_transcripts
    from ..models.transcript import TranscriptItem
except ImportError:
    from common.utils import setup_logging, create_response, create_error_response
    from common.db_service import get_db_client, get_mock_transcripts
    from models.transcript import TranscriptItem

# Set up logging
logger = setup_logging("transcript_service")


def get_all_transcripts(year=None, category=None, search=None, limit=100):
    """
    Get all transcripts with optional filtering

    Args:
        year: Filter by year
        category: Filter by category
        search: Search term in content or metadata
        limit: Maximum number of results

    Returns:
        List of transcripts as dictionaries
    """
    logger.info(
        f"Getting transcripts with filters - year: {year}, category: {category}, search: {search}"
    )

    try:
        # Get database client
        db = get_db_client()

        # Start with transcripts collection reference
        transcripts_ref = db.collection("transcripts")

        # Apply filters if provided
        if year:
            transcripts_ref = transcripts_ref.where("year", "==", year)

        if category:
            transcripts_ref = transcripts_ref.where("category", "==", category)

        # Apply limit
        transcripts_ref = transcripts_ref.limit(limit)

        # Get documents
        transcript_docs = list(transcripts_ref.stream())

        # If search term is provided and we have documents, do a client-side search
        if search and transcript_docs:
            filtered_docs = []
            search_lower = search.lower()

            for doc in transcript_docs:
                data = doc.to_dict()
                session_name = data.get("session_name", "").lower()
                category_val = data.get("category", "").lower()
                content = data.get("content", "").lower()

                if (
                    search_lower in session_name
                    or search_lower in category_val
                    or search_lower in content
                ):
                    filtered_docs.append(doc)

            transcript_docs = filtered_docs

        # Convert to TranscriptItem objects
        transcripts = []
        for doc in transcript_docs:
            try:
                transcript_item = TranscriptItem.from_firestore(doc.id, doc.to_dict())
                transcripts.append(transcript_item.to_dict())
            except Exception as e:
                logger.error(f"Error processing transcript document {doc.id}: {e}")

        # If no transcripts found, return mock data
        if not transcripts:
            logger.info("No transcripts found in Firestore, returning mock data")
            return get_mock_transcripts()

        return transcripts

    except Exception as e:
        logger.error(f"Error retrieving transcripts: {e}")
        # Fall back to mock data
        return get_mock_transcripts()


def get_transcript_by_id(transcript_id):
    """
    Get a specific transcript by ID

    Args:
        transcript_id: The transcript ID

    Returns:
        Transcript as a dictionary or None if not found
    """
    logger.info(f"Getting transcript with ID: {transcript_id}")

    try:
        # Get database client
        db = get_db_client()

        # Get document
        doc_ref = db.collection("transcripts").document(transcript_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(f"Transcript not found: {transcript_id}")
            return None

        # Convert to TranscriptItem
        transcript_item = TranscriptItem.from_firestore(doc.id, doc.to_dict())
        return transcript_item.to_dict()

    except Exception as e:
        logger.error(f"Error retrieving transcript {transcript_id}: {e}")
        return None


def get_transcripts_by_video(video_id):
    """
    Get transcripts related to a specific video

    Args:
        video_id: The video ID

    Returns:
        List of related transcripts
    """
    logger.info(f"Getting transcripts for video ID: {video_id}")

    try:
        # Get database client
        db = get_db_client()

        # Query transcripts with matching video_id
        transcripts_ref = db.collection("transcripts").where("video_id", "==", video_id)
        transcript_docs = list(transcripts_ref.stream())

        # Convert to TranscriptItem objects
        transcripts = []
        for doc in transcript_docs:
            try:
                transcript_item = TranscriptItem.from_firestore(doc.id, doc.to_dict())
                transcripts.append(transcript_item.to_dict())
            except Exception as e:
                logger.error(f"Error processing transcript document {doc.id}: {e}")

        return transcripts

    except Exception as e:
        logger.error(f"Error retrieving transcripts for video {video_id}: {e}")
        return []


def get_transcripts_by_audio(audio_id):
    """
    Get transcripts related to a specific audio

    Args:
        audio_id: The audio ID

    Returns:
        List of related transcripts
    """
    logger.info(f"Getting transcripts for audio ID: {audio_id}")

    try:
        # Get database client
        db = get_db_client()

        # Query transcripts with matching audio_id
        transcripts_ref = db.collection("transcripts").where("audio_id", "==", audio_id)
        transcript_docs = list(transcripts_ref.stream())

        # Convert to TranscriptItem objects
        transcripts = []
        for doc in transcript_docs:
            try:
                transcript_item = TranscriptItem.from_firestore(doc.id, doc.to_dict())
                transcripts.append(transcript_item.to_dict())
            except Exception as e:
                logger.error(f"Error processing transcript document {doc.id}: {e}")

        return transcripts

    except Exception as e:
        logger.error(f"Error retrieving transcripts for audio {audio_id}: {e}")
        return []


def handle_transcripts_request(request=None):
    """
    Handle request for all transcripts

    Args:
        request: The HTTP request

    Returns:
        JSON response with transcripts
    """
    # Extract query parameters if request is provided
    year = request.args.get("year") if request and hasattr(request, "args") else None
    category = (
        request.args.get("category") if request and hasattr(request, "args") else None
    )
    search = (
        request.args.get("search") if request and hasattr(request, "args") else None
    )

    # Get transcripts
    transcripts = get_all_transcripts(year, category, search)

    # Return response
    return create_response(transcripts)


def handle_transcript_request(transcript_id):
    """
    Handle request for a specific transcript

    Args:
        transcript_id: The transcript ID

    Returns:
        JSON response with transcript or error
    """
    # Get transcript
    transcript = get_transcript_by_id(transcript_id)

    # Return response
    if transcript:
        return create_response(transcript)
    else:
        return create_error_response("Transcript not found", 404)


def handle_video_transcripts_request(video_id):
    """
    Handle request for transcripts related to a video

    Args:
        video_id: The video ID

    Returns:
        JSON response with related transcripts
    """
    # Get transcripts
    transcripts = get_transcripts_by_video(video_id)

    # Return response
    return create_response(transcripts)


def handle_audio_transcripts_request(audio_id):
    """
    Handle request for transcripts related to an audio file

    Args:
        audio_id: The audio ID

    Returns:
        JSON response with related transcripts
    """
    # Get transcripts
    transcripts = get_transcripts_by_audio(audio_id)

    # Return response
    return create_response(transcripts)
