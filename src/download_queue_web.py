#!/usr/bin/env python3
"""
Web interface for the Firebase Download Queue

This script provides a web interface for managing the download queue,
allowing users to add videos to the queue and check status.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from firebase_admin import firestore

# Path constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the download queue
from src.firebase_download_queue import (
    FirebaseDownloadQueue,
    STATUS_PENDING,
    STATUS_PROCESSING,
    STATUS_COMPLETED,
    STATUS_FAILED,
)

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase queue
queue = FirebaseDownloadQueue()


@app.route("/")
def index():
    """Render the main page"""
    # Get queue statistics
    stats = queue.get_queue_stats()

    # Get queue items with pagination
    status = request.args.get("status", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))

    # Get items from Firestore
    items = []

    # Common Firestore query patterns
    query = queue.queue_ref

    # Apply status filter if provided
    if status and status in [
        STATUS_PENDING,
        STATUS_PROCESSING,
        STATUS_COMPLETED,
        STATUS_FAILED,
    ]:
        query = query.where("status", "==", status)

    # Apply sorting - first by status, then by created_at
    query = query.order_by("status").order_by("created_at", direction="DESCENDING")

    # Apply pagination
    # Note: Firestore doesn't have built-in pagination, so we would need to implement cursor-based
    # pagination for a production app. This simple offset is just for demonstration.
    offset = (page - 1) * page_size

    # Execute query
    all_docs = list(query.stream())

    # Simple pagination
    total_items = len(all_docs)
    items = all_docs[offset : offset + page_size]

    # Convert to dictionaries
    items = [
        {
            "id": doc.id,
            "url": doc.get("url"),
            "year": doc.get("year"),
            "month": doc.get("month"),
            "day": doc.get("day"),
            "committee": doc.get("committee"),
            "status": doc.get("status"),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
            "error": doc.get("error", ""),
        }
        for doc in items
    ]

    # Calculate pagination info
    total_pages = (total_items + page_size - 1) // page_size

    return render_template(
        "index.html",
        stats=stats,
        items=items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_items=total_items,
        status_filter=status,
    )


@app.route("/enqueue", methods=["POST"])
def enqueue():
    """Add a video to the download queue"""
    try:
        # Get form data
        year = request.form.get("year")
        month = request.form.get("month")
        day = request.form.get("day")
        committee = request.form.get("committee", "Education")
        code = request.form.get("code", "hedu")
        time = request.form.get("time", "0900AM")
        priority = int(request.form.get("priority", 0))

        # Add metadata if provided
        metadata = None
        metadata_str = request.form.get("metadata", "")
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                return (
                    jsonify({"success": False, "error": "Invalid metadata JSON"}),
                    400,
                )

        # Enqueue the video
        doc_id = queue.enqueue_video(
            year=year,
            month=month,
            day=day,
            committee=committee,
            code=code,
            time=time,
            priority=priority,
            metadata=metadata,
        )

        return jsonify({"success": True, "id": doc_id})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/enqueue_range", methods=["POST"])
def enqueue_range():
    """Add a range of videos to the download queue"""
    try:
        # Get form data
        year = request.form.get("year")
        committee = request.form.get("committee", "Education")
        code = request.form.get("code", "hedu")
        start_month = int(request.form.get("start_month", 1))
        end_month = int(request.form.get("end_month", 12))
        start_day = int(request.form.get("start_day", 1))
        end_day = int(request.form.get("end_day", 31))
        time = request.form.get("time", "0900AM")
        priority = int(request.form.get("priority", 0))

        # Add metadata if provided
        metadata = None
        metadata_str = request.form.get("metadata", "")
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                return (
                    jsonify({"success": False, "error": "Invalid metadata JSON"}),
                    400,
                )

        # Enqueue the range
        doc_ids = queue.enqueue_committee_range(
            year=year,
            committee=committee,
            code=code,
            start_month=start_month,
            end_month=end_month,
            start_day=start_day,
            end_day=end_day,
            time=time,
            priority=priority,
            metadata=metadata,
        )

        return jsonify({"success": True, "count": len(doc_ids)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/process", methods=["POST"])
def process_queue():
    """Process the download queue"""
    try:
        # Get form data
        output_dir = request.form.get("output_dir", "data/downloads")
        limit = int(request.form.get("limit", 10))
        convert_to_audio = (
            request.form.get("convert_to_audio", "true").lower() == "true"
        )

        # Process the queue
        results = queue.process_queue(
            output_dir=output_dir, limit=limit, convert_to_audio=convert_to_audio
        )

        return jsonify({"success": True, "results": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/item/<item_id>", methods=["GET"])
def get_item(item_id):
    """Get a single queue item"""
    try:
        doc = queue.queue_ref.document(item_id).get()

        if not doc.exists:
            return jsonify({"success": False, "error": "Item not found"}), 404

        # Convert to dictionary
        data = doc.to_dict()
        data["id"] = doc.id

        return jsonify({"success": True, "item": data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/item/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete a queue item"""
    try:
        # Get the document
        doc = queue.queue_ref.document(item_id).get()

        if not doc.exists:
            return jsonify({"success": False, "error": "Item not found"}), 404

        # Delete the document
        queue.queue_ref.document(item_id).delete()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/item/<item_id>/retry", methods=["POST"])
