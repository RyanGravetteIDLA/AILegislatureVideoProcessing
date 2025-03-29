#!/usr/bin/env python3
"""
Simple test script to check Firestore and Cloud Storage access.
"""

import os
import sys
from google.cloud import firestore
from google.cloud import storage

# Use service account credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ryangravette/Downloads/cloudrunkey.json'

# Set project ID
project_id = 'legislativevideoreviewswithai'

try:
    # Initialize Firestore client
    print(f"Initializing Firestore client for project: {project_id}")
    db = firestore.Client(project=project_id)
    
    # Try a simple write operation
    print("Attempting to write test document to Firestore...")
    doc_ref = db.collection('test').document('test-doc')
    doc_ref.set({
        'testing': True,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'message': 'This is a test document'
    })
    
    print("Success! Document written to Firestore")
    
    # Try to read it back
    print("Attempting to read test document from Firestore...")
    doc = doc_ref.get()
    if doc.exists:
        print(f"Document data: {doc.to_dict()}")
    else:
        print("Document not found")
    
    # Test Cloud Storage access
    print("\nTesting Cloud Storage access...")
    
    # Initialize storage client
    storage_client = storage.Client(project=project_id)
    
    # Try specific bucket names from the migration plan
    bucket_names = [
        "legislativevideoreviewswithai.appspot.com",  # Standard Firebase bucket
        "legislativevideoreviewswithai.firebasestorage.app",  # From migration plan
        "idaho-legislature-media",  # From cloud_storage.py default
    ]
    
    print("Trying to access specific buckets:")
    for bucket_name in bucket_names:
        print(f"\nAttempting to access bucket: {bucket_name}")
        try:
            bucket = storage_client.bucket(bucket_name)
            # Test if we can list objects
            print(f"Testing list operations on bucket: {bucket_name}")
            blobs = list(bucket.list_blobs(max_results=5))
            if blobs:
                print(f"Success! Connected to bucket: {bucket_name}")
                print("Files in bucket:")
                for blob in blobs:
                    print(f"- {blob.name} ({blob.size} bytes)")
            else:
                print(f"Success! Connected to bucket: {bucket_name}")
                print("No files found in the bucket.")
                
            # Try to create a test file
            test_blob = bucket.blob("test_file.txt")
            test_blob.upload_from_string("This is a test file", content_type="text/plain")
            print("Successfully uploaded test file to bucket")
            
            # Delete the test file to clean up
            test_blob.delete()
            print("Successfully deleted test file from bucket")
            
        except Exception as e:
            print(f"Could not access bucket {bucket_name}: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    print(traceback.format_exc())