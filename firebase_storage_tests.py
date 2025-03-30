#!/usr/bin/env python3
"""
Firebase Storage Test Script

This script validates the Firebase Storage structure and tests key storage operations.
It verifies our understanding of how media files are organized and accessed.

Run this script using:
    python firebase_storage_tests.py
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Add project root to path for imports
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("firebase_storage_tests")

# Try to import Firebase Storage modules
try:
    from src.cloud_storage import GoogleCloudStorage, get_default_gcs_client
    modules_imported = True
except ImportError as e:
    logger.error(f"Error importing Firebase Storage modules: {e}")
    modules_imported = False
    print(f"Error importing Firebase Storage modules: {e}")
    print("Make sure you're running this script from the project root.")
    sys.exit(1)


class FirebaseStorageTests:
    """Tests for validating the Firebase Storage structure"""

    def __init__(self):
        """Initialize the test class and connect to Firebase Storage"""
        self.results = {
            "test_results": {},
            "bucket_info": {},
            "file_structure": {},
            "file_samples": {},
            "media_types": {},
            "storage_paths": {},
            "statistics": {},
        }
        
        # Connect to Firebase Storage
        try:
            self.gcs = get_default_gcs_client()
            logger.info(f"Connected to Firebase Storage bucket: {self.gcs.bucket_name}")
            self.results["test_results"]["storage_connection"] = True
            self.results["bucket_info"]["name"] = self.gcs.bucket_name
        except Exception as e:
            logger.error(f"Failed to connect to Firebase Storage: {e}")
            self.results["test_results"]["storage_connection"] = False
            raise

    def run_all_tests(self):
        """Run all tests and return results"""
        self.test_bucket_access()
        self.analyze_file_structure()
        self.sample_files_by_type()
        self.analyze_path_patterns()
        self.get_storage_statistics()
        return self.results

    def test_bucket_access(self):
        """Test basic access to the storage bucket"""
        try:
            # Try to list files in the bucket (with a small limit)
            blobs = list(self.gcs.bucket.list_blobs(max_results=5))
            self.results["test_results"]["bucket_listing"] = True
            self.results["bucket_info"]["sample_files"] = [blob.name for blob in blobs]
            
            # Get bucket metadata
            bucket = self.gcs.client.get_bucket(self.gcs.bucket_name)
            self.results["bucket_info"]["location"] = bucket.location
            self.results["bucket_info"]["storage_class"] = bucket.storage_class
            self.results["bucket_info"]["created"] = bucket.time_created.isoformat() if bucket.time_created else None
            
            logger.info(f"Successfully accessed bucket: {self.gcs.bucket_name}")
        except Exception as e:
            logger.error(f"Error accessing bucket: {e}")
            self.results["test_results"]["bucket_listing"] = False

    def analyze_file_structure(self):
        """Analyze the file structure in the bucket"""
        try:
            # First list files in the root to understand top-level organization
            blobs = list(self.gcs.bucket.list_blobs(delimiter='/'))
            
            # Check for year-based organization (e.g., 2025/)
            prefixes = list(blobs.prefixes)
            self.results["file_structure"]["root_prefixes"] = list(prefixes)
            
            # Analyze a sample of year-based directories
            year_structure = {}
            for year_prefix in prefixes:
                if year_prefix.strip('/').isdigit():  # Looks like a year
                    # List files within this year
                    year_blobs = list(self.gcs.bucket.list_blobs(prefix=year_prefix, delimiter='/'))
                    year_categories = list(year_blobs.prefixes)
                    
                    # Store the categories found for this year
                    year_structure[year_prefix] = {
                        "categories": [cat.replace(year_prefix, '').strip('/') for cat in year_categories]
                    }
                    
                    # Sample one category to understand session structure
                    if year_categories:
                        sample_category = year_categories[0]
                        category_blobs = list(self.gcs.bucket.list_blobs(prefix=sample_category, delimiter='/'))
                        year_structure[year_prefix]["sample_category"] = {
                            "name": sample_category.replace(year_prefix, '').strip('/'),
                            "sessions": [session.replace(sample_category, '').strip('/') for session in category_blobs.prefixes]
                        }
            
            self.results["file_structure"]["year_structure"] = year_structure
            logger.info(f"Analyzed file structure with {len(prefixes)} root prefixes")
            
        except Exception as e:
            logger.error(f"Error analyzing file structure: {e}")
            self.results["file_structure"]["error"] = str(e)

    def sample_files_by_type(self):
        """Sample files by media type"""
        try:
            # Define media types and their extensions
            media_types = {
                "video": [".mp4"],
                "audio": [".mp3", ".wav"],
                "transcript": [".txt"]
            }
            
            samples = {}
            
            # Get a sample of files for each media type
            for media_type, extensions in media_types.items():
                samples[media_type] = []
                
                # Search for files with each extension
                for ext in extensions:
                    # Use a prefix if known, or search all files
                    if "year_structure" in self.results["file_structure"]:
                        # Look in the first year directory
                        year_prefix = list(self.results["file_structure"]["year_structure"].keys())[0]
                        blobs = list(self.gcs.bucket.list_blobs(prefix=year_prefix))
                    else:
                        blobs = list(self.gcs.bucket.list_blobs())
                    
                    # Filter by extension
                    matching_blobs = [blob for blob in blobs if blob.name.endswith(ext)]
                    
                    # Add sample files (up to 5 per extension)
                    for blob in matching_blobs[:5]:
                        samples[media_type].append({
                            "name": blob.name,
                            "size": blob.size,
                            "updated": blob.updated.isoformat() if blob.updated else None,
                            "content_type": blob.content_type,
                        })
            
            self.results["media_types"]["samples"] = samples
            logger.info(f"Collected samples for {len(samples)} media types")
            
        except Exception as e:
            logger.error(f"Error sampling files by type: {e}")
            self.results["media_types"]["error"] = str(e)

    def analyze_path_patterns(self):
        """Analyze path patterns used in the storage"""
        try:
            path_patterns = {
                "video": [],
                "audio": [],
                "transcript": []
            }
            
            # Use the samples to analyze patterns
            if "samples" in self.results.get("media_types", {}):
                samples = self.results["media_types"]["samples"]
                
                for media_type, files in samples.items():
                    for file in files:
                        path = file["name"]
                        parts = path.split('/')
                        
                        # Extract components
                        pattern = {
                            "full_path": path,
                            "segments": len(parts),
                            "components": {}
                        }
                        
                        # Try to identify components in hierarchical structure
                        if len(parts) >= 3:  # Should have year/category/[session]/filename
                            pattern["components"]["year"] = parts[0] if parts[0].isdigit() else None
                            pattern["components"]["category"] = parts[1] if len(parts) > 1 else None
                            
                            # Session might be more complex due to spaces in folder names
                            if len(parts) > 3:  # Has a session component
                                pattern["components"]["session"] = '/'.join(parts[2:-1])
                            
                            pattern["components"]["filename"] = parts[-1]
                        
                        path_patterns[media_type].append(pattern)
            
            # Identify common patterns
            common_patterns = {
                "video": self._identify_common_pattern(path_patterns["video"]),
                "audio": self._identify_common_pattern(path_patterns["audio"]),
                "transcript": self._identify_common_pattern(path_patterns["transcript"])
            }
            
            self.results["storage_paths"] = {
                "detailed_patterns": path_patterns,
                "common_patterns": common_patterns
            }
            
            logger.info("Analyzed path patterns for media types")
            
        except Exception as e:
            logger.error(f"Error analyzing path patterns: {e}")
            self.results["storage_paths"]["error"] = str(e)

    def _identify_common_pattern(self, patterns):
        """Identify common pattern in a list of path patterns"""
        if not patterns:
            return "No patterns available"
        
        # Count segment lengths
        segment_counts = {}
        for pattern in patterns:
            segments = pattern["segments"]
            segment_counts[segments] = segment_counts.get(segments, 0) + 1
        
        # Find most common segment count
        most_common_count = max(segment_counts.items(), key=lambda x: x[1])[0] if segment_counts else 0
        
        # Analyze patterns with this segment count
        common_patterns = [p for p in patterns if p["segments"] == most_common_count]
        
        if common_patterns:
            # Most common has format: year/category/session/filename
            if most_common_count >= 4:
                return "year/category/session/filename"
            # Most common has format: year/category/filename
            elif most_common_count == 3:
                return "year/category/filename"
            else:
                return f"{most_common_count} segments with no clear pattern"
        else:
            return "No clear pattern identified"

    def get_storage_statistics(self):
        """Get statistics about the storage"""
        try:
            # Count files by type
            stats = {
                "total_files": 0,
                "by_media_type": {
                    "video": 0,
                    "audio": 0,
                    "transcript": 0,
                    "other": 0
                },
                "by_year": defaultdict(int),
                "by_category": defaultdict(int),
                "total_size_bytes": 0
            }
            
            # Collect all blobs
            blobs = list(self.gcs.bucket.list_blobs())
            stats["total_files"] = len(blobs)
            
            for blob in blobs:
                # Update size
                stats["total_size_bytes"] += blob.size if hasattr(blob, 'size') else 0
                
                # Update by media type
                if blob.name.endswith('.mp4'):
                    stats["by_media_type"]["video"] += 1
                elif blob.name.endswith(('.mp3', '.wav')):
                    stats["by_media_type"]["audio"] += 1
                elif blob.name.endswith('.txt'):
                    stats["by_media_type"]["transcript"] += 1
                else:
                    stats["by_media_type"]["other"] += 1
                
                # Update by year (if year is in path)
                parts = blob.name.split('/')
                if parts and parts[0].isdigit():
                    stats["by_year"][parts[0]] += 1
                
                # Update by category (if path has year/category structure)
                if len(parts) >= 2:
                    stats["by_category"][parts[1]] += 1
            
            # Convert defaultdicts to regular dicts for JSON serialization
            stats["by_year"] = dict(stats["by_year"])
            stats["by_category"] = dict(stats["by_category"])
            
            # Calculate total size in MB and GB
            stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
            stats["total_size_gb"] = round(stats["total_size_bytes"] / (1024 * 1024 * 1024), 2)
            
            self.results["statistics"] = stats
            logger.info(f"Collected statistics on {stats['total_files']} files")
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            self.results["statistics"]["error"] = str(e)

    def test_url_generation(self):
        """Test URL generation for files"""
        try:
            url_tests = {
                "public_url": {},
                "signed_url": {}
            }
            
            # Get a sample file to test with
            if "samples" in self.results.get("media_types", {}) and self.results["media_types"]["samples"].get("video"):
                sample_path = self.results["media_types"]["samples"]["video"][0]["name"]
                
                # Test public URL
                blob = self.gcs.bucket.blob(sample_path)
                url_tests["public_url"]["path"] = sample_path
                url_tests["public_url"]["url"] = blob.public_url
                
                # Test signed URL
                try:
                    signed_url = self.gcs.get_signed_url(sample_path, expiration=3600)
                    url_tests["signed_url"]["path"] = sample_path
                    url_tests["signed_url"]["url"] = signed_url
                    url_tests["signed_url"]["expiration"] = "1 hour"
                except Exception as e:
                    url_tests["signed_url"]["error"] = str(e)
            
            self.results["url_generation"] = url_tests
            logger.info("Tested URL generation")
            
        except Exception as e:
            logger.error(f"Error testing URL generation: {e}")
            self.results["url_generation"] = {"error": str(e)}

    def save_results(self, filename="firebase_storage_analysis.json"):
        """Save test results to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False


