#!/usr/bin/env python3
"""
Test script to check a specific URL for video content.
"""

import sys
import requests
from bs4 import BeautifulSoup
import re
import os


def main():
    """
    Main function to test a specific URL for video content.
    """
    # URL to test - target URL from the education committee
    url = "https://insession.idaho.gov/IIS/2025/House/Committee/Education/250326_hedu_0900AM-Meeting.mp4"

    if len(sys.argv) > 1:
        url = sys.argv[1]

    print(f"Testing URL: {url}")

    # First try a HEAD request
    try:
        head_response = requests.head(url, timeout=5, allow_redirects=True)
        status_code = head_response.status_code
        content_type = head_response.headers.get("Content-Type", "Unknown")
        content_length = head_response.headers.get("Content-Length", "Unknown")

        print(f"Status: {status_code}")
        print(f"Content-Type: {content_type}")
        print(f"Content-Length: {content_length}")

        # Get full response if it's not too large
        if (
            content_length == "Unknown" or int(content_length) < 5 * 1024 * 1024
        ):  # 5MB max
            print("Getting full response...")
            response = requests.get(url, timeout=10)

            if "text/html" in content_type:
                print("Processing HTML content...")
                soup = BeautifulSoup(response.text, "html.parser")

                # Save HTML for inspection
                debug_dir = "data/debug"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)

                with open(
                    os.path.join(debug_dir, "response.html"), "w", encoding="utf-8"
                ) as f:
                    f.write(response.text)

                # Look for video elements
                video_elements = soup.find_all("video")
                print(f"Found {len(video_elements)} video elements")

                for i, video in enumerate(video_elements):
                    print(f"Video {i+1}:")
                    print(video)

                    for source in video.find_all("source"):
                        src = source.get("src")
                        if src:
                            print(f"  Source: {src}")

                # Look for iframe elements
                iframe_elements = soup.find_all("iframe")
                print(f"Found {len(iframe_elements)} iframe elements")

                for i, iframe in enumerate(iframe_elements):
                    src = iframe.get("src")
                    print(f"Iframe {i+1}: {src}")

                # Look for links to media
                media_links = []
                for link in soup.find_all("a"):
                    href = link.get("href")
                    text = link.text.strip()

                    if href and any(
                        ext in href.lower() for ext in [".mp4", ".webm", ".m4v", ".mp3"]
                    ):
                        media_links.append((href, text))

                print(f"Found {len(media_links)} media links")
                for href, text in media_links:
                    print(f"  {text}: {href}")

                # Check for JavaScript media URLs
                js_pattern = re.compile(
                    r'(https?://[^"\'\s]+\.(mp4|webm|m4v|mov|mpg|mpeg|avi|wmv|m3u8))'
                )
                js_matches = js_pattern.findall(response.text)

                print(f"Found {len(js_matches)} JavaScript media URLs")
                for url_tuple in js_matches:
                    print(f"  {url_tuple[0]} ({url_tuple[1]})")

                # Look for player configurations
                player_patterns = [
                    re.compile(r'file["\'\s]*:["\'\s]*(https?://[^"\'\s]+)'),
                    re.compile(
                        r'src["\'\s]*=["\'\s]*(https?://[^"\'\s]+\.(mp4|webm|m4v))'
                    ),
                    re.compile(r'stream_url["\'\s]*:["\'\s]*(https?://[^"\'\s]+)'),
                ]

                for pattern in player_patterns:
                    matches = pattern.findall(response.text)
                    if matches:
                        print(f"Found {len(matches)} player config URLs")
                        for match in matches:
                            if isinstance(match, tuple):
                                print(f"  {match[0]}")
                            else:
                                print(f"  {match}")
            else:
                # This is likely a binary file (like a video)
                print("This appears to be a binary file (likely media)")

                # Save a bit of the content for inspection
                content_preview = response.content[:100]
                print(f"Content preview (hex): {content_preview.hex()}")

                # Check for common video file signatures
                if response.content.startswith(b"\x00\x00\x00\x18ftypmp42"):
                    print("This is an MP4 file (MPEG-4)")
                elif response.content.startswith(b"\x1A\x45\xDF\xA3"):
                    print("This is a WebM file")
                elif response.content.startswith(b"\x49\x44\x33"):
                    print("This is an MP3 file")

                # Save a small sample of the file if it's media
                sample_size = min(1024 * 1024, len(response.content))  # 1MB max
                debug_dir = "data/debug"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)

                with open(os.path.join(debug_dir, "sample.bin"), "wb") as f:
                    f.write(response.content[:sample_size])

                print(f"Saved {sample_size} bytes to data/debug/sample.bin")
        else:
            print(f"Content too large ({content_length} bytes), skipping full download")

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
