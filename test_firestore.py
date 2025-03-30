#!/usr/bin/env python3
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Set environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath('./credentials/legislativevideoreviewswithai-80ed70b021b5.json')

# Try to import the firestore_db module
try:
    from src.firestore_db import get_firestore_db
    print("Successfully imported firestore_db module")
    
    # Try to initialize the Firestore DB client
    db = get_firestore_db()
    print("Successfully initialized Firestore DB client")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Media Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Videos: {stats['videos']}")
    print(f"  Audio: {stats['audio']}")
    print(f"  Transcripts: {stats['transcripts']}")
    print(f"  Other: {stats['other']}")
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)