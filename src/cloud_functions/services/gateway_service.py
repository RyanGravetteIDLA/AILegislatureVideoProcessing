"""
API Gateway service for the Idaho Legislature Media Portal API.
Routes requests to appropriate microservices.
"""

# Handle both direct import and relative import
try:
    from ..common.utils import (
        setup_logging,
        create_response,
        create_error_response,
        create_options_response,
        parse_request_path,
    )
    from .health_service import handle_health_request
    from .video_service import handle_videos_request, handle_video_request
    from .audio_service import handle_audio_request, handle_audio_item_request
    from .transcript_service import (
        handle_transcripts_request,
        handle_transcript_request,
        handle_video_transcripts_request,
        handle_audio_transcripts_request,
    )
    from .stats_service import handle_stats_request, handle_filters_request
except ImportError:
    from common.utils import (
        setup_logging,
        create_response,
        create_error_response,
        create_options_response,
        parse_request_path,
    )
    from services.health_service import handle_health_request
    from services.video_service import handle_videos_request, handle_video_request
    from services.audio_service import handle_audio_request, handle_audio_item_request
    from services.transcript_service import (
        handle_transcripts_request,
        handle_transcript_request,
        handle_video_transcripts_request,
        handle_audio_transcripts_request,
    )
    from services.stats_service import handle_stats_request, handle_filters_request

# Set up logging
logger = setup_logging("gateway_service")


def route_request(request):
    """
    Main routing function for API gateway

    Args:
        request: The HTTP request object

    Returns:
        The response from the appropriate service
    """
    # Handle OPTIONS request (CORS preflight)
    if request.method == "OPTIONS":
        return create_options_response()

    # Log the request
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request args: {request.args}")

    # Get the path
    path = parse_request_path(request)
    logger.info(f"Parsed path: {path}")

    # Route the request based on path
    try:
        # Health service
        if path == "/health" or path == "/api/health":
            return handle_health_request()

        # Videos collection endpoint
        elif path == "/videos" or path == "/api/videos":
            return handle_videos_request(request)

        # Individual video endpoint
        elif path.startswith("/api/videos/") or path.startswith("/videos/"):
            # Extract video_id from path
            parts = path.split("/")
            if len(parts) >= 3:
                video_id = parts[-1]
                return handle_video_request(video_id)
            else:
                return create_error_response("Invalid video ID", 400)

        # Audio collection endpoint
        elif path == "/audio" or path == "/api/audio":
            return handle_audio_request(request)

        # Individual audio endpoint
        elif path.startswith("/api/audio/") or path.startswith("/audio/"):
            # Extract audio_id from path
            parts = path.split("/")
            if len(parts) >= 3:
                audio_id = parts[-1]
                return handle_audio_item_request(audio_id)
            else:
                return create_error_response("Invalid audio ID", 400)

        # Transcripts collection endpoint
        elif path == "/transcripts" or path == "/api/transcripts":
            return handle_transcripts_request(request)

        # Individual transcript endpoint
        elif path.startswith("/api/transcripts/") or path.startswith("/transcripts/"):
            # Extract transcript_id from path
            parts = path.split("/")
            if len(parts) >= 3:
                transcript_id = parts[-1]
                return handle_transcript_request(transcript_id)
            else:
                return create_error_response("Invalid transcript ID", 400)

        # Video transcripts endpoint
        elif path.startswith("/api/videos/") and path.endswith("/transcripts"):
            # Extract video_id from path
            # Format: /api/videos/{video_id}/transcripts
            parts = path.split("/")
            if len(parts) >= 4:
                video_id = parts[-2]
                return handle_video_transcripts_request(video_id)
            else:
                return create_error_response("Invalid video ID", 400)

        # Audio transcripts endpoint
        elif path.startswith("/api/audio/") and path.endswith("/transcripts"):
            # Extract audio_id from path
            # Format: /api/audio/{audio_id}/transcripts
            parts = path.split("/")
            if len(parts) >= 4:
                audio_id = parts[-2]
                return handle_audio_transcripts_request(audio_id)
            else:
                return create_error_response("Invalid audio ID", 400)

        # Stats endpoint
        elif path == "/stats" or path == "/api/stats":
            return handle_stats_request()

        # Filters endpoint
        elif path == "/filters" or path == "/api/filters":
            return handle_filters_request()

        # Root or API info endpoint
        elif path == "/" or path == "/api" or not path:
            return create_response(
                {
                    "message": "Idaho Legislature Media Portal API",
                    "version": "1.0.0",
                    "timestamp": request.timestamp,
                    "endpoints": [
                        "/api/health",
                        "/api/videos",
                        "/api/audio",
                        "/api/transcripts",
                        "/api/stats",
                        "/api/filters",
                    ],
                }
            )

        # Handle unknown paths
        else:
            logger.warning(f"Unknown path requested: {path}")
            return create_error_response(f"Endpoint {path} not found", 404)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_error_response(f"Internal server error: {str(e)}", 500)
