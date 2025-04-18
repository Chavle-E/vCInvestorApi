#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database to be ready..."
python -c "
import time
from database import test_db_connection
while not test_db_connection():
    print('Database not ready yet, waiting...')
    time.sleep(2)
"
echo "Database is ready!"

# Option to reset the database if the RESET_DB environment variable is set to 'true'
if [ "$RESET_DB" = "true" ]; then
    echo "Resetting database..."
    python scripts/reset_database.py
    echo "Database reset completed."
fi

# Update the database schema
echo "Running database schema update..."
python scripts/update_schema.py
echo "Schema update completed."

# Start the application
echo "Starting the application..."
exec uvicorn app:app --host 0.0.0.0 --port 8000 $@