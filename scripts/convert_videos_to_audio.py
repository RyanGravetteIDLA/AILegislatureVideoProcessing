#!/usr/bin/env python3
"""
Convert existing videos to audio

Script to convert previously downloaded videos to audio format.
"""

import argparse
import os
import sys
import glob
import subprocess
import logging
import shutil

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.downloader import IdahoLegislatureDownloader


def setup_logging(log_file="data/logs/audio_conversion.log"):
    """Set up logging for the script"""
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def convert_existing_videos(videos_dir, audio_format="mp3"):
    """
    Convert all video files in the given directory to audio format.
    
    Args:
        videos_dir (str): Directory containing videos to convert
        audio_format (str): Format for audio conversion
        
    Returns:
        int: Number of successfully converted files
    """
    logger = setup_logging()
    
    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        logger.error("ffmpeg not found. Please install ffmpeg to convert videos to audio.")
        logger.error("Installation instructions:")
        logger.error("  macOS: brew install ffmpeg")
        logger.error("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        logger.error("  Windows: Download from https://ffmpeg.org/download.html")
        return 0
    
    # Create a downloader instance for the conversion function
    downloader = IdahoLegislatureDownloader(
        output_dir=videos_dir, 
        convert_to_audio=True,
        audio_format=audio_format
    )
    
    # Find all MP4 files in the directory and subdirectories
    video_pattern = os.path.join(videos_dir, "**", "*.mp4")
    videos = glob.glob(video_pattern, recursive=True)
    
    logger.info(f"Found {len(videos)} video files to convert")
    
    # Count successful conversions
    successful = 0
    
    # Convert each video
    for i, video_path in enumerate(videos, 1):
        logger.info(f"Converting {i}/{len(videos)}: {os.path.basename(video_path)}")
        
        # Check if audio file already exists
        video_dir = os.path.dirname(video_path)
        audio_dir = os.path.join(video_dir, 'audio')
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(audio_dir, f"{base_name}.{audio_format}")
        
        if os.path.exists(audio_path):
            logger.info(f"Audio file already exists, skipping: {audio_path}")
            successful += 1
            continue
        
        # Convert the video
        result = downloader.convert_video_to_audio(video_path)
        if result:
            successful += 1
    
    logger.info(f"Successfully converted {successful}/{len(videos)} videos to audio")
    return successful


def main():
    """Main function to parse arguments and convert videos to audio"""
    parser = argparse.ArgumentParser(description="Convert existing videos to audio format")
    parser.add_argument('--videos-dir', '-d', default="data/downloads",
                       help="Directory containing videos to convert (default: data/downloads)")
    parser.add_argument('--audio-format', '-f', default="mp3",
                       help="Audio format to convert to (default: mp3)")
    
    args = parser.parse_args()
    
    # Convert videos to audio
    count = convert_existing_videos(args.videos_dir, args.audio_format)
    
    if count > 0:
        print(f"Successfully converted {count} videos to {args.audio_format} format")
    else:
        print("No videos were converted. Check the log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()