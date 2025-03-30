"""
Common utilities for all microservices.
"""

import logging
from flask import jsonify
from datetime import datetime


# Configure logging
def setup_logging(name):
    """Set up logging for a service"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Only add handlers if they don't exist
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    return logger


# CORS headers
def get_cors_headers():
    """Get CORS headers for API responses"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }


# Standard response format
def create_response(data, status_code=200):
    """Create a standardized API response"""
    return jsonify(data), status_code, get_cors_headers()


# Error response
def create_error_response(message, status_code=400):
    """Create a standardized error response"""
    return (
        jsonify(
            {"error": True, "message": message, "timestamp": datetime.now().isoformat()}
        ),
        status_code,
        get_cors_headers(),
    )


# Options response for CORS
def create_options_response():
    """Create response for OPTIONS requests (CORS preflight)"""
    return ("", 204, get_cors_headers())


# Request parser
def parse_request_path(request):
    """Parse request path - handles direct function calls and HTTP requests"""
    # Get the path from the request
    path = request.path

    # Handle direct function calls via gcloud (which might not set the path)
    json_data = request.get_json(silent=True)
    if json_data and "path" in json_data:
        path = json_data["path"]

    return path
