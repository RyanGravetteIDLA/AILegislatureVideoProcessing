#!/usr/bin/env python3
"""
Get information about the Firestore configuration.
"""

import os
import sys
import json
from google.cloud import firestore
from google.oauth2 import service_account

# Use service account credentials
creds_path = '/Users/ryangravette/Downloads/cloudrunkey.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path

# Print credential info
print(f"Using service account credentials from: {creds_path}")
try:
    with open(creds_path, 'r') as f:
        creds_data = json.load(f)
        print(f"Service account email: {creds_data.get('client_email')}")
        print(f"Project ID: {creds_data.get('project_id')}")
except Exception as e:
    print(f"Error reading credentials file: {e}")

# Get project ID
project_id = 'legislativevideoreviewswithai'
print(f"\nTarget project ID: {project_id}")

try:
    # Initialize service account credentials explicitly
    credentials = service_account.Credentials.from_service_account_file(creds_path)
    print(f"Credentials loaded successfully: {credentials.service_account_email}")
    
    # Initialize Firestore client with explicit credentials
    print(f"Initializing Firestore client...")
    db = firestore.Client(project=project_id, credentials=credentials)
    
    # Try a read operation to the 'test' collection
    print("Attempting to list collections in Firestore...")
    collections = db.collections()
    collection_names = [collection.id for collection in collections]
    print(f"Collections: {collection_names}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    print(traceback.format_exc())