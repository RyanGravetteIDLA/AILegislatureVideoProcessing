#!/usr/bin/env python3
"""Simple script to check if the API is functioning properly."""

import urllib.request
import json
import sys

def check_endpoint(url):
    """Check if an API endpoint is responding correctly."""
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            print(f"Status: {response.status}")
            print(f"Response: {data[:200]}...")
            return True
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return False

if __name__ == "__main__":
    # Check both URLs - the one in our env file and the one from gcloud
    urls = [
        "https://media-portal-backend-335217295357.us-west1.run.app",
        "https://media-portal-backend-6alz6huq6a-uw.a.run.app"
    ]
    
    for url in urls:
        print(f"\nChecking API at: {url}")
        
        # Check health endpoint
        print("Checking API health...")
        check_endpoint(f"{url}/api/health")
        
        # Check videos endpoint
        print("\nChecking videos endpoint...")
        check_endpoint(f"{url}/api/videos")