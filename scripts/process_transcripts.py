#!/usr/bin/env python3
"""
Main script to process and upload transcripts.
This script orchestrates the workflow of scanning, updating, and uploading transcripts.
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import local modules
from scripts.scan_transcripts import scan_transcripts, generate_report
from scripts.upload_to_drive import process_uploads

# Configure logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
log_file = os.path.join('data', 'logs', f'process_transcripts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_transcripts')


def run_full_process(upload_limit=None, retry_errors=False):
    """
    Run the full transcript processing pipeline.
    
    Args:
        upload_limit: Maximum number of files to upload (None for no limit)
        retry_errors: Whether to retry previously failed uploads
    
    Returns:
        bool: True if process completed successfully, False otherwise
    """
    try:
        # Step 1: Scan for transcripts and update database
        logger.info("Step 1: Scanning transcripts...")
        scan_stats = scan_transcripts()
        logger.info(f"Scan complete. Found {scan_stats['found']} transcripts.")
        
        # Step 2: Upload transcripts to Google Drive
        logger.info("Step 2: Uploading transcripts to Google Drive...")
        upload_success = process_uploads(limit=upload_limit)
        
        # Step 3: Generate final report
        logger.info("Step 3: Generating final report...")
        total, processed, uploaded = generate_report()
        
        return upload_success and total > 0
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and upload transcripts.')
    parser.add_argument('--scan-only', action='store_true', help='Only scan for transcripts, don\'t upload')
    parser.add_argument('--upload-limit', type=int, help='Limit the number of files to upload')
    parser.add_argument('--retry-errors', action='store_true', help='Retry previously failed uploads')
    args = parser.parse_args()
    
    start_time = time.time()
    logger.info(f"Starting transcript processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        if args.scan_only:
            scan_stats = scan_transcripts()
            generate_report()
        else:
            success = run_full_process(
                upload_limit=args.upload_limit,
                retry_errors=args.retry_errors
            )
            if not success:
                logger.warning("Process completed with warnings or errors.")
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Process completed in {elapsed_time:.2f} seconds")