from fastapi import HTTPException
from datetime import datetime, timedelta, UTC
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self):
        self.requests = {}

    async def check_limit(self, user_id: str, tier_limits: dict):
        now = datetime.now(UTC)
        user_requests = self.requests.get(user_id, [])

        # Remove old requests outside the window
        window_start = now - timedelta(hours=24)
        user_requests = [req for req in user_requests if req > window_start]

        # Check against tier limit
        max_requests = tier_limits.get(user_id, 10)  # Default to 10
        if len(user_requests) >= max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit of {max_requests} requests per day exceeded"
            )

        # Add new request
        user_requests.append(now)
        self.requests[user_id] = user_requests
