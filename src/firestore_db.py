#!/usr/bin/env python3
"""
Firestore database module for accessing media data.
Replacement for the transcript_db.py module, using Firestore instead of SQLite.
"""

import os
import sys
import logging
import hashlib
import re
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Add project root to path for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Set up directory paths
logs_dir = os.path.join(base_dir, "data", "logs")

# Create directories if they don't exist
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "firestore_db.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("firestore_db")


def get_firebase_project_id():
    """
    Get the Firebase project ID from environment or configuration.

    Returns:
        str: Firebase project ID
    """
    # First try to read from environment variable
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        # Try to get from application default credentials
        try:
            import google.auth

            _, project_id = google.auth.default()
        except Exception as e:
            logger.warning(f"Could not get project ID from default credentials: {e}")

    # Fallback to hardcoded value (from our migration plan)
    if not project_id:
        project_id = "legislativevideoreviewswithai"
        logger.warning(f"Using fallback project ID: {project_id}")

    # Set the environment variable for the service account if needed
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Check for credentials in multiple locations
        possible_paths = [
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "credentials",
                "legislativevideoreviewswithai-80ed70b021b5.json",
            ),
            "/Users/ryangravette/Downloads/legislativevideoreviewswithai-firebase-adminsdk-fbsvc-f12bbdca43.json",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
                logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to {path}")
                break

    return project_id


