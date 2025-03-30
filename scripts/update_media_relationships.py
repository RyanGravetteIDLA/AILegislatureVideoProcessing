#!/usr/bin/env python3
"""
Script to update relationships between media items in Firestore.
This will add session_id, related_video_id, related_audio_id, and related_transcript_id
fields to existing documents.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import Firestore DB
try:
    from src.firestore_db import get_firestore_db
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging
log_dir = os.path.join("data", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f'update_relationships_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger("update_relationships")


def update_path_references():
    """
    Update direct path references between related media items.
    This adds related_*_path and related_*_url fields to the documents.

    Returns:
        dict: Statistics about the update process
    """
    logger.info(f"Starting path reference update at {datetime.now()}")
    start_time = time.time()

    stats = {"processed": 0, "updated": 0, "errors": 0}

    try:
        # Get Firestore DB client
        db = get_firestore_db()

        # Process videos
        logger.info("Processing videos to add path references...")
        videos = list(db.client.collection("videos").stream())
        for video in videos:
            stats["processed"] += 1
            video_data = video.to_dict()
            updates = {}

            # Check for related audio
            if "related_audio_id" in video_data and video_data["related_audio_id"]:
                audio_id = video_data["related_audio_id"]
                audio_doc = db.client.collection("audio").document(audio_id).get()
                if audio_doc.exists:
                    audio_data = audio_doc.to_dict()
                    updates["related_audio_path"] = audio_data.get("gcs_path", "")
                    updates["related_audio_url"] = audio_data.get("url", "")

            # Check for related transcript
            if (
                "related_transcript_id" in video_data
                and video_data["related_transcript_id"]
            ):
                transcript_id = video_data["related_transcript_id"]
                transcript_doc = (
                    db.client.collection("transcripts").document(transcript_id).get()
                )
                if transcript_doc.exists:
                    transcript_data = transcript_doc.to_dict()
                    updates["related_transcript_path"] = transcript_data.get(
                        "gcs_path", ""
                    )
                    updates["related_transcript_url"] = transcript_data.get("url", "")

            # Update if we have changes
            if updates:
                try:
                    video.reference.update(updates)
                    stats["updated"] += 1
                    logger.info(f"Updated video {video.id} with path references")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error updating video {video.id}: {e}")

        # Process audio
        logger.info("Processing audio to add path references...")
        audio_items = list(db.client.collection("audio").stream())
        for audio in audio_items:
            stats["processed"] += 1
            audio_data = audio.to_dict()
            updates = {}

            # Check for related video
            if "related_video_id" in audio_data and audio_data["related_video_id"]:
                video_id = audio_data["related_video_id"]
                video_doc = db.client.collection("videos").document(video_id).get()
                if video_doc.exists:
                    video_data = video_doc.to_dict()
                    updates["related_video_path"] = video_data.get("gcs_path", "")
                    updates["related_video_url"] = video_data.get("url", "")

            # Check for related transcript
            if (
                "related_transcript_id" in audio_data
                and audio_data["related_transcript_id"]
            ):
                transcript_id = audio_data["related_transcript_id"]
                transcript_doc = (
                    db.client.collection("transcripts").document(transcript_id).get()
                )
                if transcript_doc.exists:
                    transcript_data = transcript_doc.to_dict()
                    updates["related_transcript_path"] = transcript_data.get(
                        "gcs_path", ""
                    )
                    updates["related_transcript_url"] = transcript_data.get("url", "")

            # Update if we have changes
            if updates:
                try:
                    audio.reference.update(updates)
                    stats["updated"] += 1
                    logger.info(f"Updated audio {audio.id} with path references")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error updating audio {audio.id}: {e}")

        # Process transcripts
        logger.info("Processing transcripts to add path references...")
        transcripts = list(db.client.collection("transcripts").stream())
        for transcript in transcripts:
            stats["processed"] += 1
            transcript_data = transcript.to_dict()
            updates = {}

            # Check for related video
            if (
                "related_video_id" in transcript_data
                and transcript_data["related_video_id"]
            ):
                video_id = transcript_data["related_video_id"]
                video_doc = db.client.collection("videos").document(video_id).get()
                if video_doc.exists:
                    video_data = video_doc.to_dict()
                    updates["related_video_path"] = video_data.get("gcs_path", "")
                    updates["related_video_url"] = video_data.get("url", "")

            # Check for related audio
            if (
                "related_audio_id" in transcript_data
                and transcript_data["related_audio_id"]
            ):
                audio_id = transcript_data["related_audio_id"]
                audio_doc = db.client.collection("audio").document(audio_id).get()
                if audio_doc.exists:
                    audio_data = audio_doc.to_dict()
                    updates["related_audio_path"] = audio_data.get("gcs_path", "")
                    updates["related_audio_url"] = audio_data.get("url", "")

            # Update if we have changes
            if updates:
                try:
                    transcript.reference.update(updates)
                    stats["updated"] += 1
                    logger.info(
                        f"Updated transcript {transcript.id} with path references"
                    )
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error updating transcript {transcript.id}: {e}")

        # Log results
        logger.info("Path reference update complete:")
        logger.info(f"  Processed: {stats['processed']} items")
        logger.info(f"  Updated: {stats['updated']} items")
        logger.info(f"  Errors: {stats['errors']} items")

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        logger.info(
            f"Update completed in {int(minutes)} minutes, {int(seconds)} seconds"
        )

        return stats

    except Exception as e:
        logger.error(f"Error during path reference update: {e}")
        return {"processed": 0, "updated": 0, "errors": 1}


def run_update_relationships(batch_size=100, update_paths=True):
    """
    Main function to update relationships between media items.

    Args:
        batch_size (int): Number of items to process in each batch
        update_paths (bool): Whether to update path references

    Returns:
        dict: Statistics about the update process
    """
    logger.info(f"Starting media relationship update at {datetime.now()}")
    start_time = time.time()

    try:
        # Get Firestore DB client
        db = get_firestore_db()

        # Get statistics before update
        before_stats = db.get_statistics()
        logger.info(
            f"Before update - Total items: {before_stats['total']} (videos: {before_stats['videos']}, "
            f"audio: {before_stats['audio']}, transcripts: {before_stats['transcripts']})"
        )

        # Run the update process
        logger.info(f"Running relationship update with batch size {batch_size}...")
        result = db.update_all_relationships(batch_size=batch_size)

        # Log results
        logger.info("Relationship update complete:")
        logger.info(f"  Processed: {result['processed']} items")
        logger.info(f"  Updated: {result['updated']} items")
        logger.info(f"  Session IDs created: {result['session_ids_created']} items")
        logger.info(f"  Errors: {result['errors']} items")

        # Update path references if requested
        if update_paths:
            path_result = update_path_references()
            result["paths_updated"] = path_result["updated"]

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        logger.info(
            f"Update completed in {int(minutes)} minutes, {int(seconds)} seconds"
        )

        return result

    except Exception as e:
        logger.error(f"Error during relationship update: {e}")
        return {"processed": 0, "updated": 0, "errors": 1, "session_ids_created": 0}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Update relationships between media items in Firestore"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of items to process in each batch",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no updates will be made)",
    )
    parser.add_argument(
        "--paths-only",
        action="store_true",
        help="Only update path references, skip relationship update",
    )
    parser.add_argument(
        "--skip-paths", action="store_true", help="Skip path reference updates"
    )

    args = parser.parse_args()

    if args.dry_run:
        logger.info("Running in dry-run mode (no updates will be made)")
        # Get statistics and log them
        db = get_firestore_db()
        stats = db.get_statistics()
        logger.info(f"Media Statistics:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  Videos: {stats['videos']}")
        logger.info(f"  Audio: {stats['audio']}")
        logger.info(f"  Transcripts: {stats['transcripts']}")
        logger.info(f"  Other: {stats['other']}")
        sys.exit(0)

    try:
        if args.paths_only:
            logger.info("Running path reference update only")
            update_path_references()
        else:
            run_update_relationships(
                batch_size=args.batch_size, update_paths=not args.skip_paths
            )
    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
