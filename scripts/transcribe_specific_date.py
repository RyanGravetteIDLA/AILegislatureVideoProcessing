#!/usr/bin/env python3
"""
Transcribe audio for a specific date from Idaho Legislature

This script finds and transcribes audio for a specific date's session.
"""

import argparse
import os
import sys
import glob

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the transcription module and API key manager
from scripts.transcribe_audio import AudioTranscriber, process_meeting
from scripts.manage_api_keys import get_api_key


def find_meeting_directory(output_dir, year, category, date):
    """
    Find the meeting directory for a specific date.

    Args:
        output_dir (str): Base output directory
        year (str): Year of the meeting
        category (str): Category of the meeting
        date (str): Date in format 'Month Day' (e.g., 'January 8')

    Returns:
        str: Path to the meeting directory, or None if not found
    """
    # Build the path pattern
    date_pattern = f"{date.split()[0]} {date.split()[1]}"  # e.g., "January 8"
    path_pattern = os.path.join(output_dir, year, category, f"*{date_pattern}*")

    # Find matching directories
    matching_dirs = glob.glob(path_pattern)

    if not matching_dirs:
        return None

    return matching_dirs[0]


def main():
    """Main function to parse arguments and transcribe audio for a specific date."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio for a specific date from Idaho Legislature"
    )
    parser.add_argument(
        "--api-key",
        help="Google API key with Gemini access (optional if stored in keychain)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model to use for transcription (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--year", default="2025", help="Year of the meeting (default: 2025)"
    )
    parser.add_argument(
        "--category",
        default="House Chambers",
        help="Category of the meeting (default: House Chambers)",
    )
    parser.add_argument(
        "--date", required=True, help="Date in format 'Month Day' (e.g., 'January 8')"
    )
    parser.add_argument(
        "--output-dir",
        default="data/downloads",
        help="Directory containing downloads (default: data/downloads)",
    )

    args = parser.parse_args()

    # Get API key from command line or keychain
    api_key = args.api_key
    if not api_key:
        api_key = get_api_key()
        if not api_key:
            print("Error: No API key provided and none found in keychain.")
            print("Please store your API key first using:")
            print("python scripts/manage_api_keys.py store")
            sys.exit(1)

    # Find the meeting directory
    meeting_dir = find_meeting_directory(
        args.output_dir, args.year, args.category, args.date
    )

    if not meeting_dir:
        print(f"No meeting found for {args.date}, {args.year} in {args.category}")
        print(
            f"Make sure the meeting has been downloaded first using download_specific_date.py"
        )
        sys.exit(1)

    print(f"Found meeting directory: {meeting_dir}")

    # Process the meeting
    process_meeting(api_key, meeting_dir, model_name=args.model)
    print(f"Transcription completed for {args.date}, {args.year}")


if __name__ == "__main__":
    main()
