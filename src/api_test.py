#!/usr/bin/env python3
"""
Simple test API to verify deployment to Cloud Run.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("api_test")

# Initialize FastAPI app
app = FastAPI(
    title="Idaho Legislature Media API - TEST",
    description="Simple test API for Cloud Run deployment",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint to test basic functionality."""
    return {
        "message": "Idaho Legislature Media API - Test Version",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "port": os.environ.get("PORT", "Not set"),
            "host": os.environ.get("HOST", "Not set"),
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "Not set"),
            "bucket": os.environ.get("GCS_BUCKET_NAME", "Not set"),
        },
    }


@app.get("/api/health")
def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "test",
    }


@app.get("/api/videos")
def get_videos():
    """Test endpoint that returns mock video data."""
    return [
        {
            "id": "test1",
            "title": "Test Video 1",
            "description": "This is a test video",
            "year": "2025",
            "category": "House Chambers",
            "date": "2025-03-01",
            "duration": "01:30:00",
            "url": "https://example.com/test1.mp4",
        },
        {
            "id": "test2",
            "title": "Test Video 2",
            "description": "This is another test video",
            "year": "2025",
            "category": "Senate Chambers",
            "date": "2025-03-02",
            "duration": "00:45:00",
            "url": "https://example.com/test2.mp4",
        },
    ]


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting test API server on port {port}")
    uvicorn.run("api_test:app", host="0.0.0.0", port=port)
