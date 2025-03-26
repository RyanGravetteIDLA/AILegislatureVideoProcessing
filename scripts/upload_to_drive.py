#!/usr/bin/env python3
"""
Script to upload transcripts to Google Drive.
Uses the transcript database to track which files have been uploaded.
"""

import os
import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transcript_db import (
    get_processed_not_uploaded_transcripts,
    update_transcript_status,
    get_transcript_by_path
)

# For Google API
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Configure logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'drive_upload.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('upload_to_drive')

# Google API constants
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'data/service_account.json'
FOLDER_CACHE_FILE = 'data/folder_cache.json'

# Folder structure constants
ROOT_FOLDER_NAME = 'Legislative Transcripts'  # Root folder name in Google Drive


def get_credentials():
    """Get service account credentials for Google Drive API."""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
            logger.error("Please download service account JSON from Google Cloud Console.")
            sys.exit(1)
            
        # Create credentials from service account file
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        
        return creds
    
    except Exception as e:
        logger.error(f"Error loading service account credentials: {e}")
        sys.exit(1)


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
    
    return folder.get('id')


def get_folder_path(transcript_path):
    """
    Get the folder path components for a transcript.
    Returns a list of folder names to create in Google Drive.
    """
    # Convert to Path object for easier manipulation
    path = Path(transcript_path)
    
    # Get parent directory (audio folder)
    audio_dir = path.parent
    
    # Get session directory (date_name)
    session_dir = audio_dir.parent
    
    # Get category directory
    category_dir = session_dir.parent
    
    # Get year directory
    year_dir = category_dir.parent
    
    # Build the folder path
    return [
        ROOT_FOLDER_NAME,
        year_dir.name,
        category_dir.name,
        session_dir.name
    ]


def get_or_create_folder_hierarchy(service, folder_path):
    """
    Create a folder hierarchy in Google Drive.
    Returns the ID of the deepest folder.
    """
    # Initialize folder cache if it exists
    folder_cache = {}
    if os.path.exists(FOLDER_CACHE_FILE):
        try:
            with open(FOLDER_CACHE_FILE, 'r') as f:
                folder_cache = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load folder cache: {e}")
    
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
    
    # Create folder hierarchy
    parent_id = None
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
    try:
        with open(FOLDER_CACHE_FILE, 'w') as f:
            json.dump(folder_cache, f)
    except Exception as e:
        logger.warning(f"Could not save folder cache: {e}")
    
    return parent_id


def upload_transcript(service, transcript_path, parent_folder_id):
    """
    Upload a transcript file to Google Drive.
    Returns the file ID if successful, None otherwise.
    """
    filename = os.path.basename(transcript_path)
    
    try:
        # Prepare file metadata
        file_metadata = {
            'name': filename,
            'parents': [parent_folder_id]
        }
        
        # Prepare media
        media = MediaFileUpload(
            transcript_path,
            mimetype='text/plain',
            resumable=True
        )
        
        # Upload the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        logger.info(f"Uploaded {filename} to Google Drive with ID: {file_id}")
        
        return file_id
    
    except HttpError as e:
        logger.error(f"Error uploading {filename}: {e}")
        return None


def process_uploads(limit=None):
    """
    Process transcript uploads to Google Drive.
    Uploads files that have been processed but not yet uploaded.
    
    Args:
        limit: Maximum number of files to upload (None for no limit)
    """
    logger.info("Starting Google Drive upload process")
    
    # Get credentials and build service
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Error building Drive service: {e}")
        return False
    
    # Get transcripts to upload
    transcripts = get_processed_not_uploaded_transcripts()
    
    if not transcripts:
        logger.info("No transcripts to upload")
        return True
    
    logger.info(f"Found {len(transcripts)} transcripts to upload")
    
    # Limit the number of uploads if specified
    if limit and limit > 0:
        transcripts = transcripts[:limit]
        logger.info(f"Limiting upload to {limit} transcripts")
    
    # Upload each transcript
    success_count = 0
    error_count = 0
    
    for transcript in transcripts:
        file_path = transcript.file_path
        
        if not os.path.exists(file_path):
            logger.warning(f"Transcript file not found: {file_path}")
            update_transcript_status(file_path, error_message="File not found")
            error_count += 1
            continue
        
        try:
            # Get folder hierarchy
            folder_path = get_folder_path(file_path)
            
            # Create folders if needed
            parent_folder_id = get_or_create_folder_hierarchy(service, folder_path)
            
            # Upload the transcript
            file_id = upload_transcript(service, file_path, parent_folder_id)
            
            if file_id:
                # Update status in database
                drive_path = '/'.join(folder_path)
                update_transcript_status(
                    file_path,
                    uploaded=True,
                    upload_path=f"drive://{drive_path}/{os.path.basename(file_path)}"
                )
                success_count += 1
            else:
                update_transcript_status(
                    file_path,
                    error_message="Upload failed"
                )
                error_count += 1
            
            # Respect rate limits (sleep between uploads)
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            update_transcript_status(file_path, error_message=str(e))
            error_count += 1
    
    logger.info(f"Upload complete. Success: {success_count}, Errors: {error_count}")
    return success_count > 0 and error_count == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload transcripts to Google Drive.')
    parser.add_argument('--limit', type=int, help='Limit the number of files to upload')
    args = parser.parse_args()
    
    try:
        success = process_uploads(limit=args.limit)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during upload: {e}")
        sys.exit(1)