#!/usr/bin/env python3
"""
Error handling module for the Idaho Legislature Media Portal.
Provides standardized error handling utilities and custom exceptions.
"""

import os
import sys
import logging
import traceback
from functools import wraps
from typing import Callable, Any, Dict, Optional, Type, Union, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Define custom exceptions for better error categorization
class MediaPortalError(Exception):
    """Base exception class for Media Portal-specific errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DatabaseError(MediaPortalError):
    """Exception raised for database-related errors."""
    pass


class StorageError(MediaPortalError):
    """Exception raised for storage-related errors (GCS, local file system)."""
    pass


class APIError(MediaPortalError):
    """Exception raised for API-related errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        super().__init__(message, details)


class ConfigurationError(MediaPortalError):
    """Exception raised for configuration-related errors."""
    pass


class ProcessingError(MediaPortalError):
    """Exception raised for media processing errors."""
    pass


# Error handling decorators
def handle_exceptions(
    fallback_return: Any = None,
    expected_exceptions: Optional[List[Type[Exception]]] = None,
    log_level: str = "error",
):
    """
    Decorator to handle exceptions and log them appropriately.
    
    Args:
        fallback_return: Value to return if an exception occurs
        expected_exceptions: List of expected exception types to handle specially
        log_level: Logging level to use ('debug', 'info', 'warning', 'error', 'critical')
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the logger level function
                log_func = getattr(logger, log_level.lower(), logger.error)
                
                # Handle expected exceptions differently
                if expected_exceptions and any(isinstance(e, exc) for exc in expected_exceptions):
                    # For expected exceptions, we're less verbose
                    log_func(f"{func.__name__} encountered expected {e.__class__.__name__}: {str(e)}")
                else:
                    # For unexpected exceptions, include stack trace
                    log_func(f"Error in {func.__name__}: {e}")
                    if log_level in ("error", "critical"):
                        log_func(f"Stack trace: {traceback.format_exc()}")
                
                # Return the fallback value
                return fallback_return
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay_seconds: float = 1.0, backoff_factor: float = 2.0,
          expected_exceptions: Optional[List[Type[Exception]]] = None):
    """
    Decorator to retry a function in case of exceptions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay_seconds: Initial delay between retries (in seconds)
        backoff_factor: Multiplicative factor to increase delay between retries
        expected_exceptions: List of exceptions that trigger a retry
        
    Returns:
        Decorated function
    """
    import time
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay_seconds
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Only retry on expected exceptions if specified
                    if expected_exceptions and not any(isinstance(e, exc) for exc in expected_exceptions):
                        raise
                    
                    # If this was the last attempt, re-raise the exception
                    if attempt == max_attempts:
                        logger.error(f"Final retry attempt {attempt}/{max_attempts} for {func.__name__} failed: {e}")
                        raise
                    
                    # Log the retry attempt
                    logger.warning(
                        f"Retry attempt {attempt}/{max_attempts} for {func.__name__} failed: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )
                    
                    # Sleep before the next attempt
                    time.sleep(current_delay)
                    
                    # Increase the delay for the next attempt
                    current_delay *= backoff_factor
                    attempt += 1
        return wrapper
    return decorator


# Function to format error details for API responses
def format_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """
    Format an exception for an API error response.
    
    Args:
        error: The exception to format
        include_traceback: Whether to include the traceback in development environments
        
    Returns:
        Dictionary with formatted error details
    """
    error_type = error.__class__.__name__
    
    # Check if it's a custom error with details
    if isinstance(error, MediaPortalError):
        response = {
            "error": error_type,
            "message": error.message,
            "details": error.details
        }
        
        # Add status code for API errors
        if isinstance(error, APIError):
            response["status_code"] = error.status_code
    else:
        # Generic error formatting
        response = {
            "error": error_type,
            "message": str(error)
        }
    
    # Include traceback in development mode
    if include_traceback and (os.environ.get("DEBUG", "").lower() == "true" 
                            or os.environ.get("ENVIRONMENT", "").lower() == "development"):
        response["traceback"] = traceback.format_exc()
    
    return response


# Context manager for handling resources safely
class ErrorHandler:
    """
    Context manager for handling errors and resources safely.
    
    Example:
        with ErrorHandler("Processing file", cleanup_func=lambda: os.remove(temp_file)):
            process_file(temp_file)
    """
    
    def __init__(self, operation_name: str, cleanup_func: Optional[Callable] = None, 
                 reraise: bool = True, log_level: str = "error"):
        """
        Initialize the error handler.
        
        Args:
            operation_name: Name of the operation for logging
            cleanup_func: Function to call for cleanup if an exception occurs
            reraise: Whether to re-raise the exception after handling
            log_level: Logging level to use
        """
        self.operation_name = operation_name
        self.cleanup_func = cleanup_func
        self.reraise = reraise
        self.log_level = log_level
        self.exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Get the logger level function
            log_func = getattr(logger, self.log_level.lower(), logger.error)
            
            # Log the exception
            log_func(f"Error in {self.operation_name}: {exc_val}")
            
            # Save the exception for potential use by the caller
            self.exception = exc_val
            
            # Run cleanup if provided
            if self.cleanup_func:
                try:
                    self.cleanup_func()
                except Exception as cleanup_error:
                    log_func(f"Error during cleanup for {self.operation_name}: {cleanup_error}")
            
            # Return True to suppress the exception if reraise is False
            return not self.reraise
        
        return False


# Utility function to check network connectivity
def check_connectivity(target: str = "www.google.com", timeout: float = 3.0) -> bool:
    """
    Check if there is network connectivity by attempting to connect to a target.
    
    Args:
        target: The hostname to connect to
        timeout: Timeout in seconds
        
    Returns:
        True if connection successful, False otherwise
    """
    import socket
    
    try:
        socket.create_connection((target, 80), timeout=timeout)
        return True
    except (socket.timeout, socket.gaierror, OSError):
        return False


# Example of usage in code
if __name__ == "__main__":
    # Example with handle_exceptions decorator
    @handle_exceptions(fallback_return="default_value", log_level="warning")
    def risky_function(x: int) -> str:
        if x < 0:
            raise ValueError("x must be positive")
        if x > 100:
            raise OverflowError("x is too large")
        return f"The result is {100 / x}"
    
    # Example with retry decorator
    @retry(max_attempts=3, expected_exceptions=[ConnectionError])
    def fetch_data(url: str) -> str:
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise ConnectionError("Failed to connect")
        return f"Data from {url}"
    
    # Example with context manager
    def process_with_cleanup():
        temp_files = []
        
        def cleanup():
            print(f"Cleaning up {len(temp_files)} temporary files")
            for file in temp_files:
                print(f"Would remove: {file}")
        
        with ErrorHandler("file processing", cleanup_func=cleanup, reraise=False):
            temp_files.append("temp1.txt")
            temp_files.append("temp2.txt")
            # Simulate an error
            raise ProcessingError("Processing failed", {"file": "temp2.txt"})
    
    # Run examples
    print("Example 1:", risky_function(10))  # Should work
    print("Example 2:", risky_function(0))   # Should return default_value
    
    try:
        print("Example 3:", fetch_data("http://example.com"))
    except ConnectionError:
        print("Example 3: All retries failed")
    
    process_with_cleanup()
    
    # Example of API error handling
    try:
        raise APIError("Resource not found", status_code=404, details={"resource_id": "12345"})
    except Exception as e:
        error_response = format_error_response(e)
        print("API Error Response:", error_response)