def main():
    """Main function to run the tests"""
    try:
        # Print environment information
        print("Current directory:", os.getcwd())
        print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "Not set"))
        
        # Check for service account file
        credentials_path = os.path.join(base_dir, "credentials", "legislativevideoreviewswithai-80ed70b021b5.json")
        if os.path.exists(credentials_path):
            print(f"Service account file found at: {credentials_path}")
            # Set the environment variable if not already set
            if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                print(f"Set GOOGLE_APPLICATION_CREDENTIALS to {credentials_path}")
        else:
            print(f"Service account file not found at: {credentials_path}")
            
        # Initialize the tests
        print("\nInitializing Firebase Storage tests...")
        tests = FirebaseStorageTests()
        results = tests.run_all_tests()
        tests.save_results()
        
        # Print a summary of the results
        print("\n=== FIREBASE STORAGE TEST RESULTS ===\n")
        
        # Connection status
        if results["test_results"].get("storage_connection", False):
            print(f"✅ Successfully connected to Firebase Storage bucket: {results['bucket_info']['name']}")
        else:
            print("❌ Failed to connect to Firebase Storage")
        
        # File statistics
        if "error" not in results["statistics"]:
            print("\nStorage Statistics:")
            stats = results["statistics"]
            print(f"  Total files: {stats.get('total_files', 0)}")
            print(f"  Total size: {stats.get('total_size_mb', 0)} MB ({stats.get('total_size_gb', 0)} GB)")
            
            media_types = stats.get("by_media_type", {})
            print(f"  Videos: {media_types.get('video', 0)}")
            print(f"  Audio: {media_types.get('audio', 0)}")
            print(f"  Transcripts: {media_types.get('transcript', 0)}")
            print(f"  Other: {media_types.get('other', 0)}")
        
        # File organization
        if "common_patterns" in results.get("storage_paths", {}):
            print("\nFile Organization:")
            patterns = results["storage_paths"]["common_patterns"]
            print(f"  Video files: {patterns.get('video', 'Unknown')}")
            print(f"  Audio files: {patterns.get('audio', 'Unknown')}")
            print(f"  Transcript files: {patterns.get('transcript', 'Unknown')}")
        
        # Years and categories
        if "by_year" in results.get("statistics", {}):
            print("\nYears found in storage:")
            for year, count in results["statistics"]["by_year"].items():
                print(f"  {year}: {count} files")
        
        if "by_category" in results.get("statistics", {}):
            print("\nCategories found in storage:")
            for category, count in results["statistics"]["by_category"].items():
                print(f"  {category}: {count} files")
        
        print("\nDetailed results saved to firebase_storage_analysis.json")
        
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()