"""
Database module for tracking transcript processing status.
Maintains a record of transcripts, their processing status, and upload history.
"""

import os
import logging
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    inspect,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Set up directory paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logs_dir = os.path.join(base_dir, "data", "logs")
db_dir = os.path.join(base_dir, "data", "db")

# Create directories if they don't exist
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(db_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "transcript_db.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("transcript_db")

# Database setup
DB_PATH = os.path.join(db_dir, "transcripts.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Transcript(Base):
    """Model for transcript records in the database."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    year = Column(String, nullable=False)
    category = Column(String, nullable=False)
    session_name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    file_size = Column(Float, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False)
    uploaded = Column(Boolean, default=False)
    upload_path = Column(String, nullable=True)
    upload_date = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Transcript(path='{self.file_path}', processed={self.processed}, uploaded={self.uploaded})>"


def init_db():
    """Initialize the database if it doesn't exist."""
    if not os.path.exists(DB_PATH) or not inspect(engine).has_table(
        Transcript.__tablename__
    ):
        logger.info(f"Creating transcript database at {DB_PATH}")
        Base.metadata.create_all(engine)
    else:
        logger.info(f"Using existing transcript database at {DB_PATH}")


def get_transcript_by_path(file_path):
    """Get a transcript record by its file path."""
    session = Session()
    try:
        return session.query(Transcript).filter_by(file_path=file_path).first()
    finally:
        session.close()


def add_transcript(
    year,
    category,
    session_name,
    file_name,
    file_path,
    file_size=None,
    last_modified=None,
):
    """Add a new transcript to the database."""
    session = Session()
    try:
        # Check if transcript already exists
        existing = session.query(Transcript).filter_by(file_path=file_path).first()
        if existing:
            logger.debug(f"Transcript already exists: {file_path}")
            return existing

        # Create new transcript record
        transcript = Transcript(
            year=year,
            category=category,
            session_name=session_name,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            last_modified=last_modified,
            processed=False,
            uploaded=False,
        )
        session.add(transcript)
        session.commit()
        logger.info(f"Added new transcript: {file_path}")
        return transcript
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding transcript {file_path}: {e}")
        raise
    finally:
        session.close()


def update_transcript_status(
    file_path, processed=None, uploaded=None, upload_path=None, error_message=None
):
    """Update the status of a transcript."""
    session = Session()
    try:
        transcript = session.query(Transcript).filter_by(file_path=file_path).first()
        if not transcript:
            logger.warning(f"Transcript not found for update: {file_path}")
            return None

        if processed is not None:
            transcript.processed = processed

        if uploaded is not None:
            transcript.uploaded = uploaded
            if uploaded:
                transcript.upload_date = datetime.now()

        if upload_path is not None:
            transcript.upload_path = upload_path

        if error_message is not None:
            transcript.error_message = error_message

        session.commit()
        logger.info(
            f"Updated transcript status: {file_path} (processed={processed}, uploaded={uploaded})"
        )
        return transcript
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating transcript {file_path}: {e}")
        raise
    finally:
        session.close()


def get_unprocessed_transcripts():
    """Get all transcripts that haven't been processed yet."""
    session = Session()
    try:
        return session.query(Transcript).filter_by(processed=False).all()
    finally:
        session.close()


def get_processed_not_uploaded_transcripts():
    """Get all transcripts that have been processed but not uploaded."""
    session = Session()
    try:
        return session.query(Transcript).filter_by(processed=True, uploaded=False).all()
    finally:
        session.close()


def get_all_transcripts():
    """Get all transcript records."""
    session = Session()
    try:
        return session.query(Transcript).all()
    finally:
        session.close()


# Initialize the database when this module is imported
init_db()
