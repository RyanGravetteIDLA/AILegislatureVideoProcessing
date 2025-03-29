#!/usr/bin/env python3
"""
Test script to verify Idaho Legislature committee video URLs.
"""

import sys
import argparse
import requests


def main():
    """Check if a video URL is valid without downloading it."""
    parser = argparse.ArgumentParser(
        description="Test Idaho Legislature committee video URLs."
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

    print(f"Testing URL: {url}")

    # Check if the URL is valid
    try:
        head_response = requests.head(url, allow_redirects=True, timeout=10)
        status_code = head_response.status_code
        content_type = head_response.headers.get("Content-Type", "Unknown")
        content_length = head_response.headers.get("Content-Length", "Unknown")

        print(f"Status code: {status_code}")
        if status_code == 200:
            print(f"✓ URL is valid!")
            print(f"Content-Type: {content_type}")
            print(f"Content-Length: {content_length} bytes")
            print(f"Content-Length: {int(content_length) / (1024 * 1024):.2f} MB")
            print("\nDownload command:")
            print(
                f"python scripts/download_direct.py --year {year} --month {month} --day {day} --committee {committee} --code {code} --time {time}"
            )
        else:
            print(f"✗ URL is invalid (status code {status_code})")
    except Exception as e:
        print(f"Error checking URL: {e}")


if __name__ == "__main__":
    main()
