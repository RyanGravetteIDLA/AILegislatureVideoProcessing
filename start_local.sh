#\!/bin/bash

# Set credentials environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/legislativevideoreviewswithai-80ed70b021b5.json"
echo "Set GOOGLE_APPLICATION_CREDENTIALS to $GOOGLE_APPLICATION_CREDENTIALS"

# Start the application
python src/server.py

# Or uncomment to run with uvicorn
# uvicorn src.server:app --reload
