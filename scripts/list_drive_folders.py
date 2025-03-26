#!/usr/bin/env python3
"""
Script to list available Google Drive folders.
Helps identify accessible folders for the service account.
"""

import os
import sys
import json
import logging

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('list_drive_folders')

# Constants
SERVICE_ACCOUNT_FILE = 'data/service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']  # Full access scope


def get_credentials():
    """Get service account credentials for Google Drive API."""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
            sys.exit(1)
            
        # Create credentials from service account file
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        
        return creds
    
    except Exception as e:
        logger.error(f"Error loading service account credentials: {e}")
        sys.exit(1)


def list_accessible_folders():
    """List all folders the service account has access to."""
    try:
        # Get credentials and build service
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        # Query folders
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, owners, shared)'
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print("\nNo accessible folders found.")
            print("Make sure to share a folder with the service account email.")
            return []
        
        print(f"\nFound {len(items)} accessible folders:")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item.get('name')} (ID: {item.get('id')})")
        
        # Attempt to access shared drive(s)
        try:
            shared_drives = service.drives().list(fields='drives(id,name)').execute()
            drives = shared_drives.get('drives', [])
            
            if drives:
                print(f"\nFound {len(drives)} accessible shared drives:")
                for i, drive in enumerate(drives, 1):
                    print(f"{i}. {drive.get('name')} (ID: {drive.get('id')})")
        except HttpError:
            # May not have access to shared drives
            print("\nNo accessible shared drives found or no permission to list them.")
        
        return items
    
    except HttpError as e:
        logger.error(f"API Error: {e}")
        print(f"\nError: {e}")
        return []
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        return []


def check_folder_access(folder_id):
    """Check if the service account has access to a specific folder."""
    if not folder_id:
        print("No folder ID provided.")
        return False
        
    try:
        # Get credentials and build service
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        # Try to get the folder
        folder = service.files().get(fileId=folder_id, fields='id,name,capabilities').execute()
        
        print(f"\nFolder found: {folder.get('name')} (ID: {folder.get('id')})")
        
        # Check capabilities
        capabilities = folder.get('capabilities', {})
        can_edit = capabilities.get('canEdit', False)
        can_add_children = capabilities.get('canAddChildren', False)
        
        print(f"Can edit: {can_edit}")
        print(f"Can add children: {can_add_children}")
        
        if can_add_children:
            print("✓ Service account has permission to upload files to this folder.")
            return True
        else:
            print("✗ Service account does not have permission to upload files to this folder.")
            return False
            
    except HttpError as e:
        logger.error(f"Error accessing folder {folder_id}: {e}")
        print(f"\nError: Cannot access folder with ID: {folder_id}")
        print("Possible reasons:")
        print("1. The folder ID is incorrect")
        print("2. The folder doesn't exist")
        print("3. The service account doesn't have access to this folder")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='List accessible Google Drive folders.')
    parser.add_argument('--check', help='Check access to a specific folder ID')
    
    args = parser.parse_args()
    
    try:
        if args.check:
            check_folder_access(args.check)
        else:
            list_accessible_folders()
    except KeyboardInterrupt:
        sys.exit(1)