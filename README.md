# Idaho Legislature Media Portal

A comprehensive platform for downloading, processing, transcribing, serving, and analyzing Idaho legislative session videos. This project allows you to:

1. **Download legislative session videos** from the Idaho Legislature website
2. **Convert videos to audio** for easier processing 
3. **Transcribe audio to text** using Google's Gemini AI models
4. **Store all media** (videos, audio, transcripts) on Google Drive
5. **Organize content** by year, committee, and session
6. **Serve media content** through a modern web interface
7. **Automate the workflow** with scheduled tasks

Perfect for researchers, journalists, archivists, and anyone interested in preserving and analyzing legislative proceedings.

## Features

- Downloads videos from specific sessions by date
- Bulk downloads all sessions for a year and category
- Interactive workflow with option to process a specific day only
- Converts videos to audio format (requires ffmpeg)
- Transcribes audio to text using Google's Gemini API
- Saves metadata for each session
- Organizes downloads by year, category, and date
- Securely stores API keys in the system keychain
- Tracks transcript processing in a database
- Stores all media (videos, audio, transcripts) on Google Drive
- Intelligent file organization with matching folder structure
- Handles large media files with resumable uploads

## Installation

1. Clone this repository:
```bash
git clone https://github.com/RyanGravetteIDLA/AILegislatureVideoProcessing.git
cd AILegislatureVideoProcessing
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg (required for audio conversion):
```bash
# macOS (using Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. Get a Google API key with Gemini access for transcription:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gemini API
   - Create an API key
   - Store your API key securely in the system keychain:
     ```bash
     python scripts/manage_api_keys.py store
     ```

5. Set up Google Drive API for cloud storage (recommended):
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Drive API
   - Create a service account with Drive access permissions
   - Create a key for the service account (JSON format)
   - Download the service account key and save as `data/service_account.json`
   - Create a folder in your Google Drive to store legislative media
   - Share the Google Drive folder with the service account email address
   - Run the verification tool to test your setup:
     ```bash
     python scripts/manage_drive_service.py verify
     ```

## Usage

### Download a specific date's session

```bash
python scripts/download_specific_date.py 2025 "House Chambers" "January 7"
```

### Download and convert to audio

```bash
python scripts/download_specific_date.py 2025 "House Chambers" "January 7" --convert-audio
```

### Download missing videos

```bash
python scripts/download_missing_videos.py --convert-audio
```

### API Key Management

Store your Google API key in the system keychain:
```bash
python scripts/manage_api_keys.py store
```

Verify your API key is stored correctly:
```bash
python scripts/manage_api_keys.py get
```

Delete your API key from the keychain:
```bash
python scripts/manage_api_keys.py delete
```

### Transcription

#### Transcribe audio for a specific date

```bash
python scripts/transcribe_specific_date.py --date "January 8" --year 2025
```

#### Transcribe with a specific Gemini model

```bash
# Use Gemini 2.0 Flash (faster)
python scripts/transcribe_specific_date.py --date "January 8" --year 2025 --model gemini-2.0-flash

# Use Gemini 1.5 Pro (more accurate but slower)
python scripts/transcribe_specific_date.py --date "January 8" --year 2025 --model gemini-1.5-pro
```

#### List available Gemini models

```bash
python scripts/list_gemini_models.py
```

#### Transcribe all audio files in a directory

```bash
python scripts/transcribe_audio.py directory data/downloads/2025/House\ Chambers/January\ 8,\ 2025_Legislative\ Session\ Day\ 3/audio
```

#### Batch transcribe all meetings in a year/category

```bash
python scripts/transcribe_audio.py batch --year 2025 --category "House Chambers"
```

### Other Options

#### Specify custom output directory

```bash
python scripts/download_specific_date.py 2025 "House Chambers" "January 7" --output-dir custom_output
```

#### Specify audio format

```bash
python scripts/download_specific_date.py 2025 "House Chambers" "January 7" --convert-audio --audio-format wav
```

#### Convert existing videos to audio

```bash
python scripts/convert_videos_to_audio.py --videos-dir data/downloads
```

#### Limit the number of downloads

