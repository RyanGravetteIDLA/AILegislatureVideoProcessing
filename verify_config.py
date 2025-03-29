#!/usr/bin/env python3
"""
Verification script to check if the updated configuration works properly.
This script validates key components of the application without making any changes.
"""

import os
import sys
import importlib.util
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_module_imports():
    """Check if required modules can be imported."""
    modules_to_check = [
        "firebase_admin",
        "google.cloud.firestore",
        "google.cloud.storage",
        "flask",
        "fastapi"
    ]
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            logger.info(f"✅ Successfully imported {module_name}")
        except ImportError:
            logger.error(f"❌ Failed to import {module_name}")

def check_file_structure():
    """Check if key files exist and are accessible."""
    critical_files = [
        "src/cloud_functions/main.py",
        "src/cloud_functions/services/gateway_service.py",
        "src/api_firestore.py",
        "src/cloud_storage.py",
        "functions/main.py",
        "frontend/src/stores/mediaStore.js"
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            logger.info(f"✅ Found file: {file_path}")
        else:
            logger.error(f"❌ Missing file: {file_path}")

def check_deployment_files():
    """Check if deployment scripts exist and are executable."""
    deployment_scripts = [
        "deploy_cloud_run.sh",
        "deploy_function.sh",
        "frontend/deploy_to_firebase.sh"
    ]
    
    for script_path in deployment_scripts:
        if os.path.exists(script_path):
            if os.access(script_path, os.X_OK):
                logger.info(f"✅ Deployment script is executable: {script_path}")
            else:
                logger.warning(f"⚠️ Deployment script exists but is not executable: {script_path}")
                logger.info(f"   Run 'chmod +x {script_path}' to make it executable")
        else:
            logger.error(f"❌ Missing deployment script: {script_path}")

def check_environment():
    """Check if environment variables are set."""
    env_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GCS_BUCKET_NAME"
    ]
    
    for var in env_vars:
        if var in os.environ:
            value = os.environ[var]
            masked_value = value[:5] + "..." if len(value) > 10 else value
            logger.info(f"✅ Environment variable set: {var}={masked_value}")
        else:
            logger.warning(f"⚠️ Environment variable not set: {var}")

def check_cloud_functions_config():
    """Check if Cloud Functions configuration is valid."""
    try:
        # Try to import the main entry point for Cloud Functions
        spec = importlib.util.spec_from_file_location("functions.main", "functions/main.py")
        functions_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(functions_main)
        
        # Check if the required function is defined
        if hasattr(functions_main, "media_portal_api"):
            logger.info(f"✅ Cloud Function entry point found: functions.main.media_portal_api")
        else:
            logger.error(f"❌ Cloud Function entry point missing")
            
    except Exception as e:
        logger.error(f"❌ Failed to import Cloud Functions configuration: {e}")

def verify_configuration():
    """Run all verification checks."""
    logger.info("Starting configuration verification...")
    
    # Run all checks
    check_module_imports()
    check_file_structure()
    check_deployment_files()
    check_environment()
    check_cloud_functions_config()
    
    logger.info("Configuration verification complete")

if __name__ == "__main__":
    verify_configuration()