#!/usr/bin/env python3
"""
Test script to run the firestore migration in dry-run mode.
"""

import os
import sys

# Set the service account credentials and environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ryangravette/Downloads/cloudrunkey.json'
os.environ['GCS_BUCKET_NAME'] = 'legislativevideoreviewswithai.firebasestorage.app'
os.environ['USE_CLOUD_STORAGE'] = 'true'
os.environ['CLOUD_STORAGE_PUBLIC'] = 'false'

# Import the migration module
from src.firestore_migration import migrate_sqlite_to_firestore, validate_migration

def main():
    """Run the migration in dry-run mode"""
    print("Starting Firestore migration in dry-run mode...")
    
    # Run migration in dry-run mode with a small limit
    stats = migrate_sqlite_to_firestore(limit=5, dry_run=True)
    
    print("\nMigration Test Summary:")
    if stats.get('success', False):
        print(f"Total Records Processed: {stats['total']}")
        print(f"Would Have Migrated: {stats['migrated']}")
        print(f"  Videos: {stats['videos']}")
        print(f"  Audio: {stats['audio']}")
        print(f"  Transcripts: {stats['transcripts']}")
        print(f"  Other: {stats['other']}")
        print(f"Errors: {stats['errors']}")
    else:
        print(f"Migration test failed: {stats.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()