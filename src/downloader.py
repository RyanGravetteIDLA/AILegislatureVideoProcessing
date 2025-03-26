"""
Idaho Legislature Media Downloader

A class for downloading media files from the Idaho Legislature website.
Supports downloading from specific dates or bulk downloading from a year/category.
Also provides functionality to convert video files to audio format.
"""

import os
import re
import requests
import logging
import time
import urllib.parse
import hashlib
import json
import subprocess
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class IdahoLegislatureDownloader:
    """
    Class for downloading media files from the Idaho Legislature website.
    
    Provides functionality to:
    - Fetch available meetings from the website
    - Extract direct video URLs
    - Download videos to an organized folder structure
    """
    
    def __init__(self, output_dir="data/downloads", log_file="data/download.log", convert_to_audio=False, audio_format="mp3"):
        """
        Initialize the downloader with output directory and setup logging.
        
        Args:
            output_dir (str): Directory to save downloaded files
            log_file (str): Path to the log file
            convert_to_audio (bool): Whether to convert videos to audio format
            audio_format (str): Format for audio conversion (mp3, wav, m4a, etc.)
        """
        # Configure logging
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        self.convert_to_audio = convert_to_audio
        self.audio_format = audio_format
        
        # Check for ffmpeg if audio conversion is requested
        if self.convert_to_audio:
            self.ffmpeg_available = shutil.which('ffmpeg') is not None
            if not self.ffmpeg_available:
                self.logger.warning("ffmpeg not found. Audio conversion will be skipped.")
                self.logger.warning("Installation instructions:")
                self.logger.warning("  macOS: brew install ffmpeg")
                self.logger.warning("  Ubuntu/Debian: sudo apt-get install ffmpeg")
                self.logger.warning("  Windows: Download from https://ffmpeg.org/download.html")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Set up session for maintaining cookies across requests
        self.session = requests.Session()
        # Set a User-Agent to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        })
        
        # Base URL for the Idaho Legislature website
        self.base_url = "https://lso.legislature.idaho.gov/MediaArchive"
    
    def download_file(self, url, output_path):
        """
        Download a file from URL to the specified path.
        
        Args:
            url (str): URL of the file to download
            output_path (str): Path to save the file
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Create the output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"Successfully downloaded: {os.path.basename(output_path)}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return False
    
    def _soup_from_response(self, response):
        """
        Create BeautifulSoup object from a response.
        
        Args:
            response: The HTTP response object
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        from bs4 import BeautifulSoup
        return BeautifulSoup(response.text, 'html.parser')
    
    def get_available_options(self, soup):
        """
        Get available years and categories from the page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML of the main page
            
        Returns:
            tuple: (list of years, list of categories)
        """
        available_years = []
        available_categories = []
        
        try:
            # Find year dropdown (based on the actual HTML structure)
            year_select = soup.find('select', id='ShowCommitteeOrMedia_year')
            if year_select:
                available_years = [option.text.strip() for option in year_select.find_all('option') if option.text.strip()]
            
            # Find category dropdown (based on the actual HTML structure)
            category_select = soup.find('select', id='ShowCommitteeOrMedia_category')
            if category_select:
                available_categories = [option.text.strip() for option in category_select.find_all('option') if option.text.strip()]
                # Filter out the "Please Select" option
                available_categories = [cat for cat in available_categories if "Please Select" not in cat]
            
        except Exception as e:
            self.logger.error(f"Error extracting available options: {e}")
        
        return available_years, available_categories
    
    def get_meeting_results(self, year, category):
        """
        Make a POST request to get meeting results for a year and category.
        
        Args:
            year (str): The year to fetch meetings for
            category (str): The category to fetch meetings for
            
        Returns:
            str: HTML content of the results page, or None if request failed
        """
        try:
            # First, fetch the main page to get any needed cookies or tokens
            main_url = f"{self.base_url}/MainMenu.do"
            main_response = self.session.get(main_url)
            main_response.raise_for_status()
            
            # Extract the JSESSIONID from the page forms
            soup = BeautifulSoup(main_response.text, 'html.parser')
            jsessionid = ""
            for form in soup.find_all('form'):
                action = form.get('action', '')
                if 'jsessionid=' in action:
                    jsessionid = action.split('jsessionid=')[1].split(';')[0]
                    break
            
            # Now prepare to search for meetings
            if jsessionid:
                search_url = f"{self.base_url}/ShowCommitteeOrMedia.do;jsessionid={jsessionid}"
            else:
                search_url = f"{self.base_url}/ShowCommitteeOrMedia.do"
            
            self.logger.info(f"Sending request to {search_url} with year={year}, category={category}")
            
            # Include form data
            data = {
                'year': year,
                'category': category
            }
            
            # Make the POST request
            search_response = self.session.post(search_url, data=data)
            search_response.raise_for_status()
            
            return search_response.text
        except Exception as e:
            self.logger.error(f"Error fetching meeting results for {year}/{category}: {e}")
            return None
    
    def extract_meeting_links(self, html_content):
        """
        Extract meeting links from the results page.
        
        Args:
            html_content (str): HTML content of the results page
            
        Returns:
            list: List of meeting dictionaries with URL, date, title, etc.
        """
        meeting_links = []
        
        if not html_content:
            return meeting_links
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Save the HTML for debugging
            debug_dir = os.path.join(self.output_dir, '_debug')
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            with open(os.path.join(debug_dir, 'meeting_results.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Look for rows with dates and "Download Audio/Video" links
            # This matches the format from the website
            rows = soup.find_all('tr')
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:  # Need at least date, title, and download link
                        continue
                    
                    # First cell should be the date
                    meeting_date = cells[0].text.strip()
                    
                    # Second cell should be the title
                    meeting_title = cells[1].text.strip()
                    
                    # Check for "Download Audio/Video" link in the third cell
                    download_cell = cells[2]
                    download_link = download_cell.find('a', string='Download Audio/Video')
                    
                    if download_link and download_link.get('href'):
                        href = download_link.get('href')
                        # Make sure href is absolute
                        if not href.startswith('http'):
                            href = urllib.parse.urljoin("https://lso.legislature.idaho.gov", href)
                        
                        # Extract mediaId from the URL if it exists
                        media_id = None
                        parsed_url = urlparse(href)
                        query_params = parse_qs(parsed_url.query)
                        if 'mediaId' in query_params:
                            media_id = query_params['mediaId'][0]
                        
                        # Check if it's an email link
                        if href.startswith('mailto:'):
                            continue  # Skip email links
                        
                        self.logger.info(f"Found meeting: {meeting_date} - {meeting_title}")
                        
                        meeting_links.append({
                            "url": href,
                            "media_id": media_id,
                            "date": meeting_date,
                            "title": meeting_title,
                            "download_url": href  # Direct download link
                        })
                except Exception as e:
                    self.logger.warning(f"Error extracting meeting link from row: {e}")
            
            # If the above approach didn't work, fall back to the traditional table approach
            if not meeting_links:
                self.logger.info("Falling back to traditional table parsing")
                
                # Look for meeting tables or lists
                tables = soup.find_all('table')
                result_table = None
                
                for table in tables:
                    # Look for tables that might contain meeting data
                    header_cells = table.find_all('th')
                    header_text = ' '.join([cell.text.strip() for cell in header_cells])
                    
                    if 'Date' in header_text or 'Committee' in header_text or 'Meeting' in header_text:
                        result_table = table
                        break
                
                if not result_table:
                    # Try a different approach - just find any table with links
                    for table in tables:
                        if table.find('a'):
                            result_table = table
                            break
                
                if not result_table:
                    self.logger.warning("No results table found on the page")
                    return meeting_links
                
                # Get all rows in the table
                rows = result_table.find_all('tr')
                # Skip the header row if it exists
                if rows and rows[0].find('th'):
                    rows = rows[1:]
                
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if not cells:
                            continue
                        
                        meeting_date = cells[0].text.strip() if len(cells) > 0 else "Unknown Date"
                        
                        # Find all links in the row
                        links = row.find_all('a')
                        
                        for link in links:
                            if link and link.get('href'):
                                href = link.get('href')
                                link_text = link.text.strip()
                                
                                # Look for download links or meeting title links
                                if 'download' in link_text.lower() or 'audio' in link_text.lower() or 'video' in link_text.lower():
                                    # This is likely a download link
                                    download_url = href
                                    
                                    # Make sure href is absolute
                                    if not download_url.startswith('http'):
                                        download_url = urllib.parse.urljoin("https://lso.legislature.idaho.gov", download_url)
                                    
                                    # Extract mediaId from the URL if it exists
                                    media_id = None
                                    parsed_url = urlparse(download_url)
                                    query_params = parse_qs(parsed_url.query)
                                    if 'mediaId' in query_params:
                                        media_id = query_params['mediaId'][0]
                                    
                                    # Use title from previous cell if possible
                                    meeting_title = cells[1].text.strip() if len(cells) > 1 else link_text
                                    
                                    self.logger.info(f"Found meeting with download link: {meeting_date} - {meeting_title}")
                                    
                                    meeting_links.append({
                                        "url": download_url,
                                        "media_id": media_id,
                                        "date": meeting_date,
                                        "title": meeting_title,
                                        "download_url": download_url
                                    })
                    except Exception as e:
                        self.logger.warning(f"Error extracting meeting link from row: {e}")
            
        except Exception as e:
            self.logger.error(f"Error extracting meeting links: {e}")
        
        return meeting_links
    
    def direct_video_url(self, media_id):
        """
        Try to construct a direct video URL using the media ID.
        
        Args:
            media_id (str): The media ID
            
        Returns:
            str: Direct video URL if found, None otherwise
        """
        # Common patterns for direct video URLs
        patterns = [
            f"https://lso.legislature.idaho.gov/MediaArchive/mp4/{media_id}.mp4",
            f"https://lso.legislature.idaho.gov/MediaArchive/video/{media_id}.mp4",
            f"https://lso.legislature.idaho.gov/MediaPub/video/{media_id}.mp4",
            f"https://lso.legislature.idaho.gov/streaming/mp4/{media_id}.mp4",
            f"https://streaming.idaho.gov/mp4/{media_id}.mp4",
            f"https://idahoptv.org/insession/archive/{media_id}.mp4"
        ]
        
        # Try each pattern
        for url in patterns:
            try:
                self.logger.info(f"Trying direct URL: {url}")
                response = self.session.head(url)
                if response.status_code == 200:
                    self.logger.info(f"Found working direct URL: {url}")
                    return url
            except Exception:
                pass
        
        return None
    
    def extract_media_urls(self, meeting_url, media_id=None, date=None, title=None):
        """
        Visit meeting page and extract MP4 URLs.
        
        Args:
            meeting_url (str): URL of the meeting page
            media_id (str, optional): Media ID if available
            date (str, optional): Meeting date
            title (str, optional): Meeting title
            
        Returns:
            list: List of media dictionaries with URL and text
        """
        media_links = []
        
        # If it's already a direct MP4 URL, just return it
        if meeting_url.lower().endswith('.mp4'):
            self.logger.info(f"Input URL is already a direct MP4: {meeting_url}")
            media_links.append({
                "url": meeting_url,
                "text": "Direct MP4 Link"
            })
            return media_links
        
        # If we have a media_id, try to get direct URLs first
        if media_id:
            direct_url = self.direct_video_url(media_id)
            if direct_url:
                media_links.append({
                    "url": direct_url,
                    "text": "Direct MP4 Link"
                })
                return media_links
        
        # Try the insession.idaho.gov pattern
        try:
            # Extract year and month/day from URL or parameters
            year_match = re.search(r'(\d{4})', meeting_url)
            if not year_match and date:
                year_match = re.search(r'(\d{4})', date)
            
            if year_match:
                year = year_match.group(1)
                
                # Extract month and day
                date_match = None
                if date:
                    date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)', date)
                
                if not date_match:
                    date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)', meeting_url)
                
                if date_match:
                    month = date_match.group(1)
                    day = date_match.group(2)
                    
                    month_num = {
                        'January': '01', 'February': '02', 'March': '03', 'April': '04',
                        'May': '05', 'June': '06', 'July': '07', 'August': '08',
                        'September': '09', 'October': '10', 'November': '11', 'December': '12'
                    }
                    
                    day_padded = day.zfill(2)
                    month_padded = month_num.get(month, '01')
                    
                    # New pattern we discovered
                    pattern_url = f"https://insession.idaho.gov/IIS/{year}/House/Chambers/HouseChambers{month_padded}-{day_padded}-{year}.mp4"
                    self.logger.info(f"Trying insession.idaho.gov URL: {pattern_url}")
                    
                    try:
                        response = self.session.head(pattern_url, timeout=5)
                        if response.status_code == 200:
                            self.logger.info(f"Found working insession.idaho.gov URL: {pattern_url}")
                            media_links.append({
                                "url": pattern_url,
                                "text": "insession.idaho.gov MP4 Link"
                            })
                            return media_links
                    except Exception as e:
                        self.logger.debug(f"Error checking URL {pattern_url}: {e}")
                    
                    # Try a few variations
                    variations = [
                        f"https://insession.idaho.gov/IIS/{year}/House/Chambers/House{month_padded}-{day_padded}-{year}.mp4",
                        f"https://insession.idaho.gov/IIS/{year}/House/House{month_padded}-{day_padded}-{year}.mp4",
                        f"https://insession.idaho.gov/IIS/{year}/House/Day{day_padded}.mp4"
                    ]
                    
                    for var_url in variations:
                        try:
                            self.logger.info(f"Trying variation URL: {var_url}")
                            response = self.session.head(var_url, timeout=5)
                            if response.status_code == 200:
                                self.logger.info(f"Found working variation URL: {var_url}")
                                media_links.append({
                                    "url": var_url,
                                    "text": "Variation MP4 Link"
                                })
                                return media_links
                        except Exception as e:
                            self.logger.debug(f"Error checking URL {var_url}: {e}")
        except Exception as e:
            self.logger.warning(f"Error trying insession.idaho.gov patterns: {e}")
        
        # Parse chamber ID from URL if available
        chamber_id = None
        if "chamberId=" in meeting_url:
            try:
                parsed_url = urlparse(meeting_url)
                query_params = parse_qs(parsed_url.query)
                if 'chamberId' in query_params:
                    chamber_id = query_params['chamberId'][0]
                    self.logger.info(f"Extracted chamber ID: {chamber_id}")
            except Exception as e:
                self.logger.warning(f"Error parsing chamber ID: {e}")
        
        # Try some standard video patterns based on chamber ID first
        if chamber_id:
            # Try some common patterns for Idaho Legislature videos
            sample_urls = [
                f"https://idahoptv.org/insession/archive/leg{chamber_id}.mp4",
                f"https://idahoptv.org/insession/archive/house{chamber_id}.mp4",
                f"https://idahoptv.org/insession/leg/house{chamber_id}.mp4",
                f"https://idahoptv.org/insession/chamber{chamber_id}.mp4",
                f"https://streaming.legislature.idaho.gov/house{chamber_id}.mp4",
                f"https://streaming.idaho.gov/house{chamber_id}.mp4"
            ]
            
            for url in sample_urls:
                try:
                    self.logger.info(f"Trying chamber-based URL: {url}")
                    response = self.session.head(url, timeout=5)
                    if response.status_code == 200:
                        self.logger.info(f"Found working chamber-based URL: {url}")
                        media_links.append({
                            "url": url,
                            "text": "Chamber-based MP4 Link"
                        })
                        return media_links
                except Exception as e:
                    self.logger.debug(f"Error checking URL {url}: {e}")
        
        # Try specific IdahoPTV pattern
        try:
            year_chamber_match = re.search(r'(\d{4}).*?(House|Senate)', meeting_url)
            if year_chamber_match:
                year = year_chamber_match.group(1)
                chamber = year_chamber_match.group(2).lower()
                
                # Extract date from URL or title
                date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)', meeting_url)
                if date_match:
                    month = date_match.group(1)
                    day = date_match.group(2)
                    
                    # Format like "house-01-08-2024.mp4"
                    month_num = {
                        'January': '01', 'February': '02', 'March': '03', 'April': '04',
                        'May': '05', 'June': '06', 'July': '07', 'August': '08',
                        'September': '09', 'October': '10', 'November': '11', 'December': '12'
                    }
                    
                    day_padded = day.zfill(2)
                    month_padded = month_num.get(month, '01')
                    
                    pattern_url = f"https://idahoptv.org/insession/archive/{chamber}-{month_padded}-{day_padded}-{year}.mp4"
                    self.logger.info(f"Trying date-based URL: {pattern_url}")
                    
                    try:
                        response = self.session.head(pattern_url, timeout=5)
                        if response.status_code == 200:
                            self.logger.info(f"Found working date-based URL: {pattern_url}")
                            media_links.append({
                                "url": pattern_url,
                                "text": "Date-based MP4 Link"
                            })
                            return media_links
                    except Exception as e:
                        self.logger.debug(f"Error checking URL {pattern_url}: {e}")
        except Exception as e:
            self.logger.warning(f"Error creating date-based URL: {e}")
        
        # If direct approach failed, scrape the meeting page
        try:
            response = self.session.get(meeting_url)
            response.raise_for_status()
            
            # Save the HTML for debugging
            debug_dir = os.path.join(self.output_dir, '_debug')
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            with open(os.path.join(debug_dir, 'meeting_page.html'), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if page has "unexpected error"
            error_header = soup.find('h2', string='An unexpected error has occured')
            if error_header:
                self.logger.warning(f"Page shows error message for URL: {meeting_url}")
                return media_links
            
            # Look for specific patterns that might contain MP4 files
            
            # Check for direct links to MP4 files
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and '.mp4' in href.lower():
                    # Make sure href is absolute
                    if not href.startswith('http'):
                        href = urllib.parse.urljoin(meeting_url, href)
                    
                    media_links.append({
                        "url": href,
                        "text": link.text.strip() or "MP4 Link"
                    })
            
            # Check for video elements with source tags
            for video in soup.find_all('video'):
                for source in video.find_all('source'):
                    src = source.get('src')
                    if src and '.mp4' in src.lower():
                        # Make sure src is absolute
                        if not src.startswith('http'):
                            src = urllib.parse.urljoin(meeting_url, src)
                        
                        media_links.append({
                            "url": src,
                            "text": "Video Source"
                        })
            
            # Other pattern searches (onclick handlers, JavaScript variables, iframes)
            # ... (abbreviated for readability)
            
        except Exception as e:
            self.logger.error(f"Error extracting media URLs from {meeting_url}: {e}")
        
        return media_links
    
    def create_safe_dirname(self, base_name, max_length=80):
        """
        Create a safe directory name with limited length.
        
        Args:
            base_name (str): Original directory name
            max_length (int, optional): Maximum length for the directory name
            
        Returns:
            str: Safe directory name
        """
        # Remove invalid characters and replace with dashes
        safe_name = re.sub(r'[<>:"/\\|?*\r\n\t]', '-', base_name)
        safe_name = safe_name.strip()
        
        # Truncate if too long
        if len(safe_name) > max_length:
            # Create a hash of the full name to ensure uniqueness
            name_hash = hashlib.md5(safe_name.encode()).hexdigest()[:8]
            safe_name = safe_name[:max_length-9] + "_" + name_hash
        
        return safe_name
    
    def download_specific_meeting(self, year, category, target_date):
        """
        Download video from a specific date and category.
        
        Args:
            year (str): Year to download from
            category (str): Category to download from
            target_date (str): Target date (format: "Month Day", e.g., "January 6")
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        try:
            # Get available meetings for the year and category
            available_meetings = self.get_all_meetings(year, category)
            
            if not available_meetings:
                self.logger.error(f"No meetings available for {year}, {category}")
                return False
            
            # Filter for target date
            target_meetings = []
            for meeting in available_meetings:
                if target_date in meeting['date']:
                    target_meetings.append(meeting)
            
            if not target_meetings:
                self.logger.warning(f"No meetings found for date: {target_date}")
                return False
            
            self.logger.info(f"Found {len(target_meetings)} meetings for date: {target_date}")
            
            # Process each meeting for this date
            for meeting in target_meetings:
                # Create a safe directory name
                safe_title = self.create_safe_dirname(f"{meeting['date']}_{meeting['title']}")
                self.logger.info(f"Processing meeting: {safe_title}")
                
                # Create directory for the meeting
                year_dir = os.path.join(self.output_dir, year)
                category_dir = os.path.join(year_dir, self.create_safe_dirname(category))
                meeting_dir = os.path.join(category_dir, safe_title)
                
                if not os.path.exists(meeting_dir):
                    os.makedirs(meeting_dir)
                
                # Save meeting info
                meeting_info_path = os.path.join(meeting_dir, "meeting_info.json")
                with open(meeting_info_path, 'w', encoding='utf-8') as f:
                    json.dump(meeting, f, indent=2)
                
                # Determine which URL to use for extraction
                url_to_use = meeting.get('download_url', meeting['url'])
                media_id = meeting.get('media_id')
                date = meeting.get('date')
                title = meeting.get('title')
                
                # Try to download directly first if it looks like a download link
                direct_download = False
                if 'download' in url_to_use.lower() or 'audio' in url_to_use.lower() or 'video' in url_to_use.lower():
                    self.logger.info(f"Trying direct download from: {url_to_use}")
                    filename = f"direct_download.mp4"
                    output_path = os.path.join(meeting_dir, filename)
                    
                    try:
                        success = self.download_file(url_to_use, output_path)
                        if success:
                            self.logger.info(f"Successfully downloaded direct file: {filename}")
                            # Save direct download info
                            media_urls = [{
                                "url": url_to_use,
                                "text": "Direct Download Link"
                            }]
                            media_info_path = os.path.join(meeting_dir, "media_urls.json")
                            with open(media_info_path, 'w', encoding='utf-8') as f:
                                json.dump(media_urls, f, indent=2)
                            direct_download = True
                    except Exception as e:
                        self.logger.warning(f"Direct download failed: {e}")
                
                # If direct download failed, try extract media URLs from meeting page
                if not direct_download:
                    media_urls = self.extract_media_urls(url_to_use, media_id, date, title)
                    self.logger.info(f"Found {len(media_urls)} media files")
                    
                    # Save media info
                    media_info_path = os.path.join(meeting_dir, "media_urls.json")
                    with open(media_info_path, 'w', encoding='utf-8') as f:
                        json.dump(media_urls, f, indent=2)
                    
                    if len(media_urls) == 0:
                        self.logger.warning("No media files found for this meeting")
                        continue
                    
                    # Download each media file
                    downloaded_files = []
                    for idx, media in enumerate(media_urls):
                        base_filename = os.path.basename(urllib.parse.urlparse(media['url']).path)
                        if not base_filename or base_filename == '':
                            base_filename = f"video_{idx+1}.mp4"
                        
                        filename = f"{idx+1}_{base_filename}"
                        output_path = os.path.join(meeting_dir, filename)
                        
                        self.logger.info(f"Downloading {idx+1}/{len(media_urls)}: {filename}")
                        success = self.download_file(media['url'], output_path)
                        
                        if success:
                            file_info = {
                                "filename": filename,
                                "url": media['url'],
                                "size_bytes": os.path.getsize(output_path)
                            }
                            
                            # Convert to audio if requested
                            if self.convert_to_audio and self.ffmpeg_available:
                                audio_path = self.convert_video_to_audio(output_path)
                                if audio_path:
                                    file_info["audio_filename"] = os.path.basename(audio_path)
                                    file_info["audio_size_bytes"] = os.path.getsize(audio_path)
                            
                            downloaded_files.append(file_info)
                
                self.logger.info(f"Completed processing meeting: {safe_title}")
                return True  # Return after processing one meeting
            
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
        
        finally:
            self.logger.info("Download process completed")
    
    def get_all_meetings(self, year, category):
        """
        Get all meetings for a specific year and category.
        
        Args:
            year (str): Year to fetch meetings for
            category (str): Category to fetch meetings for
            
        Returns:
            list: List of meeting dictionaries
        """
        try:
            # Get the main page
            main_url = f"{self.base_url}/MainMenu.do"
            main_response = self.session.get(main_url)
            main_response.raise_for_status()
            
            soup = BeautifulSoup(main_response.text, 'html.parser')
            
            # Get available options
            available_years, available_categories = self.get_available_options(soup)
            self.logger.info(f"Available years: {available_years}")
            self.logger.info(f"Available categories: {available_categories}")
            
            # Check if year is available
            if year not in available_years:
                self.logger.error(f"Year {year} not available. Available years: {available_years}")
                return []
            
            # Check if category is available
            if category not in available_categories:
                self.logger.error(f"Category {category} not available. Available categories: {available_categories}")
                return []
            
            self.logger.info(f"Fetching meetings for Year: {year}, Category: {category}")
            
            # Get meeting results
            results_html = self.get_meeting_results(year, category)
            
            if not results_html:
                self.logger.error("Failed to get meeting results")
                return []
            
            # Extract meeting links
            meeting_links = self.extract_meeting_links(results_html)
            self.logger.info(f"Found {len(meeting_links)} meetings total")
            
            return meeting_links
            
        except Exception as e:
            self.logger.error(f"Unexpected error getting meetings: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def convert_video_to_audio(self, video_path):
        """
        Convert a video file to audio format using ffmpeg.
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Path to the converted audio file, or None if conversion failed
        """
        if not self.convert_to_audio or not self.ffmpeg_available:
            return None
            
        try:
            # Create audio directory if it doesn't exist
            video_dir = os.path.dirname(video_path)
            audio_dir = os.path.join(video_dir, 'audio')
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
            
            # Get base filename without extension
            base_name = os.path.basename(video_path)
            base_name_no_ext = os.path.splitext(base_name)[0]
            
            # Audio output path
            audio_path = os.path.join(audio_dir, f"{base_name_no_ext}.{self.audio_format}")
            
            # Run ffmpeg to convert video to audio
            self.logger.info(f"Converting {base_name} to {self.audio_format} format...")
            
            # Prepare ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # Skip video
                '-acodec', 'libmp3lame' if self.audio_format == 'mp3' else 'copy',
                '-y',  # Overwrite output file
                audio_path
            ]
            
            # Run the command
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode == 0:
                self.logger.info(f"Successfully converted to audio: {audio_path}")
                return audio_path
            else:
                self.logger.error(f"Error converting video to audio: {process.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error during audio conversion: {e}")
            return None
    
    def download_year_category(self, year, category, limit=None):
        """
        Download all videos for a specific year and category.
        
        Args:
            year (str): Year to download from
            category (str): Category to download from
            limit (int, optional): Limit the number of videos to download
            
        Returns:
            int: Number of successfully downloaded videos
        """
        self.logger.info(f"Starting download for {year}, {category}")
        
        # Get all meetings
        meetings = self.get_all_meetings(year, category)
        
        if not meetings:
            return 0
        
        if limit:
            meetings = meetings[:limit]
            self.logger.info(f"Limiting to {limit} meetings")
        
        successful_downloads = 0
        
        # Process each meeting
        for i, meeting in enumerate(meetings, 1):
            date = meeting.get("date")
            title = meeting.get("title")
            self.logger.info(f"\nProcessing meeting {i}/{len(meetings)}: {date} - {title}")
            
            # Create a date string for matching
            date_parts = date.split(" ")
            if len(date_parts) >= 2:
                target_date = f"{date_parts[0]} {date_parts[1]}"  # e.g., "January 7"
                
                # Download the meeting
                success = self.download_specific_meeting(year, category, target_date)
                
                if success:
                    self.logger.info(f"Successfully downloaded {date} - {title}")
                    successful_downloads += 1
                else:
                    self.logger.warning(f"Failed to download {date} - {title}")
                
                # Add a short delay to avoid overwhelming the server
                time.sleep(2)
            else:
                self.logger.warning(f"Skipping meeting with invalid date format: {date}")
        
        self.logger.info(f"Completed {year}, {category}. Successfully downloaded {successful_downloads}/{len(meetings)} videos.")
        return successful_downloads