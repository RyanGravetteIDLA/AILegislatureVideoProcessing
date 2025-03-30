#!/bin/bash
# Automated cleanup script for the Idaho Legislature Media Portal project

set -e  # Exit on error

echo "Starting project cleanup..."

# 1. Remove deprecated Google Drive files
echo "Removing deprecated Google Drive files..."
DRIVE_FILES=(
  "scripts/list_drive_folders.py"
  "scripts/manage_drive_service.py"
  "scripts/upload_media_to_drive.py"
  "src/drive_storage.py"
)

for file in "${DRIVE_FILES[@]}"; do
  if [ -f "$file" ]; then
    rm -f "$file"
    echo "Removed $file"
  else
    echo "File $file already removed"
  fi
done

# 2. Remove redundant deployment scripts
echo "Removing redundant deployment scripts..."
REDUNDANT_SCRIPTS=(
  "deploy_to_cloud_run.sh"
  "deploy_cloud_build.sh"
  "deploy_main_api.sh"
  "deploy_test_api.sh"
)

for script in "${REDUNDANT_SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    rm -f "$script"
    echo "Removed $script"
  else
    echo "Script $script already removed"
  fi
done

# 3. Install development dependencies
echo "Installing development dependencies..."
pip install black flake8 pytest

# 4. Format Python code
echo "Formatting Python code with Black..."
black src/ scripts/ functions/ tests/ || echo "Black formatting failed, please run manually"

# 5. Run linting
echo "Running linting with Flake8..."
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics || echo "Flake8 found issues, please fix manually"

# 6. Clean up __pycache__ directories
echo "Cleaning up __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# 7. Make script executable
chmod +x deploy_cloud_run.sh
chmod +x deploy_function.sh
chmod +x frontend/deploy_to_firebase.sh

echo "Cleanup completed! Please review the PROJECT_CLEANUP_PLAN.md for additional manual cleanup tasks."
echo "Remember to run 'git add .' and create a commit with your changes."