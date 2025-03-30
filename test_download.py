#!/usr/bin/env python3
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Set environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath('./credentials/legislativevideoreviewswithai-80ed70b021b5.json')

# Try to import and use the downloader
try:
    from src.downloader import IdahoLegislatureDownloader
    
    print("Successfully imported downloader module")
    
    # Create downloader
    output_dir = "data/downloads"
    downloader = IdahoLegislatureDownloader(output_dir=output_dir, convert_to_audio=True)
    
    # Get available years and categories
    print("Getting available years and categories...")
    
    # First, get the main page
    main_url = f"{downloader.base_url}/MainMenu.do"
    main_response = downloader.session.get(main_url)
    main_response.raise_for_status()
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(main_response.text, 'html.parser')
    
    # Get available options
    available_years, available_categories = downloader.get_available_options(soup)
    print(f"Available years: {available_years}")
    print(f"Available categories: {available_categories}")
    
    # Get meetings for one date
    year = "2025"
    category = "House Chambers"
    date = "January 8"
    
    print(f"Attempting to download: {date}, {year} from {category}")
    success = downloader.download_specific_meeting(year, category, date)
    
    if success:
        print(f"Successfully downloaded {date} video from {category}!")
    else:
        print(f"Failed to download {date} video from {category}.")
        
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)