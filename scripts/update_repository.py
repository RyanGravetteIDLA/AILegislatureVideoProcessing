#!/usr/bin/env python3
"""
Update the GitHub repository with the latest changes.

This script helps with updating the repository, committing changes,
and pushing them to GitHub using the new centralized secrets manager.
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the secrets manager
try:
    from src.secrets_manager import get_github_credentials

    secrets_available = True
except ImportError:
    secrets_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("update_repository")


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


def configure_git():
    """Configure Git with the GitHub credentials."""
    if not secrets_available:
        logger.error("Failed to import the secrets manager.")
        return False

    # Get GitHub credentials
    credentials = get_github_credentials()
    if not credentials:
        logger.error("Failed to retrieve GitHub credentials from secrets manager.")
        return False

    # Set the remote URL with token authentication
    remote_url = f"https://{credentials['token']}@github.com/{credentials['username']}/{credentials['repo_name']}.git"
    command = (
        f"git remote set-url origin {remote_url} || git remote add origin {remote_url}"
    )
    output = run_command(command, silent=True)

    if output is None:
        return False

    logger.info(
        f"Git remote configured to: github.com/{credentials['username']}/{credentials['repo_name']}"
    )
    return True


def commit_changes(message=None):
    """Commit all changes to the repository."""
    # Check if there are any changes to commit
    status = run_command("git status --porcelain", silent=True)
    if not status:
        logger.info("No changes to commit.")
        return True

    # Add all changes
    run_command("git add .")

    # Use provided message or a default
    if not message:
        message = "Update repository with centralized secrets management"

    # Create commit
    commit_command = f"""git commit -m "{message}" -m "- Added centralized secrets management
- Updated existing modules to use the new system
- Added support for Google Cloud Storage
- Updated documentation" -m "🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
"""
    output = run_command(commit_command)

    if output is None:
        return False

    logger.info("Changes committed successfully.")
    return True


def push_to_github(branch="main", force=False):
    """Push changes to GitHub."""
    # Configure Git first
    if not configure_git():
        return False

    # Push to GitHub
    force_flag = "--force" if force else ""
    command = f"git push -u origin {branch} {force_flag}"

    logger.info(f"Pushing to GitHub repository...")
    output = run_command(command)

    if output is None:
        return False

    logger.info(f"Successfully pushed to GitHub.")
    return True


def main():
    """Main function to parse arguments and update the repository."""
    parser = argparse.ArgumentParser(
        description="Update the GitHub repository with the latest changes"
    )
    parser.add_argument("--message", "-m", help="Commit message")
    parser.add_argument("--branch", default="main", help="Branch to push")
    parser.add_argument("--force", action="store_true", help="Force push")
    parser.add_argument("--push", action="store_true", help="Push changes to GitHub")

    args = parser.parse_args()

    # Commit changes
    if not commit_changes(args.message):
        logger.error("Failed to commit changes.")
        return 1

    # Push to GitHub if requested
    if args.push:
        if not push_to_github(args.branch, args.force):
            logger.error("Failed to push to GitHub.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
