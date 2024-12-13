from fastapi import HTTPException, Request
from datetime import datetime, timedelta, UTC
import logging
from typing import Dict, Optional
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app: FastAPI,
            rate_limit_duration: int = 24 * 60 * 60,  # 24 hours in seconds
            default_limit: int = 1000  # Default requests per duration
    ):
        super().__init__(app)
        self.requests: Dict[str, list] = {}
        self.rate_limit_duration = rate_limit_duration
        self.default_limit = default_limit

        # Define tier limits - you can modify these based on your needs
        self.tier_limits = {
            "basic": 1000,  # 1000 requests per day
            "professional": 5000,  # 5000 requests per day
            "enterprise": 10000  # 10000 requests per day
        }

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (you might want to use API key or token instead)
        client_id = self._get_client_identifier(request)

        # Get user's tier (you'll need to implement this based on your auth system)
        user_tier = await self._get_user_tier(request)

        try:
            # Check rate limit
            await self._check_rate_limit(client_id, user_tier)

            # Process the request
            response = await call_next(request)
            return response

        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )

    def _get_client_identifier(self, request: Request) -> str:
        # You might want to use API key or token instead of IP
        return request.client.host if request.client else "unknown"

    async def _get_user_tier(self, request: Request) -> str:
        # Implement your logic to get user tier from auth token/header
        # This is a placeholder - modify based on your auth system
        return "basic"

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


# Usage example for clearing old rate limit data
def cleanup_rate_limits(rate_limiter: RateLimitMiddleware):
    """Cleanup old rate limit data periodically"""
    now = datetime.now(UTC)
    cutoff_time = now - timedelta(seconds=rate_limiter.rate_limit_duration)

    for client_id in list(rate_limiter.requests.keys()):
        rate_limiter.requests[client_id] = [
            req_time for req_time in rate_limiter.requests[client_id]
            if req_time > cutoff_time
        ]
        # Remove empty client records
        if not rate_limiter.requests[client_id]:
            del rate_limiter.requests[client_id]