class FirestoreDB:
    """
    Firestore database client for accessing media data.
    Serves as a replacement for the SQLite-based transcript_db module.
    """

    def __init__(self, project_id=None):
        """
        Initialize the Firestore client.

        Args:
            project_id (str, optional): Firebase project ID. If None, tries to get from environment.
        """
        self.project_id = project_id or get_firebase_project_id()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Firestore client."""
        try:
            self.client = firestore.Client(project=self.project_id)
            logger.info(f"Initialized Firestore client for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

    def generate_session_id(self, file_path, file_name, year, category, date=None):
        """
        Generate a unique session ID for media items from the same session.

        Args:
            file_path (str): Path to the file
            file_name (str): Name of the file
            year (str): Year of the session
            category (str): Category of the session
            date (str, optional): Date of the session

        Returns:
            str: Unique session ID
        """
        # Extract components for the session ID
        parts = []

        # First try to extract a date from file_name or path
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        date_match = re.search(date_pattern, file_name) or re.search(
            date_pattern, file_path
        )
        if date_match:
            extracted_date = date_match.group(1)
            parts.append(extracted_date)
        elif date:
            parts.append(date)

        # Add year and category
        parts.append(year)
        parts.append(category.replace(" ", "_"))

        # Try to extract session info from file name
        session_pattern = r"(?:session|day|meeting)_?(\d+)"
        session_match = re.search(session_pattern, file_name.lower())
        if session_match:
            parts.append(f"session_{session_match.group(1)}")

        # Create a session string
        session_string = "_".join(parts)

        # Create a hash for uniqueness
        session_hash = hashlib.md5(session_string.encode()).hexdigest()[:8]

        # Final session ID
        return f"{year}_{category.replace(' ', '_')}_{session_hash}"

    def find_matching_media(
        self, file_path, file_name, media_type, year, category, session_name=None
    ):
        """
        Find matching media items based on metadata to establish relationships.

        Args:
            file_path (str): Path to the file
            file_name (str): Name of the file
            media_type (str): Type of media ('video', 'audio', 'transcript')
            year (str): Year of the media
            category (str): Category of the media
            session_name (str, optional): Session name

        Returns:
            dict: Dictionary with matching media IDs by type
        """
        matches = {
            "video_id": None,
            "audio_id": None,
            "transcript_id": None,
            "session_id": None,
        }

        # First look for existing items with session_id
        # This is the preferred matching method if we've already processed some items with the new schema
        found_session_id = None

        # Determine collections to search based on the current media type
        if media_type == "video":
            collections_to_search = ["audio", "transcripts"]
        elif media_type == "audio":
            collections_to_search = ["videos", "transcripts"]
        elif media_type == "transcript":
            collections_to_search = ["videos", "audio"]
        else:
            collections_to_search = []

        # Try to find existing session ID first
        for collection in collections_to_search:
            query = (
                self.client.collection(collection)
                .where(filter=FieldFilter("year", "==", year))
                .where(filter=FieldFilter("category", "==", category))
            )

            docs = list(query.stream())
            for doc in docs:
                data = doc.to_dict()

                # If the document has a session_id, use it
                if "session_id" in data and data["session_id"]:
                    found_session_id = data["session_id"]
                    # Also record the document ID based on its type
                    if collection == "videos":
                        matches["video_id"] = doc.id
                    elif collection == "audio":
                        matches["audio_id"] = doc.id
                    elif collection == "transcripts":
                        matches["transcript_id"] = doc.id
                    break

            if found_session_id:
                break

        # If we didn't find an existing session ID, generate a new one
        if not found_session_id:
            found_session_id = self.generate_session_id(
                file_path, file_name, year, category
            )

        # Record the session ID
        matches["session_id"] = found_session_id

        # If we still need to find matching media, try to find by metadata
        # This is a fallback for items that don't yet have a session_id
        for collection in collections_to_search:
            # Skip if we already found a match for this type
            if (
                (collection == "videos" and matches["video_id"])
                or (collection == "audio" and matches["audio_id"])
                or (collection == "transcripts" and matches["transcript_id"])
            ):
                continue

            # Query with multiple conditions
            query = (
                self.client.collection(collection)
                .where(filter=FieldFilter("year", "==", year))
                .where(filter=FieldFilter("category", "==", category))
            )

            # Execute query and check results
            docs = list(query.stream())
            if docs:
                # For simplicity, take the first match
                # In a more sophisticated implementation, we'd compare more metadata
                doc = docs[0]
                if collection == "videos":
                    matches["video_id"] = doc.id
                elif collection == "audio":
                    matches["audio_id"] = doc.id
                elif collection == "transcripts":
                    matches["transcript_id"] = doc.id

        return matches

    def get_all_media(self, media_type=None, limit=None):
        """
        Get all media records from Firestore.

        Args:
            media_type (str, optional): Filter by media type ('video', 'audio', 'transcript')
            limit (int, optional): Maximum number of records to return

        Returns:
            list: List of Firestore document snapshots
        """
        results = []
        collections = []

        # Determine which collections to query
        if media_type == "video":
            collections = ["videos"]
        elif media_type == "audio":
            collections = ["audio"]
        elif media_type == "transcript":
            collections = ["transcripts"]
        else:
            collections = ["videos", "audio", "transcripts", "other"]

        # Query each collection
        for collection in collections:
            query = self.client.collection(collection)
            if limit:
                query = query.limit(limit)

            # Execute query and add results
            docs = list(query.stream())
            for doc in docs:
                # Add collection name and document ID to the data
                data = doc.to_dict()
                data["_collection"] = collection
                data["_id"] = doc.id
                results.append(data)

        return results

    def get_media_by_id(self, media_id, collection=None):
        """
        Get a specific media record by ID.

        Args:
            media_id (str): Document ID
            collection (str, optional): Collection name. If None, searches all collections.

        Returns:
            dict: Document data or None if not found
        """
        if collection:
            collections = [collection]
        else:
            collections = ["videos", "audio", "transcripts", "other"]

        for coll in collections:
            doc_ref = self.client.collection(coll).document(media_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                data["_collection"] = coll
                data["_id"] = doc.id
                return data

        return None

    def get_related_media(self, media_id, collection):
        """
        Get related media for a specific item by session ID.

        Args:
            media_id (str): Document ID
            collection (str): Collection name

        Returns:
            dict: Dictionary with related media
        """
        result = {"video": None, "audio": None, "transcript": None, "other": []}

        # First get the original document to find its session ID
        doc = self.get_media_by_id(media_id, collection)
        if not doc:
            return result

        # If the document doesn't have a session ID, we can't find related media
        session_id = doc.get("session_id")
        if not session_id:
            return result

        # Query each collection for items with the same session ID
        for coll in ["videos", "audio", "transcripts", "other"]:
            if coll == collection and doc["_id"] == media_id:
                # Skip the original document
                continue

            query = self.client.collection(coll).where(
                filter=FieldFilter("session_id", "==", session_id)
            )

            docs = list(query.stream())
            for related_doc in docs:
                data = related_doc.to_dict()
                data["_collection"] = coll
                data["_id"] = related_doc.id

                if coll == "videos":
                    result["video"] = data
                elif coll == "audio":
                    result["audio"] = data
                elif coll == "transcript":
                    result["transcript"] = data
                else:
                    result["other"].append(data)

        return result

    def get_media_by_session_id(self, session_id):
        """
        Get all media associated with a specific session ID.

        Args:
            session_id (str): Session ID

        Returns:
            dict: Dictionary with media by type
        """
        result = {"videos": [], "audio": [], "transcripts": [], "other": []}

        # Query each collection for items with this session ID
        for collection in ["videos", "audio", "transcripts", "other"]:
            query = self.client.collection(collection).where(
                filter=FieldFilter("session_id", "==", session_id)
            )

            docs = list(query.stream())
            for doc in docs:
                data = doc.to_dict()
                data["_collection"] = collection
                data["_id"] = doc.id

                if collection == "videos":
                    result["videos"].append(data)
                elif collection == "audio":
                    result["audio"].append(data)
                elif collection == "transcripts":
                    result["transcripts"].append(data)
                else:
                    result["other"].append(data)

        return result

    def search_media(
        self, query_text, media_type=None, year=None, category=None, limit=100
    ):
        """
        Search for media records by text, year, category, etc.

        Args:
            query_text (str): Text to search for in session_name or category
            media_type (str, optional): Filter by media type
            year (str, optional): Filter by year
            category (str, optional): Filter by category
            limit (int, optional): Maximum number of results

        Returns:
            list: List of matching document data
        """
        results = []
        collections = []

        # Determine which collections to query
        if media_type == "video":
            collections = ["videos"]
        elif media_type == "audio":
            collections = ["audio"]
        elif media_type == "transcript":
            collections = ["transcripts"]
        else:
            collections = ["videos", "audio", "transcripts", "other"]

        # Query each collection
        for collection in collections:
            query = self.client.collection(collection)

            # Apply filters
            if year:
                query = query.where(filter=FieldFilter("year", "==", year))
            if category:
                query = query.where(filter=FieldFilter("category", "==", category))

            # Execute query and add results
            docs = list(query.limit(limit).stream())

            # Filter by query text manually (since Firestore doesn't support full-text search)
            for doc in docs:
                data = doc.to_dict()
                session_name = data.get("session_name", "").lower()
                category_name = data.get("category", "").lower()

                if (
                    query_text.lower() in session_name
                    or query_text.lower() in category_name
                ):
                    # Add collection name and document ID to the data
                    data["_collection"] = collection
                    data["_id"] = doc.id
                    results.append(data)

        return results[:limit]

    def get_filter_options(self):
        """
        Get available filter options (years and categories).

        Returns:
            dict: Dictionary with years and categories
        """
        years = set()
        categories = set()

        collections = ["videos", "audio", "transcripts", "other"]

        for collection in collections:
            # Get years
            year_query = self.client.collection(collection).select(["year"])
            for doc in year_query.stream():
                data = doc.to_dict()
                if "year" in data and data["year"]:
                    years.add(data["year"])

            # Get categories
            category_query = self.client.collection(collection).select(["category"])
            for doc in category_query.stream():
                data = doc.to_dict()
                if "category" in data and data["category"]:
                    categories.add(data["category"])

        return {"years": sorted(list(years)), "categories": sorted(list(categories))}

    def get_statistics(self):
        """
        Get statistics about the available media.

        Returns:
            dict: Dictionary with media counts
        """
        video_count = len(list(self.client.collection("videos").limit(1000).stream()))
        audio_count = len(list(self.client.collection("audio").limit(1000).stream()))
        transcript_count = len(
            list(self.client.collection("transcripts").limit(1000).stream())
        )
        other_count = len(list(self.client.collection("other").limit(1000).stream()))

        return {
            "total": video_count + audio_count + transcript_count + other_count,
            "videos": video_count,
            "audio": audio_count,
            "transcripts": transcript_count,
            "other": other_count,
        }

    def add_media(self, data, collection):
        """
        Add a new media record to Firestore.

        Args:
            data (dict): Media data
            collection (str): Collection name ('videos', 'audio', 'transcripts', 'other')

        Returns:
            tuple: (bool, str) - Success status and document ID
        """
        if collection not in ["videos", "audio", "transcripts", "other"]:
            logger.error(f"Invalid collection: {collection}")
            return False, None

        # Add timestamps
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()

        # Determine media type
        media_type = collection[:-1] if collection.endswith("s") else collection

        # Try to find related media and establish relationships
        matches = self.find_matching_media(
            data.get("original_path", ""),
            data.get("file_name", ""),
            media_type,
            data.get("year", ""),
            data.get("category", ""),
            data.get("session_name", ""),
        )

        # Add relationship fields
        if matches["session_id"]:
            data["session_id"] = matches["session_id"]

        # Add relationship IDs based on media type
        if media_type == "video":
            if matches["audio_id"]:
                data["related_audio_id"] = matches["audio_id"]
            if matches["transcript_id"]:
                data["related_transcript_id"] = matches["transcript_id"]
        elif media_type == "audio":
            if matches["video_id"]:
                data["related_video_id"] = matches["video_id"]
            if matches["transcript_id"]:
                data["related_transcript_id"] = matches["transcript_id"]
        elif media_type == "transcript":
            if matches["video_id"]:
                data["related_video_id"] = matches["video_id"]
            if matches["audio_id"]:
                data["related_audio_id"] = matches["audio_id"]

        try:
            # Add the document
            doc_ref = self.client.collection(collection).document()
            doc_ref.set(data)
            doc_id = doc_ref.id
            logger.info(f"Added new {collection} record: {doc_id}")

            # Update the related documents with references to this document
            self.update_relationship_references(doc_id, data, collection, matches)

            return True, doc_id

        except Exception as e:
            logger.error(f"Error adding {collection} record: {e}")
            return False, None

    def update_relationship_references(self, doc_id, data, collection, matches):
        """
        Update relationship references in related documents.

        Args:
            doc_id (str): Document ID of the new document
            data (dict): Document data
            collection (str): Collection name
            matches (dict): Dictionary with related media IDs

        Returns:
            bool: Success status
        """
        try:
            # Determine media type
            media_type = collection[:-1] if collection.endswith("s") else collection

            # Get paths to this item
            item_gcs_path = data.get("gcs_path", "")
            item_url = data.get("url", "")

            # Update video references if this is an audio or transcript
            if media_type in ["audio", "transcript"] and matches["video_id"]:
                video_ref = self.client.collection("videos").document(
                    matches["video_id"]
                )
                video_doc = video_ref.get()
                video_data = video_doc.to_dict() if video_doc.exists else {}

                updates = {"updated_at": datetime.now()}

                if media_type == "audio":
                    updates["related_audio_id"] = doc_id
                    updates["related_audio_path"] = item_gcs_path
                    updates["related_audio_url"] = item_url
                elif media_type == "transcript":
                    updates["related_transcript_id"] = doc_id
                    updates["related_transcript_path"] = item_gcs_path
                    updates["related_transcript_url"] = item_url

                video_ref.update(updates)
                logger.info(
                    f"Updated video {matches['video_id']} with reference to {media_type} {doc_id}"
                )

            # Update audio references if this is a video or transcript
            if media_type in ["video", "transcript"] and matches["audio_id"]:
                audio_ref = self.client.collection("audio").document(
                    matches["audio_id"]
                )
                audio_doc = audio_ref.get()
                audio_data = audio_doc.to_dict() if audio_doc.exists else {}

                updates = {"updated_at": datetime.now()}

                if media_type == "video":
                    updates["related_video_id"] = doc_id
                    updates["related_video_path"] = item_gcs_path
                    updates["related_video_url"] = item_url
                elif media_type == "transcript":
                    updates["related_transcript_id"] = doc_id
                    updates["related_transcript_path"] = item_gcs_path
                    updates["related_transcript_url"] = item_url

                audio_ref.update(updates)
                logger.info(
                    f"Updated audio {matches['audio_id']} with reference to {media_type} {doc_id}"
                )

            # Update transcript references if this is a video or audio
            if media_type in ["video", "audio"] and matches["transcript_id"]:
                transcript_ref = self.client.collection("transcripts").document(
                    matches["transcript_id"]
                )
                transcript_doc = transcript_ref.get()
                transcript_data = (
                    transcript_doc.to_dict() if transcript_doc.exists else {}
                )

                updates = {"updated_at": datetime.now()}

                if media_type == "video":
                    updates["related_video_id"] = doc_id
                    updates["related_video_path"] = item_gcs_path
                    updates["related_video_url"] = item_url
                elif media_type == "audio":
                    updates["related_audio_id"] = doc_id
                    updates["related_audio_path"] = item_gcs_path
                    updates["related_audio_url"] = item_url

                transcript_ref.update(updates)
                logger.info(
                    f"Updated transcript {matches['transcript_id']} with reference to {media_type} {doc_id}"
                )

            return True

        except Exception as e:
            logger.error(f"Error updating relationship references: {e}")
            return False

    def update_media(self, doc_id, data, collection):
        """
        Update an existing media record in Firestore.

        Args:
            doc_id (str): Document ID
            data (dict): Updated data
            collection (str): Collection name

        Returns:
            bool: Success status
        """
        if collection not in ["videos", "audio", "transcripts", "other"]:
            logger.error(f"Invalid collection: {collection}")
            return False

        try:
            # Update timestamps
            data["updated_at"] = datetime.now()

            # Update the document
            doc_ref = self.client.collection(collection).document(doc_id)
            doc_ref.update(data)
            logger.info(f"Updated {collection} record: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating {collection} record {doc_id}: {e}")
            return False

    def delete_media(self, doc_id, collection):
        """
        Delete a media record from Firestore.

        Args:
            doc_id (str): Document ID
            collection (str): Collection name

        Returns:
            bool: Success status
        """
        if collection not in ["videos", "audio", "transcripts", "other"]:
            logger.error(f"Invalid collection: {collection}")
            return False

        try:
            # Delete the document
            doc_ref = self.client.collection(collection).document(doc_id)
            doc_ref.delete()
            logger.info(f"Deleted {collection} record: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting {collection} record {doc_id}: {e}")
            return False

    def update_all_relationships(self, batch_size=100):
        """
        Update relationships for all existing media in the database.
        This is used to build relationships between existing items.

        Args:
            batch_size (int): Number of items to process in each batch

        Returns:
            dict: Statistics about the update process
        """
        stats = {"processed": 0, "updated": 0, "errors": 0, "session_ids_created": 0}

        try:
            # Process each collection
            for collection in ["videos", "audio", "transcripts"]:
                logger.info(
                    f"Processing {collection} collection for relationship updates"
                )

                # Get all documents in this collection
                docs = list(self.client.collection(collection).stream())
                logger.info(f"Found {len(docs)} documents in {collection}")

                # Process documents in batches
                for i in range(0, len(docs), batch_size):
                    batch = docs[i : i + batch_size]
                    logger.info(
                        f"Processing batch {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1} ({len(batch)} documents)"
                    )

                    for doc in batch:
                        stats["processed"] += 1
                        data = doc.to_dict()

                        # Skip if document already has a session_id
                        if "session_id" in data and data["session_id"]:
                            continue

                        # Generate a session ID
                        media_type = (
                            collection[:-1] if collection.endswith("s") else collection
                        )
                        session_id = self.generate_session_id(
                            data.get("original_path", ""),
                            data.get("file_name", ""),
                            data.get("year", ""),
                            data.get("category", ""),
                            data.get("date", None),
                        )

                        # Find related media
                        matches = self.find_matching_media(
                            data.get("original_path", ""),
                            data.get("file_name", ""),
                            media_type,
                            data.get("year", ""),
                            data.get("category", ""),
                            data.get("session_name", ""),
                        )

                        # Use the found session ID if available, otherwise use the generated one
                        session_id = matches["session_id"] or session_id

                        # Prepare updates
                        updates = {
                            "session_id": session_id,
                            "updated_at": datetime.now(),
                        }

                        # Add relationship IDs based on media type
                        if media_type == "video":
                            if matches["audio_id"]:
                                # Get the audio data to access paths
                                audio_doc = (
                                    self.client.collection("audio")
                                    .document(matches["audio_id"])
                                    .get()
                                )
                                if audio_doc.exists:
                                    audio_data = audio_doc.to_dict()
                                    updates["related_audio_id"] = matches["audio_id"]
                                    updates["related_audio_path"] = audio_data.get(
                                        "gcs_path", ""
                                    )
                                    updates["related_audio_url"] = audio_data.get(
                                        "url", ""
                                    )

                            if matches["transcript_id"]:
                                # Get the transcript data to access paths
                                transcript_doc = (
                                    self.client.collection("transcripts")
                                    .document(matches["transcript_id"])
                                    .get()
                                )
                                if transcript_doc.exists:
                                    transcript_data = transcript_doc.to_dict()
                                    updates["related_transcript_id"] = matches[
                                        "transcript_id"
                                    ]
                                    updates["related_transcript_path"] = (
                                        transcript_data.get("gcs_path", "")
                                    )
                                    updates["related_transcript_url"] = (
                                        transcript_data.get("url", "")
                                    )

                        elif media_type == "audio":
                            if matches["video_id"]:
                                # Get the video data to access paths
                                video_doc = (
                                    self.client.collection("videos")
                                    .document(matches["video_id"])
                                    .get()
                                )
                                if video_doc.exists:
                                    video_data = video_doc.to_dict()
                                    updates["related_video_id"] = matches["video_id"]
                                    updates["related_video_path"] = video_data.get(
                                        "gcs_path", ""
                                    )
                                    updates["related_video_url"] = video_data.get(
                                        "url", ""
                                    )

                            if matches["transcript_id"]:
                                # Get the transcript data to access paths
                                transcript_doc = (
                                    self.client.collection("transcripts")
                                    .document(matches["transcript_id"])
                                    .get()
                                )
                                if transcript_doc.exists:
                                    transcript_data = transcript_doc.to_dict()
                                    updates["related_transcript_id"] = matches[
                                        "transcript_id"
                                    ]
                                    updates["related_transcript_path"] = (
                                        transcript_data.get("gcs_path", "")
                                    )
                                    updates["related_transcript_url"] = (
                                        transcript_data.get("url", "")
                                    )

                        elif media_type == "transcript":
                            if matches["video_id"]:
                                # Get the video data to access paths
                                video_doc = (
                                    self.client.collection("videos")
                                    .document(matches["video_id"])
                                    .get()
                                )
                                if video_doc.exists:
                                    video_data = video_doc.to_dict()
                                    updates["related_video_id"] = matches["video_id"]
                                    updates["related_video_path"] = video_data.get(
                                        "gcs_path", ""
                                    )
                                    updates["related_video_url"] = video_data.get(
                                        "url", ""
                                    )

                            if matches["audio_id"]:
                                # Get the audio data to access paths
                                audio_doc = (
                                    self.client.collection("audio")
                                    .document(matches["audio_id"])
                                    .get()
                                )
                                if audio_doc.exists:
                                    audio_data = audio_doc.to_dict()
                                    updates["related_audio_id"] = matches["audio_id"]
                                    updates["related_audio_path"] = audio_data.get(
                                        "gcs_path", ""
                                    )
                                    updates["related_audio_url"] = audio_data.get(
                                        "url", ""
                                    )

                        # Update the document
                        try:
                            doc.reference.update(updates)
                            stats["updated"] += 1
                            stats["session_ids_created"] += 1
                            logger.info(
                                f"Updated {media_type} {doc.id} with session ID {session_id}"
                            )

                            # Also update relationship references in related documents
                            self.update_relationship_references(
                                doc.id, data, collection, matches
                            )
                        except Exception as e:
                            stats["errors"] += 1
                            logger.error(f"Error updating {media_type} {doc.id}: {e}")

            logger.info(
                f"Relationship update complete: {stats['updated']}/{stats['processed']} documents updated, {stats['errors']} errors"
            )
            return stats

        except Exception as e:
            logger.error(f"Error updating relationships: {e}")
            return stats

    def get_unprocessed_media(self, media_type=None):
        """
        Get media records that haven't been processed yet.

        Args:
            media_type (str, optional): Filter by media type

        Returns:
            list: List of unprocessed media records
        """
        results = []
        collections = []

        # Determine which collections to query
        if media_type == "video":
            collections = ["videos"]
        elif media_type == "audio":
            collections = ["audio"]
        elif media_type == "transcript":
            collections = ["transcripts"]
        else:
            collections = ["videos", "audio", "transcripts", "other"]

        # Query each collection
        for collection in collections:
            query = self.client.collection(collection).where(
                filter=FieldFilter("processed", "==", False)
            )

            # Execute query and add results
            docs = list(query.stream())
            for doc in docs:
                data = doc.to_dict()
                data["_collection"] = collection
                data["_id"] = doc.id
                results.append(data)

        return results


# Create a singleton instance
_firestore_db_instance = None


def get_firestore_db():
    """
    Get the Firestore DB instance (singleton pattern).

    Returns:
        FirestoreDB: Firestore database client instance
    """
    global _firestore_db_instance
    if _firestore_db_instance is None:
        _firestore_db_instance = FirestoreDB()
    return _firestore_db_instance


if __name__ == "__main__":
    # Example usage
    db = get_firestore_db()

    # Get statistics
    stats = db.get_statistics()
    print(f"Media Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Videos: {stats['videos']}")
    print(f"  Audio: {stats['audio']}")
    print(f"  Transcripts: {stats['transcripts']}")
    print(f"  Other: {stats['other']}")

    # Get filter options
    filters = db.get_filter_options()
    print(f"\nFilter Options:")
    print(f"  Years: {filters['years']}")
    print(f"  Categories: {filters['categories']}")

    # Update relationships for all media
    choice = input("Do you want to update relationships for all media? (y/n): ")
    if choice.lower() == "y":
        print("Updating relationships...")
        result = db.update_all_relationships()
        print(f"Update complete:")
        print(f"  Processed: {result['processed']}")
        print(f"  Updated: {result['updated']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Session IDs created: {result['session_ids_created']}")
