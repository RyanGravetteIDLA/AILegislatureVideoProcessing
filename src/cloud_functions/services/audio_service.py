"""
Audio service for the Idaho Legislature Media Portal API.
Provides access to audio data.
"""

# Handle both direct import and relative import
try:
    from ..common.utils import setup_logging, create_response, create_error_response
    from ..common.db_service import get_db_client, get_mock_audio
    from ..models.audio import AudioItem
except ImportError:
    from common.utils import setup_logging, create_response, create_error_response
    from common.db_service import get_db_client, get_mock_audio
    from models.audio import AudioItem

# Set up logging
logger = setup_logging("audio_service")


def get_all_audio(year=None, category=None, search=None, limit=100):
    """
    Get all audio files with optional filtering

    Args:
        year: Filter by year
        category: Filter by category
        search: Search term
        limit: Maximum number of results

    Returns:
        List of audio items as dictionaries
    """
    logger.info(
        f"Getting audio with filters - year: {year}, category: {category}, search: {search}"
    )

    try:
        # Get database client
        db = get_db_client()

        # Start with audio collection reference
        audio_ref = db.collection("audio")

        # Apply filters if provided
        if year:
            audio_ref = audio_ref.where("year", "==", year)

        if category:
            audio_ref = audio_ref.where("category", "==", category)

        # Apply limit
        audio_ref = audio_ref.limit(limit)

        # Get documents
        audio_docs = list(audio_ref.stream())

        # If no results and search term is provided, do a client-side search
        if search and not audio_docs:
            all_audio = db.collection("audio").limit(limit).stream()
            audio_docs = []

            search_lower = search.lower()
            for doc in all_audio:
                data = doc.to_dict()
                session_name = data.get("session_name", "").lower()
                category_val = data.get("category", "").lower()

                if search_lower in session_name or search_lower in category_val:
                    audio_docs.append(doc)

        # Convert to AudioItem objects
        audio_items = []
        for doc in audio_docs:
            try:
                audio_item = AudioItem.from_firestore(doc.id, doc.to_dict())
                audio_items.append(audio_item.to_dict())
            except Exception as e:
                logger.error(f"Error processing audio document {doc.id}: {e}")

        # If no audio items found, return mock data
        if not audio_items:
            logger.info("No audio found in Firestore, returning mock data")
            return get_mock_audio()

        return audio_items

    except Exception as e:
        logger.error(f"Error retrieving audio: {e}")
        # Fall back to mock data on error
        return get_mock_audio()


def get_audio_by_id(audio_id):
    """
    Get a specific audio item by ID

    Args:
        audio_id: The audio ID

    Returns:
        Audio item as a dictionary or None if not found
    """
    logger.info(f"Getting audio with ID: {audio_id}")

    try:
        # Get database client
        db = get_db_client()

        # Get document
        doc_ref = db.collection("audio").document(audio_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(f"Audio not found: {audio_id}")
            return None

        # Convert to AudioItem
        audio_item = AudioItem.from_firestore(doc.id, doc.to_dict())
        return audio_item.to_dict()

    except Exception as e:
        logger.error(f"Error retrieving audio {audio_id}: {e}")
        return None


def handle_audio_request(request=None):
    """
    Handle request for all audio files

    Args:
        request: The HTTP request

    Returns:
        JSON response with audio items
    """
    # Extract query parameters if request is provided
    year = request.args.get("year") if request and hasattr(request, "args") else None
    category = (
        request.args.get("category") if request and hasattr(request, "args") else None
    )
    search = (
        request.args.get("search") if request and hasattr(request, "args") else None
    )

    # Get audio items
    audio_items = get_all_audio(year, category, search)

    # Return response
    return create_response(audio_items)


def handle_audio_item_request(audio_id):
    """
    Handle request for a specific audio item

    Args:
        audio_id: The audio ID

    Returns:
        JSON response with audio item or error
    """
    # Get audio item
    audio_item = get_audio_by_id(audio_id)

    # Return response
    if audio_item:
        return create_response(audio_item)
    else:
        return create_error_response("Audio not found", 404)
