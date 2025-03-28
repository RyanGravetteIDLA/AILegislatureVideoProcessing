#!/usr/bin/env python3
"""
Process videos for a specific year, committee, and optionally a specific day.

This script provides an interactive workflow to:
1. Check for missing videos in a selected year and committee
2. Optionally filter to a specific day only
3. Download any missing videos
4. Convert videos to audio
5. Transcribe audio files

It handles the entire process from checking to transcription in one automated workflow.
You can either process all videos for a year/committee or focus on a single specific day.
"""

import os
import sys
import time
import glob
import argparse
from datetime import datetime
import readline  # For better command line input experience

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from src.downloader import IdahoLegislatureDownloader
from scripts.manage_api_keys import get_api_key
from scripts.transcribe_audio import AudioTranscriber


def get_user_input(prompt, options=None, default=None):
    """
    Get user input with validation against options and support for defaults.
    
    Args:
        prompt (str): The prompt to display to the user
        options (list, optional): List of valid options. If None, any input is valid.
        default (str, optional): Default value if user just presses Enter
        
    Returns:
        str: The validated user input
    """
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
    
    while True:
        user_input = input(full_prompt).strip()
        
        if not user_input and default:
            return default
        
        if not options or user_input in options:
            return user_input
        
        print(f"Invalid input. Please enter one of: {', '.join(options)}")


def get_available_options(downloader):
    """
    Get available years and categories from the website.
    
    Args:
        downloader (IdahoLegislatureDownloader): The downloader instance
        
    Returns:
        tuple: (list of years, list of categories)
    """
    print("Connecting to Idaho Legislature website to get available options...")
    
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
    meeting_dirs = [d for d in os.listdir(category_dir) 
                   if os.path.isdir(os.path.join(category_dir, d))]
    
    for dir_name in meeting_dirs:
        # Extract the date from directory names like "January 8, 2025_Legislative Session Day 3"
        parts = dir_name.split(',')
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
                parts = dir_name.split(',')
                if len(parts) >= 2:
                    # Get the date part without the year
                    date_only = parts[0].strip()
                    transcribed_dates.add(date_only)
    
    return transcribed_dates


def process_committee(year, category, output_dir="data/downloads", 
                     transcribe=True, model_name="gemini-2.0-flash", 
                     limit=None, skip_existing=True):
    """
    Process all meetings for a year and category.
    
    Args:
        year (str): Year to process
        category (str): Category to process
        output_dir (str): Output directory for downloads
        transcribe (bool): Whether to transcribe audio
        model_name (str): Gemini model to use for transcription
        limit (int, optional): Limit the number of meetings to process
        skip_existing (bool): Skip already downloaded and transcribed meetings
        
    Returns:
        tuple: (int, int, int) Number of (downloaded, converted, transcribed) meetings
    """
    # Step 1: Set up the downloader with audio conversion
    downloader = IdahoLegislatureDownloader(
        output_dir=output_dir,
        convert_to_audio=True,
        audio_format="mp3"
    )
    
    # Step 2: Get all meetings for this year and category
    print(f"\nFetching meetings for Year: {year}, Category: {category}...")
    meetings = downloader.get_all_meetings(year, category)
    
    if not meetings:
        print(f"No meetings found for {year}, {category}")
        return 0, 0, 0
    
    print(f"Found {len(meetings)} total meetings")
    
    # Step 3: Get already downloaded and transcribed dates
    downloaded_dates = get_existing_downloads(output_dir, year, category)
    transcribed_dates = get_transcribed_dates(output_dir, year, category)
    
    print(f"Already downloaded: {len(downloaded_dates)} meetings")
    print(f"Already transcribed: {len(transcribed_dates)} meetings")
    
    # Step 4: Filter meetings to process
    meetings_to_process = []
    for meeting in meetings:
        # Extract date (e.g., "January 8" from "January 8, 2025")
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
            print("Warning: No API key found in keychain. Transcription will be skipped.")
            print("To enable transcription, run: python scripts/manage_api_keys.py store")
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
        print(f"\n[{i}/{len(meetings_to_process)}] Processing: {meeting['date']} - {meeting['title']}")
        
        # Extract date for download_specific_meeting
        date_parts = meeting["date"].split(",")[0].split()
        if len(date_parts) >= 2:
            target_date = f"{date_parts[0]} {date_parts[1]}"  # e.g., "January 8"
            
            # Download the meeting
            print(f"Downloading {target_date}...")
            success = downloader.download_specific_meeting(year, category, target_date)
            
            if success:
                print(f"Successfully downloaded {meeting['date']}")
                downloaded_count += 1
                
                # Find the audio directory
                safe_title = downloader.create_safe_dirname(f"{meeting['date']}_{meeting['title']}")
                meeting_dir = os.path.join(output_dir, year, category, safe_title)
                audio_dir = os.path.join(meeting_dir, "audio")
                
                if os.path.exists(audio_dir):
                    # Audio conversion was successful
                    converted_count += 1
                    
                    # Transcribe if requested
                    if transcribe and transcriber:
                        print(f"Transcribing audio for {meeting['date']}...")
                        
                        # Find audio files
                        audio_files = glob.glob(os.path.join(audio_dir, "*.mp3"))
                        for audio_file in audio_files:
                            # Check if already transcribed
                            transcription_path = os.path.splitext(audio_file)[0] + "_transcription.txt"
                            if os.path.exists(transcription_path) and skip_existing:
                                print(f"Skipping transcription - already exists")
                                continue
                                
                            try:
                                # Process the audio file
                                transcription = transcriber.transcribe_audio(audio_file)
                                transcriber.save_transcription(audio_file, transcription)
                                print(f"Transcription completed for {os.path.basename(audio_file)}")
                                transcribed_count += 1
                            except Exception as e:
                                print(f"Error transcribing {audio_file}: {e}")
                
                # Add a short delay to avoid overwhelming the server
                time.sleep(2)
            else:
                print(f"Failed to download {meeting['date']}")
    
    print(f"\nProcess completed! Summary:")
    print(f"  - Downloaded: {downloaded_count} videos")
    print(f"  - Converted: {converted_count} videos to audio")
    print(f"  - Transcribed: {transcribed_count} audio files")
    
    return downloaded_count, converted_count, transcribed_count


