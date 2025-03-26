#!/usr/bin/env python3
"""
Script to manage Google Drive service account setup and testing.
Helps with setting up and verifying service account permissions.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Disable googleapiclient discovery cache warning
os.environ['GOOGLE_DISCOVERY_URL'] = ''

# Filter out the googleapiclient warning
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# For Google API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Configure logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'drive_service.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('manage_drive_service')

# Constants
SERVICE_ACCOUNT_FILE = 'data/service_account.json'
TEST_FILE_PATH = 'data/test_upload.txt'
ROOT_FOLDER_ID = '10B0htKFOHSuYHe5iSi94ukwmF-9I6R-D'  # Specific Google Drive folder ID
ROOT_FOLDER_NAME = 'Legislative Media'  # Name used for display/logging purposes
SCOPES = ['https://www.googleapis.com/auth/drive']  # Full access scope


def get_service_account_info():
    """Display service account information from the JSON file."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return False
    
    try:
        with open(SERVICE_ACCOUNT_FILE, 'r') as f:
            sa_info = json.load(f)
        
        print("\nService Account Information:")
        print(f"  Email: {sa_info.get('client_email')}")
        print(f"  Project ID: {sa_info.get('project_id')}")
        print(f"  Token URI: {sa_info.get('token_uri')}")
        
        print("\nIMPORTANT: Make sure to share your Google Drive folder with this email address:")
        print(f"  {sa_info.get('client_email')}")
        print("\nThe service account must have at least 'Editor' access to upload files.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error reading service account file: {e}")
        return False


def create_test_file():
    """Create a test file for uploading to Google Drive."""
    os.makedirs(os.path.dirname(TEST_FILE_PATH), exist_ok=True)
    
    with open(TEST_FILE_PATH, 'w') as f:
        f.write("This is a test file for verifying Google Drive API access.\n")
        f.write(f"Created: {datetime.now().isoformat()}\n")
    
    logger.info(f"Created test file: {TEST_FILE_PATH}")
    return True


def test_drive_connection():
    """Test connection to Google Drive API using service account."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return False
    
    try:
        # Create credentials
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        
        # Build the service
        service = build('drive', 'v3', credentials=creds)
        
        # Test API connection
        about = service.about().get(fields="user,storageQuota").execute()
        
        print("\nConnection successful!")
        print(f"User: {about.get('user', {}).get('displayName')}")
        
        return True
    
    except HttpError as e:
        logger.error(f"Error connecting to Drive API: {e}")
        print(f"\nError connecting to Drive API: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        return False


def test_drive_upload():
    """Test uploading a file to Google Drive using service account."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return False
    
    if not os.path.exists(TEST_FILE_PATH):
        create_test_file()
    
    try:
        # Create credentials
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        
        # Build the service
        service = build('drive', 'v3', credentials=creds)
        
        # Use the specified root folder ID
        try:
            # Verify the root folder exists and is accessible
            folder = service.files().get(fileId=ROOT_FOLDER_ID).execute()
            print(f"\nUsing existing folder '{folder.get('name')}' with ID: {ROOT_FOLDER_ID}")
            root_folder_id = ROOT_FOLDER_ID
        except HttpError as e:
            logger.error(f"Error accessing the specified root folder ID: {e}")
            print(f"\nError: Cannot access the specified Google Drive folder with ID: {ROOT_FOLDER_ID}")
            print("Please check that:")
            print("1. The folder ID is correct")
            print("2. The service account has access to this folder")
            print("3. You've shared the folder with the service account email")
            return False
        
        # Upload test file
        file_metadata = {
            'name': os.path.basename(TEST_FILE_PATH),
            'parents': [root_folder_id]
        }
        
        media = MediaFileUpload(
            TEST_FILE_PATH,
            mimetype='text/plain',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        print("\nFile upload successful!")
        print(f"Uploaded: {file.get('name')}")
        print(f"File ID: {file.get('id')}")
        print(f"Web Link: {file.get('webViewLink')}")
        
        return True
    
    except HttpError as e:
        logger.error(f"Error uploading to Drive: {e}")
        print(f"\nError uploading to Drive: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        return False


def verify_setup():
    """Verify the complete setup of the service account."""
    print("\n=== Google Drive Service Account Verification ===\n")
    
    steps = [
        {"name": "Verify service account file exists", "func": get_service_account_info},
        {"name": "Test Drive API connection", "func": test_drive_connection},
        {"name": "Test file upload capability", "func": test_drive_upload}
    ]
    
    all_success = True
    
    for i, step in enumerate(steps, 1):
        print(f"\n{i}. {step['name']}...")
        success = step['func']()
        status = "✓ Success" if success else "✗ Failed"
        print(f"   Status: {status}")
        
        if not success:
            all_success = False
            print(f"\nVerification stopped at step {i}. Please fix the issues and try again.")
            break
    
    if all_success:
        print("\n✓ All verification steps completed successfully!")
        print("You're all set to use the Google Drive upload functionality.")
    
    return all_success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage Google Drive service account setup.')
    parser.add_argument('command', choices=['info', 'test', 'verify'], 
                        help='Command to execute (info: show service account info, '
                             'test: test API connection, verify: complete verification)')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'info':
            get_service_account_info()
        elif args.command == 'test':
            test_drive_connection()
        elif args.command == 'verify':
            verify_setup()
    
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)