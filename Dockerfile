# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn google-cloud-firestore

# Copy only the necessary files
COPY src/simple_firestore_api.py ./src/simple_firestore_api.py
COPY credentials/ ./credentials/

# Create logs directory
RUN mkdir -p data/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV GOOGLE_CLOUD_PROJECT=legislativevideoreviewswithai
ENV GCS_BUCKET_NAME=legislativevideoreviewswithai.firebasestorage.app

# Expose the port
EXPOSE 8080

# Command to run when container starts
CMD ["python", "src/simple_firestore_api.py"]