from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import (
    investors,
    investment_funds,
    users,
    export,
    utils,
    auth
)
from database import engine, get_db, test_db_connection
from middleware.auth import AuthMiddleware, RateLimitMiddleware
import models
import os
import logging
import sys
from datetime import datetime


# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)

    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Set up file handler
    file_handler = logging.FileHandler(
        f'logs/app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    file_handler.setFormatter(formatter)

    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Investor Database API",
    description="API for managing investors and investment funds database",
    version="1.0.0"
)


# Test database connection on startup
@app.on_event("startup")
async def startup_event():
    """Run startup tasks"""
    logger.info("Starting up...")
    if not test_db_connection():
        logger.error("Database connection failed!")
        # In production, you might want to exit here
        # import sys; sys.exit(1)


# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth dependencies
auth_middleware = AuthMiddleware()
rate_limit_middleware = RateLimitMiddleware()


def get_auth_dependencies():
    """Get all auth dependencies"""
    return [
        Depends(get_db),
        Depends(auth_middleware),
        Depends(rate_limit_middleware)
    ]


# Public routes - no auth required
public_routes = [
    (auth.router, "/api/v1/auth", "auth"),
    (utils.router, "/api/v1", "utils")
]

for router, prefix, tag in public_routes:
    app.include_router(router, prefix=prefix, tags=[tag])

# Protected routes - require auth & respect rate limits
protected_routes = [
    (investors.router, "/api/v1/investors", "investors"),
    (investment_funds.router, "/api/v1/funds", "funds"),
    (export.router, "/api/v1/export", "export"),
    (users.router, "/api/v1/users", "users"),
]

for router, prefix, tag in protected_routes:
    app.include_router(
        router,
        prefix=prefix,
        tags=[tag],
        dependencies=get_auth_dependencies()
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
