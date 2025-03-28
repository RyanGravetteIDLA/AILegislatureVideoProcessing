"""
Combined server module that runs both the API and file server.
Provides a single entry point for running the backend services.
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'server.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('server')

def run_api(port):
    """Run the API server."""
    logger.info(f"Starting API server on port {port}")
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)

def run_file_server(port):
    """Run the file server."""
    logger.info(f"Starting file server on port {port}")
    uvicorn.run("file_server:app", host="0.0.0.0", port=port, reload=True)

def main():
    """Main entry point for the server."""
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
            # Run both servers concurrently
            api_process = multiprocessing.Process(target=run_api, args=(args.api_port,))
            file_process = multiprocessing.Process(target=run_file_server, args=(args.file_port,))
            
            api_process.start()
            file_process.start()
            
            # Wait for both processes to complete
            api_process.join()
            file_process.join()
    
    except KeyboardInterrupt:
        logger.info("Server stopping due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Error starting server: {e}")

if __name__ == "__main__":
    main()