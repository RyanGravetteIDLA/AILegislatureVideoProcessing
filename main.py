"""
Idaho Legislature Media Portal API - Cloud Function Version
"""

import os
import logging
from datetime import datetime
from flask import jsonify
from google.cloud import firestore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firestore client
db = None

def initialize_firestore():
    """Initialize Firestore client"""
    global db
    if db is None:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'legislativevideoreviewswithai')
        db = firestore.Client(project=project_id)
    return db

def get_mock_videos():
    """Return mock videos for testing"""
    return [
        {
            "id": "mock1",
            "title": "House Chambers - Morning Session",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-15",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/mock1.mp4"
        },
        {
            "id": "mock2",
            "title": "Senate Chambers - Afternoon Session",
            "description": "Legislative Session 2025",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-16",
            "url": "https://storage.googleapis.com/legislativevideoreviewswithai.firebasestorage.app/videos/mock2.mp4"
        }
    ]

def get_videos_from_firestore(limit=10):
    """Retrieve videos from Firestore"""
    logger.info("Retrieving videos from Firestore")
    try:
        db = initialize_firestore()
        videos_ref = db.collection('videos').limit(limit)
        videos = []
        
        for doc in videos_ref.stream():
            data = doc.to_dict()
            videos.append({
                "id": doc.id,
                "title": f"{data.get('category', 'Unknown')} - {data.get('session_name', 'Unknown')}",
                "description": f"Legislative Session {data.get('year', 'Unknown')}",
                "year": data.get('year', 'Unknown'),
                "category": data.get('category', 'Unknown'),
                "date": data.get('last_modified') or data.get('created_at'),
                "url": data.get('gcs_path', '')
            })
        
        return videos if videos else get_mock_videos()
    except Exception as e:
        logger.error(f"Error getting videos from Firestore: {e}")
        return get_mock_videos()

def api_handler(request):
    """Main Cloud Function entry point for API requests"""
    # Handle CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }
    
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    # Log the request for debugging
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request args: {request.args}")
    logger.info(f"Request json: {request.get_json(silent=True)}")
    
    # Get the path from the request
    path = request.path
    
    # Handle direct function calls via gcloud (which might not set the path)
    json_data = request.get_json(silent=True)
    if json_data and 'path' in json_data:
        path = json_data['path']
        logger.info(f"Using path from JSON data: {path}")
    
    # Route the request based on path
    if path == '/health' or path == '/api/health':
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'cloud-function'
        }), 200, headers
    
    elif path == '/videos' or path == '/api/videos':
        videos = get_videos_from_firestore()
        return jsonify(videos), 200, headers
    
    elif path == '/' or path == '/api' or not path:
        return jsonify({
            'message': 'Idaho Legislature Media Portal API',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': [
                '/api/health',
                '/api/videos'
            ]
        }), 200, headers
    
    else:
        return jsonify({
            'error': 'Not Found',
            'message': f'Endpoint {path} not found'
        }), 404, headers