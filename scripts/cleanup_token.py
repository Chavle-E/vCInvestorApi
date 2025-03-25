#!/usr/bin/env python
"""
Script to clean up expired refresh tokens.
Can be run as a cron job to keep the database tidy.
"""
import logging
import os
import sys
from datetime import datetime, UTC

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth import cleanup_expired_tokens

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('token_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main function to cleanup expired tokens"""
    try:
        logger.info("Starting expired token cleanup")
        db = next(get_db())

        deleted_count = cleanup_expired_tokens(db)

        logger.info(f"Cleanup complete. Removed {deleted_count} expired tokens")
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()