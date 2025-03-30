"""
Transcript data models for the Idaho Legislature Media Portal API.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class TranscriptItem:
    """
    Model for transcript items

    Attributes:
        id: Unique identifier for the transcript
        title: Title of the transcript
        description: Description of the transcript
        year: Year the transcript was created
        category: Category of the transcript (e.g., House Chambers)
        date: Date the transcript was created or uploaded
        url: URL to access the transcript
        content: The transcript content
        related_video_id: ID of the related video if available
        related_audio_id: ID of the related audio if available
    """

    id: str
    title: str
    year: str
    category: str
    url: str
    description: Optional[str] = None
    date: Optional[str] = None
    content: Optional[str] = None
    related_video_id: Optional[str] = None
    related_audio_id: Optional[str] = None

    @classmethod
    def from_firestore(cls, doc_id, doc_data):
        """
        Create a TranscriptItem from Firestore document data

        Args:
            doc_id: The Firestore document ID
            doc_data: The Firestore document data

        Returns:
            TranscriptItem: A new TranscriptItem instance
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

        return cls(
            id=doc_id,
            title=title,
            description=f"Legislative Session {doc_data.get('year', 'Unknown')}",
            year=doc_data.get("year", "Unknown"),
            category=doc_data.get("category", "Unknown"),
            date=date,
            content=doc_data.get("content", None),
            related_video_id=doc_data.get("video_id", None),
            related_audio_id=doc_data.get("audio_id", None),
            url=url,
        )

    def to_dict(self):
        """
        Convert TranscriptItem to dictionary

        Returns:
            dict: Dictionary representation of TranscriptItem
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "year": self.year,
            "category": self.category,
            "date": self.date,
            "content": self.content,
            "related_video_id": self.related_video_id,
            "related_audio_id": self.related_audio_id,
            "url": self.url,
        }
