from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from middleware.auth import create_token, SUBSCRIPTION_LIMITS
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import traceback

logger = logging.getLogger(__name__)


class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None


router = APIRouter()


@router.post("/login")
async def login(email: str, db: Session = Depends(get_db)):
    """Login user with email - simplified auth for MVP"""
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user with free tier for MVP
            user = User(
                email=email,
                subscription_tier="free",
                subscription_status="active",
                **SUBSCRIPTION_LIMITS["free"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create JWT token
        token = create_token(user.id, user.email)

        return {
            "access_token": token,
            "token_type": "bearer",
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    logger.info(f"Registration attempt for email: {user_data.email}")
    try:
        # Check if user exists
        if db.query(User).filter(User.email == user_data.email).first():
            logger.warning(f"Registration failed: Email already exists - {user_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        try:
            user = User(
                email=user_data.email,
                name=user_data.name,
                subscription_tier="free",
                subscription_status="active",
                **SUBSCRIPTION_LIMITS["free"]
            )
            logger.debug(f"Creating user object: {user.__dict__}")

            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"User created successfully: {user.id}")

        except Exception as e:
            logger.error(f"Database error during user creation: {str(e)}")
            logger.error(traceback.format_exc())
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error during user creation")

        # Create token
        try:
            token = create_token(user.id, user.email)
            logger.debug("Token created successfully")
        except Exception as e:
            logger.error(f"Token creation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Token creation failed")

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "subscription": {
                    "tier": user.subscription_tier,
                    "status": user.subscription_status
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

