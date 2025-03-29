#!/bin/bash
# Deploy the frontend to Firebase Hosting

# Set environment variables for production
echo "Setting up production environment..."
cat > .env.production << EOL
VITE_API_URL=https://us-west1-legislativevideoreviewswithai.cloudfunctions.net/media-portal-api
VITE_FILE_SERVER_URL=https://storage.googleapis.com/legislativevideoreviewswithai.appspot.com
EOL

# Check if firebase-tools is installed
if ! command -v firebase &> /dev/null; then
    echo "Installing firebase-tools..."
    npm install -g firebase-tools
fi

# Build the project for production
echo "Building project for production..."
npm run build

# Initialize Firebase if not already initialized
if [ ! -f .firebaserc ]; then
    echo "Initializing Firebase..."
    firebase init hosting
    
    # Create Firebase configuration
    echo "Creating Firebase configuration..."
    cat > firebase.json << EOL
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|jpg|jpeg|gif|png|svg)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      },
      {
        "source": "**",
        "headers": [
          {
            "key": "X-Content-Type-Options",
            "value": "nosniff"
          },
          {
            "key": "X-Frame-Options",
            "value": "DENY"
          },
          {
            "key": "X-XSS-Protection",
            "value": "1; mode=block"
          }
        ]
      }
    ]
  }
}
EOL

    # Create Firebase project configuration
    echo "Creating Firebase project configuration..."
    cat > .firebaserc << EOL
{
  "projects": {
    "default": "legislativevideoreviewswithai"
  }
}
EOL
fi

# Deploy to Firebase
echo "Deploying to Firebase..."
firebase deploy --only hosting

echo "Deployment complete!"
echo "Your application is live at: https://legislativevideoreviewswithai.web.app"