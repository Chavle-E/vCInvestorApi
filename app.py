from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi.params import Depends

from api.v1.endpoints import (
    investors,
    investment_funds,
    export,
    utils,
    lists,
    investor_filters,
    fund_filters,
    auth,
    google_auth
)
from database import engine, test_db_connection
import models
import os
import logging
import sys
from middleware.rate_limit import RateLimitMiddleware
from starlette.middleware.sessions import SessionMiddleware
from middleware.auth_rate_limit import AuthRateLimitMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from auth import get_current_user


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
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(AuthRateLimitMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "4GGdb2Ol15zbAeGzQQdwxH9WdW8HPCjV"),
    max_age=3600,
    same_site="lax"
)

app.add_middleware(
    RateLimitMiddleware,
    rate_limit_duration=24 * 60 * 60,  # 24 hours in seconds
    default_limit=1000  # Default requests per day
)

# Configure CORS
origins = ["*"]
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
    (utils.router, "/api/v1", "utils"),
    (auth.router, "/api/v1/auth", "authentication")
]

for router, prefix, tag in public_routes:
    app.include_router(router, prefix=prefix, tags=[tag])

protected_routes = [
    (investors.router, "/api/v1/investors", "investors", "basic"),
    (investment_funds.router, "/api/v1/funds", "funds", "basic"),
    (export.router, "/api/v1/export", "export", "professional"),
    (lists.router, "/api/v1/lists", "lists", "basic"),
    (investor_filters.router, "/api/v1/filters", "Investor Filters", "basic"),
    (fund_filters.router, "/api/v1/filters", "Fund Filters", "basic"),
    (google_auth.router, "/api/v1/auth/google", "google authentication", "basic")
]

for router, prefix, tag, _ in protected_routes:
    app.include_router(
        router,
        prefix=prefix,
        tags=[tag],
        dependencies=[Depends(get_current_user)]
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
