#!/bin/bash
# Script to configure GitHub repository with deploy key for automated processes

# Replace these variables with your actual values
GITHUB_USERNAME="RyanGravetteIDLA"
REPO_NAME="AILegislatureVideoProcessing"

# Generate a deploy key for automation
if [ ! -f deploy_key ]; then
  echo "Generating a new deploy key..."
  ssh-keygen -t ed25519 -f deploy_key -N "" -C "deploy-key-pulllegislature"
  echo "Deploy key generated."
fi

# Configure Git
echo "Please enter your Git username:"
read GIT_USERNAME
echo "Please enter your Git email:"
read GIT_EMAIL

git config user.name "$GIT_USERNAME"
git config user.email "$GIT_EMAIL"

# Configure remote origin with SSH
git remote set-url origin git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git
git branch -M main

# Print setup instructions
echo "============================================================"
echo "                   GitHub Setup Instructions                "
echo "============================================================"
echo ""
echo "1. Create a new repository at https://github.com/new named '${REPO_NAME}'"
echo "2. Go to repository Settings -> Deploy Keys"
echo "3. Add a new deploy key with the following content:"
echo ""
cat deploy_key.pub
echo ""
echo "4. Check 'Allow write access' if you want automated processes to push changes"
echo "5. Click 'Add key'"
echo "6. Run: git push -u origin main"
echo ""
echo "This deploy key can be used for automation on servers without storing your personal credentials."
