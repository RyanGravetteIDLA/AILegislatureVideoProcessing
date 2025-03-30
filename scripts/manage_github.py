#!/usr/bin/env python3
"""
GitHub repository management script.
Handles creating, updating, and publishing to GitHub repositories.
"""

import os
import sys
import argparse
import subprocess
import json
import logging
from pathlib import Path

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the centralized secrets manager
from src.secrets_manager import get_github_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("manage_github")

# Constants
CONFIG_FILE = ".github-config"
SAMPLE_CONFIG_FILE = ".github-config.sample"


def load_config():
    """Load GitHub configuration from the secrets manager."""
    try:
        # Get credentials from the centralized secrets manager
        config = get_github_credentials()

        if not config:
            logger.error("Failed to retrieve GitHub credentials from secrets manager.")
            return None

        # Convert to uppercase keys for backward compatibility
        return {
            "GITHUB_USERNAME": config["username"],
            "REPO_NAME": config["repo_name"],
            "GITHUB_TOKEN": config["token"],
            "REPO_DESCRIPTION": config["description"],
            "REPO_VISIBILITY": config["visibility"],
        }

    except Exception as e:
        logger.error(f"Error loading GitHub configuration: {e}")

        # Try legacy file-based config as fallback
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), CONFIG_FILE
        )

        if not os.path.exists(config_path):
            logger.error(f"Configuration file {CONFIG_FILE} not found.")
            logger.error(
                f"Please run 'python src/secrets_manager.py test --github' to set up GitHub credentials."
            )
            return None

        config = {}
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    config[key.strip()] = value.strip().strip('"').strip("'")

        required_keys = ["GITHUB_USERNAME", "REPO_NAME", "GITHUB_TOKEN"]
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            logger.error(f"Missing required configuration: {', '.join(missing_keys)}")
            return None

        return config


def run_command(command, silent=False):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        if not silent:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(e.stderr)
        return None


def check_repo_exists(config):
    """Check if the repository exists on GitHub."""
    username = config["GITHUB_USERNAME"]
    repo_name = config["REPO_NAME"]
    token = config["GITHUB_TOKEN"]

    command = f"gh auth login --with-token <<< {token}"
    run_command(command, silent=True)

    command = f"gh repo view {username}/{repo_name} --json name 2>/dev/null"
    output = run_command(command, silent=True)

    return output is not None and "name" in output


def create_repository(config):
    """Create a new GitHub repository."""
    username = config["GITHUB_USERNAME"]
    repo_name = config["REPO_NAME"]
    token = config["GITHUB_TOKEN"]
    description = config.get("REPO_DESCRIPTION", "")
    visibility = config.get("REPO_VISIBILITY", "public")

    # Authenticate with GitHub
    command = f"GITHUB_TOKEN={token} gh auth login --with-token <<< {token}"
    run_command(command, silent=True)

    # Check if repository exists
    if check_repo_exists(config):
        logger.info(f"Repository {username}/{repo_name} already exists.")
        return True

    # Create the repository
    visibility_flag = "--public" if visibility.lower() == "public" else "--private"
    command = (
        f"GITHUB_TOKEN={token} gh repo create {username}/{repo_name} {visibility_flag} "
    )
    if description:
        command += f'--description "{description}" '

    logger.info(f"Creating repository {username}/{repo_name}...")
    output = run_command(command)

    if output and "Created repository" in output:
        logger.info("Repository created successfully.")
        return True
    else:
        logger.error("Failed to create repository.")
        return False


def configure_git(config):
    """Configure Git with the remote repository."""
    username = config["GITHUB_USERNAME"]
    repo_name = config["REPO_NAME"]
    token = config["GITHUB_TOKEN"]

    # Set the remote URL with token authentication
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    command = (
        f"git remote set-url origin {remote_url} || git remote add origin {remote_url}"
    )
    run_command(command, silent=True)

    logger.info(f"Git remote configured to: github.com/{username}/{repo_name}")
    return True


def push_to_github(config, branch="main", force=False):
    """Push code to GitHub."""
    # Make sure the repository is configured
    configure_git(config)

    # Push to GitHub
    force_flag = "--force" if force else ""
    command = f"git push -u origin {branch} {force_flag}"

    logger.info(f"Pushing to GitHub repository...")
    output = run_command(command)

    # Consider the push successful if there was no error from the command
    if output is not None:
        logger.info(f"Successfully pushed to GitHub.")
        return True
    else:
        logger.error("Failed to push to GitHub.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Manage GitHub repository")

    # Command groups
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup GitHub repository")
    setup_parser.add_argument(
        "--create",
        action="store_true",
        help="Create the repository if it doesn't exist",
    )

    # Push command
    push_parser = subparsers.add_parser("push", help="Push to GitHub")
    push_parser.add_argument("--branch", default="main", help="Branch to push")
    push_parser.add_argument("--force", action="store_true", help="Force push")

    # Parse arguments
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    if not config:
        return 1

    if args.command == "setup":
        if args.create:
            create_repository(config)
        configure_git(config)

    elif args.command == "push":
        if not push_to_github(config, args.branch, args.force):
            return 1

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
