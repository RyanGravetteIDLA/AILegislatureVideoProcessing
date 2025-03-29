#!/usr/bin/env python3
"""
Download missing videos from Idaho Legislature website

Script to identify and download missing videos from the Idaho Legislature website.
"""

import argparse
import os
import sys
import glob
import re

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.downloader import IdahoLegislatureDownloader


def get_existing_downloads(output_dir, year, category):
    """Get list of dates that have already been downloaded"""
    downloaded_dates = set()

    # Path pattern for meeting directories
    meeting_pattern = os.path.join(
        output_dir, year, category, "*_Legislative Session Day *"
    )

    # Find all directories matching the pattern
    meeting_dirs = glob.glob(meeting_pattern)

    for meeting_dir in meeting_dirs:
        # Extract the date from the directory name
        dir_name = os.path.basename(meeting_dir)
        date_match = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),\s+\d{4}",
            dir_name,
        )

        if date_match:
            month = date_match.group(1)
            day = date_match.group(2)
            downloaded_dates.add(f"{month} {day}")

    return downloaded_dates


def main():
    """Main function to parse arguments and download missing videos"""
    parser = argparse.ArgumentParser(
        description="Download missing videos from Idaho Legislature"
    )
    parser.add_argument(
        "--year", default="2025", help="Year of the meetings (default: 2025)"
    )
    parser.add_argument(
        "--category",
        default="House Chambers",
        help="Category of the meetings (default: House Chambers)",
    )
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
    parser.add_argument(
        "--limit", "-l", type=int, help="Limit the number of videos to download"
    )

    args = parser.parse_args()

    # Create the downloader
    downloader = IdahoLegislatureDownloader(
        output_dir=args.output_dir,
        convert_to_audio=args.convert_audio,
        audio_format=args.audio_format,
    )

    # Get all available meetings
    print(f"Checking for available meetings in {args.year}, {args.category}...")
    all_meetings = downloader.get_all_meetings(args.year, args.category)

    if not all_meetings:
        print(f"No meetings found for {args.year}, {args.category}")
        sys.exit(1)

    print(f"Found {len(all_meetings)} total meetings")

    # Get already downloaded dates
    existing_downloads = get_existing_downloads(
        args.output_dir, args.year, args.category
    )
    print(
        f"Found {len(existing_downloads)} already downloaded dates: {sorted(existing_downloads)}"
    )

    # Find missing meetings
    missing_meetings = []
    for meeting in all_meetings:
        date_parts = meeting["date"].split(" ")
        if len(date_parts) >= 2:
            # Format date as "Month Day" (e.g., "January 8")
            meeting_date = f"{date_parts[0]} {date_parts[1].rstrip(',')}"

            if meeting_date not in existing_downloads:
                missing_meetings.append(meeting)

    if not missing_meetings:
        print("No missing meetings found!")
        return

    print(f"Found {len(missing_meetings)} missing meetings:")
    for meeting in missing_meetings:
        print(f"  - {meeting['date']} - {meeting['title']}")

    # Apply limit if specified
    if args.limit and args.limit < len(missing_meetings):
        print(f"Limiting to {args.limit} missing meetings")
        missing_meetings = missing_meetings[: args.limit]

    # Download missing meetings
    successful_downloads = 0
    for i, meeting in enumerate(missing_meetings, 1):
        date = meeting["date"]
        date_parts = date.split(" ")
        if len(date_parts) >= 2:
            target_date = (
                f"{date_parts[0]} {date_parts[1].rstrip(',')}"  # e.g., "January 8"
            )

            print(f"\nDownloading missing meeting {i}/{len(missing_meetings)}: {date}")
            success = downloader.download_specific_meeting(
                args.year, args.category, target_date
            )

            if success:
                print(f"Successfully downloaded {date}")
                successful_downloads += 1
            else:
                print(f"Failed to download {date}")

    print(
        f"\nCompleted! Downloaded {successful_downloads}/{len(missing_meetings)} missing videos."
    )


if __name__ == "__main__":
    main()
