from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.v1.endpoints import (
    investors,
    investment_funds,
    export,
    utils,
    lists,
    counts
)
from database import engine, get_db, test_db_connection
import models
import os
import logging
import sys
from datetime import datetime
from middleware.rate_limit import RateLimitMiddleware


# Configure logging
def setup_logging():
    """Configure logging to output to console only"""

    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    root_logger.handlers = []
    root_logger.addHandler(console_handler)

    return root_logger


logger = setup_logging()


# Startup and shutdown events
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    logger.info("Starting application...")
    if not test_db_connection():
        logger.error("Database connection failed!")
        sys.exit(1)

    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Investor Database API",
    description="API for managing investors and investment funds database",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    RateLimitMiddleware,
    rate_limit_duration=24 * 60 * 60,  # 24 hours in seconds
    default_limit=1000  # Default requests per day
)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "connected" if test_db_connection() else "error"
    }


# Public routes - no auth required
public_routes = [
    (utils.router, "/api/v1", "utils")
]

for router, prefix, tag in public_routes:
    app.include_router(router, prefix=prefix, tags=[tag])

protected_routes = [
    (investors.router, "/api/v1/investors", "investors", "basic"),
    (investment_funds.router, "/api/v1/funds", "funds", "basic"),
    (export.router, "/api/v1/export", "export", "professional"),
    (lists.router, "/api/v1/lists", "lists", "basic"),
    (counts.router, "/api/v1/counts", "counts", "basic")  # Add this line
]

for router, prefix, tag, _ in protected_routes:
    app.include_router(
        router,
        prefix=prefix,
        tags=[tag]
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
