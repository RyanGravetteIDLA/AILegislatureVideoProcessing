"""
File server module for serving static media files.
Works alongside the API to deliver video, audio, and transcript files.

This module implements a separate FastAPI application focused on serving media files.
It handles static file serving, direct file access via parameterized paths, and ensures
proper error handling when files are not found.

The file server is designed to work in conjunction with the API server, where:
- API server provides metadata and endpoints for querying content
- File server provides the actual media content delivery

This separation of concerns allows for:
- Better performance optimization for each specific task
- Independent scaling of API and file serving functions
- More focused error handling and logging

The file server supports multiple storage backends:
- Local filesystem storage (default)
- Google Cloud Storage (when configured)

This allows for efficient scaling and reduced local storage requirements.
"""

import os
import logging
import tempfile
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for imports
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the GCS and secrets modules, but don't fail if they're not available
try:
    from src.cloud_storage import get_default_gcs_client
    from src.secrets_manager import get_cloud_storage_settings

    gcs_available = True
except ImportError as e:
    print(f"Warning: Could not import cloud storage modules: {e}")
    gcs_available = False

# Configure logging
# Create logs directory if it doesn't exist
logs_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs"
)
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "file_server.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("file_server")

# Define base directory for media files
# Construct absolute paths to ensure consistency across different execution contexts
# DATA_DIR points to the main data directory of the project
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)
# DOWNLOADS_DIR is where all downloaded media files are stored in a structured way
DOWNLOADS_DIR = os.path.join(DATA_DIR, "downloads")
# TEMP_DIR is for temporarily storing files downloaded from cloud storage
TEMP_DIR = os.path.join(DATA_DIR, "temp")

# Create directories if they don't exist
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize GCS client if available
gcs_client = None
if gcs_available:
    try:
        logger.info("Initializing Google Cloud Storage client")
        gcs_client = get_default_gcs_client()
        logger.info(f"GCS client initialized for bucket: {gcs_client.bucket_name}")
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        gcs_available = False

