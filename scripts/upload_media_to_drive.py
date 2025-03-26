#!/usr/bin/env python3
"""
Script to upload all media files (videos, audio, transcripts) to Google Drive.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from glob import glob
import warnings

# Disable googleapiclient discovery cache warning
os.environ['GOOGLE_DISCOVERY_URL'] = ''

# Filter out the googleapiclient warning
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import local modules
from src.drive_storage import (
    upload_file, 
    batch_upload_files, 
    check_file_exists,
    get_path_components, 
    get_folder_id_by_path
)
from src.transcript_db import init_db, update_transcript_status, get_transcript_by_path

# Configure logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
log_file = os.path.join('data', 'logs', f'upload_media_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('upload_media')

# Constants
DOWNLOADS_DIR = os.path.join('data', 'downloads')

# Media patterns
MEDIA_PATTERNS = {
    'video': ['**/*.mp4'],
    'audio': ['**/*.mp3', '**/*.wav'],
    'transcript': ['**/*_transcription.txt']
}


def find_media_files(base_dir=DOWNLOADS_DIR, media_type=None, year=None, category=None, session=None):
    """
    Find all media files of a specific type in the downloads directory.
    
    Args:
        base_dir: Base directory to search in
        media_type: Type of media to find ('video', 'audio', 'transcript', or None for all)
        year: Optional filter by year
        category: Optional filter by category
        session: Optional filter by session name
        
    Returns:
        list: List of file paths
    """
    base_path = Path(base_dir)
    
    # Build path filters
    path_parts = []
    if year:
        path_parts.append(year)
    if category:
        path_parts.append(category)
    if session:
        path_parts.append(session)
    
    # Combine filters into partial path
    partial_path = os.path.join(*path_parts) if path_parts else ""
    search_dir = os.path.join(base_dir, partial_path)
    
    # Select patterns to search for
    if media_type and media_type in MEDIA_PATTERNS:
        patterns = MEDIA_PATTERNS[media_type]
    else:
        # Use all patterns if no specific type
        patterns = []
        for type_patterns in MEDIA_PATTERNS.values():
            patterns.extend(type_patterns)
    
    # Find files matching patterns
    result_files = []
    for pattern in patterns:
        # Use case-insensitive glob on Windows
        if os.name == 'nt':
            # Convert pattern to case-insensitive regex
            glob_pattern = os.path.join(search_dir, pattern)
            matches = [f for f in glob(glob_pattern, recursive=True) 
                      if os.path.isfile(f)]
        else:
            # Use standard glob on Unix
            glob_pattern = os.path.join(search_dir, pattern)
            matches = [f for f in glob(glob_pattern, recursive=True) 
                      if os.path.isfile(f)]
        
        result_files.extend(matches)
    
    # Remove duplicates and sort
    result_files = sorted(set(result_files))
    logger.info(f"Found {len(result_files)} {media_type or 'media'} files in {search_dir}")
    
    return result_files


def upload_media_files(file_paths, media_type=None, batch_size=10, rate_limit=1, skip_existing=True):
    """
    Upload a list of media files to Google Drive.
    
    Args:
        file_paths: List of file paths to upload
        media_type: Type of media for organization ('video', 'audio', 'transcript')
        batch_size: Number of files to upload in one batch
        rate_limit: Sleep time between uploads (seconds)
        skip_existing: Skip files that already exist in the database
        
    Returns:
        dict: Summary of upload results
    """
    if not file_paths:
        logger.info("No files to upload")
        return {"total": 0, "success": 0, "skipped": 0, "error": 0}
    
    # Track statistics
    stats = {
        'total': len(file_paths),
        'success': 0,
        'skipped': 0,
        'error': 0,
        'fileids': {}
    }
    
    # Process files in batches
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(file_paths)-1)//batch_size + 1} ({len(batch)} files)")
        
        for file_path in batch:
            # Determine media type if not provided
            detected_type = media_type
            if not detected_type:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.mp4':
                    detected_type = 'video'
                elif ext in ['.mp3', '.wav']:
                    detected_type = 'audio'
                elif ext == '.txt' and '_transcription' in file_path:
                    detected_type = 'transcript'
            
            try:
                # For transcripts, check database first
                if detected_type == 'transcript':
                    transcript = get_transcript_by_path(file_path)
                    if transcript and transcript.uploaded and skip_existing:
                        logger.info(f"Skipping already uploaded transcript: {file_path}")
                        stats['skipped'] += 1
                        continue
                
                # Get folder path
                folder_path = get_path_components(file_path, detected_type)
                
                # Check if file exists in destination folder
                if skip_existing:
                    folder_id = get_folder_id_by_path(folder_path)
                    if folder_id:
                        file_id = check_file_exists(os.path.basename(file_path), folder_id)
                        if file_id:
                            logger.info(f"File already exists in Drive, skipping: {file_path}")
                            stats['skipped'] += 1
                            
                            # Update transcript status if applicable
                            if detected_type == 'transcript' and transcript:
                                upload_path = '/'.join(folder_path)
                                update_transcript_status(
                                    file_path,
                                    uploaded=True,
                                    upload_path=f"drive://{upload_path}/{os.path.basename(file_path)}"
                                )
                            
                            continue
                
                # Upload the file
                result = upload_file(file_path, detected_type)
                
                if result:
                    stats['success'] += 1
                    file_id = result.get('id')
                    stats['fileids'][file_path] = file_id
                    
                    # Update transcript status if applicable
                    if detected_type == 'transcript':
                        upload_path = '/'.join(folder_path)
                        update_transcript_status(
                            file_path,
                            uploaded=True,
                            upload_path=f"drive://{upload_path}/{os.path.basename(file_path)}"
                        )
                        
                    logger.info(f"Successfully uploaded: {os.path.basename(file_path)}")
                else:
                    stats['error'] += 1
                    logger.error(f"Failed to upload: {file_path}")
                
                # Rate limiting
                if rate_limit > 0:
                    time.sleep(rate_limit)
                    
            except Exception as e:
                stats['error'] += 1
                logger.error(f"Error uploading {file_path}: {e}")
        
        # Log batch progress
        logger.info(f"Batch {i//batch_size + 1} complete. Success: {stats['success']}, "
                    f"Skipped: {stats['skipped']}, Errors: {stats['error']}")
    
    # Return statistics
    success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
    logger.info(f"Upload complete. Success: {stats['success']} ({success_rate:.1f}%), "
                f"Skipped: {stats['skipped']}, Errors: {stats['error']}")
    
    return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Upload media files to Google Drive.')
    
    # Filter options
    parser.add_argument('--media-type', choices=['video', 'audio', 'transcript'], 
                        help='Type of media to upload')
    parser.add_argument('--year', help='Filter by year (e.g. 2025)')
    parser.add_argument('--category', help='Filter by category (e.g. "House Chambers")')
    parser.add_argument('--session', help='Filter by session name')
    
    # Behavior options
    parser.add_argument('--batch-size', type=int, default=5, 
                        help='Number of files to upload in one batch')
    parser.add_argument('--rate-limit', type=int, default=1, 
                        help='Sleep time between uploads (seconds)')
    parser.add_argument('--force', action='store_true', 
                        help='Upload files even if they already exist')
    parser.add_argument('--limit', type=int, 
                        help='Limit the number of files to upload')
    
    args = parser.parse_args()
    
    # Initialize transcript database
    init_db()
    
    # Find media files
    files = find_media_files(
        media_type=args.media_type,
        year=args.year,
        category=args.category,
        session=args.session
    )
    
    # Apply limit if specified
    if args.limit and args.limit > 0 and args.limit < len(files):
        logger.info(f"Limiting upload to {args.limit} files")
        files = files[:args.limit]
    
    # Upload files
    stats = upload_media_files(
        files,
        media_type=args.media_type,
        batch_size=args.batch_size,
        rate_limit=args.rate_limit,
        skip_existing=not args.force
    )
    
    return stats


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)