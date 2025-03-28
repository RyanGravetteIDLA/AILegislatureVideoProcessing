#!/usr/bin/env python3
"""
Service account setup script

This script helps you download and install the correct service account key
for Firebase Admin SDK access to the Legislative Video Review project.

Usage:
  python setup_service_account.py

The script will guide you through the process of:
1. Downloading the service account key from Firebase console
2. Installing it in the correct location
3. Setting up environment variables
"""

import os
import sys
import json
import shutil
from pathlib import Path
import webbrowser
import time

# Add project root to path for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Try to import our unified secrets manager
try:
    from src.secrets_manager import SecretsManager
    secrets_manager_available = True
except ImportError:
    secrets_manager_available = False

# Set up paths
credentials_dir = os.path.join(base_dir, 'credentials')
service_account_file = os.path.join(credentials_dir, 'legislativevideoreviewswithai-80ed70b021b5.json')
downloads_dir = os.path.expanduser('~/Downloads')

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")

def wait_for_downloaded_key():
    """Wait for service account key to be downloaded and return the path."""
    print("Waiting for downloaded service account key file...")
    print("(Looking for files matching *firebase*adminsdk*legislativevideoreviewswithai*.json in Downloads directory)")
    
    max_wait_time = 120  # 2 minutes
    start_time = time.time()
    found_path = None
    
    while time.time() - start_time < max_wait_time:
        for file in os.listdir(downloads_dir):
            if (file.endswith('.json') and 
                'firebase' in file.lower() and 
                'adminsdk' in file.lower() and 
                'legislativevideoreviewswithai' in file.lower()):
                found_path = os.path.join(downloads_dir, file)
                print(f"Found key file: {found_path}")
                return found_path
        
        # Wait a bit before checking again
        time.sleep(2)
        sys.stdout.write('.')
        sys.stdout.flush()
    
    return None

