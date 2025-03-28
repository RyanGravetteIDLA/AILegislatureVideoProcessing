@echo off
echo === Idaho Legislature Media Portal - Local Development ===

REM Check if .env file exists, create from example if not
if not exist .env (
  echo Creating .env file from example...
  copy .env.example .env
  echo Created .env file. Please update it with your configuration.
)

REM Create necessary directories
if not exist data\logs mkdir data\logs
if not exist data\db mkdir data\db

REM Check if Python virtual environment exists
if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv
  call venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call venv\Scripts\activate
)

REM Start API server in a new window
echo Starting API and File servers...
start cmd /k "cd src && python server.py"

REM Sleep to allow API to start
timeout /t 5 /nobreak > nul

REM Start frontend dev server in a new window
echo Starting frontend development server...
start cmd /k "cd frontend && npm install && npm run dev"

echo.
echo === Servers are running ===
echo API Server: http://localhost:5000/api
echo File Server: http://localhost:5001/files
echo Frontend: http://localhost:5173
echo.
echo Press Ctrl+C in each window to stop the servers
echo.

pause