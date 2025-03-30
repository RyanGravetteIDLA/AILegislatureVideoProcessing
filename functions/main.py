"""
Idaho Legislature Media Portal API - Firebase Cloud Function Entry Point
"""

import logging
from firebase_functions import https_fn
from firebase_admin import initialize_app
import os
import sys

# Initialize Firebase
initialize_app()

# Configure Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the gateway service
from src.cloud_functions.services.gateway_service import route_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@https_fn.on_request()
def media_portal_api(req: https_fn.Request) -> https_fn.Response:
    """
    Main Cloud Function entry point for API requests.
    Routes all requests through the gateway service.

    Args:
        req: The HTTP request object

    Returns:
        The HTTP response
    """
    # Log the request
    logger.info(f"Received request: {req.method} {req.path}")

    try:
        # Route the request through the gateway
        response = route_request(req)

        # Convert to Firebase Functions response format
        return https_fn.Response(
            response.body, status=response.status_code, headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return https_fn.Response(
            f"Internal server error: {str(e)}",
            status=500,
            headers={"Content-Type": "text/plain"},
        )
