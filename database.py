# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment variables with fallback
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://investor_admin:your_secure_password@localhost/investor_db"
)

# Create engine with proper configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Maximum number of database connections in the pool
    max_overflow=10  # Maximum number of connections that can be created beyond pool_size
)

# Create SessionLocal class with proper configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Create Base class for declarative models
Base = declarative_base()


def get_db():
    """Dependency that provides a database session"""
    db = SessionLocal()
    try:
        logger.debug("Creating new database session")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.debug("Closing database session")
        db.close()

def test_db_connection():
    """Test database connection"""
    try:
        logger.info("Testing database connection...")
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful!")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False