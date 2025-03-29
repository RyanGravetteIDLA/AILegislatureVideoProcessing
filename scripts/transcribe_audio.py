#!/usr/bin/env python3
"""
Transcribe audio files using Google's Gemini API.

This script processes audio files from downloaded legislature sessions
and transcribes them using Google's Gemini multimodal model.
"""

import os
import sys
import argparse
import json
import glob
import time
from pathlib import Path
import google.generativeai as genai
from pydub import AudioSegment

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the centralized secrets manager
from src.secrets_manager import get_gemini_api_key


class AudioTranscriber:
    """Class to transcribe audio files using Google's Gemini API."""

    def __init__(self, api_key=None, model_name="gemini-2.0-flash"):
        """
        Initialize the transcriber with API key and model settings.

        Args:
            api_key (str, optional): Google API key with Gemini API access. If None, will try to retrieve from keychain.
            model_name (str, optional): Gemini model to use. Defaults to "gemini-2.0-flash".
        """
        # If API key is not provided, try to get it from the keychain
        if not api_key:
            api_key = get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "API key is required. Either provide it directly or store it using secrets_manager.py"
                )

        # Configure the Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        # Log which model we're using
        print(f"Using Gemini model: {model_name}")

        # Audio processing settings
        self.segment_length_ms = (
            9 * 60 * 1000
        )  # 9 minutes in milliseconds (under Gemini's 10 min limit)
        self.supported_formats = [".mp3", ".wav", ".m4a"]

    def split_audio(self, audio_path):
        """
        Split long audio files into chunks for processing.

        Args:
            audio_path (str): Path to the audio file

        Returns:
            list: List of temporary file paths for the audio segments
        """
        # Determine the audio format
        file_ext = os.path.splitext(audio_path)[1].lower()
        if file_ext not in self.supported_formats:
            raise ValueError(
                f"Unsupported audio format: {file_ext}. Supported formats: {self.supported_formats}"
            )

        # Load the audio file
        audio = AudioSegment.from_file(audio_path)

        # Split into segments of 9 minutes each (Gemini has a 10-minute limit)
        segments = []
        temp_dir = os.path.join(os.path.dirname(audio_path), "temp_segments")

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Calculate number of segments needed
        num_segments = (len(audio) // self.segment_length_ms) + (
            1 if len(audio) % self.segment_length_ms > 0 else 0
        )

        for i in range(num_segments):
            start = i * self.segment_length_ms
            end = min((i + 1) * self.segment_length_ms, len(audio))

            segment = audio[start:end]
            temp_path = os.path.join(temp_dir, f"segment_{i+1:03d}{file_ext}")
            segment.export(temp_path, format=file_ext.lstrip("."))
            segments.append(temp_path)

        return segments, temp_dir

    def transcribe_segment(self, segment_path):
        """
        Transcribe a single audio segment using Gemini.

        Args:
            segment_path (str): Path to the audio segment

        Returns:
            str: Transcribed text
        """
        print(f"Transcribing segment: {segment_path}")

        try:
            # Load audio as binary data
            with open(segment_path, "rb") as f:
                audio_data = f.read()

            # Request transcription
            prompt = """
            Please transcribe this audio recording from an Idaho Legislature session. 
            Format it as plain text with paragraphs and speaker labels when speakers change.
            Focus on high accuracy of the transcription especially for names, dates, and technical terms.
            Include all spoken content, including any procedural announcements, votes, and discussions.
            For roll calls, just indicate that a roll call happened rather than transcribing every "yes" or "here".
            """

            response = self.model.generate_content(
                [prompt, {"mime_type": "audio/mpeg", "data": audio_data}]
            )

            # Process response
            return response.text

        except Exception as e:
            print(f"Error transcribing segment {segment_path}: {e}")
            return f"[Transcription error: {e}]"

    def transcribe_audio(self, audio_path):
        """
        Transcribe a full audio file, splitting if necessary.

        Args:
            audio_path (str): Path to the audio file

        Returns:
            str: Full transcription
        """
        print(f"Processing audio file: {audio_path}")

        try:
            # Split the audio into manageable segments
            segments, temp_dir = self.split_audio(audio_path)

            # Transcribe each segment
            transcriptions = []
            for segment in segments:
                transcription = self.transcribe_segment(segment)
                transcriptions.append(transcription)

                # Add a small delay to avoid rate limiting
                time.sleep(2)

            # Combine all transcriptions
            full_transcription = "\n\n".join(transcriptions)

            # Clean up temporary files
            for segment in segments:
                if os.path.exists(segment):
                    os.remove(segment)

            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

            return full_transcription

        except Exception as e:
            print(f"Error processing audio file {audio_path}: {e}")
            return f"[Transcription failed: {e}]"

    def save_transcription(self, audio_path, transcription):
        """
        Save the transcription to a text file.

        Args:
            audio_path (str): Path to the original audio file
            transcription (str): Transcribed text

        Returns:
            str: Path to the saved transcription file
        """
        # Create path for the transcription
        base_path = os.path.splitext(audio_path)[0]
        transcription_path = f"{base_path}_transcription.txt"

        # Save the transcription
        with open(transcription_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        return transcription_path


def process_directory(
    api_key, directory, recursive=False, model_name="gemini-2.0-flash"
):
    """
    Process all audio files in a directory.

    Args:
        api_key (str): Google API key
        directory (str): Directory to process
        recursive (bool, optional): Process subdirectories. Defaults to False.
        model_name (str, optional): Gemini model to use. Defaults to "gemini-2.0-flash".
    """
    transcriber = AudioTranscriber(api_key, model_name)

    # Get all audio files
    pattern = os.path.join(directory, "**" if recursive else "", "*.[mw][ap][v3]")
    audio_files = glob.glob(pattern, recursive=recursive)

    print(f"Found {len(audio_files)} audio files to process")

    for audio_file in audio_files:
        # Check if transcription already exists
        base_path = os.path.splitext(audio_file)[0]
        transcription_path = f"{base_path}_transcription.txt"

        if os.path.exists(transcription_path):
            print(f"Skipping {audio_file} - transcription already exists")
            continue

        # Process the file
        print(f"Processing {audio_file}")
        transcription = transcriber.transcribe_audio(audio_file)
        saved_path = transcriber.save_transcription(audio_file, transcription)
        print(f"Saved transcription to {saved_path}")


def process_meeting(api_key, meeting_path, model_name="gemini-2.0-flash"):
    """
    Process a specific meeting directory.

    Args:
        api_key (str): Google API key
        meeting_path (str): Path to the meeting directory
        model_name (str, optional): Gemini model to use. Defaults to "gemini-2.0-flash".
    """
    # Look for audio directory
    audio_dir = os.path.join(meeting_path, "audio")

    if not os.path.exists(audio_dir):
        print(f"Audio directory not found: {audio_dir}")
        return

    # Process all audio files in the directory
    process_directory(api_key, audio_dir, recursive=False, model_name=model_name)


def main():
    """Main function to parse arguments and transcribe audio files."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Google's Gemini API"
    )
    parser.add_argument(
        "--api-key",
        help="Google API key with Gemini access (optional if stored in keychain)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model to use for transcription (default: gemini-2.0-flash)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Directory processor
    dir_parser = subparsers.add_parser(
        "directory", help="Process all audio files in a directory"
    )
    dir_parser.add_argument("directory", help="Directory containing audio files")
    dir_parser.add_argument(
        "--recursive", "-r", action="store_true", help="Process subdirectories"
    )

    # Meeting processor
    meeting_parser = subparsers.add_parser("meeting", help="Process a specific meeting")
    meeting_parser.add_argument("meeting_path", help="Path to the meeting directory")

    # Batch processor for all meetings in a year/category
    batch_parser = subparsers.add_parser(
        "batch", help="Process all meetings in a year/category"
    )
    batch_parser.add_argument(
        "--output-dir", default="data/downloads", help="Base output directory"
    )
    batch_parser.add_argument(
        "--year", default="2025", help="Year of meetings to process"
    )
    batch_parser.add_argument(
        "--category", default="House Chambers", help="Category of meetings to process"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get API key from command line or secrets manager
    api_key = args.api_key
    if not api_key:
        api_key = get_gemini_api_key()
        if not api_key:
            print("Error: No API key provided and none found in keychain.")
            print("Either provide an API key with --api-key or store one using:")
            print("python src/secrets_manager.py test --api-keys")
            return

    if args.command == "directory":
        process_directory(
            api_key, args.directory, args.recursive, model_name=args.model
        )

    elif args.command == "meeting":
        process_meeting(api_key, args.meeting_path, model_name=args.model)

    elif args.command == "batch":
        # Process all meetings in a year/category
        meetings_path = os.path.join(args.output_dir, args.year, args.category)
        if not os.path.exists(meetings_path):
            print(f"Meetings directory not found: {meetings_path}")
            return

        # Get all meeting directories
        meeting_dirs = [
            f.path
            for f in os.scandir(meetings_path)
            if f.is_dir() and "Legislative Session Day" in f.name
        ]
        print(f"Found {len(meeting_dirs)} meeting directories to process")

        for meeting_dir in meeting_dirs:
            print(f"\nProcessing meeting: {os.path.basename(meeting_dir)}")
            process_meeting(api_key, meeting_dir, model_name=args.model)


if __name__ == "__main__":
    main()
