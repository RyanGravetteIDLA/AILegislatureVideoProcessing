#!/usr/bin/env python3
"""
Script to update CORS settings in the API files.
This allows direct access to the API from both Firebase hosting and directly from the browser.

Note: The simple_firestore_api.py file has been removed from the project.
This script is now updated to modify api_firestore.py instead.
"""

import os
import re
import sys

def update_cors_settings():
    """Update the CORS settings in the api_firestore.py file."""
    file_path = os.path.join('src', 'api_firestore.py')
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define the CORS middleware block to replace
    cors_pattern = r'# Add CORS middleware.*?allow_origins=\[.*?\].*?allow_headers=\[".*?"\],\s*?\)'
    
    # New CORS configuration
    new_cors = """# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'https://legislativevideoreviewswithai.web.app', 
        'https://legislativevideoreviewswithai.firebaseapp.com', 
        'http://localhost:5173', 
        'http://localhost:4173',
        # Allow direct access to the API from browser
        'https://media-portal-backend-335217295357.us-west1.run.app'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
    
    # Find and replace the CORS middleware block
    updated_content = re.sub(cors_pattern, new_cors, content, flags=re.DOTALL)
    
    if updated_content == content:
        print("Warning: CORS settings block not found or already up to date.")
        return False
    
    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.write(updated_content)
    
    print(f"Successfully updated CORS settings in {file_path}")
    return True

if __name__ == "__main__":
    print("Updating CORS settings to allow direct access from the browser...")
    
    if update_cors_settings():
        print("\nCORS settings updated successfully.")
        print("To apply these changes:")
        print("1. Make sure you have Docker installed")
        print("2. Run: ./deploy_cloud_run.sh")
        print("3. This will redeploy the backend with the updated CORS settings.")
    else:
        print("\nFailed to update CORS settings.")
        sys.exit(1)