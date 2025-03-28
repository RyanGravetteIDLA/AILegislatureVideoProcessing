"""
File server module for serving static media files.
Works alongside the API to deliver video, audio, and transcript files.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'file_server.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('file_server')

# Define base directory for media files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DOWNLOADS_DIR = os.path.join(DATA_DIR, 'downloads')

# Initialize FastAPI app
app = FastAPI(
    title="Idaho Legislature Media File Server",
    description="File server for Idaho Legislature media content",
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

# Mount the downloads directory for serving files
app.mount("/files", StaticFiles(directory=DOWNLOADS_DIR), name="files")

@app.get("/api/files/{year}/{category}/{filename}")
async def get_file(year: str, category: str, filename: str):
    """
    Serve a specific media file by path.
    
    Args:
        year: The year folder
        category: The category folder
        filename: The file name
    
    Returns:
        FileResponse: The requested file
    """
    try:
        file_path = os.path.join(DOWNLOADS_DIR, year, category, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"Serving file: {file_path}")
        return FileResponse(file_path)
    
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Start the file server
    uvicorn.run("file_server:app", host="0.0.0.0", port=5001, reload=True)