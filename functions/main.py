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

# Add directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, "src")
cloud_functions_dir = os.path.join(parent_dir, "src", "cloud_functions")

# Add paths to Python path
for path in [current_dir, parent_dir, src_dir, cloud_functions_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import services (with fallback import paths)
try:
    from src.cloud_functions.services.gateway_service import route_request
except ImportError:
    try:
        from cloud_functions.services.gateway_service import route_request
    except ImportError:
        from services.gateway_service import route_request

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
