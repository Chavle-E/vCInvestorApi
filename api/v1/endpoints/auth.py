from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
import asyncio
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import logging
from datetime import datetime, timedelta, UTC
import auth
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt
from auth import verify_refresh_token, create_access_token

router = APIRouter()
logger = logging.getLogger(__name__)


async def send_verification_email(email: str, token: str):
    logger.info(f"Sending verification email to {email} with token {token}")


async def send_password_reset_email(email: str, token: str):
    logger.info(f"Sending password reset email to {email} with token {token}")


@router.post('/register', response_model=schemas.UserResponse)
async def register(
        user_in: schemas.UserCreate,
        background_tasks=BackgroundTasks,
        db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    verification_token = auth.generate_token()
    hashed_password = auth.get_password_hash(user_in.password)

    db_user = models.User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_verified=False
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    background_tasks.add_task(send_verification_email, user_in.email, verification_token)

    return db_user


@router.post("/login", response_model=schemas.Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    pwd = form_data.password.encode('utf-8')
    hashed = user.hashed_password.encode('utf-8')

    if not bcrypt.checkpw(pwd, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-email")
async def verify_email(
        verification: schemas.VerifyEmail,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.verification_token == verification.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    user.is_verified = True
    user.verification_token = None
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
        password_reset: schemas.PasswordReset,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == password_reset.email).first()

    reset_token = auth.generate_token()
    reset_token_expires = datetime.now(UTC) + timedelta(hours=24)

    if user:
        user.reset_token = reset_token
        user.reset_token_expires = reset_token_expires
        db.commit()

        background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    else:
        await asyncio.sleep(0.5)

    return {"message": "If this email is registered, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
        password_reset: schemas.PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    if password_reset.new_password != password_reset.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    user = db.query(models.User).filter(models.User.reset_token == password_reset.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    if user.reset_token_expires < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    user.hashed_password = auth.get_password_hash(password_reset.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
        password_update: schemas.PasswordUpdate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    if not auth.verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    if password_update.new_password != password_update.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    current_user.hashed_password = auth.get_password_hash(password_update.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
async def update_user(
        user_update: schemas.UserUpdate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name

    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name

    if user_update.email is not None and user_update.email != current_user.email:
        # Check if email already exists
        existing_user = db.query(models.User).filter(models.User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        current_user.email = user_update.email
        current_user.is_verified = False
        verification_token = auth.generate_token()
        current_user.verification_token = verification_token

    if user_update.profile_photo is not None:
        current_user.profile_photo = user_update.profile_photo

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/deactivate")
async def deactivate_account(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    current_user.is_active = False
    db.commit()

    return {"message": "Account deactivated successfully"}


@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(
        refresh_token: str = Body(..., embed=True),
        db: Session = Depends(get_db)
):
    user = verify_refresh_token(refresh_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
