#!/usr/bin/env python3
"""
Enhanced Process Committee Script with Support for Additional Dropdown

This script extends the process_committee.py script to handle cases where
certain categories like "House Standing Committees", "Senate Standing Committees",
and "Interim, Task Force, and Special Committees" have an additional dropdown selection.
"""

import os
import sys
import time
import glob
import argparse
import re
from datetime import datetime
import readline  # For better command line input experience
import urllib.parse
from bs4 import BeautifulSoup

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import project modules
from src.downloader import IdahoLegislatureDownloader
from scripts.manage_api_keys import get_api_key
from scripts.transcribe_audio import AudioTranscriber


def get_user_input(prompt, options=None, default=None, non_interactive=False):
    """
    Get user input with validation against options and support for defaults.

    Args:
        prompt (str): The prompt to display to the user
        options (list, optional): List of valid options. If None, any input is valid.
        default (str, optional): Default value if user just presses Enter
        non_interactive (bool): If True, return the default without prompting

    Returns:
        str: The validated user input
    """
    # In non-interactive mode, just return the default value
    if non_interactive:
        if default:
            print(f"{prompt}: Using default value '{default}' (non-interactive mode)")
            return default
        else:
            # If no default is provided in non-interactive mode, use the first option
            if options and len(options) > 0:
                default_val = options[0]
                print(
                    f"{prompt}: Using first option '{default_val}' (non-interactive mode)"
                )
                return default_val
            else:
                print(
                    f"WARNING: No default or options available for '{prompt}' in non-interactive mode"
                )
                return ""

    # Interactive mode
    if options:
        option_str = "/".join(options)
        if default:
            full_prompt = f"{prompt} [{option_str}] (default: {default}): "
        else:
            full_prompt = f"{prompt} [{option_str}]: "
    else:
        if default:
            full_prompt = f"{prompt} (default: {default}): "
        else:
            full_prompt = f"{prompt}: "

    try:
        while True:
            user_input = input(full_prompt).strip()

            if not user_input and default:
                return default

            if not options or user_input in options:
                return user_input

            print(f"Invalid input. Please select one of: {option_str}")
    except EOFError:
        # Handle EOF (common in non-interactive environments)
        print(f"\nEOF detected. Using default value: {default}")
        if default:
            return default
        elif options and len(options) > 0:
            return options[0]
        else:
            print(f"WARNING: No input provided and no default available for '{prompt}'")
            return ""


def get_available_options(downloader):
    """
    Get available years and categories from the Idaho Legislature website.

    Args:
        downloader (IdahoLegislatureDownloader): Initialized downloader instance

    Returns:
        tuple: (list of years, list of categories)
    """

    # Get the main page using the downloader's session
    try:
        main_url = f"{downloader.base_url}/MainMenu.do"
        main_response = downloader.session.get(main_url)
        main_response.raise_for_status()

        # Use the downloader's method to extract options
        years, categories = downloader.get_available_options(
            downloader._soup_from_response(main_response)
        )

        if not years or not categories:
            print("Error: Could not retrieve available options from the website.")
            return [], []

        return years, categories

    except Exception as e:
        print(f"Error retrieving options: {e}")
        return [], []


def check_for_additional_dropdown(downloader, year, category):
    """
    Check if the selected category has an additional dropdown selection.

    Args:
        downloader (IdahoLegislatureDownloader): Initialized downloader instance
        year (str): Selected year
        category (str): Selected category

    Returns:
        tuple: (has_additional_dropdown, additional_options)
    """
    try:
        # Get the results page for the year/category
        html_content = downloader.get_meeting_results(year, category)

        if not html_content:
            return False, []

        # Parse the HTML
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Look for additional dropdowns - typically for committee selection
        additional_selects = soup.find_all("select")

        # For debugging
        print(f"Found {len(additional_selects)} select elements on the page")

        for select in additional_selects:
            select_id = select.get("id", "")
            select_name = select.get("name", "")

            # Skip the main year and category selects
            if "year" in select_id.lower() or "year" in select_name.lower():
                continue
            if "category" in select_id.lower() or "category" in select_name.lower():
                continue

            # This might be an additional dropdown for committee selection
            options = select.find_all("option")
            if options:
                # Extract the options text and skip empty or "Please Select" options
                option_values = []
                for option in options:
                    value = option.get("value", "")
                    text = option.text.strip()

                    if value and text and "select" not in text.lower():
                        option_values.append((value, text))

                if option_values:
                    print(f"Found additional dropdown: {select_id or select_name}")
                    return True, option_values

        return False, []

    except Exception as e:
        print(f"Error checking for additional dropdown: {e}")
        return False, []


