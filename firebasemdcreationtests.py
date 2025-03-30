#!/usr/bin/env python3
"""
Firebase Database Architecture Test Script

This script validates assumptions about the Firestore database structure
and generates data that can be used to document the architecture.

Run this script using:
    python firebasemdcreationtests.py
"""

import os
import sys
import logging
import json
from datetime import datetime
from collections import defaultdict

# Add project root to path for imports
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("firestore_tests")

# Import Firestore implementation
try:
    # First, add src to the path
    src_path = os.path.join(base_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Now import using direct imports
    from firestore_db import get_firestore_db, FirestoreDB
    import db_interface
    
    # Try to import the cloud functions implementation if available
    try:
        cloud_functions_path = os.path.join(src_path, 'cloud_functions')
        if cloud_functions_path not in sys.path:
            sys.path.insert(0, cloud_functions_path)
            
        from common.db_service import get_db_interface_instance
        cloud_functions_available = True
    except ImportError:
        cloud_functions_available = False
except ImportError as e:
    print(f"Error importing Firestore modules: {e}")
    print("Make sure you're running this script from the project root.")
    sys.exit(1)


class FirestoreArchitectureTests:
    """Tests for validating the Firestore architecture"""

    def __init__(self):
        """Initialize the test class and connect to Firestore"""
        self.results = {
            "test_results": {},
            "collections": {},
            "sample_documents": {},
            "field_frequencies": {},
            "relationships": {},
            "schema": {},
            "statistics": {},
        }
        
        # Connect to Firestore
        try:
            self.db = get_firestore_db()
            logger.info("Connected to Firestore successfully")
            self.results["test_results"]["firestore_connection"] = True
        except Exception as e:
            logger.error(f"Failed to connect to Firestore: {e}")
            self.results["test_results"]["firestore_connection"] = False
            raise

    def run_all_tests(self):
        """Run all tests and return results"""
        self.test_collection_structure()
        self.sample_documents()
        self.analyze_field_usage()
        self.analyze_relationships()
        self.generate_schema()
        self.get_statistics()
        
        return self.results

    def test_collection_structure(self):
        """Test the structure of collections in Firestore"""
        expected_collections = ["videos", "audio", "transcripts", "other"]
        found_collections = []
        
        try:
            # Attempt to get documents from each collection to verify its existence
            for collection in expected_collections:
                docs = list(self.db.client.collection(collection).limit(1).stream())
                if docs:
                    found_collections.append(collection)
                    self.results["collections"][collection] = {"exists": True, "count": len(docs)}
                else:
                    self.results["collections"][collection] = {"exists": True, "count": 0}
            
            # Check for unexpected collections
            for collection in set(found_collections) - set(expected_collections):
                self.results["collections"][collection] = {"exists": True, "count": 0, "unexpected": True}
            
            self.results["test_results"]["collection_structure"] = {
                "passed": set(found_collections) == set(expected_collections),
                "expected": expected_collections,
                "found": found_collections
            }
            
        except Exception as e:
            logger.error(f"Error testing collection structure: {e}")
            self.results["test_results"]["collection_structure"] = {
                "passed": False,
                "error": str(e)
            }

    def sample_documents(self):
        """Get sample documents from each collection"""
        collections = ["videos", "audio", "transcripts", "other"]
        
        for collection in collections:
            try:
                docs = list(self.db.client.collection(collection).limit(1).stream())
                if docs:
                    doc = docs[0]
                    # Convert timestamps to ISO format for JSON serialization
                    sample_data = doc.to_dict()
                    for key, value in sample_data.items():
                        if isinstance(value, datetime):
                            sample_data[key] = value.isoformat()
                    
                    self.results["sample_documents"][collection] = {
                        "id": doc.id,
                        "data": sample_data
                    }
                else:
                    self.results["sample_documents"][collection] = None
            except Exception as e:
                logger.error(f"Error getting sample document from {collection}: {e}")
                self.results["sample_documents"][collection] = {"error": str(e)}

    def analyze_field_usage(self):
        """Analyze which fields are used in each collection and their frequency"""
        collections = ["videos", "audio", "transcripts", "other"]
        
        for collection in collections:
            try:
                # Get all documents in the collection (with reasonable limit)
                docs = list(self.db.client.collection(collection).limit(1000).stream())
                
                if not docs:
                    self.results["field_frequencies"][collection] = None
                    continue
                
                # Count field frequencies
                field_counter = defaultdict(int)
                total_docs = len(docs)
                
                for doc in docs:
                    data = doc.to_dict()
                    for field in data.keys():
                        field_counter[field] += 1
                
                # Calculate percentages
                field_frequencies = {}
                for field, count in field_counter.items():
                    field_frequencies[field] = {
                        "count": count,
                        "percentage": round((count / total_docs) * 100, 2)
                    }
                
                self.results["field_frequencies"][collection] = {
                    "total_documents": total_docs,
                    "fields": field_frequencies
                }
                
            except Exception as e:
                logger.error(f"Error analyzing field usage in {collection}: {e}")
                self.results["field_frequencies"][collection] = {"error": str(e)}

    def analyze_relationships(self):
        """Analyze relationships between collections"""
        relationship_fields = {
            "videos": ["related_audio_id", "related_transcript_id"],
            "audio": ["related_video_id", "related_transcript_id"],
            "transcripts": ["related_video_id", "related_audio_id"]
        }
        
        for collection, fields in relationship_fields.items():
            try:
                docs = list(self.db.client.collection(collection).limit(1000).stream())
                
                if not docs:
                    self.results["relationships"][collection] = None
                    continue
                
                relationship_stats = {}
                total_docs = len(docs)
                
                for field in fields:
                    # Count documents that have this relationship field populated
                    has_relationship = sum(1 for doc in docs if field in doc.to_dict() and doc.to_dict()[field])
                    
                    relationship_stats[field] = {
                        "count": has_relationship,
                        "percentage": round((has_relationship / total_docs) * 100, 2)
                    }
                
                self.results["relationships"][collection] = {
                    "total_documents": total_docs,
                    "relationships": relationship_stats
                }
                
            except Exception as e:
                logger.error(f"Error analyzing relationships in {collection}: {e}")
                self.results["relationships"][collection] = {"error": str(e)}

    def generate_schema(self):
        """Generate a schema definition for each collection based on sample data"""
        collections = ["videos", "audio", "transcripts", "other"]
        
        for collection in collections:
            try:
                docs = list(self.db.client.collection(collection).limit(20).stream())
                
                if not docs:
                    self.results["schema"][collection] = None
                    continue
                
                # Analyze field types across documents
                field_types = defaultdict(set)
                
                for doc in docs:
                    data = doc.to_dict()
                    for field, value in data.items():
                        if value is None:
                            field_types[field].add("null")
                        elif isinstance(value, bool):
                            field_types[field].add("boolean")
                        elif isinstance(value, int):
                            field_types[field].add("integer")
                        elif isinstance(value, float):
                            field_types[field].add("number")
                        elif isinstance(value, str):
                            field_types[field].add("string")
                        elif isinstance(value, list):
                            field_types[field].add("array")
                        elif isinstance(value, dict):
                            field_types[field].add("object")
                        elif isinstance(value, datetime):
                            field_types[field].add("datetime")
                        else:
                            field_types[field].add(str(type(value)))
                
                # Convert to a more readable schema
                schema = {}
                for field, types in field_types.items():
                    schema[field] = {
                        "types": list(types),
                        "required": all(field in doc.to_dict() for doc in docs)
                    }
                
                self.results["schema"][collection] = schema
                
            except Exception as e:
                logger.error(f"Error generating schema for {collection}: {e}")
                self.results["schema"][collection] = {"error": str(e)}

    def get_statistics(self):
        """Get statistics about the database"""
        try:
            stats = self.db.get_statistics()
            self.results["statistics"] = stats
            
            # Also get filter options
            filters = self.db.get_filter_options()
            self.results["filters"] = filters
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            self.results["statistics"] = {"error": str(e)}

    def save_results(self, filename="firestore_analysis.json"):
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
        print("Python path:", sys.path)
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
        tests = FirestoreArchitectureTests()
        results = tests.run_all_tests()
        tests.save_results()
        
        # Print a summary of the results
        print("\n=== FIRESTORE ARCHITECTURE TEST RESULTS ===\n")
        
        # Connection status
        if results["test_results"].get("firestore_connection", False):
            print("✅ Successfully connected to Firestore")
        else:
            print("❌ Failed to connect to Firestore")
        
        # Collections
        print("\nCollections:")
        for collection, info in results["collections"].items():
            if info.get("exists", False):
                print(f"  ✅ {collection} collection exists")
            else:
                print(f"  ❌ {collection} collection not found")
        
        # Statistics
        if "error" not in results["statistics"]:
            print("\nStatistics:")
            print(f"  Total documents: {results['statistics'].get('total', 0)}")
            print(f"  Videos: {results['statistics'].get('videos', 0)}")
            print(f"  Audio: {results['statistics'].get('audio', 0)}")
            print(f"  Transcripts: {results['statistics'].get('transcripts', 0)}")
            print(f"  Other: {results['statistics'].get('other', 0)}")
        
        # Schema summary
        print("\nSchema analysis:")
        for collection, schema in results["schema"].items():
            if schema and "error" not in schema:
                field_count = len(schema)
                print(f"  {collection}: {field_count} fields identified")
            elif schema is None:
                print(f"  {collection}: No documents found for analysis")
            else:
                print(f"  {collection}: Error during analysis")
        
        print("\nDetailed results saved to firestore_analysis.json")
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()