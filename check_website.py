#!/usr/bin/env python3
"""Simple script to check if the website is functioning properly."""

import urllib.request
import time

def check_website(url):
    """Check if a website is responding correctly."""
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            print(f"Status: {response.status}")
            print(f"Response size: {len(data)} bytes")
            return True
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return False

if __name__ == "__main__":
    website_url = "https://legislativevideoreviewswithai.web.app"
    
    print(f"Checking website: {website_url}")
    check_website(website_url)
    
    # Check specific pages
    pages = [
        "/videos",
        "/audio",
        "/transcripts"
    ]
    
    for page in pages:
        print(f"\nChecking page: {page}")
        time.sleep(1)  # Small delay to avoid rate limiting
        check_website(f"{website_url}{page}")