# Get cloud storage preferences from secrets manager or fall back to environment variables
if gcs_available:
    try:
        # Get settings from secrets manager
        cloud_settings = get_cloud_storage_settings()
        USE_CLOUD_STORAGE = cloud_settings.get("use_cloud_storage", False)
        CLOUD_STORAGE_PUBLIC = cloud_settings.get("cloud_storage_public", False)
        PREFER_CLOUD_STORAGE = cloud_settings.get("prefer_cloud_storage", False)
    except Exception as e:
        logger.warning(f"Failed to get cloud settings from secrets manager: {e}")
        # Fall back to environment variables
        USE_CLOUD_STORAGE = os.environ.get("USE_CLOUD_STORAGE", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        CLOUD_STORAGE_PUBLIC = os.environ.get(
            "CLOUD_STORAGE_PUBLIC", "false"
        ).lower() in ("true", "1", "yes")
        PREFER_CLOUD_STORAGE = os.environ.get(
            "PREFER_CLOUD_STORAGE", "false"
        ).lower() in ("true", "1", "yes")
else:
    # Default values if GCS is not available
    USE_CLOUD_STORAGE = False
    CLOUD_STORAGE_PUBLIC = False
    PREFER_CLOUD_STORAGE = False

logger.info(
    f"Cloud storage configuration: Enabled={USE_CLOUD_STORAGE}, Public={CLOUD_STORAGE_PUBLIC}, Preferred={PREFER_CLOUD_STORAGE}"
)

# Initialize FastAPI app
app = FastAPI(
    title="Idaho Legislature Media File Server",
    description="File server for Idaho Legislature media content",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://legislativevideoreviewswithai.web.app",
        "https://legislativevideoreviewswithai.firebaseapp.com",
        "http://localhost:5173",
        "http://localhost:4173",
    ],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the downloads directory for serving files
# This creates a static file handler at /files that serves content directly from the downloads directory
# Beneficial for handling large files efficiently without loading them into memory
app.mount("/files", StaticFiles(directory=DOWNLOADS_DIR), name="files")


def find_local_file(year, category, filename):
    """
    Find a file in the local file system, checking multiple possible paths.

    Args:
        year: The year folder
        category: The category folder
        filename: The file name

    Returns:
        str: The full file path if found, None otherwise
    """
    # Try the direct path first (no session folder)
    direct_path = os.path.join(DOWNLOADS_DIR, year, category, filename)
    if os.path.exists(direct_path) and os.path.isfile(direct_path):
        return direct_path

    # If not found, try looking in session subdirectories
    sessions_dir = os.path.join(DOWNLOADS_DIR, year, category)
    if os.path.exists(sessions_dir):
        # First check if there's a session directory that matches part of the filename
        # Example: filename = "1_HouseChambers01-09-2025_transcription.txt"
        # Look for session = "January 9, 2025_Legislative Session Day 4"
        session_dirs = [
            d
            for d in os.listdir(sessions_dir)
            if os.path.isdir(os.path.join(sessions_dir, d))
        ]

        for session_dir in session_dirs:
            # Try in the main session directory
            session_path = os.path.join(sessions_dir, session_dir, filename)
            if os.path.exists(session_path) and os.path.isfile(session_path):
                return session_path

            # Try in the audio subdirectory
            audio_path = os.path.join(sessions_dir, session_dir, "audio", filename)
            if os.path.exists(audio_path) and os.path.isfile(audio_path):
                return audio_path

    return None


def search_cloud_storage(year, category, filename):
    """
    Search for a file in Google Cloud Storage.

    Args:
        year: The year folder
        category: The category folder
        filename: The file name

    Returns:
        tuple: (bool, str) Whether file exists and the GCS path
    """
    if not gcs_available or not gcs_client:
        return False, None

    # Check multiple possible paths in GCS

    # Direct path: year/category/filename
    direct_path = f"{year}/{category}/{filename}"
    blob = gcs_client.bucket.blob(direct_path)
    if blob.exists():
        return True, direct_path

    # Try to list files in the year/category prefix to find session folders
    blobs = list(gcs_client.bucket.list_blobs(prefix=f"{year}/{category}/"))
    session_prefixes = set()

    for blob in blobs:
        # Extract session folder from path like "2025/House Chambers/January 9, 2025_Legislative Session Day 4/..."
        parts = blob.name.split("/")
        if len(parts) >= 3:
            session_prefixes.add(f"{year}/{category}/{parts[2]}/")

    # Try each session prefix
    for prefix in session_prefixes:
        # Try in main session directory
        path = f"{prefix}{filename}"
        blob = gcs_client.bucket.blob(path)
        if blob.exists():
            return True, path

        # Try in audio subdirectory
        audio_path = f"{prefix}audio/{filename}"
        blob = gcs_client.bucket.blob(audio_path)
        if blob.exists():
            return True, audio_path

    return False, None


@app.get("/api/files/{year}/{category}/{filename}")
async def get_file(year: str, category: str, filename: str, request: Request):
    """
    Serve a specific media file by path.

    This endpoint attempts to locate and serve the requested file using the following strategy:
    1. Check if file exists in local storage (with several path variants)
    2. If not found locally and cloud storage is enabled, check Google Cloud Storage
    3. If found in GCS, either redirect to a public URL or download temporarily and serve

    Args:
        year: The year folder
        category: The category folder
        filename: The file name
        request: The FastAPI request object

    Returns:
        Response: The requested file (FileResponse, RedirectResponse, or StreamingResponse)
    """
    try:
        # First, check for PREFER_CLOUD_STORAGE flag
        if gcs_available and gcs_client and USE_CLOUD_STORAGE and PREFER_CLOUD_STORAGE:
            # Check GCS first
            logger.info(f"Checking GCS first for: {year}/{category}/{filename}")
            exists_in_gcs, gcs_path = search_cloud_storage(year, category, filename)

            if exists_in_gcs:
                logger.info(f"File found in GCS: {gcs_path}")

                # If files are public, redirect to the public URL
                if CLOUD_STORAGE_PUBLIC:
                    blob = gcs_client.bucket.blob(gcs_path)
                    public_url = blob.public_url
                    logger.info(f"Redirecting to public URL: {public_url}")
                    return RedirectResponse(url=public_url)

                # Otherwise, serve via signed URL or temporary download
                blob = gcs_client.bucket.blob(gcs_path)

                # For small files, download to temp and serve
                if blob.size < 50 * 1024 * 1024:  # 50 MB threshold
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(
                        delete=False, dir=TEMP_DIR
                    ) as temp_file:
                        temp_path = temp_file.name

                    # Download the file
                    blob.download_to_filename(temp_path)
                    logger.info(f"Serving GCS file from temp: {temp_path}")

                    # Return the file and set up cleanup after response
                    return FileResponse(
                        temp_path,
                        filename=filename,
                        background=lambda: os.unlink(temp_path),
                    )
                else:
                    # For large files, generate a signed URL and redirect
                    signed_url = gcs_client.get_signed_url(gcs_path, expiration=3600)
                    logger.info(f"Redirecting to signed URL (expires in 1 hour)")
                    return RedirectResponse(url=signed_url)

        # Look for the file locally
        logger.info(f"Looking for file locally: {year}/{category}/{filename}")
        local_path = find_local_file(year, category, filename)

        if local_path:
            logger.info(f"Serving file from local storage: {local_path}")
            return FileResponse(local_path)

        # If not found locally and cloud storage is enabled, check GCS
        if (
            gcs_available
            and gcs_client
            and USE_CLOUD_STORAGE
            and not PREFER_CLOUD_STORAGE
        ):
            logger.info(f"Checking GCS as fallback for: {year}/{category}/{filename}")
            exists_in_gcs, gcs_path = search_cloud_storage(year, category, filename)

            if exists_in_gcs:
                logger.info(f"File found in GCS: {gcs_path}")

                # If files are public, redirect to the public URL
                if CLOUD_STORAGE_PUBLIC:
                    blob = gcs_client.bucket.blob(gcs_path)
                    public_url = blob.public_url
                    logger.info(f"Redirecting to public URL: {public_url}")
                    return RedirectResponse(url=public_url)

                # Otherwise, serve via signed URL or temporary download
                blob = gcs_client.bucket.blob(gcs_path)

                # For small files, download to temp and serve
                if blob.size < 50 * 1024 * 1024:  # 50 MB threshold
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(
                        delete=False, dir=TEMP_DIR
                    ) as temp_file:
                        temp_path = temp_file.name

                    # Download the file
                    blob.download_to_filename(temp_path)
                    logger.info(f"Serving GCS file from temp: {temp_path}")

                    # Return the file and set up cleanup after response
                    return FileResponse(
                        temp_path,
                        filename=filename,
                        background=lambda: os.unlink(temp_path),
                    )
                else:
                    # For large files, generate a signed URL and redirect
                    signed_url = gcs_client.get_signed_url(gcs_path, expiration=3600)
                    logger.info(f"Redirecting to signed URL (expires in 1 hour)")
                    return RedirectResponse(url=signed_url)

        # If file not found anywhere, return 404
        logger.warning(f"File not found anywhere: {year}/{category}/{filename}")
        raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    This endpoint is used by monitoring systems and load balancers to check
    if the file server is functioning correctly. It returns a simple status
    response that indicates the service is operational.

    Returns:
        Dictionary with service status information
    """
    status = {
        "status": "healthy",
        "storage": {
            "local": os.path.exists(DOWNLOADS_DIR),
            "cloud": gcs_available and gcs_client is not None,
            "cloud_enabled": USE_CLOUD_STORAGE,
        },
    }
    return status


if __name__ == "__main__":
    import uvicorn

    # Start the file server
    uvicorn.run("file_server:app", host="0.0.0.0", port=5001, reload=True)
