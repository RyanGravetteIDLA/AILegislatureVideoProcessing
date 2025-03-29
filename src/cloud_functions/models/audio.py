"""
Audio data models for the Idaho Legislature Media Portal API.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioItem:
    """
    Model for audio items

    Attributes:
        id: Unique identifier for the audio
        title: Title of the audio
        description: Description of the audio
        year: Year the audio was recorded
        category: Category of the audio (e.g., House Chambers)
        date: Date the audio was recorded or uploaded
        url: URL to access the audio
        duration: Duration of the audio
    """

    id: str
    title: str
    year: str
    category: str
    url: str
    description: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[str] = None

    @classmethod
    def from_firestore(cls, doc_id, doc_data):
        """
        Create an AudioItem from Firestore document data

        Args:
            doc_id: The Firestore document ID
            doc_data: The Firestore document data

        Returns:
            AudioItem: A new AudioItem instance
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
            duration=doc_data.get("duration", "00:00:00"),
            url=url,
        )

    def to_dict(self):
        """
        Convert AudioItem to dictionary

        Returns:
            dict: Dictionary representation of AudioItem
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "year": self.year,
            "category": self.category,
            "date": self.date,
            "duration": self.duration,
            "url": self.url,
        }
