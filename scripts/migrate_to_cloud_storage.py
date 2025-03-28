#!/usr/bin/env python3
"""
Migrate media files from local storage to Google Cloud Storage.

This script uploads existing media files to Google Cloud Storage while preserving
the directory structure. It can be run selectively for specific media types
and years/categories.
"""

import os
import sys
import glob
import time
import logging
import argparse
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the GoogleCloudStorage class
from src.cloud_storage import GoogleCloudStorage

# Set up logging
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'migrate_to_gcs_{time.strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('migrate_to_gcs')

def find_media_files(base_dir, media_type, year=None, category=None):
    """
    Find media files of a specific type.
    
    Args:
        base_dir (str): Base directory to search in
        media_type (str): Type of media ('video', 'audio', or 'transcript')
        year (str, optional): Filter by year
        category (str, optional): Filter by category
        
    Returns:
        list: List of file paths
    """
    # Determine the file extension pattern based on media type
    if media_type == 'video':
        extensions = ['mp4', 'avi', 'mov']
    elif media_type == 'audio':
        extensions = ['mp3', 'wav', 'm4a']
    elif media_type == 'transcript':
        extensions = ['txt']
    else:
        logger.error(f"Invalid media type: {media_type}")
        return []
    
    # Build the search path
    search_dir = base_dir
    if year:
        search_dir = os.path.join(search_dir, year)
    if category:
        search_dir = os.path.join(search_dir, category)
    
    # Find all matching files
    all_files = []
    for ext in extensions:
        # Search recursively through all subdirectories
        pattern = os.path.join(search_dir, '**', f'*.{ext}')
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    
    return all_files

def get_gcs_path(local_path, base_dir):
    """
    Convert local path to GCS path, preserving directory structure.
    
    Args:
        local_path (str): Local file path
        base_dir (str): Base directory to strip from path
        
    Returns:
        str: GCS path
    """
    # Make paths absolute for reliable path manipulation
    local_path = os.path.abspath(local_path)
    base_dir = os.path.abspath(base_dir)
    
    # Strip base directory and ensure proper separators
    relative_path = local_path[len(base_dir):].lstrip(os.sep)
    
    # Convert Windows backslashes to forward slashes if needed
    if os.sep != '/':
        relative_path = relative_path.replace(os.sep, '/')
    
    return relative_path

