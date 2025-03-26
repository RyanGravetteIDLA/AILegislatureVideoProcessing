"""
Google Drive storage manager for Legislature media files.
Handles uploads, downloads, and management of media files on Google Drive.
"""

import os
import sys
import time
import json
import logging
import mimetypes
from pathlib import Path
from datetime import datetime

# Disable googleapiclient discovery cache warning
os.environ['GOOGLE_DISCOVERY_URL'] = ''

# Filter out the googleapiclient warning
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

# Google API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Configure logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'drive_storage.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('drive_storage')

# Constants
SERVICE_ACCOUNT_FILE = 'data/service_account.json'
FOLDER_CACHE_FILE = 'data/folder_cache.json'
ROOT_FOLDER_ID = '10B0htKFOHSuYHe5iSi94ukwmF-9I6R-D'  # Specific Google Drive folder ID
ROOT_FOLDER_NAME = 'Legislative Media'  # Name used for display/logging purposes
SCOPES = ['https://www.googleapis.com/auth/drive']  # Full access scope

# Media type constants
MEDIA_TYPES = {
    'video': {'folder': 'Videos', 'extensions': ['.mp4']},
    'audio': {'folder': 'Audio', 'extensions': ['.mp3', '.wav']},
    'transcript': {'folder': 'Transcripts', 'extensions': ['.txt']}
}

# Local state caching
folder_cache = {}


def get_credentials():
    """Get service account credentials for Google Drive API."""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
            raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
            
        # Create credentials from service account file
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        
        return creds
    
    except Exception as e:
        logger.error(f"Error loading service account credentials: {e}")
        raise


def get_drive_service():
    """Get an authorized Google Drive API service instance."""
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    return service


def load_folder_cache():
    """Load folder ID cache from disk."""
    global folder_cache
    
    if folder_cache:
        return folder_cache
        
    if os.path.exists(FOLDER_CACHE_FILE):
        try:
            with open(FOLDER_CACHE_FILE, 'r') as f:
                folder_cache = json.load(f)
            logger.debug(f"Loaded folder cache with {len(folder_cache)} entries")
        except Exception as e:
            logger.warning(f"Could not load folder cache: {e}")
            folder_cache = {}
    else:
        folder_cache = {}
        
    return folder_cache


def save_folder_cache():
    """Save folder ID cache to disk."""
    try:
        os.makedirs(os.path.dirname(FOLDER_CACHE_FILE), exist_ok=True)
        with open(FOLDER_CACHE_FILE, 'w') as f:
            json.dump(folder_cache, f)
        logger.debug(f"Saved folder cache with {len(folder_cache)} entries")
    except Exception as e:
        logger.warning(f"Could not save folder cache: {e}")


def create_folder_if_not_exists(service, folder_name, parent_id=None):
    """
    Create a folder in Google Drive if it doesn't exist.
    Returns the folder ID.
    """
    # Prepare the query
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    query += " and trashed=false"
    
    # Execute the query
    response = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    # Check if the folder exists
    for file in response.get('files', []):
        return file.get('id')
    
    # If folder doesn't exist, create it
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    logger.info(f"Created folder: {folder_name} with ID: {folder.get('id')}")
    return folder.get('id')


def get_path_components(file_path, media_type=None):
    """
    Parse a file path into Drive folder components.
    Returns a list of folder names to create in Google Drive.
    
    Structure: /MEDIA_TYPE/YEAR/CATEGORY/SESSION_NAME
    Note: The root folder is not included in the returned path as we use a direct ID.
    """
    path = Path(file_path)
    
    # Detect media type if not provided
    if not media_type:
        suffix = path.suffix.lower()
        for mtype, info in MEDIA_TYPES.items():
            if suffix in info['extensions']:
                media_type = mtype
                break
        if not media_type:
            media_type = 'other'
    
    # Build folder components based on path structure
    filename = path.name
    
    # Find year, category, and session directories
    parts = list(path.parts)
    
    # Create folder structure
    if 'data/downloads' in str(file_path):
        # Standard structure detection
        try:
            # Find index of 'downloads' in the path
            downloads_idx = [i for i, part in enumerate(parts) if part == 'downloads'][0]
            
            # Get parts after 'downloads'
            year = parts[downloads_idx + 1] if len(parts) > downloads_idx + 1 else "Unknown"
            category = parts[downloads_idx + 2] if len(parts) > downloads_idx + 2 else "Unknown"
            session_name = parts[downloads_idx + 3] if len(parts) > downloads_idx + 3 else "Unknown"
            
            # Build drive path (without root folder since we use its ID directly)
            folder_path = [
                MEDIA_TYPES.get(media_type, {}).get('folder', 'Other'),
                year,
                category,
                session_name
            ]
            
        except (IndexError, ValueError):
            # Fallback to simple structure
            folder_path = [
                MEDIA_TYPES.get(media_type, {}).get('folder', 'Other'),
                datetime.now().strftime("%Y"),
                "Unsorted"
            ]
    else:
        # Simple fallback structure for non-standard paths
        folder_path = [
            MEDIA_TYPES.get(media_type, {}).get('folder', 'Other'),
            datetime.now().strftime("%Y"),
            "Unsorted"
        ]
    
    return folder_path


