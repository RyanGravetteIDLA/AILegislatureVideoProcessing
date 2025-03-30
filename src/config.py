#!/usr/bin/env python3
"""
Configuration management module for the Idaho Legislature Media Portal.
Centralizes configuration loading, validation, and access throughout the application.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List, Set, Union
from pathlib import Path

# Import error handling
try:
    from error_handling import ConfigurationError, handle_exceptions
except ImportError:
    # Define minimal error classes if error_handling module isn't available
    class ConfigurationError(Exception):
        pass

    def handle_exceptions(fallback_return=None, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error in {func.__name__}: {e}")
                    return fallback_return
            return wrapper
        return decorator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Environment variable names
ENV_VAR_PREFIX = "MEDIA_PORTAL_"
ENV_VAR_CONFIG_FILE = f"{ENV_VAR_PREFIX}CONFIG_FILE"
ENV_VAR_ENV = f"{ENV_VAR_PREFIX}ENV"

# Default configuration settings
DEFAULT_CONFIG = {
    "project": {
        "name": "Idaho Legislature Media Portal",
        "version": "1.0.0",
    },
    "api": {
        "port": 5000,
        "host": "0.0.0.0",
        "debug": False,
        "cors_origins": ["*"],
    },
    "file_server": {
        "port": 5001,
        "host": "0.0.0.0",
    },
    "database": {
        "type": "firestore",  # Options: firestore, sqlite
        "sqlite_path": "data/db/transcripts.db",
        "firestore_project": "legislativevideoreviewswithai",
    },
    "storage": {
        "use_cloud_storage": True,
        "prefer_cloud_storage": True,
        "gcs_bucket_name": "legislativevideoreviewswithai.appspot.com",
        "local_storage_path": "data/downloads",
    },
    "logging": {
        "level": "INFO",
        "file": "data/logs/app.log",
    },
    "temp": {
        "dir": "data/temp",
    },
    "deployment": {
        "service_account": "firebase-adminsdk-fbsvc@legislativevideoreviewswithai.iam.gserviceaccount.com",
        "region": "us-west1",
    },
}

# Singleton configuration
_config = None


def get_config() -> Dict[str, Any]:
    """
    Get the application configuration.
    Loads and caches the configuration if not already loaded.
    
    Returns:
        Dict containing the application configuration
    """
    global _config
    
    if _config is None:
        _config = load_config()
        
    return _config


@handle_exceptions(fallback_return=DEFAULT_CONFIG)
def load_config() -> Dict[str, Any]:
    """
    Load the application configuration from environment and files.
    
    The configuration is loaded from multiple sources in this order:
    1. Default configuration (hardcoded)
    2. Configuration file specified by MEDIA_PORTAL_CONFIG_FILE environment variable
    3. Environment-specific config file (e.g., .env.development, .env.production)
    4. Environment variables with MEDIA_PORTAL_ prefix
    
    Returns:
        Dict containing the merged configuration
    """
    config = DEFAULT_CONFIG.copy()
    
    # Determine environment
    env = os.environ.get(ENV_VAR_ENV, "development").lower()
    logger.info(f"Loading configuration for environment: {env}")
    
    # Load from config file if specified
    config_file = os.environ.get(ENV_VAR_CONFIG_FILE)
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
            config = deep_merge(config, file_config)
    
    # Load from environment-specific config file
    env_config_file = os.path.join(PROJECT_ROOT, f".env.{env}.json")
    if os.path.exists(env_config_file):
        with open(env_config_file, 'r') as f:
            env_config = json.load(f)
            logger.info(f"Loaded environment-specific configuration from {env_config_file}")
            config = deep_merge(config, env_config)
    
    # Load from environment variables
    env_config = {}
    for key, value in os.environ.items():
        if key.startswith(ENV_VAR_PREFIX):
            # Strip prefix and convert to lowercase
            config_key = key[len(ENV_VAR_PREFIX):].lower()
            
            # Handle nested keys with double underscore
            if "__" in config_key:
                parts = config_key.split("__")
                current = env_config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = parse_env_value(value)
            else:
                env_config[config_key] = parse_env_value(value)
    
    if env_config:
        logger.info(f"Loaded configuration from environment variables")
        config = deep_merge(config, env_config)
    
    # Set derived values based on environment
    if env == "development":
        # Development-specific overrides
        config["api"]["debug"] = True
    
    # Ensure required directories exist
    ensure_directories(config)
    
    return config


def ensure_directories(config: Dict[str, Any]) -> None:
    """
    Ensure that directories required by the configuration exist.
    
    Args:
        config: Application configuration
    """
    # Create log directory
    log_dir = os.path.dirname(config["logging"]["file"])
    os.makedirs(log_dir, exist_ok=True)
    
    # Create temp directory
    os.makedirs(config["temp"]["dir"], exist_ok=True)
    
    # Create local storage directory
    os.makedirs(config["storage"]["local_storage_path"], exist_ok=True)
    
    # Create database directory if using SQLite
    if config["database"]["type"] == "sqlite":
        db_dir = os.path.dirname(config["database"]["sqlite_path"])
        os.makedirs(db_dir, exist_ok=True)


def parse_env_value(value: str) -> Union[str, int, float, bool, None]:
    """
    Parse environment variable values into appropriate types.
    
    Args:
        value: The string value from the environment variable
        
    Returns:
        Parsed value as the appropriate type
    """
    # Check for boolean values
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False
    
    # Check for None
    if value.lower() in ("none", "null"):
        return None
    
    # Check for integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Check for float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value


def deep_merge(source: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with values from override taking precedence.
    
    Args:
        source: Base dictionary
        override: Dictionary with overrides
        
    Returns:
        A new dictionary with merged values
    """
    result = source.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # If both values are dictionaries, merge them recursively
            result[key] = deep_merge(result[key], value)
        else:
            # Otherwise, override the value
            result[key] = value
    
    return result


def get_database_config() -> Dict[str, Any]:
    """Get database-specific configuration."""
    return get_config()["database"]


def get_storage_config() -> Dict[str, Any]:
    """Get storage-specific configuration."""
    return get_config()["storage"]


def get_api_config() -> Dict[str, Any]:
    """Get API-specific configuration."""
    return get_config()["api"]


def get_file_server_config() -> Dict[str, Any]:
    """Get file server-specific configuration."""
    return get_config()["file_server"]


def get_logging_config() -> Dict[str, Any]:
    """Get logging-specific configuration."""
    return get_config()["logging"]


def get_temp_dir() -> str:
    """Get temporary directory path."""
    return get_config()["temp"]["dir"]


def get_deployment_config() -> Dict[str, Any]:
    """Get deployment-specific configuration."""
    return get_config()["deployment"]


def configure_logging() -> None:
    """Configure application logging based on the configuration."""
    config = get_logging_config()
    
    # Get log level
    level_name = config.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    
    # Configure the root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config["file"]),
            logging.StreamHandler(),
        ],
    )
    
    # Log the configuration
    logger.info(f"Logging configured with level {level_name}")


# Initialize configuration when module is imported
if __name__ != "__main__":
    get_config()


if __name__ == "__main__":
    # Display the current configuration when run as a script
    print("Idaho Legislature Media Portal Configuration")
    print("=" * 50)
    config = get_config()
    
    # Pretty print the configuration
    import pprint
    pprint.pprint(config)
    
    # Test accessing specific configuration sections
    print("\nDatabase Config:")
    print(get_database_config())
    
    print("\nStorage Config:")
    print(get_storage_config())
    
    print("\nAPI Config:")
    print(get_api_config())