def verify_service_account_key(file_path):
    """Verify that the service account key is valid and has the correct email."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        expected_email = "firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com"
        actual_email = data.get('client_email', '')
        
        if not actual_email:
            print("ERROR: Service account file does not contain client_email field.")
            return False
        
        if actual_email != expected_email and not actual_email.startswith('firebase-adminsdk'):
            print(f"WARNING: Service account email does not match expected format.")
            print(f"Expected: {expected_email}")
            print(f"Actual: {actual_email}")
            choice = input("Continue anyway? (y/n): ").lower()
            return choice in ('y', 'yes')
        
        return True
    except json.JSONDecodeError:
        print(f"ERROR: {file_path} is not a valid JSON file.")
        return False
    except FileNotFoundError:
        print(f"ERROR: {file_path} not found.")
        return False
    except Exception as e:
        print(f"ERROR: Could not verify service account key: {e}")
        return False

def install_service_account_key(source_path):
    """Install the service account key to the credentials directory."""
    # Create credentials directory if it doesn't exist
    os.makedirs(credentials_dir, exist_ok=True)
    
    # Copy the file
    try:
        shutil.copy(source_path, service_account_file)
        print(f"Successfully installed service account key to {service_account_file}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to install service account key: {e}")
        return False

def setup_environment_variables():
    """Set up environment variables for local development."""
    try:
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file
        
        # For Windows, create a .bat file
        if os.name == 'nt':
            bat_path = os.path.join(base_dir, 'set_credentials.bat')
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\nset GOOGLE_APPLICATION_CREDENTIALS={service_account_file}\necho Environment variable GOOGLE_APPLICATION_CREDENTIALS is set to %GOOGLE_APPLICATION_CREDENTIALS%\n')
            print(f"Created {bat_path} for setting environment variables on Windows")
        
        # For Mac/Linux, create a .sh file
        else:
            sh_path = os.path.join(base_dir, 'set_credentials.sh')
            with open(sh_path, 'w') as f:
                f.write(f'#!/bin/bash\nexport GOOGLE_APPLICATION_CREDENTIALS="{service_account_file}"\necho "Environment variable GOOGLE_APPLICATION_CREDENTIALS is set to $GOOGLE_APPLICATION_CREDENTIALS"\n')
            os.chmod(sh_path, 0o755)  # Make executable
            print(f"Created {sh_path} for setting environment variables on Mac/Linux")
        
        # Store in secrets manager if available
        if secrets_manager_available:
            try:
                with open(service_account_file, 'r') as f:
                    service_account_content = json.load(f)
                
                SecretsManager.store_service_account_content('gcs', service_account_content)
                print("Successfully stored service account in secrets manager")
            except Exception as e:
                print(f"Warning: Could not store in secrets manager: {e}")
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to set up environment variables: {e}")
        return False

def test_authentication():
    """Test authentication with the service account."""
    print("\nTesting authentication...")
    
    try:
        # Try to import and use Firebase Admin SDK
        from google.cloud import firestore
        
        print("Attempting to connect to Firestore...")
        client = firestore.Client()
        print("Successfully connected to Firestore!")
        
        try:
            # Try to get collection names (which requires actual permissions)
            collections = list(client.collections())
            print(f"Successfully accessed Firestore collections: {', '.join(col.id for col in collections[:5])}")
        except Exception as e:
            print(f"Could access Firestore but not list collections: {e}")
            print("This is normal if your service account doesn't have sufficient permissions.")
        
        return True
    except Exception as e:
        print(f"Authentication test failed: {e}")
        return False

def main():
    print_header("Firebase Admin SDK Service Account Setup")
    
    print("This script will help you set up the Firebase Admin SDK service account key.")
    print("Follow these steps:\n")
    
    # Step 1: Direct user to Firebase console
    print("Step 1: Download the service account key from Firebase console")
    print("1. Visit the Firebase console at https://console.firebase.google.com")
    print("2. Select project 'legislativevideoreviewswithai'")
    print("3. Click Project Settings (gear icon)")
    print("4. Go to the 'Service accounts' tab")
    print("5. Click 'Generate new private key' button")
    print("6. Save the file to your Downloads folder\n")
    
    choice = input("Open the Firebase console in your browser? (y/n): ").lower()
    if choice in ('y', 'yes'):
        webbrowser.open('https://console.firebase.google.com/project/legislativevideoreviewswithai/settings/serviceaccounts/adminsdk')
    
    print("\nWaiting for you to download the service account key...")
    input("Press Enter after you've downloaded the key...")
    
    # Step 2: Find and verify the downloaded key
    key_path = wait_for_downloaded_key()
    
    if not key_path:
        print("Could not find downloaded service account key after waiting.")
        key_path = input("Please enter the full path to the downloaded service account key: ")
    
    if not os.path.exists(key_path):
        print(f"ERROR: File not found: {key_path}")
        return False
    
    # Verify the key
    if not verify_service_account_key(key_path):
        print("Service account key verification failed.")
        choice = input("Continue anyway? (y/n): ").lower()
        if choice not in ('y', 'yes'):
            return False
    
    # Step 3: Install the key
    if not install_service_account_key(key_path):
        return False
    
    # Step 4: Set up environment variables
    if not setup_environment_variables():
        return False
    
    # Step 5: Test authentication
    auth_success = test_authentication()
    
    # Final summary
    print_header("Setup Complete")
    
    print("Service account key has been installed at:")
    print(f"  {service_account_file}")
    print("\nTo use this service account for local development:")
    
    if os.name == 'nt':
        print("  Run set_credentials.bat before running your application")
        print("  OR set the environment variable in your system settings")
    else:
        print("  Run source set_credentials.sh before running your application")
        print("  OR add this to your .bash_profile or .zshrc:")
        print(f'  export GOOGLE_APPLICATION_CREDENTIALS="{service_account_file}"')
    
    print("\nFor deployed applications, set the service account directly:")
    print("  gcloud run deploy media-portal-backend \\")
    print("    --service-account=firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com \\")
    print("    ... other parameters ...")
    
    if auth_success:
        print("\nAuthentication test PASSED! You are ready to use the application.")
    else:
        print("\nAuthentication test FAILED. Please check the errors above.")
        print("This may be because the service account doesn't have sufficient permissions.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)