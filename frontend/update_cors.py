#!/usr/bin/env python3
"""
This script updates the CORS configuration in the backend API files to 
specifically allow the Firebase Hosting domains instead of all origins.
"""

import os
import re
import sys

# Firebase Hosting domains for the project
FIREBASE_DOMAINS = [
    "https://legislativevideoreviewswithai.web.app",
    "https://legislativevideoreviewswithai.firebaseapp.com",
    "http://localhost:5173",  # Vite dev server
    "http://localhost:4173",  # Vite preview
]

# Files to update
FILES_TO_UPDATE = [
    "../src/api.py",
    "../src/api_firestore.py", 
    "../src/file_server.py"
]

def update_cors_config(file_path):
    """Update the CORS configuration in the given file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the allow_origins list
    pattern = r'allow_origins=\["\*"\]'
    replacement = f'allow_origins={FIREBASE_DOMAINS}'
    
    if not re.search(pattern, content):
        print(f"CORS configuration not found in {file_path}")
        return False
    
    new_content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated CORS configuration in {file_path}")
    return True

def main():
    """Main function to update CORS configuration in all backend files."""
    print("Updating CORS configuration to allow Firebase Hosting domains...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    success_count = 0
    
    for rel_path in FILES_TO_UPDATE:
        file_path = os.path.normpath(os.path.join(script_dir, rel_path))
        if update_cors_config(file_path):
            success_count += 1
    
    print(f"Updated {success_count} of {len(FILES_TO_UPDATE)} files.")
    
    if success_count == len(FILES_TO_UPDATE):
        print("\nSuccess! Backend is now configured to accept requests from Firebase Hosting domains.")
        print("Remember to deploy these changes to the Cloud Run backend before deploying the frontend.")
    else:
        print("\nWarning: Not all files were updated. Check the messages above for details.")
    
    return 0 if success_count == len(FILES_TO_UPDATE) else 1

if __name__ == "__main__":
    sys.exit(main())