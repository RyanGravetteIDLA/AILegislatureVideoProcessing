#!/usr/bin/env python3
"""
Centralized secrets management for Idaho Legislature Media Portal

This module provides a unified interface for storing and retrieving
sensitive information such as API keys, credentials, and configuration.
It uses the system keychain as the primary storage method with fallbacks
to environment variables and interactive prompts.

The module is designed to be a central point for all secrets management
across the application, providing consistent access patterns and security.
"""

import os
import sys
import logging
import getpass
import keyring
import json
from pathlib import Path

# Configure logging
logs_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs"
)
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "secrets_manager.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("secrets_manager")

# Base directory for the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Constants for keychain services
KEYCHAIN_SERVICES = {
    "gemini_api": "IdahoLegislatureDownloader",
    "cloud_storage": "IdahoLegislatureCloudStorage",
    "github": "IdahoLegislatureGitHub",
    "service_accounts": "IdahoLegislatureServiceAccounts",
}

# Environment variable prefixes
ENV_PREFIX = "IDAHO_LEG_"

# Service account paths
SERVICE_ACCOUNT_PATHS = {
    "drive": os.path.join(BASE_DIR, "data", "service_account.json"),
    "gcs": os.path.join(BASE_DIR, "data", "gcs_service_account.json"),
}