def get_committee_meetings(downloader, year, category, committee_id=None):
    """
    Get all meetings for a specific year, category, and optional committee ID.

    Special handling is provided for categories that require committee selection:
    - House Standing Committees
    - Senate Standing Committees
    - Interim, Task Force, and Special Committees

    Args:
        downloader (IdahoLegislatureDownloader): Initialized downloader instance
        year (str): Year of the meetings
        category (str): Category of the meetings
        committee_id (str, optional): Committee ID for additional dropdown

    Returns:
        list: List of meetings
    """
    try:
        # If we have a committee ID, we need to send a special request
        if committee_id:
            # Get any CSRF tokens first by accessing the main page
            main_url = f"{downloader.base_url}/MainMenu.do"
            main_response = downloader.session.get(main_url)
            main_response.raise_for_status()

            # Extract hidden fields for token
            soup = BeautifulSoup(main_response.text, "html.parser")
            token_name = None
            token_value = None

            for hidden in soup.find_all("input", type="hidden"):
                if "token" in hidden.get("name", "").lower():
                    token_name = hidden.get("name")
                    token_value = hidden.get("value")
                    break

            # Try both forms - some committees might use different endpoints
            # First try ShowMediaByCommittee.do
            data = {"year": year, "category": category, "committeeId": committee_id}

            # Add token if found
            if token_name and token_value:
                data[token_name] = token_value

            # First approach: ShowMediaByCommittee.do
            print(f"Trying ShowMediaByCommittee.do for committee ID: {committee_id}")
            search_url = f"{downloader.base_url}/ShowMediaByCommittee.do"

            try:
                search_response = downloader.session.post(search_url, data=data)
                search_response.raise_for_status()

                # Save the HTML for debugging
                debug_dir = os.path.join(downloader.output_dir, "_debug")
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)

                with open(
                    os.path.join(debug_dir, "committee_meetings_method1.html"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(search_response.text)

                # Extract meeting links from the response
                html_content = search_response.text
                meetings1 = downloader.extract_meeting_links(html_content)
                print(f"Method 1 found {len(meetings1)} meetings")

                # Check if we found any meetings
                if meetings1:
                    return meetings1
            except Exception as e:
                print(f"Error with Method 1: {e}")

            # Second approach: Use ShowCommitteeOrMeeting.do
            print(f"Trying ShowCommitteeOrMedia.do for committee ID: {committee_id}")
            data = {
                "year": year,
                "category": category,
                "committee": committee_id,  # Different parameter name
            }

            # Add token if found
            if token_name and token_value:
                data[token_name] = token_value

            search_url = f"{downloader.base_url}/ShowCommitteeOrMedia.do"

            try:
                search_response = downloader.session.post(search_url, data=data)
                search_response.raise_for_status()

                debug_dir = os.path.join(downloader.output_dir, "_debug")
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)

                with open(
                    os.path.join(debug_dir, "committee_meetings_method2.html"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(search_response.text)

                # Extract meeting links from the response
                html_content = search_response.text
                meetings2 = downloader.extract_meeting_links(html_content)
                print(f"Method 2 found {len(meetings2)} meetings")

                if meetings2:
                    return meetings2
            except Exception as e:
                print(f"Error with Method 2: {e}")

            # Third method: Try using committeeId as a parameter
            print(f"Trying direct committee access for ID: {committee_id}")

            # This form might be specific to the website structure - adjust as needed
            media_url = f"{downloader.base_url}/ShowCommitteeMedia.do?committeeId={committee_id}&year={year}"

            try:
                media_response = downloader.session.get(media_url)
                media_response.raise_for_status()

                debug_dir = os.path.join(downloader.output_dir, "_debug")
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)

                with open(
                    os.path.join(debug_dir, "committee_meetings_method3.html"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(media_response.text)

                # Try to find meeting links in this response
                html_content = media_response.text
                meetings3 = downloader.extract_meeting_links(html_content)
                print(f"Method 3 found {len(meetings3)} meetings")

                if meetings3:
                    return meetings3
            except Exception as e:
                print(f"Error with Method 3: {e}")

            # If we've tried all methods and found nothing, try to parse any result we got
            print("Using fallback approach to extract meetings...")

            # If we got to this point, try to manually parse the last response
            soup = BeautifulSoup(search_response.text, "html.parser")

            # Look for links that might contain meeting information
            fallback_meetings = []
            for link in soup.find_all("a"):
                href = link.get("href", "")
                text = link.text.strip()

                # Skip empty or navigation links
                if not text or text.lower() in ["home", "back", "return", "menu"]:
                    continue

                # Look for date-like patterns in the text
                if any(
                    month in text
                    for month in [
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
                ):
                    # This might be a meeting
                    url = href
                    if not url.startswith("http"):
                        url = urllib.parse.urljoin(
                            f"https://lso.legislature.idaho.gov", url
                        )

                    # Extract a date if possible
                    date_match = re.search(
                        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+",
                        text,
                    )
                    date = date_match.group(0) + f", {year}" if date_match else text

                    fallback_meetings.append(
                        {
                            "url": url,
                            "media_id": None,
                            "date": date,
                            "title": text,
                            "download_url": url,
                        }
                    )

            print(
                f"Fallback approach found {len(fallback_meetings)} potential meetings"
            )
            if fallback_meetings:
                return fallback_meetings

            print(
                f"All methods failed to find meetings for committee ID: {committee_id}"
            )
            return []

        else:
            # Use the standard method for non-committee categories
            return downloader.get_all_meetings(year, category)

    except Exception as e:
        print(f"Error getting committee meetings: {e}")
        import traceback

        print(traceback.format_exc())
        return []


def process_committee(
    year,
    category,
    target_day=None,
    output_dir="data/downloads",
    limit=None,
    skip_existing=True,
    transcribe=True,
    model_name="gemini-2.0-flash",
    committee_id=None,
):
    """
    Process all videos for a specific year and category.

    Args:
        year (str): Year of the meetings
        category (str): Category of the meetings
        target_day (str, optional): Process only a specific day
        output_dir (str): Directory to save downloads
        limit (int, optional): Maximum number of meetings to process
        skip_existing (bool): Skip meetings that have already been downloaded
        transcribe (bool): Whether to transcribe audio files
        model_name (str): Gemini model to use for transcription
        committee_id (str, optional): Committee ID for additional dropdown

    Returns:
        tuple: (int, int, int) Number of (downloaded, converted, transcribed) meetings
    """
    # Step 1: Set up the downloader with audio conversion
    downloader = IdahoLegislatureDownloader(
        output_dir=output_dir, convert_to_audio=True, audio_format="mp3"
    )

    # Step 2: Get all available meetings
    print(f"Checking for available meetings in {year}, {category}...")
    if committee_id:
        print(f"Using committee ID: {committee_id}")

    meetings = get_committee_meetings(downloader, year, category, committee_id)

    if not meetings:
        print(f"No meetings found for {year}, {category}")
        return 0, 0, 0

    print(f"Found {len(meetings)} total meetings")

    # Step 3: Check already downloaded and transcribed dates
    downloaded_dates = get_existing_downloads(output_dir, year, category)
    transcribed_dates = get_transcribed_dates(output_dir, year, category)

    print(f"Already downloaded: {len(downloaded_dates)} meetings")
    print(f"Already transcribed: {len(transcribed_dates)} meetings")

    # Step 4: Filter meetings to process
    meetings_to_process = []

    # If a specific day is requested, filter to just that day
    if target_day:
        for meeting in meetings:
            date_parts = meeting["date"].split(",")
            if len(date_parts) >= 1:
                date_only = date_parts[0].strip()

                if target_day.lower() in date_only.lower():
                    # Skip if already downloaded and skip_existing is True
                    if skip_existing and date_only in downloaded_dates:
                        continue

                    meetings_to_process.append((meeting, date_only))
    else:
        # Process all meetings
        for meeting in meetings:
            date_parts = meeting["date"].split(",")
            if len(date_parts) >= 1:
                date_only = date_parts[0].strip()

                # Skip if already downloaded and skip_existing is True
                if skip_existing and date_only in downloaded_dates:
                    continue

                meetings_to_process.append((meeting, date_only))

    if limit and limit < len(meetings_to_process):
        print(f"Limiting to {limit} meetings")
        meetings_to_process = meetings_to_process[:limit]

    if not meetings_to_process:
        print("No new meetings to process")
        return 0, 0, 0

    print(f"\nWill process {len(meetings_to_process)} meetings:")
    for meeting, date_only in meetings_to_process:
        print(f"  - {meeting['date']} - {meeting['title']}")

    # Step 5: Process selected meetings
    downloaded_count = 0
    converted_count = 0
    transcribed_count = 0

    # Get API key for transcription if needed
    api_key = None
    if transcribe:
        api_key = get_api_key()
        if not api_key:
            print(
                "Warning: No API key found in keychain. Transcription will be skipped."
            )
            print(
                "To enable transcription, run: python scripts/manage_api_keys.py store"
            )
            transcribe = False

    # Create transcriber if needed
    transcriber = None
    if transcribe and api_key:
        try:
            transcriber = AudioTranscriber(api_key, model_name)
        except Exception as e:
            print(f"Error creating transcriber: {e}")
            transcribe = False

    for i, (meeting, date_only) in enumerate(meetings_to_process, 1):
        print(
            f"\n[{i}/{len(meetings_to_process)}] Processing: {meeting['date']} - {meeting['title']}"
        )

        # Extract date for download_specific_meeting
        date_parts = meeting["date"].split(",")[0].split()
        if len(date_parts) >= 2:
            target_date = f"{date_parts[0]} {date_parts[1]}"  # e.g., "January 8"

            # Download the meeting
            print(f"Downloading {target_date}...")

            # For meetings with committee selection, we need special handling
            if committee_id:
                print(f"Using committee ID: {committee_id} for download")

                # We need to get the meeting details first
                meetings = get_committee_meetings(
                    downloader, year, category, committee_id
                )

                # Check for direct video URL pattern for this committee
                # House Education Committee has a predictable URL pattern
                if (
                    category == "House Standing Committees"
                    and committee_id == "11"
                    and len(target_date.split()) >= 2
                ):
                    month_name = target_date.split()[0]
                    day_number = target_date.split()[1].strip(",")

                    month_to_num = {
                        "January": "01",
                        "February": "02",
                        "March": "03",
                        "April": "04",
                        "May": "05",
                        "June": "06",
                        "July": "07",
                        "August": "08",
                        "September": "09",
                        "October": "10",
                        "November": "11",
                        "December": "12",
                    }

                    if month_name in month_to_num:
                        month_str = month_to_num[month_name]
                        day_str = day_number.zfill(2)

                        # Format like: https://insession.idaho.gov/IIS/2025/House/Committee/Education/250326_hedu_0900AM-Meeting.mp4
                        direct_url = f"https://insession.idaho.gov/IIS/{year}/House/Committee/Education/{year[-2:]}{month_str}{day_str}_hedu_0900AM-Meeting.mp4"

                        print(
                            f"Trying direct URL for House Education Committee: {direct_url}"
                        )

                        # Verify if the URL is valid
                        try:
                            response = downloader.session.head(direct_url, timeout=5)
                            if response.status_code == 200:
                                print(
                                    f"✓ Direct URL is valid! Content-Type: {response.headers.get('Content-Type', 'Unknown')}"
                                )
                                print(
                                    f"Content size: {response.headers.get('Content-Length', 'Unknown')} bytes"
                                )

                                # Add this as a meeting
                                date_str = f"{month_name} {day_number}, {year}"
                                direct_meeting = {
                                    "url": direct_url,
                                    "media_id": None,
                                    "date": date_str,
                                    "title": f"Education Committee Meeting - Video",
                                    "download_url": direct_url,
                                }

                                # Add to the meetings list if not already there
                                if not any(m["url"] == direct_url for m in meetings):
                                    meetings.append(direct_meeting)
                        except Exception as e:
                            print(f"Error verifying direct URL: {e}")

                # Filter for the target date
                target_meetings = [m for m in meetings if target_date in m["date"]]

                # Filter out meetings that are just "Agenda" items - they usually don't have videos
                has_video_meetings = [
                    m for m in target_meetings if "agenda" not in m["title"].lower()
                ]

                if has_video_meetings:
                    # Prefer meetings that aren't just agenda items
                    target_meetings = has_video_meetings
                    print(
                        f"Found {len(target_meetings)} meetings that likely have media content"
                    )
                else:
                    print(
                        f"Found {len(target_meetings)} meetings, but they appear to be agenda items without video/audio"
                    )

                if not target_meetings:
                    print(f"No meetings found for date: {target_date}")
                    success = False
                    return success

                # Create a safe directory name for the first matching meeting
                meeting = target_meetings[0]

                # Check if this is likely just an agenda item without media
                if "agenda" in meeting["title"].lower():
                    print(
                        f"WARNING: This appears to be an agenda item which may not have associated media."
                    )
                    print(
                        f"The website often lists agendas separately from actual meeting recordings."
                    )
                    print(
                        f"Will attempt to download anyway, but it may not contain media files."
                    )

                safe_title = downloader.create_safe_dirname(
                    f"{meeting['date']}_{meeting['title']}"
                )

                # Create directory structure
                year_dir = os.path.join(output_dir, year)
                category_dir = os.path.join(
                    year_dir, downloader.create_safe_dirname(category)
                )
                meeting_dir = os.path.join(category_dir, safe_title)

                if not os.path.exists(meeting_dir):
                    os.makedirs(meeting_dir)

                # Save meeting info
                meeting_info_path = os.path.join(meeting_dir, "meeting_info.json")
                with open(meeting_info_path, "w", encoding="utf-8") as f:
                    import json

                    json.dump(meeting, f, indent=2)

                # Try to download the media
                url_to_use = meeting.get("download_url", meeting["url"])
                media_id = meeting.get("media_id")

                print(f"Downloading from URL: {url_to_use}")

                # Try to get the actual media page first to see if there's a direct download link
                try:
                    print(
                        f"First checking for direct download links on the meeting page..."
                    )
                    meeting_response = downloader.session.get(url_to_use)
                    meeting_response.raise_for_status()

                    # Parse the page
                    meeting_soup = BeautifulSoup(meeting_response.text, "html.parser")

                    # Save the meeting page HTML for inspection
                    debug_dir = os.path.join(downloader.output_dir, "_debug")
                    if not os.path.exists(debug_dir):
                        os.makedirs(debug_dir)

                    with open(
                        os.path.join(debug_dir, "meeting_page.html"),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(meeting_response.text)

                    # Look for video elements first (these are embedded players)
                    direct_links = []
                    video_elements = meeting_soup.find_all("video")
                    if video_elements:
                        print(f"Found {len(video_elements)} video elements on the page")
                        for video in video_elements:
                            for source in video.find_all("source"):
                                src = source.get("src")
                                if src:
                                    # Make src absolute if needed
                                    if not src.startswith("http"):
                                        src = urllib.parse.urljoin(
                                            "https://lso.legislature.idaho.gov", src
                                        )

                                    direct_links.append(
                                        {"url": src, "text": "Video Source"}
                                    )

                    # Look for iframe elements (embedded videos from other services)
                    iframe_elements = meeting_soup.find_all("iframe")
                    if iframe_elements:
                        print(
                            f"Found {len(iframe_elements)} iframe elements on the page"
                        )
                        for iframe in iframe_elements:
                            src = iframe.get("src")
                            if src:
                                # Make src absolute if needed
                                if not src.startswith("http"):
                                    src = urllib.parse.urljoin(
                                        "https://lso.legislature.idaho.gov", src
                                    )

                                # Add the iframe source as a potential video
                                direct_links.append(
                                    {"url": src, "text": "Iframe Source"}
                                )

                    # Look for 'Download' links and media links in the page
                    for link in meeting_soup.find_all("a"):
                        href = link.get("href", "")
                        link_text = link.text.strip().lower()

                        # Check for mp4 downloads or other media links
                        if (
                            href.endswith(".mp4")
                            or "mp4" in href
                            or "download" in link_text
                            or "video" in link_text
                            or "audio" in link_text
                            or "watch" in link_text
                            or "stream" in link_text
                            or "play" in link_text
                        ):

                            # Make href absolute if needed
                            if not href.startswith("http"):
                                href = urllib.parse.urljoin(
                                    "https://lso.legislature.idaho.gov", href
                                )

                            direct_links.append(
                                {
                                    "url": href,
                                    "text": link.text.strip() or "Direct Link",
                                }
                            )

                    # Search for embedded JavaScript variables with media URLs
                    # Look for common video formats
                    js_pattern = re.compile(
                        r'(https?://[^"\'\s]+\.(mp4|webm|m4v|mov|mpg|mpeg|avi|wmv|m3u8))'
                    )
                    js_matches = js_pattern.findall(meeting_response.text)
                    if js_matches:
                        print(
                            f"Found {len(js_matches)} potential media URLs in JavaScript"
                        )
                        for url_tuple in js_matches:
                            url = url_tuple[
                                0
                            ]  # The full URL is the first element in the tuple
                            direct_links.append(
                                {
                                    "url": url,
                                    "text": f"JavaScript Media URL ({url_tuple[1].upper()})",
                                }
                            )

                            # For M3U8 playlists (HLS streaming), we should add the direct TS segments too if we can find them
                            if url_tuple[1] == "m3u8":
                                print(f"Found M3U8 (HLS) stream: {url}")
                                try:
                                    # Try to get the playlist
                                    playlist_response = downloader.session.get(
                                        url, timeout=5
                                    )
                                    playlist_response.raise_for_status()

                                    # Look for segment URLs
                                    ts_segments = []
                                    for line in playlist_response.text.splitlines():
                                        if line.endswith(".ts") and not line.startswith(
                                            "#"
                                        ):
                                            # Make the URL absolute if needed
                                            if not line.startswith("http"):
                                                base_url = url.rsplit("/", 1)[0]
                                                ts_url = f"{base_url}/{line}"
                                            else:
                                                ts_url = line

                                            ts_segments.append(ts_url)

                                    if ts_segments:
                                        print(
                                            f"Found {len(ts_segments)} TS segments in M3U8 playlist"
                                        )
                                        # Just add the first segment as an example
                                        direct_links.append(
                                            {
                                                "url": ts_segments[0],
                                                "text": f"HLS Segment (first of {len(ts_segments)})",
                                            }
                                        )
                                except Exception as e:
                                    print(f"Error parsing M3U8 playlist: {e}")

                    # Check for players that might be loaded dynamically
                    player_patterns = [
                        # Look for JW Player config
                        re.compile(r'file["\'\s]*:["\'\s]*(https?://[^"\'\s]+)'),
                        # Look for VideoJS or HTML5 video sources
                        re.compile(
                            r'src["\'\s]*=["\'\s]*(https?://[^"\'\s]+\.(mp4|webm|m4v))'
                        ),
                        # Look for streaming URLs
                        re.compile(r'stream_url["\'\s]*:["\'\s]*(https?://[^"\'\s]+)'),
                    ]

                    for pattern in player_patterns:
                        matches = pattern.findall(meeting_response.text)
                        if matches:
                            print(
                                f"Found {len(matches)} potential media URLs in player config"
                            )
                            for match in matches:
                                if isinstance(match, tuple):
                                    url = match[0]  # First element is the URL
                                else:
                                    url = match

                                direct_links.append(
                                    {"url": url, "text": "Player Config URL"}
                                )

                    if direct_links:
                        print(
                            f"Found {len(direct_links)} direct download links on the meeting page"
                        )
                        # Print all links for debugging
                        for i, link in enumerate(direct_links):
                            print(f"  {i+1}. {link['text']}: {link['url']}")
                        media_urls = direct_links
                    else:
                        # Fall back to standard method
                        print(
                            "No direct links found, trying extract_media_urls method..."
                        )
                        media_urls = downloader.extract_media_urls(
                            url_to_use,
                            media_id=media_id,
                            date=meeting["date"],
                            title=meeting["title"],
                        )
                except Exception as e:
                    print(f"Error checking for direct links: {e}")
                    # Fall back to standard method
                    media_urls = downloader.extract_media_urls(
                        url_to_use,
                        media_id=media_id,
                        date=meeting["date"],
                        title=meeting["title"],
                    )

                # Save media URLs
                media_info_path = os.path.join(meeting_dir, "media_urls.json")
                with open(media_info_path, "w", encoding="utf-8") as f:
                    import json

                    json.dump(media_urls, f, indent=2)

                download_success = False
                if media_urls:
                    print(f"Found {len(media_urls)} media files to download")

                    # First try to verify which URLs are valid
                    verified_urls = []
                    print("Verifying media URLs...")

                    for idx, media in enumerate(media_urls):
                        media_url = media["url"]
                        try:
                            # Try HEAD request first to check if URL exists
                            head_response = downloader.session.head(
                                media_url, timeout=5, allow_redirects=True
                            )
                            status_code = head_response.status_code
                            content_type = head_response.headers.get(
                                "Content-Type", "Unknown"
                            )
                            content_length = head_response.headers.get(
                                "Content-Length", "Unknown"
                            )

                            print(f"  URL {idx+1}: {media_url}")
                            print(
                                f"    Status: {status_code}, Type: {content_type}, Size: {content_length}"
                            )

                            if status_code == 200:
                                # If it's a media type, add it to verified URLs
                                if (
                                    "video" in content_type
                                    or "audio" in content_type
                                    or "application/octet-stream" in content_type
                                    or media_url.endswith(
                                        (
                                            ".mp4",
                                            ".m4v",
                                            ".mp3",
                                            ".wav",
                                            ".webm",
                                            ".m3u8",
                                        )
                                    )
                                ):
                                    verified_urls.append(media)
                                    print(f"    ✓ Valid media URL")
                                else:
                                    print(f"    ✗ Not a media file")
                            else:
                                print(f"    ✗ Invalid URL (status code {status_code})")

                        except Exception as e:
                            print(f"  Error checking URL {media_url}: {e}")

                    # If we have verified URLs, use those
                    if verified_urls:
                        print(f"Found {len(verified_urls)} verified media URLs")
                        media_urls = verified_urls
                    else:
                        print("No verified media URLs found. Trying all links anyway.")

                    for idx, media in enumerate(media_urls):
                        media_url = media["url"]
                        base_filename = os.path.basename(
                            urllib.parse.urlparse(media_url).path
                        )
                        if not base_filename or base_filename.count(".") == 0:
                            extension = ".mp4"  # Default extension
                            for ext in [".mp4", ".mp3", ".m3u8", ".webm"]:
                                if media_url.endswith(ext):
                                    extension = ext
                                    break
                            base_filename = f"video_{idx+1}{extension}"

                        print(f"Downloading {media_url} to {base_filename}...")
                        output_path = os.path.join(meeting_dir, base_filename)
                        file_success = downloader.download_file(media_url, output_path)

                        if file_success:
                            download_success = True
                            print(f"Successfully downloaded: {base_filename}")

                            # Convert to audio if requested
                            if (
                                downloader.convert_to_audio
                                and downloader.ffmpeg_available
                            ):
                                audio_path = downloader.convert_video_to_audio(
                                    output_path
                                )
                                if audio_path:
                                    print(
                                        f"Converted to audio: {os.path.basename(audio_path)}"
                                    )
                        else:
                            print(f"Failed to download: {base_filename}")

                success = download_success
            else:
                # Use standard downloader for non-committee meetings
                success = downloader.download_specific_meeting(
                    year, category, target_date
                )

            if success:
                print(f"Successfully downloaded {meeting['date']}")
                downloaded_count += 1
                converted_count += 1

                # Handle transcription if requested
                if transcribe and transcriber:
                    # Look for downloaded audio files
                    category_dir = os.path.join(output_dir, year, category)
                    # We need to find the exact directory for this meeting (date)
                    possible_dirs = [
                        d
                        for d in os.listdir(category_dir)
                        if os.path.isdir(os.path.join(category_dir, d))
                        and date_only in d
                    ]

                    for dir_name in possible_dirs:
                        meeting_dir = os.path.join(category_dir, dir_name)
                        audio_dir = os.path.join(meeting_dir, "audio")

                        if os.path.exists(audio_dir):
                            # Find audio files
                            audio_files = [
                                f for f in os.listdir(audio_dir) if f.endswith(".mp3")
                            ]

                            for audio_file in audio_files:
                                audio_path = os.path.join(audio_dir, audio_file)
                                transcription_path = (
                                    os.path.splitext(audio_path)[0]
                                    + "_transcription.txt"
                                )

                                # Skip if already transcribed
                                if os.path.exists(transcription_path) and skip_existing:
                                    print(f"  Already transcribed: {audio_file}")
                                    continue

                                print(f"  Transcribing: {audio_file}")
                                try:
                                    success = transcriber.transcribe_audio_file(
                                        audio_path, transcription_path
                                    )
                                    if success:
                                        print(
                                            f"  Transcription completed: {os.path.basename(transcription_path)}"
                                        )
                                        transcribed_count += 1
                                    else:
                                        print(
                                            f"  Transcription failed for {audio_file}"
                                        )
                                except Exception as e:
                                    print(f"  Error transcribing {audio_file}: {e}")
            else:
                print(f"Failed to download {meeting['date']}")

    print(f"\nProcess completed! Summary:")
    print(f"  - Downloaded: {downloaded_count} videos")
    print(f"  - Converted: {converted_count} videos to audio")
    print(f"  - Transcribed: {transcribed_count} audio files")

    return downloaded_count, converted_count, transcribed_count


def get_existing_downloads(output_dir, year, category):
    """
    Get list of dates that have already been downloaded.

    Args:
        output_dir (str): Base output directory
        year (str): Year of the meetings
        category (str): Category of the meetings

    Returns:
        list: List of date strings that have been downloaded
    """
    downloaded_dates = set()

    # Path pattern for meeting directories
    category_dir = os.path.join(output_dir, year, category)
    if not os.path.exists(category_dir):
        return downloaded_dates

    # Find all directories that might contain meetings
    meeting_dirs = [
        d
        for d in os.listdir(category_dir)
        if os.path.isdir(os.path.join(category_dir, d))
    ]

    for dir_name in meeting_dirs:
        # Extract the date from directory names like "January 8, 2025_Legislative Session Day 3"
        parts = dir_name.split(",")
        if len(parts) >= 2:
            # Get the date part without the year and any text after the comma
            date_only = parts[0].strip()
            # Check if the directory has an audio or video file
            dir_path = os.path.join(category_dir, dir_name)
            has_files = False
            for pattern in ["*.mp4", "*.mp3", "audio/*.mp3"]:
                if glob.glob(os.path.join(dir_path, pattern)):
                    has_files = True
                    break

            if has_files:
                downloaded_dates.add(date_only)

    return downloaded_dates


def get_transcribed_dates(output_dir, year, category):
    """
    Get list of dates that have already been transcribed.

    Args:
        output_dir (str): Base output directory
        year (str): Year of the meetings
        category (str): Category of the meetings

    Returns:
        list: List of date strings that have been transcribed
    """
    transcribed_dates = set()

    # Path pattern for transcription files
    category_dir = os.path.join(output_dir, year, category)
    if not os.path.exists(category_dir):
        return transcribed_dates

    # Find all transcription files
    for root, _, files in os.walk(category_dir):
        for file in files:
            if file.endswith("_transcription.txt"):
                # Extract date from the directory path
                dir_name = os.path.basename(os.path.dirname(os.path.dirname(root)))
                parts = dir_name.split(",")
                if len(parts) >= 2:
                    # Get the date part without the year
                    date_only = parts[0].strip()
                    transcribed_dates.add(date_only)

    return transcribed_dates


def main():
    """Main function to parse arguments and process committee meetings."""
    parser = argparse.ArgumentParser(
        description="Process all videos and audio for a specific year and committee"
    )
    parser.add_argument("--year", help="Year of the meetings")
    parser.add_argument("--category", help="Category of the meetings")
    parser.add_argument(
        "--day", help="Specific day to process (format: 'Month Day', e.g., 'January 6')"
    )
    parser.add_argument(
        "--output-dir",
        default="data/downloads",
        help="Directory to save downloads to (default: data/downloads)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model to use for transcription (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--limit", "-l", type=int, help="Limit the number of meetings to process"
    )
    parser.add_argument(
        "--skip-transcription", action="store_true", help="Skip transcription step"
    )
    parser.add_argument(
        "--process-existing",
        action="store_true",
        help="Process already downloaded videos that haven't been transcribed",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip all confirmation prompts"
    )
    parser.add_argument(
        "--committee-id", help="Committee ID for additional dropdown (advanced)"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode, using defaults for all prompts",
    )

    args = parser.parse_args()

    # Create a downloader to get available options
    downloader = IdahoLegislatureDownloader(output_dir=args.output_dir)

    # Get available years and categories
    available_years, available_categories = get_available_options(downloader)

    if not available_years or not available_categories:
        print("Failed to retrieve options from the website. Exiting.")
        sys.exit(1)

    # Prompt for year if not provided
    year = args.year
    if not year:
        print("\nAvailable years:")
        for i, yr in enumerate(available_years, 1):
            print(f"  {i}. {yr}")

        # Set default to the latest year
        default_year = available_years[0] if available_years else None

        # Get selection (either by number or directly by year)
        selection = get_user_input(
            "Select year",
            default=default_year,
            non_interactive=args.non_interactive or args.yes,
        )

        # Check if the input is a number
        if selection.isdigit() and 1 <= int(selection) <= len(available_years):
            year = available_years[int(selection) - 1]
        else:
            # Otherwise, treat the input as a year
            year = selection

    # Prompt for category if not provided
    category = args.category
    if not category:
        print("\nAvailable categories:")
        for i, cat in enumerate(available_categories, 1):
            print(f"  {i}. {cat}")

        # Set default to House Chambers
        default_category = "House Chambers"
        if default_category not in available_categories and available_categories:
            default_category = available_categories[0]

        # Get selection (either by number or directly by category)
        selection = get_user_input(
            "Select category",
            default=default_category,
            non_interactive=args.non_interactive or args.yes,
        )

        # Check if the input is a number
        if selection.isdigit() and 1 <= int(selection) <= len(available_categories):
            category = available_categories[int(selection) - 1]
        else:
            # Otherwise, treat the input as a category
            category = selection

    # Special handling for categories that require committee selection
    committee_id = args.committee_id
    if (
        category
        in [
            "Interim, Task Force, and Special Committees",
            "House Standing Committees",
            "Senate Standing Committees",
        ]
        and not committee_id
    ):
        print(f"\nYou selected '{category}'")
        print("This category requires selecting a specific committee.")

        # Get the committee selection page
        try:
            # First, fetch the main page to get any needed cookies or tokens
            main_url = f"{downloader.base_url}/MainMenu.do"
            main_response = downloader.session.get(main_url)
            main_response.raise_for_status()

            # Make the POST request to get the committee selection page
            search_url = f"{downloader.base_url}/ShowCommitteeOrMedia.do"
            data = {"year": year, "category": category}

            print(f"Fetching committee selection page with URL: {search_url}")
            print(f"POST data: {data}")

            search_response = downloader.session.post(search_url, data=data)
            search_response.raise_for_status()

            # Debug - save the HTML response for examination
            debug_dir = os.path.join(args.output_dir, "_debug")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)

            with open(
                os.path.join(debug_dir, "committee_selection_page.html"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(search_response.text)

            # Parse the response to find the committee dropdown
            soup = BeautifulSoup(search_response.text, "html.parser")

            # Analyze the forms on the page
            print("\nForms found on the page:")
            for i, form in enumerate(soup.find_all("form")):
                form_id = form.get("id", "")
                form_name = form.get("name", "")
                form_action = form.get("action", "")
                print(
                    f"Form #{i+1}: id='{form_id}', name='{form_name}', action='{form_action}'"
                )

                # List inputs in the form
                inputs = form.find_all(["input", "select", "textarea"])
                if inputs:
                    print(f"  Form inputs:")
                    for input_elem in inputs:
                        input_type = input_elem.name
                        input_id = input_elem.get("id", "")
                        input_name = input_elem.get("name", "")
                        input_value = input_elem.get("value", "")
                        print(
                            f"    {input_type}: id='{input_id}', name='{input_name}', value='{input_value}'"
                        )

            # Look for any hidden fields that might be required
            print("\nHidden fields:")
            for hidden in soup.find_all("input", type="hidden"):
                hidden_name = hidden.get("name", "")
                hidden_value = hidden.get("value", "")
                print(f"  {hidden_name}: {hidden_value}")

            # Find the committee dropdown (usually has "committee" in the id or name)
            committee_select = None

            # Print all select elements for debugging
            print("\nAll select elements found on the page:")
            for i, select in enumerate(soup.find_all("select")):
                select_id = select.get("id", "").lower()
                select_name = select.get("name", "").lower()
                select_options = len(select.find_all("option"))
                print(
                    f"  Select #{i+1}: id='{select_id}', name='{select_name}', options={select_options}"
                )

                # Checking for committee-related selects
                if "committee" in select_id or "committee" in select_name:
                    committee_select = select
                    print(f"  Found committee select: {select_id or select_name}")

            # If no committee-specific select found, look for any non-year, non-category select
            if not committee_select:
                print(
                    "No select with 'committee' in name found. Looking for alternative selects..."
                )
                for select in soup.find_all("select"):
                    select_id = select.get("id", "").lower()
                    select_name = select.get("name", "").lower()

                    # Skip year and category selects
                    if (
                        "year" in select_id
                        or "year" in select_name
                        or "category" in select_id
                        or "category" in select_name
                    ):
                        continue

                    # This might be our committee select
                    committee_select = select
                    print(f"  Using alternative select: {select_id or select_name}")
                    break

            if committee_select:
                # Extract committee options
                committee_options = []
                for option in committee_select.find_all("option"):
                    value = option.get("value", "")
                    text = option.text.strip()

                    if value and text and "select" not in text.lower():
                        committee_options.append((value, text))

                # Show available committees
                print("\nAvailable committees:")
                for i, (value, text) in enumerate(committee_options, 1):
                    print(f"  {i}. {text}")

                # Get selection
                default_option = "1" if committee_options else None
                selection = get_user_input(
                    "Select committee",
                    default=default_option,
                    non_interactive=args.non_interactive or args.yes,
                )

                # Check if the input is a number
                if selection.isdigit() and 1 <= int(selection) <= len(
                    committee_options
                ):
                    committee_id = committee_options[int(selection) - 1][
                        0
                    ]  # Extract the value
                    committee_name = committee_options[int(selection) - 1][
                        1
                    ]  # Extract the text
                    print(f"Selected committee: {committee_name} (ID: {committee_id})")
                else:
                    # Otherwise, use direct input
                    committee_id = selection
            else:
                print(
                    "Could not find committee selection dropdown. Please enter committee ID manually."
                )
                try:
                    committee_id = input("Enter committee ID: ")
                except EOFError:
                    print(
                        "Non-interactive mode detected. Using default committee ID: 1"
                    )
                    committee_id = "1"

        except Exception as e:
            print(f"Error retrieving committee options: {e}")
            print("Please enter committee ID manually:")
            try:
                committee_id = input("Enter committee ID: ")
            except EOFError:
                print("Non-interactive mode detected. Using default committee ID: 1")
                committee_id = "1"

    # For other categories, check for additional dropdown if needed
    elif not committee_id:
        has_additional_dropdown, committee_options = check_for_additional_dropdown(
            downloader, year, category
        )

        if has_additional_dropdown and committee_options:
            print("\nThis category requires selecting a specific committee:")
            for i, (value, text) in enumerate(committee_options, 1):
                print(f"  {i}. {text} (ID: {value})")

            # Default to first option if available
            default_committee = "1" if committee_options else None

            # Get selection
            selection = get_user_input(
                "Select committee",
                default=default_committee,
                non_interactive=args.non_interactive or args.yes,
            )

            # Check if the input is a number
            if selection.isdigit() and 1 <= int(selection) <= len(committee_options):
                committee_id = committee_options[int(selection) - 1][
                    0
                ]  # Extract the value
                committee_name = committee_options[int(selection) - 1][
                    1
                ]  # Extract the text
                print(f"Selected committee: {committee_name} (ID: {committee_id})")
            else:
                # Otherwise, use as direct ID
                committee_id = selection

    # Prompt for specific day if not provided
    target_day = args.day
    if not target_day:
        # Ask if user wants to process a specific day
        process_specific_day = get_user_input(
            "Process a specific day only?",
            options=["y", "n"],
            default="n",
            non_interactive=args.non_interactive or args.yes,
        )

        if process_specific_day.lower() == "y":
            # First get all available meetings to show dates
            meetings = get_committee_meetings(downloader, year, category, committee_id)

            # Special handling for Education committee videos - the URLs follow a standard pattern
            if (
                category == "House Standing Committees" and committee_id == "11"
            ):  # Education committee
                print("Adding special direct URL pattern for House Education Committee")

                # Add direct MP4 URLs following the standard pattern
                # Format: https://insession.idaho.gov/IIS/2025/House/Committee/Education/250326_hedu_0900AM-Meeting.mp4
                for month_idx, month in enumerate(
                    [
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
                    ],
                    1,
                ):
                    for day in range(1, 32):
                        if (month_idx, day) in [
                            (2, 29),
                            (2, 30),
                            (2, 31),
                            (4, 31),
                            (6, 31),
                            (9, 31),
                            (11, 31),
                        ]:
                            continue  # Skip invalid dates

                        # Format date components for the URL
                        month_str = f"{month_idx:02d}"
                        day_str = f"{day:02d}"

                        # Generate the video URL (pattern observed from actual videos)
                        video_url = f"https://insession.idaho.gov/IIS/{year}/House/Committee/Education/{year[-2:]}{month_str}{day_str}_hedu_0900AM-Meeting.mp4"

                        # Add as a meeting
                        date_str = f"{month} {day}, {year}"
                        meetings.append(
                            {
                                "url": video_url,
                                "media_id": None,
                                "date": date_str,
                                "title": f"Education Committee Meeting",
                                "download_url": video_url,
                            }
                        )

            if meetings:
                print("\nAvailable dates:")

                # Extract unique dates
                unique_dates = set()
                date_meetings = {}

                for meeting in meetings:
                    date_parts = meeting["date"].split(",")
                    if len(date_parts) >= 1:
                        date_only = date_parts[0].strip()
                        unique_dates.add(date_only)

                        # Store meetings by date
                        if date_only not in date_meetings:
                            date_meetings[date_only] = []
                        date_meetings[date_only].append(meeting)

                # Print sorted dates
                sorted_dates = sorted(list(unique_dates))
                for i, date in enumerate(sorted_dates, 1):
                    # Show how many meetings on this date
                    meetings_count = len(date_meetings.get(date, []))
                    print(
                        f"  {i}. {date} ({meetings_count} meeting{'s' if meetings_count != 1 else ''})"
                    )

                # Get selection (either by number or directly by date)
                selection = get_user_input(
                    "Select date",
                    default=sorted_dates[0] if sorted_dates else None,
                    non_interactive=args.non_interactive or args.yes,
                )

                # Check if the input is a number
                if selection.isdigit() and 1 <= int(selection) <= len(sorted_dates):
                    target_day = sorted_dates[int(selection) - 1]
                else:
                    # Otherwise, treat the input as a date
                    target_day = selection
            else:
                print("No meetings found. Please enter date manually.")
                target_day = input(
                    "Enter date (format: 'Month Day', e.g., 'January 6'): "
                )

    # Determine if transcription is needed
    transcribe = not args.skip_transcription
    if transcribe:
        confirm_transcription = get_user_input(
            "Enable transcription?",
            options=["y", "n"],
            default="y",
            non_interactive=args.non_interactive or args.yes,
        )
        transcribe = confirm_transcription.lower() == "y"

    # Determine model to use if transcribing
    model_name = args.model
    if transcribe:
        confirm_model = get_user_input(
            f"Use default model ({model_name})?",
            options=["y", "n"],
            default="y",
            non_interactive=args.non_interactive or args.yes,
        )

        if confirm_model.lower() != "y":
            available_models = [
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ]
            print("\nAvailable models:")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model}")

            selection = get_user_input(
                "Select model",
                default="1",
                non_interactive=args.non_interactive or args.yes,
            )
            if selection.isdigit() and 1 <= int(selection) <= len(available_models):
                model_name = available_models[int(selection) - 1]
            else:
                model_name = selection

    # Confirm processing
    print(f"\nWill process:")
    print(f"  - Year: {year}")
    print(f"  - Category: {category}")
    if committee_id:
        print(f"  - Committee ID: {committee_id}")
    if target_day:
        print(f"  - Specific day: {target_day}")
    else:
        print(f"  - Days: All available")
    print(f"  - Transcription: {'Enabled' if transcribe else 'Disabled'}")
    if transcribe:
        print(f"  - Transcription model: {model_name}")
    print(f"  - Maximum meetings: {args.limit if args.limit else 'All'}")
    print(f"  - Skip existing: {not args.process_existing}")

    if not args.yes:
        confirm = get_user_input(
            "Proceed?",
            options=["y", "n"],
            default="y",
            non_interactive=args.non_interactive or args.yes,
        )
        if confirm.lower() != "y":
            print("Operation canceled.")
            return

    # Process the committee
    start_time = time.time()

    # Process with new options
    downloaded, converted, transcribed = process_committee(
        year=year,
        category=category,
        target_day=target_day,
        output_dir=args.output_dir,
        limit=args.limit,
        skip_existing=not args.process_existing,
        transcribe=transcribe,
        model_name=model_name,
        committee_id=committee_id,  # Pass the committee ID
    )

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)

    print(f"\nCompleted processing in {int(minutes)} minutes, {int(seconds)} seconds")
    print(f"Downloaded: {downloaded} videos")
    print(f"Converted: {converted} videos to audio")
    print(f"Transcribed: {transcribed} audio files")

    # Provide next steps
    if downloaded > 0:
        print("\nNext steps:")
        print(
            "1. Run 'python scripts/scan_transcripts.py' to update the transcript database"
        )
        print(
            "2. Run 'python scripts/upload_media_to_cloud.py' to upload to Google Cloud Storage"
        )
        print("3. Start the web interface with './start_local.sh'")


if __name__ == "__main__":
    main()
