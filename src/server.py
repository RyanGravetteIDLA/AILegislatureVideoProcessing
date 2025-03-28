"""
Combined server module that runs both the API and file server.
Provides a single entry point for running the backend services.

This module serves as the main entry point for running the Idaho Legislature Media
backend services. It can launch both the API server and file server concurrently
using Python's multiprocessing, or run just one of them based on command-line arguments.

Features:
- Environment variable configuration via dotenv
- Command-line argument support for flexible deployment
- Concurrent execution of both services
- Proper process management and error handling
- Configurable ports for each service

Usage examples:
- Run both services:    python server.py
- Run only API:         python server.py --api-only
- Run only file server: python server.py --file-only
- Custom ports:         python server.py --api-port 8000 --file-port 8001
"""

import os
import logging
import argparse
import multiprocessing
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'server.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('server')

def run_api(port):
    """Run the API server."""
    logger.info(f"Starting API server on port {port}")
    # Use Firestore backend instead of SQLite
    # First try to rename transcript_db.py to transcript_db_sqlite.py if not already done
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'transcript_db_sqlite.py')):
        try:
            src_path = os.path.join(os.path.dirname(__file__), 'transcript_db.py')
            dst_path = os.path.join(os.path.dirname(__file__), 'transcript_db_sqlite.py')
            if os.path.exists(src_path):
                import shutil
                shutil.copy2(src_path, dst_path)
                logger.info(f"Backed up SQLite implementation to transcript_db_sqlite.py")
        except Exception as e:
            logger.warning(f"Could not backup transcript_db.py: {e}")
    
    # Now use the Firestore version as transcript_db.py
    try:
        src_path = os.path.join(os.path.dirname(__file__), 'transcript_db_firestore.py')
        dst_path = os.path.join(os.path.dirname(__file__), 'transcript_db.py')
        if os.path.exists(src_path):
            import shutil
            shutil.copy2(src_path, dst_path)
            logger.info(f"Using Firestore implementation for transcript_db.py")
    except Exception as e:
        logger.warning(f"Could not use Firestore transcript_db: {e}")
    
    # Run the API server
    uvicorn.run("src.api_firestore:app", host="0.0.0.0", port=port, reload=True)

def run_file_server(port):
    """Run the file server."""
    logger.info(f"Starting file server on port {port}")
    uvicorn.run("src.file_server:app", host="0.0.0.0", port=port, reload=True)

def main():
    """
    Main entry point for the server.
    
    This function:
    1. Parses command-line arguments
    2. Determines which servers to run based on arguments
    3. Launches server process(es) either individually or concurrently
    4. Handles process lifecycle and exceptions
    
    Command-line arguments:
    - --api-port: Specify custom port for the API server
    - --file-port: Specify custom port for the file server
    - --api-only: Run only the API server
    - --file-only: Run only the file server
    """
    parser = argparse.ArgumentParser(description="Run the Idaho Legislature Media backend services")
    parser.add_argument("--api-port", type=int, default=int(os.getenv("API_PORT", 5000)),
                        help="Port for the API server (default: 5000)")
    parser.add_argument("--file-port", type=int, default=int(os.getenv("FILE_PORT", 5001)),
                        help="Port for the file server (default: 5001)")
    parser.add_argument("--api-only", action="store_true", help="Run only the API server")
    parser.add_argument("--file-only", action="store_true", help="Run only the file server")
    
    args = parser.parse_args()
    
    try:
        if args.api_only:
            run_api(args.api_port)
        elif args.file_only:
            run_file_server(args.file_port)
        else:
            # Run both servers concurrently using Python's multiprocessing
            # This allows each server to run in its own process with separate resources
            logger.info(f"Starting both API server (port {args.api_port}) and file server (port {args.file_port})...")
            
            # Create process objects for each server
            api_process = multiprocessing.Process(target=run_api, args=(args.api_port,))
            file_process = multiprocessing.Process(target=run_file_server, args=(args.file_port,))
            
            # Start both processes
            api_process.start()
            file_process.start()
            
            # Wait for both processes to complete
            # This blocks the main thread until both servers are terminated
            # which allows for proper cleanup on exit
            api_process.join()
            file_process.join()
    
    except KeyboardInterrupt:
        logger.info("Server stopping due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Error starting server: {e}")

if __name__ == "__main__":
    main()