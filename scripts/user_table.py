from database import engine, Base
import models
import logging

logger = logging.getLogger(__name__)


def add_user_table():
    try:
        logger.info("Creating User table if it doesn't exist...")
        models.User.__table__.create(bind=engine, checkfirst=True)
        logger.info("User table created successfully")
    except Exception as e:
        logger.error(f"Error creating User table: {str(e)}")
        raise


if __name__ == "__main__":
    add_user_table()
