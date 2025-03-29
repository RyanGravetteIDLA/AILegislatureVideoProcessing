#!/usr/bin/env python3
"""
Minimal Flask API for Cloud Run deployment testing
"""

import os
import logging
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/")
def home():
    logger.info("Root endpoint called")
    return jsonify(
        {
            "message": "Idaho Legislature Media Portal API - Minimal Version",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/health")
def health():
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/api/videos")
def videos():
    logger.info("Videos endpoint called")
    return jsonify(
        [
            {
                "id": "test1",
                "title": "Test Video 1",
                "year": "2025",
                "category": "House Chambers",
                "url": "https://example.com/video1.mp4",
            },
            {
                "id": "test2",
                "title": "Test Video 2",
                "year": "2025",
                "category": "Senate Chambers",
                "url": "https://example.com/video2.mp4",
            },
        ]
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting minimal API on port {port}")
    app.run(host="0.0.0.0", port=port)
