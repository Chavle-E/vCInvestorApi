# middleware/user_token_rate_limit.py
from fastapi import HTTPException, Request
from datetime import datetime, timedelta, UTC
import logging
from typing import Dict, Optional, Tuple
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError
import os

logger = logging.getLogger(__name__)


class UserTokenRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app: FastAPI,
            rate_limit_duration: int = 24 * 60 * 60,  # 24 hours in seconds
            default_limit: int = 1000,  # Default requests per duration
            jwt_secret_key: str = None,
            jwt_algorithm: str = "HS256",
            exclude_paths: list = None
    ):
        super().__init__(app)
        self.requests: Dict[str, list] = {}
        self.rate_limit_duration = rate_limit_duration
        self.default_limit = default_limit
        self.jwt_secret_key = jwt_secret_key or os.getenv("JWT_SECRET_KEY", "")
        self.jwt_algorithm = jwt_algorithm
        self.exclude_paths = exclude_paths or ["/api/v1/auth/login", "/api/v1/auth/refresh", "/health"]

        # Define tier limits
        self.tier_limits = {
            "free": 100,
            "basic": 1000,
            "professional": 5000,
            "enterprise": 10000,
            "admin": 50000
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        path = request.url.path
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)

        try:
            # Extract user identifier and tier from token
            client_id, tier = await self._get_token_info(request)

            # If no valid token, fall back to IP-based rate limiting
            if not client_id:
                client_id = self._get_client_ip(request)
                tier = "basic"  # Default tier for unauthenticated requests

            # Check rate limit
            await self._check_rate_limit(client_id, tier)

            # Process the request
            response = await call_next(request)
            return response

        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address as fallback identifier"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the original client IP (first in the list)
            client_ip = forwarded_for.split(",")[0].strip()
            return f"ip_{client_ip}"  # Prefix to distinguish from user IDs

        # Fall back to direct client IP
        return f"ip_{request.client.host if request.client else 'unknown'}"

    async def _get_token_info(self, request: Request) -> Tuple[Optional[str], str]:
        """Extract user ID and tier from JWT token"""
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None, "basic"

        token = auth_header.replace("Bearer ", "")

        try:
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=[self.jwt_algorithm]
            )

            # Extract user ID from token
            user_id = payload.get("sub")
            if not user_id:
                return None, "basic"

            # Get user tier from token or default to basic
            tier = payload.get("tier", "basic")

            return f"user_{user_id}", tier

        except JWTError:
            logger.debug("Invalid JWT token for rate limiting")
            return None, "basic"

    async def _check_rate_limit(self, client_id: str, tier: str):
        now = datetime.now(UTC)

        # Initialize client's request history if not exists
        if client_id not in self.requests:
            self.requests[client_id] = []

        # Remove old requests
        cutoff_time = now - timedelta(seconds=self.rate_limit_duration)
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff_time
        ]

        # Get limit based on tier
        limit = self.tier_limits.get(tier, self.default_limit)

        # Check if limit exceeded
        if len(self.requests[client_id]) >= limit:
            logger.warning(f"Rate limit exceeded for client {client_id} (tier: {tier})")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit of {limit} requests per {self.rate_limit_duration // 3600} hours exceeded"
            )

        # Add current request
        self.requests[client_id].append(now)