```bash
python scripts/download_year_category.py 2025 "House Chambers" --limit 5
```

## Project Structure

- `src/` - Core source code modules:
  - `downloader.py` - Video downloading engine
  - `transcript_db.py` - Database for tracking transcript processing
  - `drive_storage.py` - Google Drive integration
  - `api.py` - REST API for the frontend
  - `file_server.py` - Serves media files
  - `server.py` - Combined server entry point
- `scripts/` - Command-line tools for various functions
- `data/` - Data storage directory:
  - `data/downloads/` - Downloaded videos and audio files
  - `data/logs/` - Processing logs
  - `data/db/` - SQLite database for transcript tracking
  - `data/service_account.json` - Google service account credentials (you create this)
- `frontend/` - Vue.js frontend application:
  - `frontend/src/views/` - Main application views
  - `frontend/src/components/` - Reusable UI components
  - `frontend/src/stores/` - Pinia state stores
  - `frontend/src/router/` - Vue Router configuration

## Quick Start Guide

### 1. Download, Convert, and Transcribe Videos

The easiest way to start downloading, converting, and transcribing videos is to use the interactive process_committee.py script:

```bash
python scripts/process_committee.py
```

This script will:
- Show you available years and categories from the Idaho Legislature website
- Let you select which ones you want to download
- Ask if you want to process a specific day only (NEW)
- If yes, show available dates to choose from (NEW)
- Download the videos
- Convert them to audio
- Transcribe the audio files using Google's Gemini API

You can also run it with specific options:
```bash
# Process all videos in a category
python scripts/process_committee.py --year 2025 --category "House Chambers" --limit 5 --yes

# Process a specific day only
python scripts/process_committee.py --year 2025 --category "House Chambers" --day "January 8" --yes
```

### 2. Start the Web Interface

After processing videos, start the API server and web interface to browse your media:

```bash
# Start both API server and web interface
./start_local.sh

# The web interface will be available at:
# - Frontend: http://localhost:5173
# - API: http://localhost:5000/api
# - Files: http://localhost:5001/files
```

### Starting Services Individually

You can also start each service separately:

```bash
# Start just the API server
cd src
python server.py --api-only

# Start just the file server
cd src
python server.py --file-only

# Start the frontend development server
cd frontend
npm run dev
```

## Workflow

The project offers multiple workflow options depending on your needs, including interactive processes, manual steps, and automatic cloud storage.

### Interactive All-in-One Process

Use the interactive script to handle the download and transcription workflow:

```bash
python scripts/process_committee.py
```

This script will:
1. Present you with available years and committees
2. Check for missing videos from your selection
3. Download missing videos
4. Convert videos to audio files
5. Transcribe audio to text using Gemini AI

You can also run with specific options:
```bash
# Process all videos in a category
python scripts/process_committee.py --year 2025 --category "House Chambers" --limit 5

# Process a specific day only (new feature)
python scripts/process_committee.py --year 2025 --category "House Chambers" --day "January 8"
```

### Complete Workflow with Cloud Storage

For a complete end-to-end workflow including cloud storage:

1. Download and process videos/audio/transcripts:
   ```bash
   # Process all videos in a category
   python scripts/process_committee.py --year 2025 --category "House Chambers"
   
   # Or process a specific day only
   python scripts/process_committee.py --year 2025 --category "House Chambers" --day "January 8"
   ```

2. Scan and update the transcript database:
   ```bash
   python scripts/scan_transcripts.py
   ```

3. Upload all media to Google Drive:
   ```bash
   python scripts/daily_upload.py
   ```

4. Start the web interface to browse processed media:
   ```bash
   ./start_local.sh
   ```

5. Access your files either through:
   - The web interface at http://localhost:5173
   - Google Drive organized by media type, year, category, and session

### Transcript Management and Upload

For managing transcripts and uploading to Google Drive:

```bash
# Scan for transcripts and update the database
python scripts/scan_transcripts.py

# Upload transcripts to Google Drive
python scripts/upload_media_to_drive.py --media-type transcript

# All-in-one process: scan, update DB, and upload
python scripts/process_transcripts.py

# Only scan transcripts, don't upload
python scripts/process_transcripts.py --scan-only

# Limit the number of uploads in one run
python scripts/process_transcripts.py --upload-limit 5
```