class SecretsManager:
    """
    Centralized manager for all application secrets and credentials.

    This class provides methods to securely store and retrieve sensitive
    information using the system keychain as the primary storage mechanism.
    """

    @staticmethod
    def store_secret(secret_type, username, value, sensitive=True):
        """
        Store a secret in the system keychain.

        Args:
            secret_type: Category of secret (e.g., 'gemini_api', 'cloud_storage')
            username: Identifier for the secret within the category
            value: The secret value to store
            sensitive: Whether the value is sensitive (affects logging)

        Returns:
            bool: True if successful, False otherwise
        """
        service = KEYCHAIN_SERVICES.get(secret_type)
        if not service:
            logger.error(f"Unknown secret type: {secret_type}")
            return False

        try:
            keyring.set_password(service, username, value)
            if sensitive:
                logger.info(f"Stored secret {username} in {secret_type} keychain")
            else:
                logger.info(f"Stored {username}={value} in {secret_type} keychain")
            return True
        except Exception as e:
            logger.error(
                f"Error storing secret {username} in {secret_type} keychain: {e}"
            )
            return False

    @staticmethod
    def get_secret(secret_type, username, prompt=None, env_var=None, allow_empty=False):
        """
        Get a secret with fallbacks to environment variables and interactive prompts.

        Args:
            secret_type: Category of secret (e.g., 'gemini_api', 'cloud_storage')
            username: Identifier for the secret within the category
            prompt: Optional prompt text for interactive input
            env_var: Optional environment variable name to check
            allow_empty: Whether an empty secret is acceptable

        Returns:
            str: The secret value or None if not found and no prompt provided
        """
        service = KEYCHAIN_SERVICES.get(secret_type)
        if not service:
            logger.error(f"Unknown secret type: {secret_type}")
            return None

        # Try keychain first
        try:
            value = keyring.get_password(service, username)
            if value:
                logger.debug(f"Retrieved secret {username} from {secret_type} keychain")
                return value
        except Exception as e:
            logger.warning(
                f"Error retrieving secret {username} from {secret_type} keychain: {e}"
            )

        # Try environment variable if provided
        if env_var:
            full_env_var = f"{ENV_PREFIX}{env_var}"
            value = os.environ.get(full_env_var)
            if value:
                logger.debug(
                    f"Retrieved secret {username} from environment variable {full_env_var}"
                )
                return value

        # If automatic options failed and prompt is provided, ask interactively
        if prompt:
            logger.info(
                f"Secret {username} not found in keychain or environment, prompting user"
            )
            if (
                "password" in username.lower()
                or "key" in username.lower()
                or "token" in username.lower()
            ):
                # Hide input for sensitive fields
                value = getpass.getpass(prompt)
            else:
                value = input(prompt)

            if value or allow_empty:
                # Store the provided value for future use
                SecretsManager.store_secret(secret_type, username, value)
                return value

        logger.warning(
            f"Secret {username} not found and no interactive prompt provided"
        )
        return None

    @staticmethod
    def delete_secret(secret_type, username):
        """
        Delete a secret from the system keychain.

        Args:
            secret_type: Category of secret (e.g., 'gemini_api', 'cloud_storage')
            username: Identifier for the secret within the category

        Returns:
            bool: True if successful, False otherwise
        """
        service = KEYCHAIN_SERVICES.get(secret_type)
        if not service:
            logger.error(f"Unknown secret type: {secret_type}")
            return False

        try:
            keyring.delete_password(service, username)
            logger.info(f"Deleted secret {username} from {secret_type} keychain")
            return True
        except keyring.errors.PasswordDeleteError:
            logger.warning(f"Secret {username} not found in {secret_type} keychain")
            return False
        except Exception as e:
            logger.error(
                f"Error deleting secret {username} from {secret_type} keychain: {e}"
            )
            return False

    @staticmethod
    def get_gemini_api_key():
        """
        Get the Google Gemini API key.

        Returns:
            str: API key or None if not found
        """
        return SecretsManager.get_secret(
            "gemini_api",
            "GeminiAPI",
            prompt="Enter your Google Gemini API key: ",
            env_var="GEMINI_API_KEY",
        )

    @staticmethod
    def get_github_credentials():
        """
        Get GitHub credentials.

        Returns:
            dict: GitHub credentials (username, repo_name, token)
        """
        # Get username
        username = SecretsManager.get_secret(
            "github",
            "username",
            prompt="Enter your GitHub username: ",
            env_var="GITHUB_USERNAME",
        )

        # Get repository name
        repo_name = SecretsManager.get_secret(
            "github",
            "repo_name",
            prompt="Enter your GitHub repository name: ",
            env_var="GITHUB_REPO_NAME",
        )

        # Get token (most sensitive)
        token = SecretsManager.get_secret(
            "github",
            "token",
            prompt="Enter your GitHub personal access token: ",
            env_var="GITHUB_TOKEN",
        )

        # Get optional description
        description = (
            SecretsManager.get_secret(
                "github",
                "description",
                prompt="Enter a description for your repository (optional): ",
                env_var="GITHUB_REPO_DESCRIPTION",
                allow_empty=True,
            )
            or ""
        )

        # Get visibility preference
        visibility = (
            SecretsManager.get_secret(
                "github",
                "visibility",
                prompt="Repository visibility (public/private) [default: public]: ",
                env_var="GITHUB_REPO_VISIBILITY",
                allow_empty=True,
            )
            or "public"
        )

        return {
            "username": username,
            "repo_name": repo_name,
            "token": token,
            "description": description,
            "visibility": visibility.lower(),
        }

    @staticmethod
    def get_cloud_storage_settings():
        """
        Get GCS bucket settings.

        Returns:
            dict: GCS settings
        """
        # Get bucket name
        bucket_name = SecretsManager.get_secret(
            "cloud_storage",
            "GCS_BUCKET_NAME",
            prompt="Enter your Google Cloud Storage bucket name: ",
            env_var="GCS_BUCKET_NAME",
        )

        # Get boolean settings with defaults
        settings = {"bucket_name": bucket_name}

        # Boolean settings
        for key, prompt_text, env_var, default in [
            (
                "use_cloud_storage",
                "Enable cloud storage? (true/false): ",
                "USE_CLOUD_STORAGE",
                "false",
            ),
            (
                "cloud_storage_public",
                "Make files publicly accessible? (true/false): ",
                "CLOUD_STORAGE_PUBLIC",
                "false",
            ),
            (
                "prefer_cloud_storage",
                "Prefer cloud over local storage? (true/false): ",
                "PREFER_CLOUD_STORAGE",
                "false",
            ),
        ]:
            value = (
                SecretsManager.get_secret(
                    "cloud_storage",
                    env_var,
                    prompt=f"{prompt_text} [default: {default}]: ",
                    env_var=env_var,
                    allow_empty=True,
                )
                or default
            )

            # Convert string to boolean
            settings[key] = value.lower() in ("true", "yes", "1")

        return settings

    @staticmethod
    def get_service_account_path(service_type):
        """
        Get the path to a service account file.

        Args:
            service_type: Type of service ('drive' or 'gcs')

        Returns:
            str: Path to the service account file
        """
        default_path = SERVICE_ACCOUNT_PATHS.get(service_type)
        if not default_path:
            logger.error(f"Unknown service type: {service_type}")
            return None

        # Check if we have a custom path stored
        custom_path = SecretsManager.get_secret(
            "service_accounts",
            f"{service_type}_path",
            env_var=f"{service_type.upper()}_SERVICE_ACCOUNT_PATH",
            allow_empty=True,
        )

        # Use the custom path if available, otherwise use default
        path = custom_path or default_path

        # Verify that the file exists
        if not os.path.exists(path):
            logger.warning(f"Service account file not found: {path}")

            # If user is in interactive mode, prompt for the file
            if sys.stdin.isatty():
                prompt = f"Enter path to {service_type} service account JSON file: "
                custom_path = input(prompt)

                if custom_path and os.path.exists(custom_path):
                    # Store the custom path for future use
                    SecretsManager.store_secret(
                        "service_accounts",
                        f"{service_type}_path",
                        custom_path,
                        sensitive=False,
                    )
                    return custom_path

        return path

    @staticmethod
    def store_service_account_content(service_type, json_content):
        """
        Store service account JSON content directly in the keychain.

        Args:
            service_type: Type of service ('drive' or 'gcs')
            json_content: JSON content of the service account file

        Returns:
            bool: True if successful, False otherwise
        """
        if isinstance(json_content, dict):
            json_content = json.dumps(json_content)

        return SecretsManager.store_secret(
            "service_accounts", f"{service_type}_content", json_content
        )

    @staticmethod
    def get_service_account_content(service_type):
        """
        Get service account JSON content from the keychain.

        Args:
            service_type: Type of service ('drive' or 'gcs')

        Returns:
            dict: Service account JSON content or None if not found
        """
        json_content = SecretsManager.get_secret(
            "service_accounts",
            f"{service_type}_content",
            env_var=f"{service_type.upper()}_SERVICE_ACCOUNT_CONTENT",
        )

        if not json_content:
            # If not in keychain, try to read from file
            path = SecretsManager.get_service_account_path(service_type)
            if path and os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        json_content = f.read()

                    # Store the content for future use
                    SecretsManager.store_service_account_content(
                        service_type, json_content
                    )
                except Exception as e:
                    logger.error(f"Error reading service account file {path}: {e}")
                    return None
            else:
                return None

        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON content for {service_type} service account")
            return None


