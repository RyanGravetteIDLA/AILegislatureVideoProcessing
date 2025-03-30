#!/usr/bin/env python3
"""
Direct downloader for Idaho Legislature committee videos.

This script downloads videos directly from the Idaho Legislature website
using the predictable URL pattern for committee videos.
"""

import os
import sys
import argparse
import requests
from pathlib import Path


def download_file(url, output_path):
    """
    Download a file from a URL to the specified path.

    Args:
        url (str): URL of the file to download
        output_path (str): Path to save the file

    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        print(f"Downloading {url}")
        print(f"Output path: {output_path}")

        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Download the file with progress updates
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))

            # Get size in MB for display
            total_mb = total_size / (1024 * 1024)
            print(f"File size: {total_mb:.2f} MB")

            # Download the file with a progress bar
            downloaded = 0
            last_percent = 0

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Update progress every 5%
                        percent = int((downloaded / total_size) * 100)
                        if percent >= last_percent + 5:
                            last_percent = percent
                            downloaded_mb = downloaded / (1024 * 1024)
                            print(
                                f"Progress: {percent}% ({downloaded_mb:.2f} MB / {total_mb:.2f} MB)"
                            )

            print(f"Successfully downloaded: {output_path}")
            return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def main():
    """Main function to handle argument parsing and file downloading."""
    parser = argparse.ArgumentParser(
        description="Download Idaho Legislature committee videos directly."
    )
    parser.add_argument(
        "--year", required=True, help="Year of the meeting (e.g., 2025)"
    )
    parser.add_argument("--month", required=True, help="Month of the meeting (1-12)")
    parser.add_argument("--day", required=True, help="Day of the meeting (1-31)")
    parser.add_argument(
        "--committee", default="Education", help="Committee name (default: Education)"
    )
    parser.add_argument("--code", default="hedu", help="Committee code (default: hedu)")
    parser.add_argument(
        "--time", default="0900AM", help="Meeting time (default: 0900AM)"
    )
    parser.add_argument(
        "--output-dir", default="data/downloads", help="Output directory"
    )

    args = parser.parse_args()

    # Format the parameters
    year = args.year
    month = f"{int(args.month):02d}"
    day = f"{int(args.day):02d}"
    committee = args.committee
    code = args.code
    time = args.time

    # Construct the URL in the format:
    # https://insession.idaho.gov/IIS/2025/House/Committee/Education/250326_hedu_0900AM-Meeting.mp4
    url = f"https://insession.idaho.gov/IIS/{year}/House/Committee/{committee}/{year[-2:]}{month}{day}_{code}_{time}-Meeting.mp4"

    # Check if the URL is valid
    try:
        head_response = requests.head(url, allow_redirects=True)
        if head_response.status_code == 200:
            print(f"URL is valid: {url}")
            print(
                f"Content-Type: {head_response.headers.get('Content-Type', 'Unknown')}"
            )
            print(
                f"Content-Length: {head_response.headers.get('Content-Length', 'Unknown')} bytes"
            )
        else:
            print(f"URL returned status code {head_response.status_code}: {url}")
            return
    except Exception as e:
        print(f"Error checking URL: {e}")
        return

    # Create the output path
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    month_name = month_names[int(month) - 1]
    date_folder = f"{month_name} {int(day)}, {year}_{committee} Committee Meeting"

    output_dir = (
        Path(args.output_dir) / year / "House Standing Committees" / date_folder
    )
    output_file = output_dir / f"{year}{month}{day}_{code}_{time}-Meeting.mp4"

    # Download the file
    success = download_file(url, str(output_file))

    if success:
        # Output path for potential conversion to audio
        audio_dir = output_dir / "audio"
        audio_file = audio_dir / f"{year}{month}{day}_{code}_{time}-Meeting.mp3"

        # Check if ffmpeg is available
        import shutil

        if shutil.which("ffmpeg"):
            try:
                # Create audio directory
                os.makedirs(audio_dir, exist_ok=True)

                print(f"Converting video to audio: {audio_file}")
                # Construct ffmpeg command
                import subprocess

                cmd = [
                    "ffmpeg",
                    "-i",
                    str(output_file),
                    "-vn",  # Skip video
                    "-acodec",
                    "libmp3lame",
                    "-y",  # Overwrite output file
                    str(audio_file),
                ]

                # Run the command
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                if result.returncode == 0:
                    print(f"Successfully converted to audio: {audio_file}")
                else:
                    print(f"Error converting video to audio: {result.stderr}")
            except Exception as e:
                print(f"Error during audio conversion: {e}")
        else:
            print("ffmpeg not found, skipping audio conversion")
            print("To enable audio conversion, install ffmpeg:")
            print("  - macOS: brew install ffmpeg")
            print("  - Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("  - Windows: Download from https://ffmpeg.org/download.html")


if __name__ == "__main__":
    main()
