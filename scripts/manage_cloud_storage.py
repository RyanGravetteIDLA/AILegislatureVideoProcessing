#!/usr/bin/env python3
"""
Script to manage Google Cloud Storage setup and credentials.
Helps with setting up and verifying bucket access permissions.
"""

import os
import sys
import json
import logging
import argparse
import keyring
import getpass
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logs_dir = os.path.join("data", "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "cloud_storage.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger("manage_cloud_storage")

# Service name for storing secrets in keychain
KEYCHAIN_SERVICE = "IdahoLegislatureCloudStorage"

# Constants for service account
SERVICE_ACCOUNT_FILE = "data/gcs_service_account.json"
TEST_FILE_PATH = "data/test_gcs_upload.txt"

try:
    # Import the Cloud Storage module
    from src.cloud_storage import GoogleCloudStorage

    gcs_available = True
except ImportError:
    gcs_available = False
    logger.warning("GoogleCloudStorage module not available")


def store_setting(setting_name, prompt_text=None, sensitive=False):
    """
    Store a setting in the system keychain.

    Args:
        setting_name: Name of the setting (used as username in keychain)
        prompt_text: Text to display when prompting for the value
        sensitive: Whether the input should be treated as sensitive (no echo)

    Returns:
        bool: True if successful, False otherwise
    """
    if not prompt_text:
        prompt_text = f"Enter {setting_name}: "

    # Prompt for the value
    if sensitive:
        value = getpass.getpass(prompt_text)
    else:
        value = input(prompt_text)

    if not value:
        print(f"Error: Value for {setting_name} cannot be empty")
        return False

    try:
        # Store the value in keychain
        keyring.set_password(KEYCHAIN_SERVICE, setting_name, value)
        print(f"Successfully stored {setting_name} in the system keychain")
        return True
    except Exception as e:
        print(f"Error storing {setting_name}: {e}")
        return False


def get_setting(setting_name):
    """
    Retrieve a setting from the system keychain.

    Args:
        setting_name: Name of the setting (used as username in keychain)

    Returns:
        str: The setting value or None if not found
    """
    try:
        value = keyring.get_password(KEYCHAIN_SERVICE, setting_name)
        if not value:
            print(f"{setting_name} not found in keychain. Please store it first.")
            return None
        return value
    except Exception as e:
        print(f"Error retrieving {setting_name}: {e}")
        return None


def delete_setting(setting_name):
    """
    Delete a setting from the system keychain.

    Args:
        setting_name: Name of the setting to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.delete_password(KEYCHAIN_SERVICE, setting_name)
        print(f"Successfully deleted {setting_name} from the system keychain")
        return True
    except keyring.errors.PasswordDeleteError:
        print(f"No {setting_name} found in the keychain")
        return False
    except Exception as e:
        print(f"Error deleting {setting_name}: {e}")
        return False


def store_bucket_name():
    """
    Store the Google Cloud Storage bucket name in the system keychain.

    Returns:
        bool: True if successful, False otherwise
    """
    print("\nStoring Google Cloud Storage bucket name")
    print(
        "The bucket name will be saved securely and used for all cloud storage operations"
    )

    return store_setting(
        "GCS_BUCKET_NAME", "Enter your GCS bucket name: ", sensitive=False
    )


def store_cloud_settings():
    """
    Store all cloud storage settings in the system keychain.

    Returns:
        bool: True if successful, False otherwise
    """
    print("\n=== Google Cloud Storage Configuration ===")

    success = store_bucket_name()

    # Store boolean flags with default values
    for setting, prompt, default in [
        ("USE_CLOUD_STORAGE", "Enable cloud storage? (true/false): ", "true"),
        (
            "CLOUD_STORAGE_PUBLIC",
            "Make files publicly accessible? (true/false): ",
            "false",
        ),
        (
            "PREFER_CLOUD_STORAGE",
            "Prefer cloud over local storage? (true/false): ",
            "false",
        ),
    ]:
        print(f"\nConfiguring {setting}")
        value = input(f"{prompt} [default: {default}]: ").strip().lower()

        # Use default if no input
        if not value:
            value = default

        # Validate boolean value
        if value not in ("true", "false", "yes", "no", "1", "0"):
            print(f"Invalid value for {setting}. Using default: {default}")
            value = default

        # Store the setting
        success = store_setting(setting, None, False) and success

    if success:
        print("\nAll cloud storage settings have been stored successfully")
    else:
        print("\nSome settings could not be stored. Please try again.")

    return success


def get_cloud_settings():
    """
    Retrieve and display all cloud storage settings.

    Returns:
        dict: Cloud storage settings or None if not all settings are available
    """
    settings = {}

    # Required settings
    required_settings = ["GCS_BUCKET_NAME", "USE_CLOUD_STORAGE"]

    # Optional settings with defaults
    optional_settings = {
        "CLOUD_STORAGE_PUBLIC": "false",
        "PREFER_CLOUD_STORAGE": "false",
    }

    # Get all settings
    print("\n=== Google Cloud Storage Settings ===")

    # Get required settings
    for setting in required_settings:
        value = get_setting(setting)
        if value:
            if setting == "GCS_BUCKET_NAME":
                print(f"{setting}: {value}")
            else:
                print(f"{setting}: {value}")
            settings[setting] = value
        else:
            print(f"{setting}: Not found (REQUIRED)")
            return None

    # Get optional settings with defaults
    for setting, default in optional_settings.items():
        value = get_setting(setting)
        if not value:
            value = default
            print(f"{setting}: {value} (default)")
        else:
            print(f"{setting}: {value}")
        settings[setting] = value

    # Convert boolean strings to Python booleans
    for setting in [
        "USE_CLOUD_STORAGE",
        "CLOUD_STORAGE_PUBLIC",
        "PREFER_CLOUD_STORAGE",
    ]:
        settings[setting] = settings[setting].lower() in ("true", "yes", "1")

    return settings


def delete_cloud_settings():
    """
    Delete all cloud storage settings from the system keychain.

    Returns:
        bool: True if successful, False otherwise
    """
    settings = [
        "GCS_BUCKET_NAME",
        "USE_CLOUD_STORAGE",
        "CLOUD_STORAGE_PUBLIC",
        "PREFER_CLOUD_STORAGE",
    ]

    success = True
    for setting in settings:
        success = delete_setting(setting) and success

    if success:
        print("\nAll cloud storage settings have been deleted from the keychain")
    else:
        print("\nSome settings could not be deleted. They might not exist.")

    return success


def create_test_file():
    """
    Create a test file for uploading to Google Cloud Storage.

    Returns:
        bool: True if successful, False otherwise
    """
    os.makedirs(os.path.dirname(TEST_FILE_PATH), exist_ok=True)

    try:
        with open(TEST_FILE_PATH, "w") as f:
            f.write(
                "This is a test file for verifying Google Cloud Storage API access.\n"
            )
            f.write(f"Created: {datetime.now().isoformat()}\n")

        logger.info(f"Created test file: {TEST_FILE_PATH}")
        print(f"Created test file: {TEST_FILE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error creating test file: {e}")
        print(f"Error creating test file: {e}")
        return False


def test_cloud_storage():
    """
    Test connection to Google Cloud Storage.

    Returns:
        bool: True if successful, False otherwise
    """
    if not gcs_available:
        print("Error: Google Cloud Storage module is not available.")
        print("Please install required packages: pip install google-cloud-storage")
        return False

    settings = get_cloud_settings()
    if not settings:
        print("Error: Cloud storage settings not found. Please run setup first.")
        return False

    # Check for service account file
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            credentials_path = os.path.abspath(SERVICE_ACCOUNT_FILE)
            print(f"Using service account file: {credentials_path}")
        else:
            print(
                "Warning: No service account file found. Using application default credentials."
            )
            print(
                "If this fails, set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON file."
            )
            credentials_path = None

    try:
        # Initialize storage client
        print(f"\nConnecting to GCS bucket: {settings['GCS_BUCKET_NAME']}")
        gcs = GoogleCloudStorage(settings["GCS_BUCKET_NAME"], credentials_path)

        # Test listing files
        print("\nListing files in bucket...")
        files = gcs.list_files()
        print(f"Success! Found {len(files)} files/folders in bucket.")

        return True
    except Exception as e:
        logger.error(f"Error connecting to Cloud Storage: {e}")
        print(f"\nError connecting to Cloud Storage: {e}")
        return False


def test_upload():
    """
    Test uploading a file to Google Cloud Storage.

    Returns:
        bool: True if successful, False otherwise
    """
    if not gcs_available:
        print("Error: Google Cloud Storage module is not available.")
        print("Please install required packages: pip install google-cloud-storage")
        return False

    settings = get_cloud_settings()
    if not settings:
        print("Error: Cloud storage settings not found. Please run setup first.")
        return False

    # Create test file if it doesn't exist
    if not os.path.exists(TEST_FILE_PATH):
        if not create_test_file():
            return False

    # Check for service account file
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            credentials_path = os.path.abspath(SERVICE_ACCOUNT_FILE)
            print(f"Using service account file: {credentials_path}")
        else:
            print(
                "Warning: No service account file found. Using application default credentials."
            )
            print(
                "If this fails, set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON file."
            )
            credentials_path = None

    try:
        # Initialize storage client
        print(f"\nConnecting to GCS bucket: {settings['GCS_BUCKET_NAME']}")
        gcs = GoogleCloudStorage(settings["GCS_BUCKET_NAME"], credentials_path)

        # Upload test file
        print(f"Uploading test file: {TEST_FILE_PATH}")
        result = gcs.upload_file(
            TEST_FILE_PATH,
            remote_path="test/test_upload.txt",
            make_public=settings["CLOUD_STORAGE_PUBLIC"],
        )

        if result:
            print(f"Success! File uploaded to: {result}")
            return True
        else:
            print("Upload failed.")
            return False
    except Exception as e:
        logger.error(f"Error uploading to Cloud Storage: {e}")
        print(f"\nError uploading to Cloud Storage: {e}")
        return False


def verify_setup():
    """
    Verify the complete setup of the cloud storage.

    Returns:
        bool: True if successful, False otherwise
    """
    print("\n=== Google Cloud Storage Verification ===\n")

    steps = [
        {"name": "Verify cloud storage settings", "func": get_cloud_settings},
        {"name": "Test Cloud Storage connection", "func": test_cloud_storage},
        {"name": "Test file upload capability", "func": test_upload},
    ]

    all_success = True

    for i, step in enumerate(steps, 1):
        print(f"\n{i}. {step['name']}...")
        result = step["func"]()
        success = result is not None
        status = "✓ Success" if success else "✗ Failed"
        print(f"   Status: {status}")

        if not success:
            all_success = False
            print(
                f"\nVerification stopped at step {i}. Please fix the issues and try again."
            )
            break

    if all_success:
        print("\n✓ All verification steps completed successfully!")
        print("You're all set to use the Google Cloud Storage functionality.")

    return all_success


def setup_storage_env(export=False):
    """
    Set up environment variables for cloud storage.

    Args:
        export: Whether to print export statements for shell usage

    Returns:
        bool: True if successful, False otherwise
    """
    settings = get_cloud_settings()
    if not settings:
        print("Error: Cloud storage settings not found. Please run setup first.")
        return False

    # Convert booleans to strings
    for key in ["USE_CLOUD_STORAGE", "CLOUD_STORAGE_PUBLIC", "PREFER_CLOUD_STORAGE"]:
        settings[key] = "true" if settings[key] else "false"

    # Check for service account file
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            credentials_path = os.path.abspath(SERVICE_ACCOUNT_FILE)
        else:
            credentials_path = ""

    # Create environment settings
    env_settings = {
        "GCS_BUCKET_NAME": settings["GCS_BUCKET_NAME"],
        "USE_CLOUD_STORAGE": settings["USE_CLOUD_STORAGE"],
        "CLOUD_STORAGE_PUBLIC": settings["CLOUD_STORAGE_PUBLIC"],
        "PREFER_CLOUD_STORAGE": settings["PREFER_CLOUD_STORAGE"],
        "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
    }

    if export:
        print("\n# Add these to your shell environment (e.g., .bashrc, .zshrc):")
        for key, value in env_settings.items():
            print(f'export {key}="{value}"')
    else:
        # Set environment variables for the current process
        for key, value in env_settings.items():
            os.environ[key] = value

        print("\nEnvironment variables set for the current session:")
        for key, value in env_settings.items():
            print(f"{key}={value}")

    return True


def main():
    """Main function to parse arguments and manage cloud storage."""
    parser = argparse.ArgumentParser(description="Manage Google Cloud Storage settings")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up cloud storage settings")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get cloud storage settings")

    # Delete command
    delete_parser = subparsers.add_parser(
        "delete", help="Delete cloud storage settings"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Test cloud storage connection")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify cloud storage setup")

    # Env command
    env_parser = subparsers.add_parser("env", help="Set up environment variables")
    env_parser.add_argument(
        "--export", action="store_true", help="Print export statements for shell usage"
    )

    args = parser.parse_args()

    if args.command == "setup":
        success = store_cloud_settings()
        sys.exit(0 if success else 1)
    elif args.command == "get":
        settings = get_cloud_settings()
        sys.exit(0 if settings else 1)
    elif args.command == "delete":
        success = delete_cloud_settings()
        sys.exit(0 if success else 1)
    elif args.command == "test":
        success = test_cloud_storage()
        sys.exit(0 if success else 1)
    elif args.command == "verify":
        success = verify_setup()
        sys.exit(0 if success else 1)
    elif args.command == "env":
        success = setup_storage_env(args.export)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