# Convenience functions for direct imports
def get_gemini_api_key():
    """Get the Google Gemini API key."""
    return SecretsManager.get_gemini_api_key()


def get_github_credentials():
    """Get GitHub credentials."""
    return SecretsManager.get_github_credentials()


def get_cloud_storage_settings():
    """Get Google Cloud Storage settings."""
    return SecretsManager.get_cloud_storage_settings()


def get_service_account_path(service_type):
    """Get the path to a service account file."""
    return SecretsManager.get_service_account_path(service_type)


def get_service_account_content(service_type):
    """Get service account JSON content."""
    return SecretsManager.get_service_account_content(service_type)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage application secrets")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test secrets retrieval")
    test_parser.add_argument(
        "--api-keys", action="store_true", help="Test API key retrieval"
    )
    test_parser.add_argument(
        "--github", action="store_true", help="Test GitHub credentials retrieval"
    )
    test_parser.add_argument(
        "--cloud", action="store_true", help="Test cloud storage settings retrieval"
    )
    test_parser.add_argument(
        "--service-accounts", action="store_true", help="Test service account retrieval"
    )

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate", help="Migrate existing secrets to the new format"
    )

    args = parser.parse_args()

    if args.command == "test":
        if args.api_keys or not (args.github or args.cloud or args.service_accounts):
            print("\n=== Testing Gemini API Key ===")
            api_key = get_gemini_api_key()
            if api_key:
                masked_key = f"{api_key[:4]}...{api_key[-4:]}"
                print(f"API key found: {masked_key}")
            else:
                print("API key not found")

        if args.github:
            print("\n=== Testing GitHub Credentials ===")
            github_creds = get_github_credentials()
            if github_creds:
                print(f"Username: {github_creds['username']}")
                print(f"Repository: {github_creds['repo_name']}")
                print(
                    f"Token: {github_creds['token'][:4]}...{github_creds['token'][-4:]}"
                )
                print(f"Description: {github_creds['description']}")
                print(f"Visibility: {github_creds['visibility']}")
            else:
                print("GitHub credentials not found")

        if args.cloud:
            print("\n=== Testing Cloud Storage Settings ===")
            cloud_settings = get_cloud_storage_settings()
            if cloud_settings:
                print(f"Bucket name: {cloud_settings['bucket_name']}")
                print(f"Use cloud storage: {cloud_settings['use_cloud_storage']}")
                print(f"Cloud storage public: {cloud_settings['cloud_storage_public']}")
                print(f"Prefer cloud storage: {cloud_settings['prefer_cloud_storage']}")
            else:
                print("Cloud storage settings not found")

        if args.service_accounts:
            print("\n=== Testing Service Account Access ===")
            for service_type in ["drive", "gcs"]:
                print(f"\n{service_type.upper()} Service Account:")
                path = get_service_account_path(service_type)
                print(f"Path: {path}")

                content = get_service_account_content(service_type)
                if content:
                    print(f"Client email: {content.get('client_email')}")
                    print(f"Project ID: {content.get('project_id')}")
                else:
                    print("Service account content not found")

    elif args.command == "migrate":
        print("\n=== Migrating Existing Secrets ===")

        # Migrate Gemini API key
        try:
            from scripts.manage_api_keys import (
                get_api_key,
                KEYCHAIN_SERVICE,
                KEYCHAIN_USERNAME,
            )

            print("\nMigrating Gemini API key...")
            api_key = get_api_key()
            if api_key:
                if SecretsManager.store_secret("gemini_api", "GeminiAPI", api_key):
                    print("✓ Successfully migrated Gemini API key")
                else:
                    print("✗ Failed to migrate Gemini API key")
            else:
                print("No Gemini API key found to migrate")
        except ImportError:
            print("Skipping Gemini API key migration (module not found)")

        # Migrate GitHub credentials
        try:
            from scripts.manage_github import load_config

            print("\nMigrating GitHub credentials...")
            config = load_config()
            if config:
                github_creds = {
                    "username": config.get("GITHUB_USERNAME"),
                    "repo_name": config.get("REPO_NAME"),
                    "token": config.get("GITHUB_TOKEN"),
                    "description": config.get("REPO_DESCRIPTION", ""),
                    "visibility": config.get("REPO_VISIBILITY", "public"),
                }

                success = True
                for key, value in github_creds.items():
                    if value:
                        if not SecretsManager.store_secret("github", key, value):
                            success = False

                if success:
                    print("✓ Successfully migrated GitHub credentials")
                else:
                    print("✗ Failed to migrate some GitHub credentials")
            else:
                print("No GitHub credentials found to migrate")
        except ImportError:
            print("Skipping GitHub credentials migration (module not found)")

        # Migrate Cloud Storage settings
        try:
            from scripts.manage_cloud_storage import get_setting

            print("\nMigrating Cloud Storage settings...")

            settings = {
                "GCS_BUCKET_NAME": get_setting("GCS_BUCKET_NAME"),
                "USE_CLOUD_STORAGE": get_setting("USE_CLOUD_STORAGE"),
                "CLOUD_STORAGE_PUBLIC": get_setting("CLOUD_STORAGE_PUBLIC"),
                "PREFER_CLOUD_STORAGE": get_setting("PREFER_CLOUD_STORAGE"),
            }

            success = True
            for key, value in settings.items():
                if value:
                    if not SecretsManager.store_secret("cloud_storage", key, value):
                        success = False

            if success:
                print("✓ Successfully migrated Cloud Storage settings")
            else:
                print("✗ Failed to migrate some Cloud Storage settings")
        except ImportError:
            print("Skipping Cloud Storage settings migration (module not found)")

        # Migrate service account files
        print("\nMigrating service account files...")
        for service_type, path in SERVICE_ACCOUNT_PATHS.items():
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        content = json.load(f)

                    if SecretsManager.store_service_account_content(
                        service_type, content
                    ):
                        print(f"✓ Successfully migrated {service_type} service account")
                    else:
                        print(f"✗ Failed to migrate {service_type} service account")
                except Exception as e:
                    print(f"✗ Error migrating {service_type} service account: {e}")
            else:
                print(f"No {service_type} service account file found at {path}")

    else:
        parser.print_help()
