#!/usr/bin/env python3
"""
Download specific date from Idaho Legislature website

Script to download a single date's meeting video from the Idaho Legislature website.
"""

import argparse
import os
import sys

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.downloader import IdahoLegislatureDownloader


def main():
    """Main function to parse arguments and download a specific meeting date"""
    parser = argparse.ArgumentParser(
        description="Download a specific date's video from Idaho Legislature"
    )
    parser.add_argument("year", help="Year of the meeting (e.g., 2025)")
    parser.add_argument(
        "category",
        help="Category of the meeting (e.g., 'House Chambers', 'Senate Chambers')",
    )
    parser.add_argument("date", help="Date in format 'Month Day' (e.g., 'January 6')")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="data/downloads",
        help="Directory to save downloads to (default: data/downloads)",
    )
    parser.add_argument(
        "--convert-audio",
        "-a",
        action="store_true",
        help="Convert videos to audio format after download",
    )
    parser.add_argument(
        "--audio-format",
        "-f",
        default="mp3",
        help="Audio format to convert to (default: mp3)",
    )

    args = parser.parse_args()

    # Create the downloader
    downloader = IdahoLegislatureDownloader(
        output_dir=args.output_dir,
        convert_to_audio=args.convert_audio,
        audio_format=args.audio_format,
    )

    # Download the meeting
    print(f"Downloading {args.date}, {args.year} from {args.category}...")
    success = downloader.download_specific_meeting(args.year, args.category, args.date)

    if success:
        print(f"Successfully downloaded {args.date} video from {args.category}!")
    else:
        print(f"Failed to download {args.date} video from {args.category}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
