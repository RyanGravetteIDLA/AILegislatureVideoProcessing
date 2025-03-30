"""
Unit tests for the GoogleCloudStorage class.
These tests use mocks to avoid real Cloud Storage connections.
"""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch


class TestGoogleCloudStorage:
    @pytest.fixture
    def mock_storage_client(self):
        """Create a mock Storage client."""
        with patch("google.cloud.storage.Client") as mock_client:
            # Mock the client and its methods
            instance = mock_client.return_value

            # Mock bucket
            mock_bucket = MagicMock()
            instance.bucket.return_value = mock_bucket

            # Mock blob
            mock_blob = MagicMock()
            mock_bucket.blob.return_value = mock_blob

            # Configure mock blob methods
            mock_blob.exists.return_value = False
            mock_blob.public_url = (
                "https://storage.googleapis.com/mock-bucket/path/to/file.txt"
            )
            mock_blob.size = 1024 * 1024  # 1 MB

            # Configure mock list_blobs
            mock_bucket.list_blobs.return_value = [mock_blob]

            yield instance, mock_bucket, mock_blob

    @patch("src.cloud_storage.get_default_gcs_client")
    def test_upload_file(self, mock_get_client, mock_storage_client):
        """Test the upload_file method."""
        from src.cloud_storage import GoogleCloudStorage

        # Unpack the mock objects
        mock_client, mock_bucket, mock_blob = mock_storage_client

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(b"Test content")
            temp_path = temp.name

        try:
            # Create GoogleCloudStorage instance
            gcs = GoogleCloudStorage("mock-bucket")
            gcs.client = mock_client
            gcs.bucket = mock_bucket

            # Test file upload
            remote_path = "test/path/file.txt"
            result = gcs.upload_file(temp_path, remote_path)

            # Verify the blob was created
            mock_bucket.blob.assert_called_with(remote_path)

            # Verify the file was uploaded
            mock_blob.upload_from_filename.assert_called_with(temp_path)

            # Verify non-public URL is returned
            assert result == f"gs://{gcs.bucket_name}/{remote_path}"

            # Test public file upload
            mock_blob.reset_mock()
            result = gcs.upload_file(temp_path, remote_path, make_public=True)

            # Verify the file was made public
            mock_blob.make_public.assert_called_once()

            # Verify public URL is returned
            assert result == mock_blob.public_url

        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    @patch("src.cloud_storage.get_default_gcs_client")
    def test_download_file(self, mock_get_client, mock_storage_client):
        """Test the download_file method."""
        from src.cloud_storage import GoogleCloudStorage

        # Unpack the mock objects
        mock_client, mock_bucket, mock_blob = mock_storage_client

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "downloaded_file.txt")

            # Create GoogleCloudStorage instance
            gcs = GoogleCloudStorage("mock-bucket")
            gcs.client = mock_client
            gcs.bucket = mock_bucket

            # Test file download
            remote_path = "test/path/file.txt"
            result = gcs.download_file(remote_path, local_path)

            # Verify the blob was retrieved
            mock_bucket.blob.assert_called_with(remote_path)

            # Verify the file was downloaded
            mock_blob.download_to_filename.assert_called_with(local_path)

            # Verify success result
            assert result is True

    @patch("src.cloud_storage.get_default_gcs_client")
    def test_list_files(self, mock_get_client, mock_storage_client):
        """Test the list_files method."""
        from src.cloud_storage import GoogleCloudStorage

        # Unpack the mock objects
        mock_client, mock_bucket, _ = mock_storage_client

        # Create GoogleCloudStorage instance
        gcs = GoogleCloudStorage("mock-bucket")
        gcs.client = mock_client

        # Test listing files
        result = gcs.list_files(prefix="test/path")

        # Verify the list_blobs was called with prefix
        mock_client.list_blobs.assert_called_once()

        # Verify a list is returned
        assert isinstance(result, list)

    @patch("src.cloud_storage.get_default_gcs_client")
    def test_delete_file(self, mock_get_client, mock_storage_client):
        """Test the delete_file method."""
        from src.cloud_storage import GoogleCloudStorage

        # Unpack the mock objects
        mock_client, mock_bucket, mock_blob = mock_storage_client

        # Create GoogleCloudStorage instance
        gcs = GoogleCloudStorage("mock-bucket")
        gcs.client = mock_client
        gcs.bucket = mock_bucket

        # Test file deletion
        remote_path = "test/path/file.txt"
        result = gcs.delete_file(remote_path)

        # Verify the blob was retrieved
        mock_bucket.blob.assert_called_with(remote_path)

        # Verify the file was deleted
        mock_blob.delete.assert_called_once()

        # Verify success result
        assert result is True

    @patch("src.cloud_storage.get_default_gcs_client")
    def test_get_signed_url(self, mock_get_client, mock_storage_client):
        """Test the get_signed_url method."""
        from src.cloud_storage import GoogleCloudStorage
        import datetime

        # Unpack the mock objects
        mock_client, mock_bucket, mock_blob = mock_storage_client

        # Configure mock blob to return a signed URL
        mock_blob.generate_signed_url.return_value = (
            "https://signed-url.example.com/file.txt"
        )

        # Create GoogleCloudStorage instance
        gcs = GoogleCloudStorage("mock-bucket")
        gcs.client = mock_client
        gcs.bucket = mock_bucket

        # Test generating a signed URL
        remote_path = "test/path/file.txt"
        result = gcs.get_signed_url(remote_path, expiration=3600)

        # Verify the blob was retrieved
        mock_bucket.blob.assert_called_with(remote_path)

        # Verify the signed URL was generated
        mock_blob.generate_signed_url.assert_called_once()

        # Verify correct URL is returned
        assert result == "https://signed-url.example.com/file.txt"
