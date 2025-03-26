#!/usr/bin/env python3
"""
List available Gemini models for the configured API key.

This script checks which Gemini models are available for use with the given API key.
"""

import sys
import os
import google.generativeai as genai

# Add parent directory to path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the API key manager
from scripts.manage_api_keys import get_api_key

def main():
    """List available Gemini models."""
    # Get API key from keychain
    api_key = get_api_key()
    if not api_key:
        print("Error: No API key found in keychain.")
        print("Please store your API key first using:")
        print("python scripts/manage_api_keys.py store")
        sys.exit(1)
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        print("Fetching available models...")
        models = genai.list_models()
        
        print("\nAvailable Gemini models:")
        for model in models:
            if "gemini" in model.name.lower():
                print(f"- {model.name}")
                print(f"  Description: {model.description}")
                print(f"  Supported generation methods: {', '.join(model.supported_generation_methods)}")
                print(f"  Input token limit: {model.input_token_limit}")
                print(f"  Output token limit: {model.output_token_limit}")
                print("")
        
    except Exception as e:
        print(f"Error listing models: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()