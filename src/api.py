"""
API module for serving media data to the frontend application.
Provides RESTful endpoints for videos, audio, and transcripts.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Local imports
from transcript_db import get_all_transcripts, Session as DBSession, Transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'api.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('api')

# Initialize FastAPI app
app = FastAPI(
    title="Idaho Legislature Media API",
    description="API for accessing Idaho Legislature media content",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

# Data models for API responses
class MediaBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    year: str
    category: str
    date: Optional[str] = None
    
    class Config:
        orm_mode = True

class VideoItem(MediaBase):
    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    url: str

class AudioItem(MediaBase):
    duration: Optional[str] = None
    url: str

class TranscriptItem(MediaBase):
    url: str

# Helper functions
def format_date(timestamp: Optional[datetime]) -> Optional[str]:
    """Format a datetime object to ISO date string."""
    if timestamp:
        return timestamp.strftime("%Y-%m-%d")
    return None

def transcript_to_model(transcript: Transcript) -> Dict[str, Any]:
    """Convert a Transcript database model to API response model."""
    session_title = f"{transcript.category} - {transcript.session_name}"
    
    # Determine the media type based on file extension
    file_ext = os.path.splitext(transcript.file_path)[1].lower()
    
    base_data = {
        "id": transcript.id,
        "title": session_title,
        "description": f"Legislative Session {transcript.year}",
        "year": transcript.year,
        "category": transcript.category,
        "date": format_date(transcript.last_modified)
    }
    
    # For now, use file_path as URL (will be updated with actual URLs later)
    base_url = f"/api/files/{transcript.year}/{transcript.category}/{transcript.file_name}"
    
    return {
        **base_data,
        "url": base_url,
        "duration": "00:00:00"  # Placeholder
    }

# API Routes
@app.get("/api/videos", response_model=List[VideoItem])
def get_videos(
    db: Session = Depends(get_db),
    year: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get a list of available videos.
    Optionally filter by year, category, or search term.
    """
    try:
        # Get all transcripts
        transcripts = get_all_transcripts()
        
        # Filter to only include videos
        video_files = [t for t in transcripts if os.path.splitext(t.file_path)[1].lower() in ['.mp4', '.avi', '.mov']]
        
        # Apply filters
        if year:
            video_files = [v for v in video_files if v.year == year]
        if category:
            video_files = [v for v in video_files if v.category == category]
        if search:
            search_lower = search.lower()
            video_files = [v for v in video_files if 
                          search_lower in v.session_name.lower() or 
                          search_lower in v.category.lower()]
        
        # Convert to response models
        return [VideoItem(**transcript_to_model(v)) for v in video_files]
    
    except Exception as e:
        logger.error(f"Error retrieving videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/videos/{video_id}", response_model=VideoItem)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get a specific video by ID."""
    try:
        transcripts = get_all_transcripts()
        video = next((t for t in transcripts if t.id == video_id and 
                     os.path.splitext(t.file_path)[1].lower() in ['.mp4', '.avi', '.mov']), None)
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return VideoItem(**transcript_to_model(video))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio", response_model=List[AudioItem])
def get_audio_files(
    db: Session = Depends(get_db),
    year: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get a list of available audio files.
    Optionally filter by year, category, or search term.
    """
    try:
        # Get all transcripts
        transcripts = get_all_transcripts()
        
        # Filter to only include audio files
        audio_files = [t for t in transcripts if os.path.splitext(t.file_path)[1].lower() in ['.mp3', '.wav', '.m4a']]
        
        # Apply filters
        if year:
            audio_files = [a for a in audio_files if a.year == year]
        if category:
            audio_files = [a for a in audio_files if a.category == category]
        if search:
            search_lower = search.lower()
            audio_files = [a for a in audio_files if 
                          search_lower in a.session_name.lower() or 
                          search_lower in a.category.lower()]
        
        # Convert to response models
        return [AudioItem(**transcript_to_model(a)) for a in audio_files]
    
    except Exception as e:
        logger.error(f"Error retrieving audio files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{audio_id}", response_model=AudioItem)
def get_audio(audio_id: int, db: Session = Depends(get_db)):
    """Get a specific audio file by ID."""
    try:
        transcripts = get_all_transcripts()
        audio = next((t for t in transcripts if t.id == audio_id and 
                     os.path.splitext(t.file_path)[1].lower() in ['.mp3', '.wav', '.m4a']), None)
        
        if not audio:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return AudioItem(**transcript_to_model(audio))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audio {audio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transcripts", response_model=List[TranscriptItem])
def get_transcripts(
    db: Session = Depends(get_db),
    year: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get a list of available transcripts.
    Optionally filter by year, category, or search term.
    """
    try:
        # Get all transcripts
        transcripts = get_all_transcripts()
        
        # Filter to only include transcript files
        transcript_files = [t for t in transcripts if os.path.splitext(t.file_path)[1].lower() in ['.txt', '.pdf', '.docx', '.md']]
        
        # Apply filters
        if year:
            transcript_files = [t for t in transcript_files if t.year == year]
        if category:
            transcript_files = [t for t in transcript_files if t.category == category]
        if search:
            search_lower = search.lower()
            transcript_files = [t for t in transcript_files if 
                               search_lower in t.session_name.lower() or 
                               search_lower in t.category.lower()]
        
        # Convert to response models
        return [TranscriptItem(**transcript_to_model(t)) for t in transcript_files]
    
    except Exception as e:
        logger.error(f"Error retrieving transcripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transcripts/{transcript_id}", response_model=TranscriptItem)
def get_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """Get a specific transcript by ID."""
    try:
        transcripts = get_all_transcripts()
        transcript = next((t for t in transcripts if t.id == transcript_id and 
                          os.path.splitext(t.file_path)[1].lower() in ['.txt', '.pdf', '.docx', '.md']), None)
        
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return TranscriptItem(**transcript_to_model(transcript))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcript {transcript_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filters")
def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options (years and categories)."""
    try:
        transcripts = get_all_transcripts()
        
        years = sorted(list(set(t.year for t in transcripts)))
        categories = sorted(list(set(t.category for t in transcripts)))
        
        return {
            "years": years,
            "categories": categories
        }
    
    except Exception as e:
        logger.error(f"Error retrieving filter options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Get statistics about the available media."""
    try:
        transcripts = get_all_transcripts()
        
        video_count = len([t for t in transcripts if os.path.splitext(t.file_path)[1].lower() in ['.mp4', '.avi', '.mov']])
        audio_count = len([t for t in transcripts if os.path.splitext(t.file_path)[1].lower() in ['.mp3', '.wav', '.m4a']])
        transcript_count = len([t for t in transcripts if os.path.splitext(t.file_path)[1].lower() in ['.txt', '.pdf', '.docx', '.md']])
        
        return {
            "total": len(transcripts),
            "videos": video_count,
            "audio": audio_count,
            "transcripts": transcript_count
        }
    
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a health check endpoint
@app.get("/api/health")
def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    # Start the server
    uvicorn.run("api:app", host="0.0.0.0", port=5000, reload=True)