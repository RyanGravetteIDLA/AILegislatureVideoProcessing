#!/usr/bin/env python3
"""
Script to check the distribution of media files in the SQLite database.
"""

from src.transcript_db import get_all_transcripts, init_db

def main():
    # Initialize the database
    init_db()
    
    # Get all transcripts
    transcripts = get_all_transcripts()
    print(f"Total records in SQLite database: {len(transcripts)}")
    
    # Analyze file extensions
    extensions = {}
    for t in transcripts:
        ext = t.file_path.split('.')[-1].lower()
        if ext not in extensions:
            extensions[ext] = 0
        extensions[ext] += 1
    
    print("\nFile Extensions:")
    for ext, count in extensions.items():
        print(f"  .{ext}: {count} files")
    
    # Check videos vs audio vs transcripts
    media_types = {
        'video': 0,
        'audio': 0,
        'transcript': 0,
        'other': 0
    }
    
    for t in transcripts:
        ext = t.file_path.split('.')[-1].lower()
        path = t.file_path.lower()
        
        if ext in ['mp4', 'avi', 'mov']:
            media_types['video'] += 1
        elif ext in ['mp3', 'wav', 'm4a'] or '/audio/' in path:
            media_types['audio'] += 1
        elif ext in ['txt', 'pdf', 'docx', 'md'] or 'transcript' in path:
            media_types['transcript'] += 1
        else:
            media_types['other'] += 1
    
    print("\nMedia Types:")
    for media_type, count in media_types.items():
        print(f"  {media_type}: {count} files")
    
    # Sample paths
    print("\nSample file paths:")
    for category in ['video', 'audio', 'transcript']:
        found = False
        for t in transcripts:
            ext = t.file_path.split('.')[-1].lower()
            path = t.file_path.lower()
            
            is_match = False
            if category == 'video' and ext in ['mp4', 'avi', 'mov']:
                is_match = True
            elif category == 'audio' and (ext in ['mp3', 'wav', 'm4a'] or '/audio/' in path):
                is_match = True
            elif category == 'transcript' and (ext in ['txt', 'pdf'] or 'transcript' in path):
                is_match = True
                
            if is_match:
                print(f"  {category}: {t.file_path}")
                found = True
                break
        
        if not found:
            print(f"  {category}: No files found")
    
if __name__ == "__main__":
    main()