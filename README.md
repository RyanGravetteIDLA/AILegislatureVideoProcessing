# Idaho Legislature Media Downloader

A Python tool for downloading legislative session videos from the Idaho Legislature website, converting them to audio, and transcribing the content.

## Features

- Downloads videos from specific sessions by date
- Bulk downloads all sessions for a year and category
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
git clone <repository-url>
cd pullLegislature
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

5. Set up Google Drive API for transcript uploads (optional):
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Drive API
   - Create a service account with Drive access permissions
   - Create a key for the service account (JSON format)
   - Download the service account key and save as `data/service_account.json`
   - Share the destination Google Drive folder with the service account email

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

- `src/` - Source code for the downloader
- `scripts/` - Command-line scripts
- `data/` - Default directory for downloads and logs
  - `data/downloads/` - Downloaded videos and audio files
  - `data/logs/` - Log files
  - `data/db/` - SQLite database for transcript tracking

## Workflow

### Interactive All-in-One Process

Use the interactive script to handle the complete workflow:

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
python scripts/process_committee.py --year 2025 --category "House Chambers" --limit 5
```

### Transcript Management and Upload

For managing transcripts and uploading to Google Drive:

```bash
# Scan for transcripts and update the database
python scripts/scan_transcripts.py

# Upload transcripts to Google Drive
python scripts/upload_to_drive.py

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
8. **Review**: Access your media files organized in Google Drive

### Scheduling Automatic Uploads

You can set up daily automated uploads using cron (Linux/Mac) or Task Scheduler (Windows):

#### Using cron (Linux/Mac)

Add a daily cron job by editing your crontab:

```bash
crontab -e
```

Add a line like this to run the upload daily at 2 AM:

```
0 2 * * * cd /path/to/PullLegislature2 && python scripts/daily_upload.py --recent-only --days 1 >> data/logs/cron_upload.log 2>&1
```

#### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a Basic Task
3. Set a daily trigger
4. Action: Start a program
5. Program/script: `python`
6. Add arguments: `scripts/daily_upload.py --recent-only --days 1`
7. Start in: `C:\path\to\PullLegislature2`

## License

MIT

## Acknowledgements

- IdahoPTV for hosting the legislative session videos
- Idaho Legislature for providing the media archive service
- Google for the Gemini API used in transcription