def main():
    """Main function to parse arguments and process committee meetings."""
    parser = argparse.ArgumentParser(
        description="Process all videos and audio for a specific year and committee")
    parser.add_argument('--year', help="Year of the meetings")
    parser.add_argument('--category', help="Category of the meetings")
    parser.add_argument('--day', help="Specific day to process (format: 'Month Day', e.g., 'January 6')")
    parser.add_argument('--output-dir', default="data/downloads",
                        help="Directory to save downloads to (default: data/downloads)")
    parser.add_argument('--model', default="gemini-2.0-flash",
                        help="Gemini model to use for transcription (default: gemini-2.0-flash)")
    parser.add_argument('--limit', '-l', type=int,
                        help="Limit the number of meetings to process")
    parser.add_argument('--skip-transcription', action='store_true',
                        help="Skip transcription step")
    parser.add_argument('--process-existing', action='store_true',
                        help="Process already downloaded videos that haven't been transcribed")
    parser.add_argument('--yes', '-y', action='store_true',
                        help="Skip all confirmation prompts")
    
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
        selection = get_user_input("Select year", default=default_year)
        
        # Check if the input is a number
        if selection.isdigit() and 1 <= int(selection) <= len(available_years):
            year = available_years[int(selection) - 1]
        else:
            year = selection
    
    # Prompt for category if not provided
    category = args.category
    if not category:
        print("\nAvailable categories:")
        for i, cat in enumerate(available_categories, 1):
            print(f"  {i}. {cat}")
        
        # Set default to "House Chambers"
        default_category = "House Chambers" if "House Chambers" in available_categories else available_categories[0]
        
        # Get selection (either by number or directly by category)
        selection = get_user_input("Select category", default=default_category)
        
        # Check if the input is a number
        if selection.isdigit() and 1 <= int(selection) <= len(available_categories):
            category = available_categories[int(selection) - 1]
        else:
            category = selection
    
    # Prompt for specific day if not provided
    target_day = args.day
    if not target_day:
        use_specific_day = get_user_input("Process a specific day only?", 
                                         options=["y", "n"], 
                                         default="n")
        
        if use_specific_day.lower() == "y":
            # Get available meetings to show available dates
            available_meetings = downloader.get_all_meetings(year, category)
            
            if available_meetings:
                # Extract unique dates for display
                unique_dates = set()
                for meeting in available_meetings:
                    date_parts = meeting["date"].split(",")
                    if len(date_parts) >= 1:
                        date_only = date_parts[0].strip()
                        unique_dates.add(date_only)
                
                # Sort dates for display
                sorted_dates = sorted(list(unique_dates))
                
                print("\nAvailable dates:")
                for i, date in enumerate(sorted_dates, 1):
                    print(f"  {i}. {date}")
                
                # Get selection
                selection = get_user_input("Select date")
                
                # Check if the input is a number
                if selection.isdigit() and 1 <= int(selection) <= len(sorted_dates):
                    target_day = sorted_dates[int(selection) - 1]
                else:
                    target_day = selection
            else:
                print("\nNo meetings found. Please enter date manually.")
                target_day = get_user_input("Enter date (format: 'Month Day', e.g., 'January 6')")
        else:
            target_day = None
    
    # Confirm transcription
    transcribe = not args.skip_transcription
    if transcribe and not args.yes:
        # Check if API key is available
        api_key = get_api_key()
        if not api_key:
            print("\nNo API key found in keychain.")
            store_key = get_user_input("Do you want to store an API key now?", 
                                      options=["y", "n"], default="y")
            if store_key.lower() == "y":
                os.system("python scripts/manage_api_keys.py store")
                api_key = get_api_key()
                if not api_key:
                    print("Failed to store API key. Transcription will be skipped.")
                    transcribe = False
            else:
                print("Transcription will be skipped.")
                transcribe = False
    
    # Set model
    model_name = args.model
    if transcribe and not args.yes:
        # Ask for model confirmation
        confirm_model = get_user_input(
            f"Use {model_name} for transcription?", 
            options=["y", "n"], 
            default="y"
        )
        if confirm_model.lower() != "y":
            available_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
            print("\nAvailable models:")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model}")
            
            selection = get_user_input("Select model", default="1")
            if selection.isdigit() and 1 <= int(selection) <= len(available_models):
                model_name = available_models[int(selection) - 1]
            else:
                model_name = selection
    
    # Confirm processing
    print(f"\nWill process:")
    print(f"  - Year: {year}")
    print(f"  - Category: {category}")
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
        confirm = get_user_input("Proceed?", options=["y", "n"], default="y")
        if confirm.lower() != "y":
            print("Operation canceled.")
            return
    
    # Process the committee
    start_time = time.time()
    
    if target_day:
        # If a specific day is requested, use the direct download method
        print(f"\nProcessing specific day: {target_day}")
        downloader = IdahoLegislatureDownloader(
            output_dir=args.output_dir,
            convert_to_audio=True,
            audio_format="mp3"
        )
        
        success = downloader.download_specific_meeting(year, category, target_day)
        
        if success:
            print(f"Successfully downloaded {target_day}")
            downloaded = 1
            converted = 1
            
            # Handle transcription if requested
            transcribed = 0
            if transcribe:
                # Get API key for transcription
                api_key = get_api_key()
                if not api_key:
                    print("Warning: No API key found in keychain. Transcription will be skipped.")
                else:
                    try:
                        # Create transcriber
                        transcriber = AudioTranscriber(api_key, model_name)
                        
                        # Find the audio directory for this meeting
                        # We need to search for directories that might match this date
                        date_dirs = []
                        category_dir = os.path.join(args.output_dir, year, category)
                        if os.path.exists(category_dir):
                            for dirname in os.listdir(category_dir):
                                if target_day in dirname and os.path.isdir(os.path.join(category_dir, dirname)):
                                    date_dirs.append(os.path.join(category_dir, dirname))
                        
                        for meeting_dir in date_dirs:
                            audio_dir = os.path.join(meeting_dir, "audio")
                            if os.path.exists(audio_dir):
                                # Find and transcribe audio files
                                audio_files = glob.glob(os.path.join(audio_dir, "*.mp3"))
                                for audio_file in audio_files:
                                    # Check if already transcribed
                                    transcription_path = os.path.splitext(audio_file)[0] + "_transcription.txt"
                                    if os.path.exists(transcription_path) and not args.process_existing:
                                        print(f"Skipping transcription - already exists")
                                        continue
                                    
                                    try:
                                        # Process the audio file
                                        transcription = transcriber.transcribe_audio(audio_file)
                                        transcriber.save_transcription(audio_file, transcription)
                                        print(f"Transcription completed for {os.path.basename(audio_file)}")
                                        transcribed += 1
                                    except Exception as e:
                                        print(f"Error transcribing {audio_file}: {e}")
                    except Exception as e:
                        print(f"Error during transcription: {e}")
        else:
            print(f"Failed to download {target_day}")
            downloaded = 0
            converted = 0
            transcribed = 0
    else:
        # Process all meetings as before
        downloaded, converted, transcribed = process_committee(
            year=year,
            category=category,
            output_dir=args.output_dir,
            transcribe=transcribe,
            model_name=model_name,
            limit=args.limit,
            skip_existing=not args.process_existing
        )
    end_time = time.time()
    
    # Print summary
    print(f"\nOperation completed in {end_time - start_time:.1f} seconds")
    print(f"Downloaded: {downloaded} videos")
    print(f"Converted: {converted} videos to audio")
    print(f"Transcribed: {transcribed} audio files")
    

if __name__ == "__main__":
    main()