def get_or_create_folder_hierarchy(service, folder_path):
    """
    Create a folder hierarchy in Google Drive.
    Returns the ID of the deepest folder.
    
    Uses the ROOT_FOLDER_ID as the starting point for all folders.
    """
    # Initialize folder cache
    load_folder_cache()
    
    # Generate cache key
    cache_key = '>'.join(folder_path)
    
    # Check if we've already created this folder hierarchy
    if cache_key in folder_cache:
        folder_id = folder_cache[cache_key]
        # Verify folder still exists
        try:
            service.files().get(fileId=folder_id).execute()
            return folder_id
        except HttpError:
            # Folder doesn't exist anymore, remove from cache
            del folder_cache[cache_key]
    
    # Create folder hierarchy starting with the root folder ID
    parent_id = ROOT_FOLDER_ID  # Start with the specified root folder
    current_path = []
    
    for folder_name in folder_path:
        current_path.append(folder_name)
        current_key = '>'.join(current_path)
        
        # Check if this intermediate folder is in cache
        if current_key in folder_cache:
            folder_id = folder_cache[current_key]
            try:
                service.files().get(fileId=folder_id).execute()
                parent_id = folder_id
                continue
            except HttpError:
                # Folder doesn't exist anymore, remove from cache
                del folder_cache[current_key]
        
        # Create the folder
        parent_id = create_folder_if_not_exists(service, folder_name, parent_id)
        
        # Update cache
        folder_cache[current_key] = parent_id
    
    # Save updated cache
    save_folder_cache()
    
    return parent_id


def upload_file(file_path, media_type=None, custom_folder_path=None):
    """
    Upload a file to Google Drive.
    
    Args:
        file_path: Path to the file to upload
        media_type: Type of media ('video', 'audio', 'transcript')
        custom_folder_path: Optional custom folder path list
        
    Returns:
        dict: File metadata or None if upload failed
    """
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        # Get the Drive service
        service = get_drive_service()
        
        # Get folder path
        folder_path = custom_folder_path or get_path_components(file_path, media_type)
        
        # Create folders if needed
        parent_folder_id = get_or_create_folder_hierarchy(service, folder_path)
        
        # Prepare metadata
        filename = os.path.basename(file_path)
        file_metadata = {
            'name': filename,
            'parents': [parent_folder_id],
            'description': f"Uploaded from {file_path} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # Get mimetype
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            # Fallback mimetypes
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.mp4':
                mimetype = 'video/mp4'
            elif ext == '.mp3':
                mimetype = 'audio/mpeg'
            elif ext == '.wav':
                mimetype = 'audio/wav'
            elif ext == '.txt':
                mimetype = 'text/plain'
            else:
                mimetype = 'application/octet-stream'
        
        # Prepare media
        media = MediaFileUpload(
            file_path,
            mimetype=mimetype,
            resumable=True
        )
        
        # Upload the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink,size,createdTime,modifiedTime'
        ).execute()
        
        logger.info(f"Uploaded {filename} to Google Drive with ID: {file.get('id')}")
        return file
    
    except HttpError as e:
        logger.error(f"Error uploading {file_path}: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error uploading {file_path}: {e}")
        return None


