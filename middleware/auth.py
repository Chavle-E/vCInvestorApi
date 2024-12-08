from datetime import datetime, timezone, timedelta, UTC
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from database import get_db
from models import User
import os
import logging
import traceback

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')  # Change in production
JWT_ALGORITHM = "HS256"

SUBSCRIPTION_LIMITS = {
    "free": {
        "monthly_searches": 10,
        "can_export": False,
        "can_see_full_profiles": False,
        "can_see_contact_info": False
    },
    "basic": {
        "monthly_searches": 500,
        "can_export": True,
        "can_see_full_profiles": True,
        "can_see_contact_info": False
    },
    "professional": {
        "monthly_searches": -1,  # Unlimited
        "can_export": True,
        "can_see_full_profiles": True,
        "can_see_contact_info": True
    }
}


def create_token(user_id: int, email: str) -> str:
    """Create JWT token"""
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expires
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


class AuthMiddleware:
    async def __call__(self, request: Request, db: Session = Depends(get_db)):
        logger.debug(f"Processing request: {request.method} {request.url.path}")
        try:
            # Skip auth for login/register endpoints
            if request.url.path.startswith("/api/v1/auth"):
                return

            auth = request.headers.get("Authorization")
            if not auth or not auth.startswith("Bearer "):
                logger.warning("No token provided in Authorization header")
                raise HTTPException(status_code=401, detail="Missing token")

            token = auth.split(" ")[1]
            try:
                payload = decode_token(token)
                logger.debug(f"Token decoded for user_id: {payload.get('user_id')}")
            except Exception as e:
                logger.error(f"Token decode error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid token")

            # Get user from database
            user = db.query(User).filter(User.id == payload["user_id"]).first()
            if not user:
                logger.warning(f"User not found for id: {payload['user_id']}")
                raise HTTPException(status_code=401, detail="User not found")

            logger.debug(f"Auth successful for user: {user.id}")
            request.state.user = user
            request.state.db = db

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=401, detail="Authentication failed")


class RateLimitMiddleware:
    """Rate limiting middleware to control API access"""

    async def __call__(self, request: Request):
        """Check if user has exceeded their rate limits"""
        try:
            # Skip rate limiting for auth routes
            if request.url.path.startswith("/api/v1/auth"):
                return

            user = request.state.user

            # Check monthly search limits
            if user.monthly_search_limit != -1:  # -1 means unlimited
                if user.monthly_searches >= user.monthly_search_limit:
                    raise HTTPException(
                        status_code=429,
                        detail="Monthly search limit exceeded"
                    )

            # Update search counters if this is a search request
            if request.url.path.endswith("/search"):
                user.monthly_searches += 1
                user.total_searches += 1
                request.state.db.commit()

        except Exception as e:
            logger.error(f"Rate limit error: {str(e)}")
            raise HTTPException(status_code=429, detail="Rate limit error")


class AuthHandler:
    def __init__(self):
        self.secret = os.getenv('JWT_SECRET')
        self.algorithm = 'HS256'
        self.access_token_expire = 24  # hours
        self.refresh_token_expire = 7  # days

    def create_access_token(self, user_id: int):
        expires = datetime.now(UTC) + timedelta(hours=self.access_token_expire)
        return self._create_token(
            data={"user_id": user_id, "type": "access"},
            expires=expires
        )

    def create_refresh_token(self, user_id: int):
        expires = datetime.now(UTC) + timedelta(days=self.refresh_token_expire)
        return self._create_token(
            data={"user_id": user_id, "type": "refresh"},
            expires=expires
        )
