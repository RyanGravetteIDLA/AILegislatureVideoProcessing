#!/usr/bin/env python3
"""
Daily script to scan for new files and upload them to Google Drive.
Can be run as a scheduled task.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Disable googleapiclient discovery cache warning
os.environ['GOOGLE_DISCOVERY_URL'] = ''
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

# Import scan_transcripts to update the database
from scripts.scan_transcripts import scan_transcripts
from scripts.upload_media_to_drive import find_media_files, upload_media_files

# Configure logging
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'daily_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('daily_upload')


def daily_upload(recent_only=False, days=1, rate_limit=1, skip_existing=True, batch_size=5):
    """
    Process daily uploads to Google Drive.
    
    Args:
        recent_only: Only upload files modified in the last X days
        days: Number of days to look back for recent files
        rate_limit: Sleep time between uploads
        skip_existing: Skip files already in Google Drive
        batch_size: Number of files to process in each batch
    
    Returns:
        dict: Statistics about the upload process
    """
    start_time = time.time()
    logger.info(f"Starting daily upload at {datetime.now()}")
    
    # Stats tracking
    stats = {
        'scan': {'found': 0},
        'video': {'total': 0, 'success': 0, 'skipped': 0, 'error': 0},
        'audio': {'total': 0, 'success': 0, 'skipped': 0, 'error': 0},
        'transcript': {'total': 0, 'success': 0, 'skipped': 0, 'error': 0},
    }
    
    try:
        # 1. Scan for transcripts and update the database
        logger.info("Step 1: Scanning for transcripts and updating database")
        scan_results = scan_transcripts()
        stats['scan'] = scan_results
        
        # 2. Find media files
        logger.info("Step 2: Searching for media files")
        
        # Find media files by type
        media_types = ['video', 'audio', 'transcript']
        files_by_type = {}
        
        for media_type in media_types:
            files = find_media_files(media_type=media_type)
            
            # Filter for recent files if requested
            if recent_only and days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                recent_files = []
                
                for file_path in files:
                    try:
                        mtime = os.path.getmtime(file_path)
                        file_date = datetime.fromtimestamp(mtime)
                        if file_date >= cutoff_date:
                            recent_files.append(file_path)
                    except OSError:
                        # If there's an error getting the file time, include it anyway
                        recent_files.append(file_path)
                
                files = recent_files
                logger.info(f"Found {len(files)} {media_type} files modified in the last {days} days")
            
            files_by_type[media_type] = files
        
        # 3. Upload files by type
        logger.info("Step 3: Uploading files to Google Drive")
        
        for media_type in media_types:
            files = files_by_type[media_type]
            if not files:
                logger.info(f"No {media_type} files to upload")
                continue
                
            logger.info(f"Uploading {len(files)} {media_type} files")
            
            # Upload files
            upload_stats = upload_media_files(
                files,
                media_type=media_type,
                batch_size=batch_size,
                rate_limit=rate_limit,
                skip_existing=skip_existing
            )
            
            # Update statistics
            stats[media_type] = upload_stats
        
        # 4. Log results
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        logger.info(f"Daily upload completed in {int(minutes)} minutes, {int(seconds)} seconds")
        logger.info("Upload statistics:")
        for media_type in media_types:
            media_stats = stats[media_type]
            success_rate = media_stats['success'] / media_stats['total'] * 100 if media_stats['total'] > 0 else 0
            logger.info(f"  {media_type.capitalize()}: {media_stats['success']}/{media_stats['total']} uploaded ({success_rate:.1f}%), {media_stats['skipped']} skipped, {media_stats['error']} errors")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error during daily upload: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily script to upload files to Google Drive")
    
    parser.add_argument('--recent-only', action='store_true', 
                        help='Only upload files modified recently')
    parser.add_argument('--days', type=int, default=1, 
                        help='Number of days to look back for recent files')
    parser.add_argument('--rate-limit', type=int, default=1, 
                        help='Sleep time between uploads (seconds)')
    parser.add_argument('--force', action='store_true', 
                        help='Upload files even if they already exist in Google Drive')
    parser.add_argument('--batch-size', type=int, default=5, 
                        help='Number of files to process in each batch')
    
    args = parser.parse_args()
    
    try:
        daily_upload(
            recent_only=args.recent_only,
            days=args.days,
            rate_limit=args.rate_limit,
            skip_existing=not args.force,
            batch_size=args.batch_size
        )
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)