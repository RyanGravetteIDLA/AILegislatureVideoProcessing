"""
Health service for the Idaho Legislature Media Portal API.
"""

from datetime import datetime
from ..common.utils import setup_logging, create_response

# Set up logging
logger = setup_logging('health_service')

def handle_health_request():
    """Handle health check request"""
    logger.info("Health check endpoint called")
    
    return create_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'health_service',
        'version': '1.0.0'
    })