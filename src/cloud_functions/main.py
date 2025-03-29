"""
Idaho Legislature Media Portal API - Cloud Functions Main Entry Point
"""

import logging
import os
import sys
from datetime import datetime

# Add directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import services
from services.gateway_service import route_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def api_handler(request):
    """
    Main Cloud Function entry point for API requests.
    Routes all requests through the gateway service.

    Args:
        request: The HTTP request object

    Returns:
        The HTTP response
    """
    # Add timestamp to request object for easier access
    request.timestamp = datetime.now().isoformat()

    # Log the request
    logger.info(f"Received request: {request.method} {request.path}")

    # Route the request through the gateway
    return route_request(request)
