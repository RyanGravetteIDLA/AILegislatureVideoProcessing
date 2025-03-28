#!/usr/bin/env python3
"""
Google Cloud Storage module for storing and retrieving media files.
Provides an alternative to the drive_storage module for cloud storage.
"""

import os
import logging
import mimetypes
from datetime import datetime
from google.cloud import storage
from google.cloud.exceptions import NotFound

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import our unified secrets manager
try:
    from src.secrets_manager import get_cloud_storage_settings, get_service_account_content
    secrets_manager_available = True
except ImportError:
    secrets_manager_available = False

# Set up directory paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logs_dir = os.path.join(base_dir, 'data', 'logs')

# Create directory if it doesn't exist
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'cloud_storage.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('cloud_storage')

class GoogleCloudStorage:
    """
    Handles Google Cloud Storage operations for media files.
    
    This class provides methods to upload, download, and manage media files
    in Google Cloud Storage.
    """
    
    def __init__(self, bucket_name, credentials_path=None):
        """
        Initialize the Google Cloud Storage client.
        
        Args:
            bucket_name (str): The name of the GCS bucket to use
            credentials_path (str, optional): Path to the service account credentials file.
                If None, will use application default credentials.
        """
        self.bucket_name = bucket_name
        
        # Initialize GCS client with credentials if provided
        if credentials_path and os.path.exists(credentials_path):
            self.client = storage.Client.from_service_account_json(credentials_path)
            logger.info(f"Using GCS credentials from {credentials_path}")
        else:
            # Use application default credentials
            self.client = storage.Client()
            logger.info("Using application default credentials for GCS")
        
        # Get the bucket reference without checking existence
        # This avoids requiring storage.buckets.get permission
        self.bucket = self.client.bucket(bucket_name)
        logger.info(f"Created reference to GCS bucket: {bucket_name}")
        
        # We know the bucket exists from our tests, so we'll skip the existence check
        # that would require storage.buckets.get permission
    
    def upload_file(self, local_path, remote_path=None, make_public=False, content_type=None):
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            local_path (str): Local path to the file to upload
            remote_path (str, optional): Remote path within the bucket. 
                If None, uses the filename from local_path.
            make_public (bool): Whether to make the file publicly accessible
            content_type (str, optional): Content type of the file. 
                If None, will be detected from the file extension.
                
        Returns:
            str: Public URL or cloud storage path of the uploaded file
        """
        if not os.path.exists(local_path):
            logger.error(f"File not found: {local_path}")
            return None
        
        # If remote_path is not specified, use the filename from local_path
        if not remote_path:
            remote_path = os.path.basename(local_path)
        
        # Create a blob (object) in the bucket
        blob = self.bucket.blob(remote_path)
        
        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type:
                blob.content_type = content_type
        
        try:
            # Start upload
            file_size = os.path.getsize(local_path)
            logger.info(f"Uploading {local_path} to gs://{self.bucket_name}/{remote_path} ({file_size/1024/1024:.2f} MB)")
            
            # Upload the file
            blob.upload_from_filename(local_path)
            
            # Make public if requested
            if make_public:
                blob.make_public()
                public_url = blob.public_url
                logger.info(f"File uploaded and made public: {public_url}")
                return public_url
            else:
                gs_path = f"gs://{self.bucket_name}/{remote_path}"
                logger.info(f"File uploaded: {gs_path}")
                return gs_path
        
        except Exception as e:
            logger.error(f"Error uploading file {local_path}: {e}")
            return None
    
    def download_file(self, remote_path, local_path):
        """
        Download a file from Google Cloud Storage.
        
        Args:
            remote_path (str): Remote path within the bucket
            local_path (str): Local path to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get the blob
            blob = self.bucket.blob(remote_path)
            
            # Skip existence check as it requires additional permissions
            # We'll just try to download and catch any errors
            
            # Download the file
            logger.info(f"Downloading gs://{self.bucket_name}/{remote_path} to {local_path}")
            blob.download_to_filename(local_path)
            logger.info(f"File downloaded: {local_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error downloading file {remote_path}: {e}")
            return False
    
    def list_files(self, prefix=None, delimiter=None):
        """
        List files in the bucket.
        
        Args:
            prefix (str, optional): Filter results to objects whose names begin with this prefix
            delimiter (str, optional): Delimiter to use (e.g., '/' for directory-like listing)
            
        Returns:
            list: List of blob objects
        """
        try:
            blobs = self.client.list_blobs(
                self.bucket_name, 
                prefix=prefix, 
                delimiter=delimiter
            )
            return list(blobs)
        
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def delete_file(self, remote_path):
        """
        Delete a file from Google Cloud Storage.
        
        Args:
            remote_path (str): Remote path within the bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(remote_path)
            
            # Skip existence check as it requires additional permissions
            # We'll just try to delete and catch any errors
            
            # Delete the blob
            blob.delete()
            logger.info(f"File deleted: gs://{self.bucket_name}/{remote_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting file {remote_path}: {e}")
            return False
    
    def get_signed_url(self, remote_path, expiration=3600):
        """
        Generate a signed URL for temporary access to a file.
        
        Args:
            remote_path (str): Remote path within the bucket
            expiration (int): URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Signed URL or None if generation fails
        """
        try:
            blob = self.bucket.blob(remote_path)
            
            # Skip existence check as it requires additional permissions
            # We'll just try to generate the URL and catch any errors
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(seconds=expiration),
                method="GET"
            )
            
            logger.info(f"Generated signed URL for {remote_path} (expires in {expiration} seconds)")
            return url
        
        except Exception as e:
            logger.error(f"Error generating signed URL for {remote_path}: {e}")
            return None

def get_default_gcs_client():
    """
    Get the default GCS client using secrets manager or environment variables.
    
    Returns:
        GoogleCloudStorage: A configured GCS client instance
    """
    # Try to get settings from secrets manager
    if secrets_manager_available:
        try:
            cloud_settings = get_cloud_storage_settings()
            bucket_name = cloud_settings.get('bucket_name')
            
            # Try to get service account content from secrets manager
            sa_content = get_service_account_content('gcs')
            
            if sa_content and bucket_name:
                # Create a temporary file for the service account
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    json.dump(sa_content, temp_file)
                    credentials_path = temp_file.name
                    
                # Create the client with these credentials
                client = GoogleCloudStorage(bucket_name, credentials_path)
                
                # Clean up the temporary file
                os.unlink(credentials_path)
                return client
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client from secrets manager: {e}")
    
    # Fall back to environment variables
    bucket_name = os.environ.get('GCS_BUCKET_NAME', 'legislativevideoreviewswithai.firebasestorage.app')
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    # If credentials not set, try to find the credential file
    if not credentials_path:
        possible_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'credentials', 'legislativevideoreviewswithai-80ed70b021b5.json')
        if os.path.exists(possible_path):
            credentials_path = possible_path
            logger.info(f"Using credentials file: {credentials_path}")
    
    return GoogleCloudStorage(bucket_name, credentials_path)


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Cloud Storage CLI')
    parser.add_argument('--bucket', default=os.environ.get('GCS_BUCKET_NAME', 'idaho-legislature-media'),
                        help='GCS bucket name')
    parser.add_argument('--credentials', default=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                        help='Path to service account credentials JSON file')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a file')
    upload_parser.add_argument('local_path', help='Local file path')
    upload_parser.add_argument('--remote-path', help='Remote file path (default: basename of local path)')
    upload_parser.add_argument('--public', action='store_true', help='Make the file publicly accessible')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download a file')
    download_parser.add_argument('remote_path', help='Remote file path')
    download_parser.add_argument('local_path', help='Local file path')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List files')
    list_parser.add_argument('--prefix', help='Filter by prefix')
    list_parser.add_argument('--delimiter', help='Delimiter (e.g., "/" for directory-like listing)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a file')
    delete_parser.add_argument('remote_path', help='Remote file path')
    
    # URL command
    url_parser = subparsers.add_parser('url', help='Generate signed URL')
    url_parser.add_argument('remote_path', help='Remote file path')
    url_parser.add_argument('--expiration', type=int, default=3600, help='URL expiration time in seconds')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        exit(1)
    
    # Initialize GCS client
    gcs = GoogleCloudStorage(args.bucket, args.credentials)
    
    # Execute command
    if args.command == 'upload':
        result = gcs.upload_file(args.local_path, args.remote_path, args.public)
        if result:
            print(f"Uploaded: {result}")
        else:
            print("Upload failed")
    
    elif args.command == 'download':
        success = gcs.download_file(args.remote_path, args.local_path)
        if success:
            print(f"Downloaded to: {args.local_path}")
        else:
            print("Download failed")
    
    elif args.command == 'list':
        blobs = gcs.list_files(args.prefix, args.delimiter)
        for blob in blobs:
            size_mb = blob.size / 1024 / 1024 if hasattr(blob, 'size') else 0
            print(f"{blob.name} ({size_mb:.2f} MB)")
    
    elif args.command == 'delete':
        success = gcs.delete_file(args.remote_path)
        if success:
            print(f"Deleted: {args.remote_path}")
        else:
            print("Delete failed")
    
    elif args.command == 'url':
        url = gcs.get_signed_url(args.remote_path, args.expiration)
        if url:
            print(f"Signed URL (expires in {args.expiration} seconds):")
            print(url)
        else:
            print("Failed to generate URL")