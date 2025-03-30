#!/usr/bin/env python3
"""
Ultra-simple Flask application for testing Cloud Run deployment.
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        {
            "status": "ok",
            "message": "Idaho Legislature API Test Server",
            "environment": {
                "PORT": os.environ.get("PORT", "Not set"),
            },
        }
    )


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "message": "Server is running"})


if __name__ == "__main__":
    # Get port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))

    # Run the app, listening on all IPs with the given port
    app.run(host="0.0.0.0", port=port, debug=True)
