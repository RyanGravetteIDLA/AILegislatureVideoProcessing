"""
Idaho Legislature Media Portal API - Cloud Functions Main Entry Point
"""

import logging
from datetime import datetime
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