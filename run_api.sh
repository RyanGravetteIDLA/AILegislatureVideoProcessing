#!/bin/bash

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env file from .env.example. Please update it with your configuration."
  exit 1
fi

# Create necessary directories
mkdir -p data/logs data/db

# Start the API and file server
cd src
python server.py