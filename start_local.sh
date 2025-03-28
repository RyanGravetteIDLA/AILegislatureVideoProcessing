#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Idaho Legislature Media Portal - Local Development ===${NC}\n"

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
  echo -e "${BLUE}Creating .env file from example...${NC}"
  cp .env.example .env
  echo -e "${GREEN}Created .env file. Please update it with your configuration.${NC}"
fi

# Create necessary directories
mkdir -p data/logs data/db

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
  echo -e "${BLUE}Creating Python virtual environment...${NC}"
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

# Start API server in the background
echo -e "${BLUE}Starting API and File servers...${NC}"
cd src
python server.py &
API_PID=$!
cd ..

# Sleep to allow API to start
sleep 2

# Start frontend dev server
echo -e "${BLUE}Starting frontend development server...${NC}"
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

# Function to handle script termination
cleanup() {
  echo -e "\n${BLUE}Shutting down servers...${NC}"
  kill $API_PID
  kill $FRONTEND_PID
  echo -e "${GREEN}Servers stopped. Goodbye!${NC}"
  exit 0
}

# Set the cleanup function to run on script termination
trap cleanup SIGINT SIGTERM

echo -e "\n${GREEN}=== Servers are running ===${NC}"
echo -e "${GREEN}API Server:${NC} http://localhost:5000/api"
echo -e "${GREEN}File Server:${NC} http://localhost:5001/files"
echo -e "${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "\n${BLUE}Press Ctrl+C to stop all servers${NC}"

# Wait for user to press Ctrl+C
wait