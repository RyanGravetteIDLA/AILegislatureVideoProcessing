#!/usr/bin/env python3
"""
Manage API keys securely in the system keychain

This script helps store and retrieve API keys from the system keychain,
without exposing the keys in command line arguments or environment variables.
"""

import argparse
import sys
import keyring
import getpass

# Service name for storing the key in keychain
KEYCHAIN_SERVICE = "IdahoLegislatureDownloader"
KEYCHAIN_USERNAME = "GeminiAPI"


def store_api_key():
    """Store the Google API key in the system keychain"""
    print("Storing Google Gemini API key in the system keychain")
    print("The key will be saved securely and can be accessed by the transcription scripts")
    
    # Prompt for API key without echoing to terminal
    api_key = getpass.getpass("Enter your Google Gemini API key: ")
    
    if not api_key:
        print("Error: API key cannot be empty")
        return False
    
    try:
        # Store the API key in the keychain
        keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME, api_key)
        print("API key successfully stored in the system keychain")
        return True
    except Exception as e:
        print(f"Error storing API key: {e}")
        return False


def get_api_key():
    """Retrieve the Google API key from the system keychain"""
    try:
        api_key = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)
        if not api_key:
            print("API key not found in keychain. Please store it first using:")
            print("python scripts/manage_api_keys.py store")
            return None
        return api_key
    except Exception as e:
        print(f"Error retrieving API key: {e}")
        return None


def delete_api_key():
    """Delete the Google API key from the system keychain"""
    try:
        keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)
        print("API key successfully deleted from the system keychain")
        return True
    except keyring.errors.PasswordDeleteError:
        print("No API key found in the keychain")
        return False
    except Exception as e:
        print(f"Error deleting API key: {e}")
        return False


def main():
    """Main function to parse arguments and manage API keys"""
    parser = argparse.ArgumentParser(description="Manage API keys in the system keychain")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Store command
    store_parser = subparsers.add_parser('store', help='Store API key in keychain')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Retrieve API key from keychain')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete API key from keychain')
    
    args = parser.parse_args()
    
    if args.command == 'store':
        success = store_api_key()
        sys.exit(0 if success else 1)
    elif args.command == 'get':
        api_key = get_api_key()
        if api_key:
            # Only print the first few and last few characters for verification
            masked_key = f"{api_key[:4]}...{api_key[-4:]}"
            print(f"API key found in keychain: {masked_key}")
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.command == 'delete':
        success = delete_api_key()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()