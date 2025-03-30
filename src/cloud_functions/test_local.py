#!/usr/bin/env python3
"""
Test the microservices locally.
This script simulates Flask requests to test the Cloud Function locally.
"""

import json
import sys
from datetime import datetime
from main import api_handler


class MockRequest:
    """Mock Flask request object"""

    def __init__(self, method="GET", path="/", args=None, json_data=None):
        self.method = method
        self.path = path
        self.args = args or {}
        self._json = json_data
        self.timestamp = datetime.now().isoformat()

    def get_json(self, silent=False):
        """Mock get_json method"""
        return self._json


def print_result(result):
    """Print the result of a request"""
    if isinstance(result, tuple) and len(result) >= 3:
        response, status_code, headers = result

        print(f"Status: {status_code}")
        print("Headers:")
        for k, v in headers.items():
            print(f"  {k}: {v}")

        print("\nResponse:")
        if hasattr(response, "get_data"):
            # Flask Response object
            data = response.get_data(as_text=True)
            try:
                parsed = json.loads(data)
                print(json.dumps(parsed, indent=2))
            except:
                print(data)
        else:
            # JSON data
            print(json.dumps(response.json, indent=2))
    else:
        print(result)


def test_endpoint(method, path, args=None, json_data=None):
    """Test an endpoint"""
    print(f"\n{'=' * 50}")
    print(f"Testing: {method} {path}")
    if args:
        print(f"Args: {args}")
    if json_data:
        print(f"JSON: {json_data}")
    print(f"{'-' * 50}")

    # Create request
    request = MockRequest(method, path, args, json_data)

    # Call the handler
    result = api_handler(request)

    # Print result
    print_result(result)


def main():
    """Main function"""
    print("Testing Idaho Legislature Media Portal API")

    # Test root endpoint
    test_endpoint("GET", "/")

    # Test health endpoint
    test_endpoint("GET", "/api/health")

    # Test videos endpoint
    test_endpoint("GET", "/api/videos")

    # Test videos endpoint with filters
    test_endpoint("GET", "/api/videos", {"year": "2025"})

    # Test video by ID endpoint
    test_endpoint("GET", "/api/videos/mock1")

    # Test unknown endpoint
    test_endpoint("GET", "/api/unknown")

    # Test CORS preflight
    test_endpoint("OPTIONS", "/api/videos")

    # Test direct function call with data
    test_endpoint("POST", "/", None, {"path": "/api/health"})


if __name__ == "__main__":
    main()
