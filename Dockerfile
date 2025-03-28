# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example ./.env.example

# Create necessary directories
RUN mkdir -p data/db data/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the ports that API and File Server will run on
EXPOSE 5000
EXPOSE 5001

# Command to run when container starts
# Default to running both servers, can be overridden
CMD ["python", "src/server.py"]

# For running just the API server:
# CMD ["python", "src/server.py", "--api-only"]

# For running just the file server:
# CMD ["python", "src/server.py", "--file-only"]