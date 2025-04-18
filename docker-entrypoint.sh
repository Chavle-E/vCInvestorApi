#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database to be ready..."
python -c "
import time
import sys
sys.path.append('/app')  # Add the app directory to Python path
from database import test_db_connection
while not test_db_connection():
    print('Database not ready yet, waiting...')
    time.sleep(2)
"
echo "Database is ready!"

# Update the database schema
echo "Running database schema update..."
cd /app  # Ensure we're in the right directory
python -m scripts.update_schema  # Run script as a module
echo "Schema update completed."

# Start the application
echo "Starting the application..."
exec uvicorn app:app --host 0.0.0.0 --port 8000