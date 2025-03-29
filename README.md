# Idaho Legislature Media Portal

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Google Cloud Storage](https://img.shields.io/badge/Storage-Google_Cloud-4285F4?logo=google-cloud&logoColor=white)
![Gemini AI](https://img.shields.io/badge/AI-Gemini-4E8AF4?logo=google&logoColor=white)

A comprehensive platform for downloading, processing, transcribing, serving, and analyzing Idaho legislative session videos. This project leverages Google Cloud technologies to create a modern media portal for legislative content.

## Quick Start
```bash
# For an interactive workflow that handles everything:
python scripts/process_committee.py

# This will guide you through selecting a year, committee, and optionally a specific day
# It will download videos, convert to audio, and handle transcription in one process
```

The platform provides:

1. **Download legislative session videos** from the Idaho Legislature website
2. **Convert videos to audio** for easier processing 
3. **Transcribe audio to text** using Google's Gemini AI models
4. **Store all media** (videos, audio, transcripts) on Google Cloud Storage
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
- Stores all media (videos, audio, transcripts) on Google Cloud Storage
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

5. Set up Google Cloud Storage:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Cloud Storage API
   - Create a bucket to store your media files
   - Create a service account with Storage Admin permissions
   - Create a key for the service account (JSON format)
   - Download the service account key and save as `data/service_account.json`
   - Configure your cloud storage settings:
     ```bash
     python scripts/manage_cloud_storage.py setup
     ```
   - Or use the centralized secrets manager:
     ```bash
     python src/secrets_manager.py test --cloud
     ```
   - Verify your setup:
     ```bash
     python scripts/manage_cloud_storage.py verify
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

### Secrets Management

This project uses a centralized secrets management system that securely stores all credentials and API keys in your system's keychain. This approach is more secure than storing credentials in environment variables or configuration files.

#### Migrating to the Centralized Secrets Manager

If you're upgrading from a previous version, you can migrate your existing secrets to the new system:

```bash
python scripts/migrate_secrets.py
```

#### Managing API Keys

Store your Google API key in the system keychain:
```bash
python src/secrets_manager.py test --api-keys
```

Verify your API key is stored correctly:
```bash
python src/secrets_manager.py test --api-keys
```

#### Managing GitHub Credentials

Set up or check your GitHub credentials:
```bash
python src/secrets_manager.py test --github
```

#### Managing Cloud Storage Settings

Configure Google Cloud Storage settings:
```bash
python src/secrets_manager.py test --cloud
```

#### Managing Service Account Credentials

Check your service account configurations:
```bash
python src/secrets_manager.py test --service-accounts
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

## Architecture

### Project Structure

- `src/` - Core source code modules:
  - `downloader.py` - Video downloading engine
  - `transcript_db.py` - Database for tracking transcript processing
  - `cloud_storage.py` - Google Cloud Storage integration
  - `secrets_manager.py` - Centralized secrets management
  - `api.py` - REST API for the frontend
  - `file_server.py` - Serves media files
  - `server.py` - Combined server entry point
- `scripts/` - Command-line tools for various functions:
  - Processing scripts (download, convert, transcribe)
  - Cloud storage management and upload
  - Utility scripts for maintenance
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

### Cloud Architecture

The application utilizes Google Cloud services for scalable and reliable operation:

- **Google Cloud Storage**: Stores all media files (videos, audio, transcripts)
- **Google Gemini AI**: Handles transcription and analysis
- **Firebase/Firestore**: Hosts the web frontend and provides NoSQL database
- **Cloud Functions**: Deploys the backend API (replaced Cloud Run)
- **Firebase Hosting**: Serves the frontend application

Benefits of this cloud architecture:
- Serverless architecture with minimal configuration
- Pay-per-use pricing model
- Scales automatically based on demand
- Reduces local storage requirements 
- Accelerates media delivery
- Allows access from anywhere
- Improves reliability with Google's infrastructure

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

The project offers multiple workflow options depending on your needs, including interactive processes, manual steps, and automatic cloud storage with Google Cloud Storage.

### Using the Downloader Module

The core functionality for downloading media from the Idaho Legislature website is provided by the `src/downloader.py` module, which is used by all the download scripts. This module provides the `IdahoLegislatureDownloader` class with these key functions:

- `download_specific_meeting(year, category, target_date)` - Downloads media files for a specific date
- `download_year_category(year, category, limit=None)` - Downloads all media for a year/category, with optional limit
- `get_all_meetings(year, category)` - Gets all available meetings for a year/category
- `convert_video_to_audio(video_path)` - Converts videos to audio format using ffmpeg

The following scripts are available to interact with the downloader:

1. **Download Specific Date**: 
   ```bash
   python scripts/download_specific_date.py 2025 "House Chambers" "January 8" --convert-audio
   ```

2. **Download All Videos for Year/Category**: 
   ```bash
   python scripts/download_year_category.py 2025 "House Chambers" --convert-audio
   ```

3. **Download Missing Videos**: 
   ```bash
   python scripts/download_missing_videos.py --year 2025 --category "House Chambers" --convert-audio
   ```

4. **Daily Cloud Ingest** (combines downloading & uploading to cloud):
   ```bash
   python scripts/daily_cloud_ingest.py
   ```

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

3. Upload all media to Google Cloud Storage:
   ```bash
   python scripts/upload_media_to_cloud.py
   ```

4. Start the web interface to browse processed media:
   ```bash
   ./start_local.sh
   ```

5. Access your files either through:
   - The web interface at http://localhost:5173
   - Google Cloud Storage organized by media type, year, category, and session

### Transcript Management and Upload

For managing transcripts and uploading to Google Cloud Storage:

```bash
# Scan for transcripts and update the database
python scripts/scan_transcripts.py

# Upload transcripts to Google Cloud Storage
python scripts/upload_media_to_cloud.py --media-type transcript

# All-in-one process: scan, update DB, and upload
python scripts/process_transcripts.py

# Only scan transcripts, don't upload
python scripts/process_transcripts.py --scan-only

# Limit the number of uploads in one run
python scripts/process_transcripts.py --upload-limit 5
```

### Cloud Storage

The project supports Google Cloud Storage for efficient and reliable cloud storage.

For storing and managing media files on Google Cloud Storage:

```bash
# Set up your GCS credentials and settings
python scripts/manage_cloud_storage.py setup

# Test connection to Google Cloud Storage
python scripts/manage_cloud_storage.py test

# Complete verification process
python scripts/manage_cloud_storage.py verify

# View your current settings
python scripts/manage_cloud_storage.py get

# Set up environment variables for the current session
python scripts/manage_cloud_storage.py env

# Generate export statements for your shell
python scripts/manage_cloud_storage.py env --export

# Migrate files to Google Cloud Storage
python scripts/migrate_to_cloud_storage.py

# Migrate specific types of files
python scripts/migrate_to_cloud_storage.py --media-types video,audio

# Control migration behavior
python scripts/migrate_to_cloud_storage.py --batch-size 10 --rate-limit 1 --limit 20

# Upload all media files (videos, audio, transcripts) to Google Cloud Storage
python scripts/upload_media_to_cloud.py

# Upload specific media type
python scripts/upload_media_to_cloud.py --media-type video
python scripts/upload_media_to_cloud.py --media-type audio
python scripts/upload_media_to_cloud.py --media-type transcript

# Upload media from specific sessions
python scripts/upload_media_to_cloud.py --year 2025 --category "House Chambers" --session "January 8, 2025_Legislative Session Day 3"

# Control upload behavior
python scripts/upload_media_to_cloud.py --batch-size 10 --rate-limit 2 --limit 20

# Automated Daily Upload
python scripts/daily_upload.py --recent-only --days 1

# Options for daily upload
python scripts/daily_upload.py --recent-only --days 7  # Upload files from the last week
python scripts/daily_upload.py --force  # Upload all files, even if they already exist
python scripts/daily_upload.py --batch-size 10 --rate-limit 2  # Customize upload performance
```

Once configured, the file server will automatically serve files from Google Cloud Storage when enabled in your settings.

### Manual Step-by-Step Workflow

If you prefer to run the process manually step-by-step:

1. **Download Videos**: Use `download_specific_date.py` or `download_missing_videos.py` to download videos
2. **Convert to Audio**: Add the `--convert-audio` flag when downloading to automatically convert
3. **Store API Key**: Use `manage_api_keys.py store` to securely save your Google API key
4. **Transcribe**: Use `transcribe_specific_date.py` to transcribe the audio to text
5. **Scan & Track**: Use `scan_transcripts.py` to catalog all transcriptions in the database
6. **Set Up Cloud Storage**: Use `manage_cloud_storage.py verify` to set up Google Cloud Storage access
7. **Upload Media**: Use `upload_media_to_cloud.py` to upload all media to Google Cloud Storage
8. **Start Website**: Use `./start_local.sh` to start the web interface
9. **Review**: Access your media files through the web interface or organized in Google Cloud Storage

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

## Deployment

This project is designed to be deployed on Google Cloud Platform, with the frontend on Firebase Hosting and the backend on Cloud Functions (previously Cloud Run).

### Backend Deployment

#### Cloud Functions (Current Approach)

We now use Cloud Functions for the backend API instead of Cloud Run, which simplifies the deployment process:

```bash
# Deploy the Cloud Function
./deploy_simple_function.sh
```

The deployment script configures a Cloud Function with:
- Region: us-west1
- Memory: 256MB
- Runtime: Python 3.9
- Service account: firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
- Public access (no authentication required)

For complete details on this approach, see [CLOUD_FUNCTION_DEPLOYMENT.md](CLOUD_FUNCTION_DEPLOYMENT.md).

#### Cloud Run (Legacy Approach)

The previous approach used Cloud Run:

```bash
# Deploy with Cloud Build (legacy)
./deploy_cloud_build.sh

# Or deploy directly to Cloud Run (legacy)
./deploy_cloud_run.sh
```

The Cloud Run deployment configured:
- Region: us-west1
- Memory: 1GB
- Service account: firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com
- Public access (no authentication required)

### Frontend Deployment (Firebase)

To deploy the frontend to Firebase Hosting:

```bash
# Deploy to Firebase
cd frontend
./deploy_to_firebase.sh
```

For additional Firebase configuration details, see [FIREBASE_DEPLOYMENT.md](frontend/FIREBASE_DEPLOYMENT.md).

## Testing the API

The project includes a comprehensive API testing framework and a deployed Cloud Run backend at:
```
https://media-portal-backend-335217295357.us-west1.run.app
```

### Automated API Testing

We provide a robust testing framework to verify the functionality and performance of the API:

```bash
# Run the core API tests
./run_real_api_tests.sh --core

# Run extended tests including filtering and search
./run_real_api_tests.sh --extended

# Run all tests including performance and concurrency
./run_real_api_tests.sh --all

# Export API responses as JSON for documentation
./run_real_api_tests.sh --export

# Test against the new Cloud Function API
./run_real_api_tests.sh --url https://media-portal-api-6alz6huq6a-uw.a.run.app

# Test against a local server
./run_real_api_tests.sh --url http://localhost:5000

# Show all options
./run_real_api_tests.sh --help
```

The testing framework includes:
- Core endpoint tests (health, videos, audio, transcripts)
- Data filtering and search tests
- Performance and concurrency tests
- CORS and browser simulation
- Error handling verification

For complete API testing documentation, see [REAL_API_TESTING_GUIDE.md](REAL_API_TESTING_GUIDE.md).

### Manual API Testing

You can also test the API endpoints directly:

```bash
# Health check
curl https://media-portal-api-6alz6huq6a-uw.a.run.app/api/health

# Videos
curl https://media-portal-api-6alz6huq6a-uw.a.run.app/api/videos

# Filter by year
curl "https://media-portal-api-6alz6huq6a-uw.a.run.app/api/videos?year=2025"

# Filter by category
curl "https://media-portal-api-6alz6huq6a-uw.a.run.app/api/videos?category=House%20Chambers"

# Search
curl "https://media-portal-api-6alz6huq6a-uw.a.run.app/api/videos?search=session"
```

Alternatively, you can use the Cloud Function URL:

```bash
curl https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api/api/health
```

For troubleshooting and connection issues, see [TEST_API_CONNECTION.md](TEST_API_CONNECTION.md) or use the diagnostic page at https://legislativevideoreviewswithai.web.app/diagnostic.html.

### API Endpoints Reference

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/health` | GET | API health status | None |
| `/api/videos` | GET | List all videos | `year`, `category`, `search` |
| `/api/videos/{id}` | GET | Get specific video | None |
| `/api/audio` | GET | List all audio files | `year`, `category`, `search` |
| `/api/audio/{id}` | GET | Get specific audio file | None |
| `/api/transcripts` | GET | List all transcripts | `year`, `category`, `search` |
| `/api/transcripts/{id}` | GET | Get specific transcript | None |
| `/api/filters` | GET | Get available filters | None |
| `/api/stats` | GET | Get media statistics | None |

### Common Issues

- **CORS**: Verify CORS settings in `src/api_firestore.py` if the frontend can't connect
- **Environment Variables**: Check `.env.production` for correct API URLs
- **Cloud Storage**: Ensure your service account has proper permissions
- **Firestore Connection**: Verify database connectivity if no data appears
- **API Changes**: If the API structure has changed, the tests will identify the issues

## License

MIT

## Acknowledgements

- IdahoPTV for hosting the legislative session videos
- Idaho Legislature for providing the media archive service
- Google for the Gemini API used in transcription