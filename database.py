from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
from dotenv import load_dotenv
import logging
import traceback
from fastapi import HTTPException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")

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
    db = SessionLocal()
    try:
        yield db
    finally:
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