def check_file_exists(filename, parent_folder_id=None):
    """
    Check if a file already exists in Google Drive.
    
    Args:
        filename: Name of the file to check
        parent_folder_id: Optional folder ID to check in
        
    Returns:
        str: File ID if exists, None otherwise
    """
    try:
        service = get_drive_service()
        
        # Prepare the query
        query = f"name='{filename}' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        # Execute the query
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, size, modifiedTime)'
        ).execute()
        
        # Check if the file exists
        files = response.get('files', [])
        if files:
            return files[0].get('id')
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking if file exists: {e}")
        return None


def batch_upload_files(file_paths, media_type=None, rate_limit_sleep=1):
    """
    Upload multiple files to Google Drive.
    
    Args:
        file_paths: List of file paths to upload
        media_type: Type of media ('video', 'audio', 'transcript')
        rate_limit_sleep: Sleep time between uploads (seconds)
        
    Returns:
        dict: Mapping of file paths to upload results
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = upload_file(file_path, media_type)
        
        if rate_limit_sleep > 0:
            time.sleep(rate_limit_sleep)
    
    return results


def download_file(file_id, destination_path):
    """
    Download a file from Google Drive.
    
    Args:
        file_id: ID of the file to download
        destination_path: Where to save the file
        
    Returns:
        bool: Success status
    """
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Get the Drive service
        service = get_drive_service()
        
        # Get file metadata
        file = service.files().get(fileId=file_id).execute()
        filename = file.get('name')
        
        # Download the file
        request = service.files().get_media(fileId=file_id)
        
        with open(destination_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")
        
        logger.info(f"Downloaded {filename} to {destination_path}")
        return True
        
    except HttpError as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error downloading file {file_id}: {e}")
        return False


def list_files_in_folder(folder_id, file_type=None):
    """
    List all files in a Google Drive folder.
    
    Args:
        folder_id: ID of the folder to list
        file_type: Optional filter by file type (mimetype)
        
    Returns:
        list: List of file metadata
    """
    try:
        service = get_drive_service()
        
        # Prepare the query
        query = f"'{folder_id}' in parents and trashed=false"
        if file_type:
            query += f" and mimeType contains '{file_type}'"
        
        # Execute the query
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, size, createdTime, modifiedTime)'
        ).execute()
        
        return response.get('files', [])
        
    except Exception as e:
        logger.error(f"Error listing files in folder {folder_id}: {e}")
        return []


def delete_file(file_id):
    """
    Delete a file from Google Drive.
    
    Args:
        file_id: ID of the file to delete
        
    Returns:
        bool: Success status
    """
    try:
        service = get_drive_service()
        service.files().delete(fileId=file_id).execute()
        logger.info(f"Deleted file with ID: {file_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        return False


def update_file(file_id, file_path):
    """
    Update a file in Google Drive with new content.
    
    Args:
        file_id: ID of the file to update
        file_path: Path to the new content
        
    Returns:
        dict: Updated file metadata or None if update failed
    """
    try:
        # Get the Drive service
        service = get_drive_service()
        
        # Get mimetype
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.mp4':
                mimetype = 'video/mp4'
            elif ext == '.mp3':
                mimetype = 'audio/mpeg'
            elif ext == '.wav':
                mimetype = 'audio/wav'
            elif ext == '.txt':
                mimetype = 'text/plain'
            else:
                mimetype = 'application/octet-stream'
        
        # Prepare media
        media = MediaFileUpload(
            file_path,
            mimetype=mimetype,
            resumable=True
        )
        
        # Update the file
        file = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id,name,webViewLink,size,modifiedTime'
        ).execute()
        
        logger.info(f"Updated file {file.get('name')} with ID: {file.get('id')}")
        return file
        
    except Exception as e:
        logger.error(f"Error updating file {file_id}: {e}")
        return None


def get_folder_id_by_path(folder_path):
    """
    Get the folder ID for a specific path.
    
    Args:
        folder_path: List of folder names
        
    Returns:
        str: Folder ID or None if not found
    """
    # Load cache
    load_folder_cache()
    
    # Check cache
    cache_key = '>'.join(folder_path)
    if cache_key in folder_cache:
        return folder_cache[cache_key]
    
    # Not in cache, try to create it
    try:
        service = get_drive_service()
        folder_id = get_or_create_folder_hierarchy(service, folder_path)
        return folder_id
    except Exception as e:
        logger.error(f"Error getting folder ID for path {folder_path}: {e}")
        return None