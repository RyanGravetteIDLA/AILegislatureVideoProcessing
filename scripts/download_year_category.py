#!/usr/bin/env python3
"""
Download all videos from a year and category

Script to download all meeting videos from a specific year and category.
"""

import argparse
import os
import sys

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.downloader import IdahoLegislatureDownloader


def main():
    """Main function to parse arguments and download videos for a year and category"""
    parser = argparse.ArgumentParser(description="Download videos from Idaho Legislature by year and category")
    parser.add_argument('year', help="Year of the meetings (e.g., 2025)")
    parser.add_argument('category', 
                       help="Category of the meetings (e.g., 'House Chambers', 'Senate Chambers')")
    parser.add_argument('--limit', '-l', type=int, default=None,
                       help="Limit the number of videos to download (default: download all)")
    parser.add_argument('--output-dir', '-o', default="data/downloads",
                       help="Directory to save downloads to (default: data/downloads)")
    parser.add_argument('--convert-audio', '-a', action='store_true',
                       help="Convert videos to audio format after download")
    parser.add_argument('--audio-format', '-f', default="mp3",
                       help="Audio format to convert to (default: mp3)")
    
    args = parser.parse_args()
    
    # Create the downloader
    downloader = IdahoLegislatureDownloader(
        output_dir=args.output_dir,
        convert_to_audio=args.convert_audio,
        audio_format=args.audio_format
    )
    
    # Download the videos
    print(f"Downloading videos from {args.year}, {args.category}...")
    if args.limit:
        print(f"Limiting to {args.limit} videos")
        
    count = downloader.download_year_category(args.year, args.category, limit=args.limit)
    
    print(f"Downloaded {count} videos from {args.year}, {args.category}")


if __name__ == "__main__":
    main()