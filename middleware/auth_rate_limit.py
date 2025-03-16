from fastapi import HTTPException, Request
from datetime import datetime, timedelta, UTC
import logging
from typing import Dict, List
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time

logger = logging.getLogger(__name__)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app: FastAPI,
            login_limit: int = 5,  # Maximum login attempts per window
            window_seconds: int = 300,  # 5-minute window
            block_seconds: int = 900  # 15-minute block after exceeding limit
    ):
        super().__init__(app)
        self.login_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.login_limit = login_limit
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds

    async def dispatch(self, request: Request, call_next):
        # Only apply to auth endpoints
        path = request.url.path
        if not path.startswith("/api/v1/auth") or request.method != "POST":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            block_until = self.blocked_ips[client_ip]
            if datetime.now(UTC) < block_until:
                remaining_seconds = int((block_until - datetime.now(UTC)).total_seconds())
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Too many failed attempts. Try again in {remaining_seconds} seconds."
                    }
                )
            else:
                # Remove from blocked list if time has expired
                del self.blocked_ips[client_ip]

        # Cleanup old attempts
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=self.window_seconds)

        if client_ip in self.login_attempts:
            self.login_attempts[client_ip] = [
                t for t in self.login_attempts[client_ip] if t > cutoff
            ]

            # Check if limit reached
            if len(self.login_attempts[client_ip]) >= self.login_limit:
                # Block IP
                self.blocked_ips[client_ip] = now + timedelta(seconds=self.block_seconds)
                logger.warning(f"IP {client_ip} blocked for {self.block_seconds} seconds due to too many auth attempts")
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Too many authentication attempts. Try again in {self.block_seconds} seconds."
                    }
                )

        # Process the request
        response = await call_next(request)

        # If auth failed, record the attempt
        if path in ["/api/v1/auth/login", "/api/v1/auth/refresh"] and response.status_code == 401:
            if client_ip not in self.login_attempts:
                self.login_attempts[client_ip] = []

            self.login_attempts[client_ip].append(now)
            logger.info(
                f"Failed auth attempt from {client_ip} ({len(self.login_attempts[client_ip])}/{self.login_limit})")

        return response
