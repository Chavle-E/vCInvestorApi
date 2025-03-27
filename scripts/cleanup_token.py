from database import get_db
from auth import cleanup_expired_tokens
import logging
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """Main function to clean up expired tokens"""
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
