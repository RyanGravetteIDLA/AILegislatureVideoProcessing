#!/usr/bin/env python3
"""
Script to run the server with Firestore configuration.
"""

import os
import sys
import subprocess

# Set all environment variables needed by the server
env_vars = {
    'GOOGLE_APPLICATION_CREDENTIALS': '/Users/ryangravette/Downloads/cloudrunkey.json',
    'GCS_BUCKET_NAME': 'legislativevideoreviewswithai.firebasestorage.app',
    'USE_CLOUD_STORAGE': 'true',
    'CLOUD_STORAGE_PUBLIC': 'false',
    'PREFER_CLOUD_STORAGE': 'true',
    # Also set with the IDAHO_LEG_ prefix used by the secrets_manager
    'IDAHO_LEG_GCS_BUCKET_NAME': 'legislativevideoreviewswithai.firebasestorage.app',
    'IDAHO_LEG_USE_CLOUD_STORAGE': 'true',
    'IDAHO_LEG_CLOUD_STORAGE_PUBLIC': 'false',
    'IDAHO_LEG_PREFER_CLOUD_STORAGE': 'true',
}

# Print the environment variables being set
print("Setting environment variables:")
for key, value in env_vars.items():
    print(f"  {key}={value}")
    os.environ[key] = value

# Run the server
print("\nStarting server...")
server_args = sys.argv[1:] if len(sys.argv) > 1 else []
cmd = ["python", "-m", "src.server"] + server_args
subprocess.run(cmd)