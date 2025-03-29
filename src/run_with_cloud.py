#!/usr/bin/env python3
"""
Helper script to run the server with the correct Cloud Run environment variables.
"""

import os
import sys
import logging
import argparse
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("run_with_cloud")


def get_cloud_environment():
    """Return a dictionary with the environment variables for Cloud Run."""
    env = os.environ.copy()

    # Set Cloud Run specific variables
    env.update(
        {
            "GOOGLE_CLOUD_PROJECT": "legislativevideoreviewswithai",
            "GCS_BUCKET_NAME": "legislativevideoreviewswithai.firebasestorage.app",
            "USE_CLOUD_STORAGE": "true",
            "PREFER_CLOUD_STORAGE": "true",
        }
    )

    # Check for service account credentials
    if "GOOGLE_APPLICATION_CREDENTIALS" not in env:
        # Look for a default path
        default_paths = [
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "credentials",
                "legislativevideoreviewswithai-*.json",
            ),
            os.path.join(os.path.expanduser("~"), "Downloads", "cloudrunkey.json"),
        ]

        for path_pattern in default_paths:
            import glob

            matches = glob.glob(path_pattern)
            if matches:
                env["GOOGLE_APPLICATION_CREDENTIALS"] = matches[0]
                logger.info(f"Using service account credentials: {matches[0]}")
                break

        if "GOOGLE_APPLICATION_CREDENTIALS" not in env:
            logger.warning(
                "No GOOGLE_APPLICATION_CREDENTIALS found. Firebase/Cloud Storage operations may fail."
            )

    return env


def main():
    """Main entry point for running the server with cloud environment."""
    parser = argparse.ArgumentParser(
        description="Run the server with cloud environment"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8080,
        help="Port for the API server (default: 8080)",
    )
    parser.add_argument(
        "--file-port",
        type=int,
        default=8080,
        help="Port for the file server (default: 8080)",
    )
    parser.add_argument(
        "--api-only", action="store_true", help="Run only the API server"
    )
    parser.add_argument(
        "--file-only", action="store_true", help="Run only the file server"
    )

    args = parser.parse_args()

    # Get the environment with Cloud Run variables
    env = get_cloud_environment()

    # Build the server command
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "server.py")]

    # Add command line arguments
    if args.api_only:
        cmd.append("--api-only")
    elif args.file_only:
        cmd.append("--file-only")

    cmd.extend(["--api-port", str(args.api_port), "--file-port", str(args.file_port)])

    logger.info(f"Running command: {' '.join(cmd)}")

    # Run the server with the cloud environment
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Server exited with error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