def retry_item(item_id):
    """Retry a failed queue item"""
    try:
        # Get the document
        doc = queue.queue_ref.document(item_id).get()

        if not doc.exists:
            return jsonify({"success": False, "error": "Item not found"}), 404

        data = doc.to_dict()
        status = data.get("status")

        if status != STATUS_FAILED:
            return (
                jsonify(
                    {"success": False, "error": "Only failed items can be retried"}
                ),
                400,
            )

        # Update the document
        queue.queue_ref.document(item_id).update(
            {
                "status": STATUS_PENDING,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "retry_count": firestore.Increment(1),
            }
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/item/<item_id>/status", methods=["PUT"])
def update_status(item_id):
    """Update a queue item status"""
    try:
        # Get the document
        doc = queue.queue_ref.document(item_id).get()

        if not doc.exists:
            return jsonify({"success": False, "error": "Item not found"}), 404

        # Get new status
        status = request.json.get("status")

        if status not in [
            STATUS_PENDING,
            STATUS_PROCESSING,
            STATUS_COMPLETED,
            STATUS_FAILED,
        ]:
            return jsonify({"success": False, "error": "Invalid status"}), 400

        # Update the document
        queue.queue_ref.document(item_id).update(
            {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def get_stats():
    """Get download queue statistics"""
    try:
        stats = queue.get_queue_stats()
        return jsonify({"success": True, "stats": stats})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def create_templates():
    """Create the HTML templates for the web interface"""
    # Create the templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    os.makedirs(templates_dir, exist_ok=True)

    # Create the base template
    base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Idaho Legislature Media Download Queue{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 20px; padding-bottom: 20px; }
        .status-pending { background-color: #fff3cd; }
        .status-processing { background-color: #cfe2ff; }
        .status-completed { background-color: #d1e7dd; }
        .status-failed { background-color: #f8d7da; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <div class="container">
        <header class="mb-4">
            <h1>Idaho Legislature Media Download Queue</h1>
        </header>
        
        <main>
            {% block content %}{% endblock %}
        </main>
        
        <footer class="mt-5 pt-3 border-top text-center text-muted">
            <p>&copy; 2025 Idaho Legislature Media Portal</p>
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

    # Create the index template
    index_html = """{% extends "base.html" %}

{% block title %}Idaho Legislature Media Download Queue{% endblock %}

{% block content %}
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h2>Queue Statistics</h2>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col">
                            <div class="card text-white bg-primary">
                                <div class="card-body">
                                    <h5 class="card-title">Total</h5>
                                    <h2 class="card-text">{{ stats.total }}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card text-white bg-warning">
                                <div class="card-body">
                                    <h5 class="card-title">Pending</h5>
                                    <h2 class="card-text">{{ stats.pending }}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card text-white bg-info">
                                <div class="card-body">
                                    <h5 class="card-title">Processing</h5>
                                    <h2 class="card-text">{{ stats.processing }}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card text-white bg-success">
                                <div class="card-body">
                                    <h5 class="card-title">Completed</h5>
                                    <h2 class="card-text">{{ stats.completed }}</h2>
                                </div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card text-white bg-danger">
                                <div class="card-body">
                                    <h5 class="card-title">Failed</h5>
                                    <h2 class="card-text">{{ stats.failed }}</h2>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-4">
            <div class="card mb-4">
                <div class="card-header">
                    <h3>Add Video</h3>
                </div>
                <div class="card-body">
                    <form id="enqueueForm">
                        <div class="mb-3">
                            <label for="year" class="form-label">Year</label>
                            <input type="text" class="form-control" id="year" name="year" value="2025" required>
                        </div>
                        <div class="mb-3">
                            <label for="month" class="form-label">Month (1-12)</label>
                            <input type="number" class="form-control" id="month" name="month" min="1" max="12" value="1" required>
                        </div>
                        <div class="mb-3">
                            <label for="day" class="form-label">Day (1-31)</label>
                            <input type="number" class="form-control" id="day" name="day" min="1" max="31" value="1" required>
                        </div>
                        <div class="mb-3">
                            <label for="committee" class="form-label">Committee</label>
                            <input type="text" class="form-control" id="committee" name="committee" value="Education">
                        </div>
                        <div class="mb-3">
                            <label for="code" class="form-label">Committee Code</label>
                            <input type="text" class="form-control" id="code" name="code" value="hedu">
                        </div>
                        <div class="mb-3">
                            <label for="time" class="form-label">Time</label>
                            <input type="text" class="form-control" id="time" name="time" value="0900AM">
                        </div>
                        <div class="mb-3">
                            <label for="priority" class="form-label">Priority</label>
                            <input type="number" class="form-control" id="priority" name="priority" value="0">
                        </div>
                        <button type="submit" class="btn btn-primary">Add to Queue</button>
                    </form>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <h3>Add Video Range</h3>
                </div>
                <div class="card-body">
                    <form id="enqueueRangeForm">
                        <div class="mb-3">
                            <label for="range_year" class="form-label">Year</label>
                            <input type="text" class="form-control" id="range_year" name="year" value="2025" required>
                        </div>
                        <div class="mb-3">
                            <label for="range_committee" class="form-label">Committee</label>
                            <input type="text" class="form-control" id="range_committee" name="committee" value="Education">
                        </div>
                        <div class="mb-3">
                            <label for="range_code" class="form-label">Committee Code</label>
                            <input type="text" class="form-control" id="range_code" name="code" value="hedu">
                        </div>
                        <div class="row">
                            <div class="col">
                                <div class="mb-3">
                                    <label for="start_month" class="form-label">Start Month</label>
                                    <input type="number" class="form-control" id="start_month" name="start_month" min="1" max="12" value="1">
                                </div>
                            </div>
                            <div class="col">
                                <div class="mb-3">
                                    <label for="end_month" class="form-label">End Month</label>
                                    <input type="number" class="form-control" id="end_month" name="end_month" min="1" max="12" value="12">
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col">
                                <div class="mb-3">
                                    <label for="start_day" class="form-label">Start Day</label>
                                    <input type="number" class="form-control" id="start_day" name="start_day" min="1" max="31" value="1">
                                </div>
                            </div>
                            <div class="col">
                                <div class="mb-3">
                                    <label for="end_day" class="form-label">End Day</label>
                                    <input type="number" class="form-control" id="end_day" name="end_day" min="1" max="31" value="31">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="range_time" class="form-label">Time</label>
                            <input type="text" class="form-control" id="range_time" name="time" value="0900AM">
                        </div>
                        <div class="mb-3">
                            <label for="range_priority" class="form-label">Priority</label>
                            <input type="number" class="form-control" id="range_priority" name="priority" value="0">
                        </div>
                        <button type="submit" class="btn btn-primary">Add Range to Queue</button>
                    </form>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <h3>Process Queue</h3>
                </div>
                <div class="card-body">
                    <form id="processForm">
                        <div class="mb-3">
                            <label for="output_dir" class="form-label">Output Directory</label>
                            <input type="text" class="form-control" id="output_dir" name="output_dir" value="data/downloads">
                        </div>
                        <div class="mb-3">
                            <label for="limit" class="form-label">Limit</label>
                            <input type="number" class="form-control" id="limit" name="limit" min="1" value="10">
                        </div>
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="convert_to_audio" name="convert_to_audio" checked>
                            <label class="form-check-label" for="convert_to_audio">Convert to Audio</label>
                        </div>
                        <button type="submit" class="btn btn-success">Process Queue</button>
                    </form>
                </div>
            </div>
        </div>
        
        <div class="col-md-8">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h3>Queue Items</h3>
                    <div class="d-flex">
                        <div class="dropdown me-2">
                            <button class="btn btn-secondary dropdown-toggle" type="button" id="statusFilterDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                                {% if status_filter %}{{ status_filter }}{% else %}All{% endif %}
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="statusFilterDropdown">
                                <li><a class="dropdown-item" href="{{ url_for('index') }}">All</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('index', status='pending') }}">Pending</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('index', status='processing') }}">Processing</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('index', status='completed') }}">Completed</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('index', status='failed') }}">Failed</a></li>
                            </ul>
                        </div>
                        <button class="btn btn-primary" onclick="location.reload()">Refresh</button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Committee</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% if items %}
                                    {% for item in items %}
                                        <tr class="status-{{ item.status }}">
                                            <td>{{ item.month }}/{{ item.day }}/{{ item.year }}</td>
                                            <td>{{ item.committee }}</td>
                                            <td>{{ item.status }}</td>
                                            <td>{{ item.created_at }}</td>
                                            <td>
                                                <div class="btn-group" role="group">
                                                    <button type="button" class="btn btn-sm btn-info" onclick="viewItem('{{ item.id }}')">View</button>
                                                    {% if item.status == 'failed' %}
                                                        <button type="button" class="btn btn-sm btn-warning" onclick="retryItem('{{ item.id }}')">Retry</button>
                                                    {% endif %}
                                                    <button type="button" class="btn btn-sm btn-danger" onclick="deleteItem('{{ item.id }}')">Delete</button>
                                                </div>
                                            </td>
                                        </tr>
                                    {% endfor %}
                                {% else %}
                                    <tr>
                                        <td colspan="5" class="text-center">No items found</td>
                                    </tr>
                                {% endif %}
                            </tbody>
                        </table>
                    </div>
                    
                    {% if total_pages > 1 %}
                    <nav aria-label="Page navigation">
                        <ul class="pagination justify-content-center">
                            <li class="page-item {% if page == 1 %}disabled{% endif %}">
                                <a class="page-link" href="{{ url_for('index', page=page-1, status=status_filter) }}">Previous</a>
                            </li>
                            
                            {% for p in range(1, total_pages + 1) %}
                                <li class="page-item {% if p == page %}active{% endif %}">
                                    <a class="page-link" href="{{ url_for('index', page=p, status=status_filter) }}">{{ p }}</a>
                                </li>
                            {% endfor %}
                            
                            <li class="page-item {% if page == total_pages %}disabled{% endif %}">
                                <a class="page-link" href="{{ url_for('index', page=page+1, status=status_filter) }}">Next</a>
                            </li>
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <!-- View Item Modal -->
    <div class="modal fade" id="viewItemModal" tabindex="-1" aria-labelledby="viewItemModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="viewItemModalLabel">Item Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="itemDetails" class="mb-3">
                        <pre id="itemJson"></pre>
                    </div>
                    <div id="itemActions">
                        <button type="button" class="btn btn-sm btn-warning" id="retryItemBtn" style="display: none;">Retry</button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Process Results Modal -->
    <div class="modal fade" id="processResultsModal" tabindex="-1" aria-labelledby="processResultsModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="processResultsModalLabel">Processing Results</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <pre id="processResults"></pre>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    // Add Video Form
    document.getElementById('enqueueForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        fetch('/enqueue', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Video added to queue successfully!');
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    });
    
    // Add Video Range Form
    document.getElementById('enqueueRangeForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!confirm('This may add many videos to the queue. Are you sure?')) {
            return;
        }
        
        const formData = new FormData(this);
        
        fetch('/enqueue_range', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`${data.count} videos added to queue successfully!`);
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    });
    
    // Process Queue Form
    document.getElementById('processForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!confirm('This will process items in the queue. Are you sure?')) {
            return;
        }
        
        const formData = new FormData(this);
        formData.set('convert_to_audio', document.getElementById('convert_to_audio').checked);
        
        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('processResults').textContent = JSON.stringify(data.results, null, 2);
                new bootstrap.Modal(document.getElementById('processResultsModal')).show();
                setTimeout(() => location.reload(), 5000);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    });
    
    // View Item
    function viewItem(id) {
        fetch(`/item/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('itemJson').textContent = JSON.stringify(data.item, null, 2);
                
                // Show retry button if the item is failed
                const retryBtn = document.getElementById('retryItemBtn');
                if (data.item.status === 'failed') {
                    retryBtn.style.display = 'inline-block';
                    retryBtn.onclick = function() { retryItem(id); };
                } else {
                    retryBtn.style.display = 'none';
                }
                
                new bootstrap.Modal(document.getElementById('viewItemModal')).show();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
    
    // Delete Item
    function deleteItem(id) {
        if (!confirm('Are you sure you want to delete this item?')) {
            return;
        }
        
        fetch(`/item/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Item deleted successfully!');
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
    
    // Retry Item
    function retryItem(id) {
        if (!confirm('Are you sure you want to retry this item?')) {
            return;
        }
        
        fetch(`/item/${id}/retry`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Item queued for retry!');
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
</script>
{% endblock %}
"""

    # Write the templates
    with open(os.path.join(templates_dir, "base.html"), "w") as f:
        f.write(base_html)

    with open(os.path.join(templates_dir, "index.html"), "w") as f:
        f.write(index_html)

    print(f"Created templates in {templates_dir}")


def main():
    """Main function for running the web server"""
    import argparse

    parser = argparse.ArgumentParser(description="Download Queue Web Interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--create-templates", action="store_true", help="Create HTML templates"
    )

    args = parser.parse_args()

    if args.create_templates:
        create_templates()

    # Check if templates exist
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    if not os.path.exists(templates_dir) or not os.listdir(templates_dir):
        print("Templates directory is empty or missing. Creating templates...")
        create_templates()

    print(f"Starting web server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
