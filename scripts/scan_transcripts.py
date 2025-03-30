#!/usr/bin/env python3
"""
Script to scan for transcripts and update the tracking database.
Identifies all available transcripts and maintains their processing status.
"""

import os
import sys
import logging
import re
import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.transcript_db import (
    add_transcript,
    update_transcript_status,
    get_all_transcripts,
)

# Configure logging
os.makedirs(os.path.join("data", "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("data", "logs", "transcript_scan.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("scan_transcripts")

# Constants
DOWNLOADS_DIR = os.path.join("data", "downloads")
TRANSCRIPT_PATTERN = re.compile(r"(.+)_transcription\.txt$")


def scan_transcripts():
    """
    Scan for all transcript files in the downloads directory and update the database.
    """
    logger.info("Starting transcript scan")

    # Track statistics
    stats = {"found": 0, "new": 0, "updated": 0, "skipped": 0, "error": 0}

    # Walk through the directory structure
    for year_dir in Path(DOWNLOADS_DIR).glob("*"):
        if not year_dir.is_dir() or year_dir.name.startswith("_"):
            continue

        year = year_dir.name

        for category_dir in year_dir.glob("*"):
            if not category_dir.is_dir():
                continue

            category = category_dir.name

            for session_dir in category_dir.glob("*"):
                if not session_dir.is_dir():
                    continue

                session_name = session_dir.name
                audio_dir = session_dir / "audio"

                if not audio_dir.exists() or not audio_dir.is_dir():
                    continue

                # Look for transcript files in the audio directory
                for transcript_file in audio_dir.glob("*_transcription.txt"):
                    stats["found"] += 1
                    file_name = transcript_file.name
                    file_path = str(transcript_file.absolute())

                    try:
                        # Get file metadata
                        stat_info = transcript_file.stat()
                        file_size = stat_info.st_size / 1024.0  # Size in KB
                        last_modified = datetime.datetime.fromtimestamp(
                            stat_info.st_mtime
                        )

                        # Match to get base filename
                        match = TRANSCRIPT_PATTERN.match(file_name)
                        if not match:
                            logger.warning(
                                f"Unexpected transcript filename format: {file_name}"
                            )
                            stats["skipped"] += 1
                            continue

                        # Add or update in database
                        transcript = add_transcript(
                            year=year,
                            category=category,
                            session_name=session_name,
                            file_name=file_name,
                            file_path=file_path,
                            file_size=file_size,
                            last_modified=last_modified,
                        )

                        # Mark as processed since we found it
                        update_transcript_status(file_path, processed=True)

                        if transcript:
                            logger.debug(f"Added/updated transcript: {file_path}")
                            stats[
                                (
                                    "new"
                                    if transcript.created_at == transcript.updated_at
                                    else "updated"
                                )
                            ] += 1
                        else:
                            stats["skipped"] += 1

                    except Exception as e:
                        logger.error(f"Error processing transcript {file_path}: {e}")
                        stats["error"] += 1

    logger.info(
        f"Scan completed. Found: {stats['found']}, New: {stats['new']}, "
        f"Updated: {stats['updated']}, Skipped: {stats['skipped']}, Errors: {stats['error']}"
    )
    return stats


def generate_report():
    """Generate a report of all transcripts in the database."""
    logger.info("Generating transcript report")

    transcripts = get_all_transcripts()
    total = len(transcripts)
    processed = sum(1 for t in transcripts if t.processed)
    uploaded = sum(1 for t in transcripts if t.uploaded)

    print(f"\nTranscript Database Report")
    print(f"=========================")
    print(f"Total transcripts: {total}")
    percentage_processed = processed / total * 100 if total > 0 else 0
    percentage_uploaded = uploaded / total * 100 if total > 0 else 0
    print(f"Processed: {processed} ({percentage_processed:.1f}%)")
    print(f"Uploaded: {uploaded} ({percentage_uploaded:.1f}%)")
    print(f"Remaining to upload: {processed - uploaded}")
    print(f"\nRecent transcripts:")

    # Show 10 most recent transcripts
    for i, transcript in enumerate(
        sorted(
            transcripts,
            key=lambda t: t.last_modified or datetime.datetime.min,
            reverse=True,
        )[:10]
    ):
        status = "✓" if transcript.uploaded else "⨯"
        print(
            f"{i+1}. [{status}] {transcript.year}/{transcript.category}/{transcript.session_name}/{transcript.file_name}"
        )

    return total, processed, uploaded


if __name__ == "__main__":
    try:
        scan_transcripts()
        generate_report()
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        sys.exit(1)
