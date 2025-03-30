"""
Video data models for the Idaho Legislature Media Portal API.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoItem:
    """
    Model for video items

    Attributes:
        id: Unique identifier for the video
        title: Title of the video
        description: Description of the video
        year: Year the video was recorded
        category: Category of the video (e.g., House Chambers)
        date: Date the video was recorded or uploaded
        url: URL to access the video
        duration: Duration of the video
        thumbnail: URL to a thumbnail image
        session_id: Unique identifier for the legislative session
        session_name: Name of the legislative session
        related_audio_id: ID of related audio file
        related_audio_url: URL of related audio file
        related_transcript_id: ID of related transcript
        related_transcript_url: URL of related transcript
    """

    id: str
    title: str
    year: str
    category: str
    url: str
    description: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    session_id: Optional[str] = None
    session_name: Optional[str] = None
    related_audio_id: Optional[str] = None
    related_audio_url: Optional[str] = None
    related_transcript_id: Optional[str] = None
    related_transcript_url: Optional[str] = None

    @classmethod
    def from_firestore(cls, doc_id, doc_data):
        """
        Create a VideoItem from Firestore document data

        Args:
            doc_id: The Firestore document ID
            doc_data: The Firestore document data

        Returns:
            VideoItem: A new VideoItem instance
        """
        # Create a title from category and session name
        title = f"{doc_data.get('category', 'Unknown')} - {doc_data.get('session_name', 'Unknown')}"

        # Format date if available
        date = None
        date_value = doc_data.get("last_modified") or doc_data.get("created_at")
        if date_value:
            if hasattr(date_value, "strftime"):
                date = date_value.strftime("%Y-%m-%d")
            elif isinstance(date_value, str):
                date = date_value[:10]  # Extract YYYY-MM-DD part

        # Construct file URL
        gcs_path = doc_data.get("gcs_path", "")
        if gcs_path:
            # This URL pattern will be resolved by our file server component
            url = f"/api/files/gcs/{gcs_path}"
        else:
            # Fallback to original path if available
            url = f"/api/files/{doc_data.get('year', 'unknown')}/{doc_data.get('category', 'unknown')}/{doc_data.get('file_name', 'unknown')}"

        # Get related audio information
        related_audio_id = doc_data.get("related_audio_id")
        related_audio_url = None
        if related_audio_id:
            related_audio_path = doc_data.get("related_audio_path")
            if related_audio_path:
                related_audio_url = f"/api/files/gcs/{related_audio_path}"
            else:
                # If we have an ID but no path, create a direct API URL
                related_audio_url = f"/api/audio/{related_audio_id}"

        # Get related transcript information
        related_transcript_id = doc_data.get("related_transcript_id")
        related_transcript_url = None
        if related_transcript_id:
            related_transcript_path = doc_data.get("related_transcript_path")
            if related_transcript_path:
                related_transcript_url = f"/api/files/gcs/{related_transcript_path}"
            else:
                # If we have an ID but no path, create a direct API URL
                related_transcript_url = f"/api/transcripts/{related_transcript_id}"

        return cls(
            id=doc_id,
            title=title,
            description=f"Legislative Session {doc_data.get('year', 'Unknown')}",
            year=doc_data.get("year", "Unknown"),
            category=doc_data.get("category", "Unknown"),
            date=date,
            duration=doc_data.get("duration", "00:00:00"),
            thumbnail=doc_data.get("thumbnail", None),
            url=url,
            session_id=doc_data.get("session_id"),
            session_name=doc_data.get("session_name"),
            related_audio_id=related_audio_id,
            related_audio_url=related_audio_url, 
            related_transcript_id=related_transcript_id,
            related_transcript_url=related_transcript_url,
        )

    def to_dict(self):
        """
        Convert VideoItem to dictionary

        Returns:
            dict: Dictionary representation of VideoItem
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "year": self.year,
            "category": self.category,
            "date": self.date,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "url": self.url,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "related_audio_id": self.related_audio_id,
            "related_audio_url": self.related_audio_url,
            "related_transcript_id": self.related_transcript_id,
            "related_transcript_url": self.related_transcript_url,
        }
