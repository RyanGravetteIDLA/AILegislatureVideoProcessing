#!/usr/bin/env python3
"""
Firebase Download Queue

This module provides functionality to enqueue and process video download requests
using Firebase Firestore as a pub/sub system. Videos to be downloaded are stored
in a queue collection in Firestore, and can be processed by a separate worker.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Path constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the direct downloader
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
from download_direct import download_file

# Constants
COLLECTION_NAME = "download_queue"
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


class FirebaseDownloadQueue:
    """
    A class to manage a download queue using Firebase Firestore.
    """

    def __init__(self, credentials_path=None):
        """
        Initialize the Firebase connection.

        Args:
            credentials_path (str, optional): Path to the Firebase credentials JSON file.
                If None, uses the GOOGLE_APPLICATION_CREDENTIALS environment variable.
        """
        # Initialize Firebase
        if credentials_path:
            # Use provided credentials
            cred = credentials.Certificate(credentials_path)
            try:
                firebase_admin.initialize_app(cred)
            except ValueError:
                # App already initialized
                pass
        else:
            # Use default credentials from environment variable
            try:
                firebase_admin.initialize_app()
            except ValueError:
                # App already initialized
                pass

        # Get Firestore client
        self.db = firestore.client()

        # Reference to the download queue collection
        self.queue_ref = self.db.collection(COLLECTION_NAME)

        print(
            f"Initialized Firebase Download Queue using collection: {COLLECTION_NAME}"
        )

    def enqueue_video(
        self,
        year,
        month,
        day,
        committee="Education",
        code="hedu",
        time="0900AM",
        priority=0,
        metadata=None,
    ):
        """
        Add a video to the download queue.

        Args:
            year (str): Year of the video
            month (int or str): Month of the video (1-12)
            day (int or str): Day of the video (1-31)
            committee (str, optional): Committee name. Defaults to 'Education'.
            code (str, optional): Committee code. Defaults to 'hedu'.
            time (str, optional): Meeting time. Defaults to '0900AM'.
            priority (int, optional): Priority of the download (lower number = higher priority)
            metadata (dict, optional): Additional metadata about the video

        Returns:
            str: The document ID of the newly created queue item
        """
        # Format the parameters
        year_str = str(year)
        month_str = f"{int(month):02d}"
        day_str = f"{int(day):02d}"

        # Construct the URL
        url = f"https://insession.idaho.gov/IIS/{year_str}/House/Committee/{committee}/{year_str[-2:]}{month_str}{day_str}_{code}_{time}-Meeting.mp4"

        # Create entry data
        timestamp = firestore.SERVER_TIMESTAMP
        entry_data = {
            "url": url,
            "year": year_str,
            "month": month_str,
            "day": day_str,
            "committee": committee,
            "code": code,
            "time": time,
            "status": STATUS_PENDING,
            "priority": priority,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Add optional metadata
        if metadata:
            entry_data["metadata"] = metadata

        # Check if this video is already in the queue
        existing_query = (
            self.queue_ref.where("year", "==", year_str)
            .where("month", "==", month_str)
            .where("day", "==", day_str)
            .where("committee", "==", committee)
            .where("code", "==", code)
            .where("time", "==", time)
            .limit(1)
        )

        existing_docs = list(existing_query.stream())

        if existing_docs:
            existing_id = existing_docs[0].id
            existing_status = existing_docs[0].get("status")
            print(
                f"Video already in queue with ID {existing_id}, status: {existing_status}"
            )

            # If it failed before, we can retry by updating the status
            if existing_status == STATUS_FAILED:
                self.queue_ref.document(existing_id).update(
                    {
                        "status": STATUS_PENDING,
                        "updated_at": timestamp,
                        "retry_count": firestore.Increment(1),
                    }
                )
                print(f"Updated failed entry to pending for retry: {existing_id}")

            return existing_id

        # Add to Firestore
        doc_ref = self.queue_ref.document()
        doc_ref.set(entry_data)

        doc_id = doc_ref.id
        print(f"Added video to download queue with ID: {doc_id}")
        print(f"URL: {url}")

        return doc_id

    def enqueue_committee_range(
        self,
        year,
        committee="Education",
        code="hedu",
        start_month=1,
        end_month=12,
        start_day=1,
        end_day=31,
        time="0900AM",
        priority=0,
        metadata=None,
    ):
        """
        Add a range of videos for a committee to the download queue.

        Args:
            year (str): Year of the videos
            committee (str, optional): Committee name. Defaults to 'Education'.
            code (str, optional): Committee code. Defaults to 'hedu'.
            start_month (int, optional): First month to include. Defaults to 1.
            end_month (int, optional): Last month to include. Defaults to 12.
            start_day (int, optional): First day to include. Defaults to 1.
            end_day (int, optional): Last day to include. Defaults to 31.
            time (str, optional): Meeting time. Defaults to '0900AM'.
            priority (int, optional): Priority of the download (lower number = higher priority)
            metadata (dict, optional): Additional metadata about the videos

        Returns:
            list: List of document IDs added to the queue
        """
        doc_ids = []

        invalid_dates = [
            (2, 29),
            (2, 30),
            (2, 31),  # February
            (4, 31),
            (6, 31),
            (9, 31),
            (11, 31),  # 30-day months
        ]

        # Simple leap year check
        is_leap_year = (int(year) % 4 == 0 and int(year) % 100 != 0) or (
            int(year) % 400 == 0
        )
        if is_leap_year and (2, 29) in invalid_dates:
            invalid_dates.remove((2, 29))  # February 29 is valid in leap years

        for month in range(start_month, end_month + 1):
            month_start = start_day if month == start_month else 1
            month_end = end_day if month == end_month else 31

            for day in range(month_start, month_end + 1):
                # Skip invalid dates
                if (month, day) in invalid_dates:
                    continue

                # Enqueue this video
                doc_id = self.enqueue_video(
                    year=year,
                    month=month,
                    day=day,
                    committee=committee,
                    code=code,
                    time=time,
                    priority=priority,
                    metadata=metadata,
                )

                if doc_id:
                    doc_ids.append(doc_id)

        print(f"Added {len(doc_ids)} videos to the download queue")
        return doc_ids

    def process_queue(
        self, output_dir="data/downloads", limit=10, convert_to_audio=True
    ):
        """
        Process pending items in the download queue.

        Args:
            output_dir (str, optional): Directory to save downloads to. Defaults to 'data/downloads'.
            limit (int, optional): Maximum number of videos to download. Defaults to 10.
            convert_to_audio (bool, optional): Whether to convert videos to audio. Defaults to True.

        Returns:
            dict: Summary of processing results
        """
        # Query for pending items, ordered by priority (ascending) and creation time (ascending)
        pending_query = (
            self.queue_ref.where("status", "==", STATUS_PENDING)
            .order_by("priority")
            .order_by("created_at")
            .limit(limit)
        )

        pending_docs = list(pending_query.stream())
        print(f"Found {len(pending_docs)} pending downloads in the queue")

        results = {"total": len(pending_docs), "success": 0, "failed": 0, "skipped": 0}

        for doc in pending_docs:
            doc_id = doc.id
            data = doc.to_dict()

            url = data.get("url")
            year = data.get("year")
            month = data.get("month")
            day = data.get("day")
            committee = data.get("committee")
            code = data.get("code")
            time = data.get("time")

            print(f"\nProcessing queue item {doc_id}: {url}")

            # Mark as processing
            self.queue_ref.document(doc_id).update(
                {
                    "status": STATUS_PROCESSING,
                    "processing_started_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            try:
                # Check if URL exists
                import requests

                head_response = requests.head(url, allow_redirects=True, timeout=10)

                if head_response.status_code != 200:
                    print(
                        f"URL returned status {head_response.status_code}, skipping: {url}"
                    )
                    self.queue_ref.document(doc_id).update(
                        {
                            "status": STATUS_FAILED,
                            "error": f"URL check failed with status code {head_response.status_code}",
                            "updated_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                    results["failed"] += 1
                    continue

                # Create the output path
                month_names = [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]
                month_name = month_names[int(month) - 1]
                date_folder = (
                    f"{month_name} {int(day)}, {year}_{committee} Committee Meeting"
                )

                # Use pathlib for better path handling
                from pathlib import Path

                output_dir_path = (
                    Path(output_dir) / year / "House Standing Committees" / date_folder
                )
                output_file = (
                    output_dir_path / f"{year}{month}{day}_{code}_{time}-Meeting.mp4"
                )

                # Download the file
                success = download_file(url, str(output_file))

                if success:
                    print(f"Successfully downloaded: {output_file}")

                    file_info = {
                        "file_path": str(output_file),
                        "size_bytes": os.path.getsize(str(output_file)),
                    }

                    # Optional: Convert to audio
                    if convert_to_audio:
                        # Create audio directory
                        audio_dir = output_dir_path / "audio"
                        audio_file = (
                            audio_dir / f"{year}{month}{day}_{code}_{time}-Meeting.mp3"
                        )

                        # Check if ffmpeg is available
                        import shutil

                        if shutil.which("ffmpeg"):
                            try:
                                os.makedirs(audio_dir, exist_ok=True)

                                print(f"Converting video to audio: {audio_file}")
                                import subprocess

                                cmd = [
                                    "ffmpeg",
                                    "-i",
                                    str(output_file),
                                    "-vn",  # Skip video
                                    "-acodec",
                                    "libmp3lame",
                                    "-y",  # Overwrite output file
                                    str(audio_file),
                                ]

                                result = subprocess.run(
                                    cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                )

                                if result.returncode == 0:
                                    print(
                                        f"Successfully converted to audio: {audio_file}"
                                    )
                                    file_info["audio_path"] = str(audio_file)
                                    file_info["audio_size_bytes"] = os.path.getsize(
                                        str(audio_file)
                                    )
                                else:
                                    print(
                                        f"Error converting video to audio: {result.stderr}"
                                    )
                                    file_info["audio_conversion_error"] = result.stderr
                            except Exception as e:
                                print(f"Error during audio conversion: {e}")
                                file_info["audio_conversion_error"] = str(e)

                    # Mark as completed
                    self.queue_ref.document(doc_id).update(
                        {
                            "status": STATUS_COMPLETED,
                            "completed_at": firestore.SERVER_TIMESTAMP,
                            "updated_at": firestore.SERVER_TIMESTAMP,
                            "file_info": file_info,
                        }
                    )

                    results["success"] += 1
                else:
                    print(f"Failed to download: {url}")
                    # Mark as failed
                    self.queue_ref.document(doc_id).update(
                        {
                            "status": STATUS_FAILED,
                            "error": "Download failed",
                            "updated_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                    results["failed"] += 1

            except Exception as e:
                print(f"Error processing queue item {doc_id}: {e}")
                # Mark as failed
                self.queue_ref.document(doc_id).update(
                    {
                        "status": STATUS_FAILED,
                        "error": str(e),
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    }
                )
                results["failed"] += 1

        print("\nQueue processing complete")
        print(f"Total: {results['total']}")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")

        return results

    def get_queue_stats(self):
        """
        Get statistics about the download queue.

        Returns:
            dict: Statistics about the queue
        """
        stats = {"total": 0, "pending": 0, "processing": 0, "completed": 0, "failed": 0}

        # Get total count
        all_docs = list(self.queue_ref.stream())
        stats["total"] = len(all_docs)

        # Count by status
        for doc in all_docs:
            status = doc.get("status")
            if status in stats:
                stats[status] += 1

        return stats


def main():
    """Main function to parse arguments and perform actions."""
    parser = argparse.ArgumentParser(description="Firebase Download Queue Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Enqueue command
    enqueue_parser = subparsers.add_parser(
        "enqueue", help="Add a video to the download queue"
    )
    enqueue_parser.add_argument(
        "--year", required=True, help="Year of the meeting (e.g., 2025)"
    )
    enqueue_parser.add_argument(
        "--month", required=True, help="Month of the meeting (1-12)"
    )
    enqueue_parser.add_argument(
        "--day", required=True, help="Day of the meeting (1-31)"
    )
    enqueue_parser.add_argument(
        "--committee", default="Education", help="Committee name (default: Education)"
    )
    enqueue_parser.add_argument(
        "--code", default="hedu", help="Committee code (default: hedu)"
    )
    enqueue_parser.add_argument(
        "--time", default="0900AM", help="Meeting time (default: 0900AM)"
    )
    enqueue_parser.add_argument(
        "--priority",
        type=int,
        default=0,
        help="Priority (lower number = higher priority)",
    )
    enqueue_parser.add_argument(
        "--metadata", help="JSON string with additional metadata"
    )
    enqueue_parser.add_argument(
        "--credentials", help="Path to Firebase credentials JSON file"
    )

    # Enqueue range command
    range_parser = subparsers.add_parser(
        "enqueue-range", help="Add a range of videos to the download queue"
    )
    range_parser.add_argument(
        "--year", required=True, help="Year of the meetings (e.g., 2025)"
    )
    range_parser.add_argument(
        "--committee", default="Education", help="Committee name (default: Education)"
    )
    range_parser.add_argument(
        "--code", default="hedu", help="Committee code (default: hedu)"
    )
    range_parser.add_argument(
        "--start-month", type=int, default=1, help="First month to include (default: 1)"
    )
    range_parser.add_argument(
        "--end-month", type=int, default=12, help="Last month to include (default: 12)"
    )
    range_parser.add_argument(
        "--start-day", type=int, default=1, help="First day to include (default: 1)"
    )
    range_parser.add_argument(
        "--end-day", type=int, default=31, help="Last day to include (default: 31)"
    )
    range_parser.add_argument(
        "--time", default="0900AM", help="Meeting time (default: 0900AM)"
    )
    range_parser.add_argument(
        "--priority",
        type=int,
        default=0,
        help="Priority (lower number = higher priority)",
    )
    range_parser.add_argument("--metadata", help="JSON string with additional metadata")
    range_parser.add_argument(
        "--credentials", help="Path to Firebase credentials JSON file"
    )

    # Process command
    process_parser = subparsers.add_parser(
        "process", help="Process pending items in the download queue"
    )
    process_parser.add_argument(
        "--output-dir", default="data/downloads", help="Directory to save downloads to"
    )
    process_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of videos to download"
    )
    process_parser.add_argument(
        "--no-audio", action="store_true", help="Skip audio conversion"
    )
    process_parser.add_argument(
        "--credentials", help="Path to Firebase credentials JSON file"
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Get statistics about the download queue"
    )
    stats_parser.add_argument(
        "--credentials", help="Path to Firebase credentials JSON file"
    )

    args = parser.parse_args()

    # Initialize the queue manager
    queue = FirebaseDownloadQueue(
        credentials_path=args.credentials if hasattr(args, "credentials") else None
    )

    if args.command == "enqueue":
        # Parse metadata if provided
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print(f"Error parsing metadata JSON: {args.metadata}")
                return

        # Enqueue the video
        queue.enqueue_video(
            year=args.year,
            month=args.month,
            day=args.day,
            committee=args.committee,
            code=args.code,
            time=args.time,
            priority=args.priority,
            metadata=metadata,
        )

    elif args.command == "enqueue-range":
        # Parse metadata if provided
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print(f"Error parsing metadata JSON: {args.metadata}")
                return

        # Enqueue range of videos
        queue.enqueue_committee_range(
            year=args.year,
            committee=args.committee,
            code=args.code,
            start_month=args.start_month,
            end_month=args.end_month,
            start_day=args.start_day,
            end_day=args.end_day,
            time=args.time,
            priority=args.priority,
            metadata=metadata,
        )

    elif args.command == "process":
        # Process the queue
        queue.process_queue(
            output_dir=args.output_dir,
            limit=args.limit,
            convert_to_audio=not args.no_audio,
        )

    elif args.command == "stats":
        # Get queue statistics
        stats = queue.get_queue_stats()
        print("\nDownload Queue Statistics:")
        print(f"Total items: {stats['total']}")
        print(f"Pending: {stats['pending']}")
        print(f"Processing: {stats['processing']}")
        print(f"Completed: {stats['completed']}")
        print(f"Failed: {stats['failed']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
