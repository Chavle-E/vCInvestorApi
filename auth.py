import os
import secrets
import string
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import get_db
import bcrypt
import logging

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",
    bcrypt__default_rounds=12
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verify_password(plain_password, hashed_password):
    try:
        if not hashed_password or hashed_password.strip() == '':
            return False

        # Convert inputs to bytes if they're strings
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')

        # Use bcrypt directly to verify
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        # Log the error
        logger.error(f"Password verification error: {str(e)}")
        # Return False for any error - this indicates password verification failed
        return False


def set_password_for_oauth_user(db: Session, user_id: int, password: str) -> bool:
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False

        # Set the password hash
        user.hashed_password = get_password_hash(password)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error setting password for OAuth user: {str(e)}")
        db.rollback()
        return False


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_token(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def create_refresh_token(user_id: int, db: Session) -> str:
    expires_delta = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))
    expires_at = datetime.now(UTC) + expires_delta

    # Generate token
    token = secrets.token_urlsafe(64)

    # Create refresh token record
    refresh_token = models.RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )

    db.add(refresh_token)
    db.commit()

    return token


def verify_refresh_token(token: str, db: Session) -> Optional[models.User]:
    # Get token from database
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == token,
        models.RefreshToken.revoked == False,
        models.RefreshToken.expires_at > datetime.now(UTC)
    ).first()

    if not db_token:
        return None

    return db_token.user
