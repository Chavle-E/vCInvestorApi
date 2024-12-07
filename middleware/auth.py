from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Depends
import jwt
from sqlalchemy.orm import Session
from database import get_db
from models import User
import os
import logging

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
    return PyJWT.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        return PyJWT.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except PyJWT.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except PyJWT.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


class AuthMiddleware:
    async def __call__(self, request: Request, db: Session = Depends(get_db)):
        logger.debug(f"Processing request: {request.method} {request.url.path}")
        try:
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

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=401, detail="Authentication failed")