### Google Drive Storage

For storing and managing media files on Google Drive:

```bash
# Show service account information
python scripts/manage_drive_service.py info

# Test connection to Google Drive API
python scripts/manage_drive_service.py test

# Complete verification process (info, connection test, upload test)
python scripts/manage_drive_service.py verify

# Upload all media files (videos, audio, transcripts) to Google Drive
python scripts/upload_media_to_drive.py

# Upload specific media type
python scripts/upload_media_to_drive.py --media-type video
python scripts/upload_media_to_drive.py --media-type audio
python scripts/upload_media_to_drive.py --media-type transcript

# Upload media from specific sessions
python scripts/upload_media_to_drive.py --year 2025 --category "House Chambers" --session "January 8, 2025_Legislative Session Day 3"

# Control upload behavior
python scripts/upload_media_to_drive.py --batch-size 10 --rate-limit 2 --limit 20

# Automated Daily Upload
python scripts/daily_upload.py --recent-only --days 1

# Options for daily upload
python scripts/daily_upload.py --recent-only --days 7  # Upload files from the last week
python scripts/daily_upload.py --force  # Upload all files, even if they already exist
python scripts/daily_upload.py --batch-size 10 --rate-limit 2  # Customize upload performance
```

### Manual Step-by-Step Workflow

If you prefer to run the process manually step-by-step:

1. **Download Videos**: Use `download_specific_date.py` or `download_missing_videos.py` to download videos
2. **Convert to Audio**: Add the `--convert-audio` flag when downloading to automatically convert
3. **Store API Key**: Use `manage_api_keys.py store` to securely save your Google API key
4. **Transcribe**: Use `transcribe_specific_date.py` to transcribe the audio to text
5. **Scan & Track**: Use `scan_transcripts.py` to catalog all transcriptions in the database
6. **Set Up Drive**: Use `manage_drive_service.py verify` to set up Google Drive access
7. **Upload Media**: Use `upload_media_to_drive.py` to upload all media to Google Drive
8. **Start Website**: Use `./start_local.sh` to start the web interface
9. **Review**: Access your media files through the web interface or organized in Google Drive

#### Example Command Sequence

```bash
# 1. Download a specific date
python scripts/download_specific_date.py 2025 "House Chambers" "January 6" --convert-audio

# 2. Transcribe the audio
python scripts/transcribe_audio.py meeting data/downloads/2025/House\ Chambers/January_6_2025_Session

# 3. Update the database
python scripts/scan_transcripts.py

# 4. Start the web interface
./start_local.sh
```

### GitHub Repository Management

The project includes tools for managing the GitHub repository:

```bash
# Initialize GitHub setup (create config from sample)
cp .github-config.sample .github-config
# Edit .github-config with your GitHub username and token

# Create and configure the repository
python scripts/manage_github.py setup --create

# Push changes to GitHub
python scripts/manage_github.py push

# Force push to GitHub (use with caution)
python scripts/manage_github.py push --force

# Push to a different branch
python scripts/manage_github.py push --branch feature-branch
```

### Scheduling Automatic Uploads

You can set up daily automated uploads using cron (Linux/Mac) or Task Scheduler (Windows):

#### Using cron (Linux/Mac)

Add a daily cron job by editing your crontab:

```bash
crontab -e
```

Add a line like this to run the upload daily at 2 AM:

```
0 2 * * * cd /path/to/AILegislatureVideoProcessing && python scripts/daily_upload.py --recent-only --days 1 >> data/logs/cron_upload.log 2>&1
```

#### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a Basic Task
3. Set a daily trigger
4. Action: Start a program
5. Program/script: `python`
6. Add arguments: `scripts/daily_upload.py --recent-only --days 1`
7. Start in: `C:\path\to\AILegislatureVideoProcessing`

## License

MIT

## Acknowledgements

- IdahoPTV for hosting the legislative session videos
- Idaho Legislature for providing the media archive service
- Google for the Gemini API used in transcription