def migrate_to_gcs(bucket_name, base_dir, media_types=None, 
                  year=None, category=None, credentials_path=None, 
                  public=False, batch_size=10, rate_limit=1, 
                  dry_run=False, force=False, limit=None):
    """
    Migrate files to Google Cloud Storage.
    
    Args:
        bucket_name (str): GCS bucket name
        base_dir (str): Base directory containing media files
        media_types (list, optional): List of media types to migrate. If None, migrate all.
        year (str, optional): Filter by year
        category (str, optional): Filter by category
        credentials_path (str, optional): Path to service account credentials file
        public (bool): Whether to make files publicly accessible
        batch_size (int): Number of files to process in a batch before reporting progress
        rate_limit (int): Sleep time between uploads (seconds)
        dry_run (bool): If True, just list files without uploading
        force (bool): If True, upload even if file already exists in GCS
        limit (int, optional): Limit the number of files to process
        
    Returns:
        dict: Migration statistics
    """
    if not media_types:
        media_types = ['video', 'audio', 'transcript']
    
    # Initialize GCS client
    gcs = GoogleCloudStorage(bucket_name, credentials_path)
    
    # Statistics
    stats = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'error': 0,
        'types': {t: {'total': 0, 'success': 0, 'skipped': 0, 'error': 0} for t in media_types}
    }
    
    # Process each media type
    for media_type in media_types:
        logger.info(f"Finding {media_type} files...")
        files = find_media_files(base_dir, media_type, year, category)
        
        if limit and len(files) > limit:
            logger.info(f"Limiting to {limit} {media_type} files (from {len(files)} total)")
            files = files[:limit]
        
        stats['total'] += len(files)
        stats['types'][media_type]['total'] = len(files)
        
        if not files:
            logger.info(f"No {media_type} files found")
            continue
        
        logger.info(f"Migrating {len(files)} {media_type} files to GCS bucket: {bucket_name}")
        
        # Use tqdm for progress reporting
        with tqdm(total=len(files), desc=f"Uploading {media_type}", unit="file") as progress:
            for i, local_path in enumerate(files):
                # Get GCS path
                remote_path = get_gcs_path(local_path, base_dir)
                
                # Check if we should process this file
                if dry_run:
                    logger.info(f"[DRY RUN] Would upload: {local_path} -> gs://{bucket_name}/{remote_path}")
                    stats['types'][media_type]['skipped'] += 1
                    stats['skipped'] += 1
                    progress.update(1)
                    continue
                
                # Check if file already exists in GCS
                blob = gcs.bucket.blob(remote_path)
                if blob.exists() and not force:
                    logger.info(f"Skipping (already exists): gs://{bucket_name}/{remote_path}")
                    stats['types'][media_type]['skipped'] += 1
                    stats['skipped'] += 1
                    progress.update(1)
                    continue
                
                # Upload the file
                result = gcs.upload_file(local_path, remote_path, make_public=public)
                
                if result:
                    stats['types'][media_type]['success'] += 1
                    stats['success'] += 1
                else:
                    stats['types'][media_type]['error'] += 1
                    stats['error'] += 1
                
                # Update progress
                progress.update(1)
                
                # Rate limiting
                if i < len(files) - 1 and rate_limit > 0:
                    time.sleep(rate_limit)
                
                # Batch reporting
                if (i + 1) % batch_size == 0 or i == len(files) - 1:
                    logger.info(f"Progress: {i + 1}/{len(files)} {media_type} files processed")
        
        logger.info(f"Completed {media_type} migration: {stats['types'][media_type]['success']} succeeded, "
                   f"{stats['types'][media_type]['skipped']} skipped, "
                   f"{stats['types'][media_type]['error']} failed")
    
    # Print summary
    logger.info(f"Migration complete!")
    logger.info(f"Total files: {stats['total']}")
    logger.info(f"Succeeded: {stats['success']}")
    logger.info(f"Skipped: {stats['skipped']}")
    logger.info(f"Failed: {stats['error']}")
    
    return stats

def main():
    """Main function to parse arguments and start migration."""
    parser = argparse.ArgumentParser(description='Migrate media files to Google Cloud Storage')
    
    # GCS configuration
    parser.add_argument('--bucket', default=os.environ.get('GCS_BUCKET_NAME', 'idaho-legislature-media'),
                        help='GCS bucket name')
    parser.add_argument('--credentials', default=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                        help='Path to service account credentials JSON file')
    
    # Source data configuration
    parser.add_argument('--base-dir', default='data/downloads',
                        help='Base directory containing media files')
    
    # Selection options
    parser.add_argument('--media-type', choices=['video', 'audio', 'transcript', 'all'],
                        default='all', help='Media type to migrate')
    parser.add_argument('--year', help='Filter by year')
    parser.add_argument('--category', help='Filter by category')
    
    # Behavior options
    parser.add_argument('--public', action='store_true',
                        help='Make files publicly accessible')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of files to process in a batch')
    parser.add_argument('--rate-limit', type=int, default=1,
                        help='Sleep time between uploads (seconds)')
    parser.add_argument('--dry-run', action='store_true',
                        help='List files without uploading')
    parser.add_argument('--force', action='store_true',
                        help='Upload even if file already exists in GCS')
    parser.add_argument('--limit', type=int,
                        help='Limit the number of files to process')
    
    args = parser.parse_args()
    
    # Resolve media types
    if args.media_type == 'all':
        media_types = ['video', 'audio', 'transcript']
    else:
        media_types = [args.media_type]
    
    try:
        # Start migration
        migrate_to_gcs(
            bucket_name=args.bucket,
            base_dir=args.base_dir,
            media_types=media_types,
            year=args.year,
            category=args.category,
            credentials_path=args.credentials,
            public=args.public,
            batch_size=args.batch_size,
            rate_limit=args.rate_limit,
            dry_run=args.dry_run,
            force=args.force,
            limit=args.limit
        )
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()