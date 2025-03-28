#!/usr/bin/env python3
"""
Simplified Firestore API for Cloud Run deployment.
Provides access to videos, audio, and transcripts in Firestore.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger('simple_firestore_api')

# Initialize FastAPI app
app = FastAPI(
    title="Idaho Legislature Media API - Simplified",
    description="Simple Firestore API for Idaho Legislature media content",
    version="1.0.0"
)

# Add CORS middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://legislativevideoreviewswithai.web.app', 
                  'https://legislativevideoreviewswithai.firebaseapp.com', 
                  'http://localhost:5173', 
                  'http://localhost:4173'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firestore client
def get_firestore_client():
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'legislativevideoreviewswithai')
    logger.info(f"Initializing Firestore client for project: {project_id}")
    
    try:
        return firestore.Client(project=project_id)
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}")
        raise

# Create a global client
try:
    db = get_firestore_client()
    logger.info("Firestore client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firestore: {e}")
    db = None

@app.get("/")
def root():
    """Root endpoint to test basic functionality."""
    return {
        "message": "Idaho Legislature Media API - Simplified Firestore Version",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "port": os.environ.get("PORT", "Not set"),
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "Not set"),
            "bucket": os.environ.get("GCS_BUCKET_NAME", "Not set"),
            "firestore": "Connected" if db is not None else "Not connected"
        }
    }

@app.get("/api/health")
def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "database": "firestore"
    }

@app.get("/api/videos")
def get_videos():
    """Get videos from Firestore."""
    if db is None:
        return [
            {"id": "mock1", "title": "Mock Video (Firestore not connected)", "description": "This is a mock video", "year": "2025", "category": "House Chambers"}
        ]
    
    try:
        # Get videos from Firestore
        videos_ref = db.collection('videos').limit(10)
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
        
        return videos
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio")
def get_audio():
    """Get audio files from Firestore."""
    if db is None:
        return [
            {"id": "mock1", "title": "Mock Audio (Firestore not connected)", "description": "This is a mock audio file", "year": "2025", "category": "House Chambers"}
        ]
    
    try:
        # Get audio from Firestore
        audio_ref = db.collection('audio').limit(10)
        audio_files = []
        
        for doc in audio_ref.stream():
            data = doc.to_dict()
            audio_files.append({
                "id": doc.id,
                "title": f"{data.get('category', 'Unknown')} - {data.get('session_name', 'Unknown')}",
                "description": f"Legislative Session {data.get('year', 'Unknown')}",
                "year": data.get('year', 'Unknown'),
                "category": data.get('category', 'Unknown'),
                "date": data.get('last_modified') or data.get('created_at'),
                "url": data.get('gcs_path', '')
            })
        
        return audio_files
    except Exception as e:
        logger.error(f"Error getting audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transcripts")
def get_transcripts():
    """Get transcripts from Firestore."""
    if db is None:
        return [
            {"id": "mock1", "title": "Mock Transcript (Firestore not connected)", "description": "This is a mock transcript", "year": "2025", "category": "House Chambers"}
        ]
    
    try:
        # Get transcripts from Firestore
        transcripts_ref = db.collection('transcripts').limit(10)
        transcripts = []
        
        for doc in transcripts_ref.stream():
            data = doc.to_dict()
            transcripts.append({
                "id": doc.id,
                "title": f"{data.get('category', 'Unknown')} - {data.get('session_name', 'Unknown')}",
                "description": f"Legislative Session {data.get('year', 'Unknown')}",
                "year": data.get('year', 'Unknown'),
                "category": data.get('category', 'Unknown'),
                "date": data.get('last_modified') or data.get('created_at'),
                "url": data.get('gcs_path', '')
            })
        
        return transcripts
    except Exception as e:
        logger.error(f"Error getting transcripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    """Get media statistics from Firestore."""
    if db is None:
        return {"total": 0, "videos": 0, "audio": 0, "transcripts": 0}
    
    try:
        # Count documents in each collection
        videos = len(list(db.collection('videos').limit(1000).stream()))
        audio = len(list(db.collection('audio').limit(1000).stream()))
        transcripts = len(list(db.collection('transcripts').limit(1000).stream()))
        
        return {
            "total": videos + audio + transcripts,
            "videos": videos,
            "audio": audio,
            "transcripts": transcripts
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting simplified Firestore API server on port {port}")
    uvicorn.run("simple_firestore_api:app", host="0.0.0.0", port=port)