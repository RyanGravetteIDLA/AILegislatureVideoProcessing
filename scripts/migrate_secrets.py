#!/usr/bin/env python3
"""
Migrate existing secrets to the new centralized secrets manager.

This script helps with migrating from the old individualized
secrets management approaches to the new centralized secrets_manager.py.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migrate_secrets")

# Import the secrets manager
try:
    from src.secrets_manager import SecretsManager

    secrets_available = True
except ImportError:
    logger.error(
        "Failed to import the secrets manager. Make sure it exists at src/secrets_manager.py"
    )
    secrets_available = False


def migrate_api_keys():
    """Migrate API keys from the old system to the new secrets manager."""
    try:
        from scripts.manage_api_keys import (
            get_api_key,
            KEYCHAIN_SERVICE,
            KEYCHAIN_USERNAME,
        )

        logger.info("Migrating Gemini API key...")
        api_key = get_api_key()

        if api_key:
            if SecretsManager.store_secret("gemini_api", "GeminiAPI", api_key):
                logger.info("✓ Successfully migrated Gemini API key")
                return True
            else:
                logger.error("✗ Failed to migrate Gemini API key")
                return False
        else:
            logger.warning("No Gemini API key found to migrate")
            return False
    except ImportError as e:
        logger.error(f"Failed to import the old API key manager: {e}")
        return False


def migrate_github_credentials():
    """Migrate GitHub credentials from the config file to the secrets manager."""
    try:
        github_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".github-config",
        )

        if not os.path.exists(github_config_path):
            logger.warning("No GitHub config file found to migrate")
            return False

        logger.info("Migrating GitHub credentials...")

        # Parse the config file
        config = {}
        with open(github_config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    config[key.strip()] = value.strip().strip('"').strip("'")

        # Map the old keys to new keys
        credential_map = {
            "GITHUB_USERNAME": "username",
            "REPO_NAME": "repo_name",
            "GITHUB_TOKEN": "token",
            "REPO_DESCRIPTION": "description",
            "REPO_VISIBILITY": "visibility",
        }

        # Migrate each credential
        success = True
        for old_key, new_key in credential_map.items():
            if old_key in config:
                logger.info(f"Migrating {old_key} to {new_key}")
                if not SecretsManager.store_secret(
                    "github",
                    new_key,
                    config[old_key],
                    sensitive=old_key == "GITHUB_TOKEN",
                ):
                    success = False
                    logger.error(f"Failed to migrate {old_key}")

        if success:
            logger.info("✓ Successfully migrated GitHub credentials")
            return True
        else:
            logger.error("✗ Failed to migrate some GitHub credentials")
            return False
    except Exception as e:
        logger.error(f"Error migrating GitHub credentials: {e}")
        return False


def migrate_cloud_storage_settings():
    """Migrate cloud storage settings to the secrets manager."""
    try:
        from scripts.manage_cloud_storage import get_setting

        logger.info("Migrating Cloud Storage settings...")

        settings = {
            "GCS_BUCKET_NAME": get_setting("GCS_BUCKET_NAME"),
            "USE_CLOUD_STORAGE": get_setting("USE_CLOUD_STORAGE"),
            "CLOUD_STORAGE_PUBLIC": get_setting("CLOUD_STORAGE_PUBLIC"),
            "PREFER_CLOUD_STORAGE": get_setting("PREFER_CLOUD_STORAGE"),
        }

        # Filter out None values
        settings = {k: v for k, v in settings.items() if v is not None}

        if not settings:
            logger.warning("No Cloud Storage settings found to migrate")
            return False

        # Migrate each setting
        success = True
        for key, value in settings.items():
            logger.info(f"Migrating {key}")
            if not SecretsManager.store_secret(
                "cloud_storage", key, value, sensitive=False
            ):
                success = False
                logger.error(f"Failed to migrate {key}")

        if success:
            logger.info("✓ Successfully migrated Cloud Storage settings")
            return True
        else:
            logger.error("✗ Failed to migrate some Cloud Storage settings")
            return False
    except Exception as e:
        logger.error(f"Error migrating Cloud Storage settings: {e}")
        return False


def migrate_service_accounts():
    """Migrate service account files to the secrets manager."""
    logger.info("Migrating service account files...")

    service_accounts = {
        "drive": os.path.join("data", "service_account.json"),
        "gcs": os.path.join("data", "gcs_service_account.json"),
    }

    # Get the project root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    success = True
    for service_type, relative_path in service_accounts.items():
        file_path = os.path.join(root_dir, relative_path)

        if os.path.exists(file_path):
            logger.info(f"Migrating {service_type} service account from {file_path}")

            try:
                # Store the file path
                path_success = SecretsManager.store_secret(
                    "service_accounts",
                    f"{service_type}_path",
                    os.path.abspath(file_path),
                    sensitive=False,
                )

                # Store the content
                with open(file_path, "r") as f:
                    content = json.load(f)

                content_success = SecretsManager.store_service_account_content(
                    service_type, content
                )

                if path_success and content_success:
                    logger.info(
                        f"✓ Successfully migrated {service_type} service account"
                    )
                else:
                    logger.error(f"✗ Failed to migrate {service_type} service account")
                    success = False
            except Exception as e:
                logger.error(f"Error migrating {service_type} service account: {e}")
                success = False
        else:
            logger.warning(
                f"No {service_type} service account file found at {file_path}"
            )

    return success


def main():
    """Main function to run the migration."""
    if not secrets_available:
        logger.error("Cannot proceed with migration due to missing secrets manager.")
        return 1

    logger.info("=== Starting secrets migration ===")

    # Track overall success
    success = True

    # Migrate each type of secret
    api_keys_success = migrate_api_keys()
    github_success = migrate_github_credentials()
    cloud_storage_success = migrate_cloud_storage_settings()
    service_accounts_success = migrate_service_accounts()

    # Check overall success
    success = (
        api_keys_success
        and github_success
        and cloud_storage_success
        and service_accounts_success
    )

    if success:
        logger.info("=== Migration completed successfully ===")
        logger.info(
            "All secrets have been migrated to the new centralized secrets manager."
        )
    else:
        logger.warning("=== Migration completed with some issues ===")
        logger.warning("Some secrets may not have been migrated properly.")
        logger.warning("Please review the logs and fix any issues manually.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
