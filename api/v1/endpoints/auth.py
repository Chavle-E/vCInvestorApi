from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
from fastapi.responses import JSONResponse
import asyncio
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import logging
from datetime import datetime, timedelta, UTC
import auth
import bcrypt
from auth import verify_refresh_token, create_access_token, create_refresh_token, revoke_refresh_token
from services.loops_client import LoopsClient
from services.user_tier_service import get_user_tier
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)
loops = LoopsClient()


def generate_verification_code(length=6):
    """Generate a numeric verification code of specified length"""
    import random
    # Generate random digits
    digits = ''.join(str(random.randint(0, 9)) for _ in range(length))
    return digits


async def send_otp_email(email: str, otp: str, first_name: str = None):
    """Send OTP email via Loops.so"""
    try:
        # Send the OTP email using our updated LoopsClient
        result = loops.send_otp_email(email, otp, first_name)

        if result:
            logger.info(f"OTP email sent successfully to {email}")
        else:
            logger.error(f"Failed to send OTP email to {email} - no result from API")
    except Exception as e:
        logger.error(f"Exception sending OTP email to {email}: {str(e)}", exc_info=True)


async def send_verification_email(email: str, token: str, first_name: str = None):
    """Send verification email via Loops.so"""
    try:
        # Send the verification email using our updated LoopsClient
        result = loops.send_verification_email(email, token, first_name)

        if result:
            logger.info(f"Verification email sent successfully to {email}")
        else:
            logger.error(f"Failed to send verification email to {email} - no result from API")
    except Exception as e:
        logger.error(f"Exception sending verification email to {email}: {str(e)}", exc_info=True)


async def send_password_reset_email(email: str, token: str, first_name: str = None):
    """Send password reset email via Loops.so"""
    try:
        logger.info(f"Attempting to send password reset email to {email}")
        # Send the password reset email using our updated LoopsClient
        result = loops.send_password_reset_email(email, token, first_name)

        if result:
            logger.info(f"Password reset email sent successfully to {email}")
        else:
            logger.error(f"Failed to send password reset email to {email}")
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {str(e)}", exc_info=True)


@router.post('/register', response_model=None)
async def register(
        user_in: schemas.UserCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    verification_id = str(uuid.uuid4())  # Generate a unique ID
    verification_code = generate_verification_code(6)
    hashed_password = auth.get_password_hash(user_in.password)

    db_user = models.User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=hashed_password,
        verification_token=verification_code,
        verification_id=verification_id,
        is_verified=False
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    background_tasks.add_task(
        send_verification_email,
        user_in.email,
        verification_code,
        user_in.first_name
    )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )

    refresh_token = auth.create_refresh_token(user_id=db_user.id, db=db)

    return JSONResponse(
        status_code=status.HTTP_302_FOUND,
        content={"verification_id": verification_id, "flow": "email_verification"}
    )


@router.post("/login", response_model=None)  # Remove the response_model
async def login(
        credentials: schemas.UserLogin,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert password to bytes if it's a string
    pwd = credentials.password.encode('utf-8') if isinstance(credentials.password, str) else credentials.password
    hashed = user.hashed_password.encode('utf-8') if isinstance(user.hashed_password, str) else user.hashed_password

    if not bcrypt.checkpw(pwd, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if email is verified
    if not user.is_verified:
        # Generate new verification code
        verification_id = str(uuid.uuid4())
        verification_code = generate_verification_code(6)
        user.verification_token = verification_code
        user.verification_id = verification_id
        db.commit()

        # Send verification email
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            send_verification_email,
            user.email,
            verification_code,
            user.first_name
        )

        # Return 302 status code for email verification
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content={"verification_id": verification_id, "flow": "email_verification"}
        )

    # Generate OTP for 2FA
    otp_code = generate_verification_code(6)

    # Store OTP in a temporary field (add this field to User model)
    user.otp_code = otp_code
    user.otp_created_at = datetime.now(UTC)
    db.commit()

    # Send OTP via email
    background_tasks = BackgroundTasks()
    background_tasks.add_task(
        send_otp_email,  # You'll need to create this function
        user.email,
        otp_code,
        user.first_name
    )

    # Return 302 status code for 2FA verification
    return JSONResponse(
        status_code=status.HTTP_302_FOUND,
        content={"user_id": str(user.id), "flow": "2fa_verification"}
    )


@router.post("/verify-email")
async def verify_email(
        verification: schemas.VerifyEmail,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.verification_id == verification.verification_id,
        models.User.verification_token == verification.code
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_id = None
    user.last_login = datetime.now(UTC)
    db.commit()

    user_tier = get_user_tier(user)

    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id), "tier": user_tier},
        expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token = auth.create_refresh_token(user_id=user.id, db=db)

    return {
        "message": "Email verified successfully",
        "user_id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_verified": True,
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


@router.post("/verify-otp")
async def verify_otp(
        otp_data: schemas.VerifyOTP,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == otp_data.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    # Check if OTP is valid
    if user.otp_code != otp_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )

    # Check if OTP has expired (10 minutes)
    otp_expiry = user.otp_created_at + timedelta(minutes=10)
    if datetime.now(UTC) > otp_expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    # Clear OTP data
    user.otp_code = None
    user.otp_created_at = None
    user.last_login = datetime.now(UTC)
    db.commit()

    user_tier = get_user_tier(user)

    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id), "tier": user_tier},
        expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token = auth.create_refresh_token(user_id=user.id, db=db)

    return {
        "message": "OTP verified successfully",
        "user_id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


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

        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            reset_token,
            user.first_name
        )
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

    # Create new refresh token (token rotation for better security)
    new_refresh_token = create_refresh_token(user_id=user.id, db=db)

    # Revoke the old refresh token
    revoke_refresh_token(refresh_token, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }


@router.post("/logout")
async def logout(
        refresh_token: str = Body(..., embed=True),
        db: Session = Depends(get_db)
):
    """Revoke refresh token on logout"""
    success = auth.revoke_refresh_token(refresh_token, db)

    return {"message": "Successfully logged out"}
