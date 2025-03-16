from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import logging
import auth
from database import get_db
import models
import schemas
from secrets import token_hex
from urllib.parse import urlencode

router = APIRouter()
logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/login")
async def login_via_google(request: Request):
    """Redirect to Google OAuth login with state parameter for security"""
    # Generate a random state value for CSRF protection
    state = token_hex(16)

    # Store the state in the session
    request.session["oauth_state"] = state

    # Build the Google OAuth URL
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "state": state
    }

    # Create the query string
    auth_url = f"{google_auth_url}?{urlencode(params)}"

    return RedirectResponse(auth_url)


@router.get("/callback")
async def google_auth_callback(
        request: Request,
        db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Get state parameter from callback URL
        state_param = request.query_params.get("state")
        # Get state from session
        session_state = request.session.get("oauth_state")

        # Log for debugging
        logger.info(f"Callback state param: {state_param}")
        logger.info(f"Session stored state: {session_state}")

        if not state_param or not session_state or state_param != session_state:
            logger.error("CSRF attempt detected in OAuth callback")
            logger.error(f"State param: {state_param}, Session state: {session_state}")
            return RedirectResponse(f"{FRONTEND_URL}/auth-error?message=Invalid+state+parameter")

        # Clear the state from session after verifying
        if "oauth_state" in request.session:
            del request.session["oauth_state"]

        # Get authorization code from query parameters
        code = request.query_params.get("code")
        if not code:
            logger.error("Authorization code not provided")
            return RedirectResponse(f"{FRONTEND_URL}/auth-error?message=Authorization+code+not+provided")

        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            logger.error(f"Google token error: {token_response.text}")
            return RedirectResponse(f"{FRONTEND_URL}/auth-error?message=Failed+to+get+token+from+Google")

        token_info = token_response.json()

        # Verify the ID token
        try:
            id_info = id_token.verify_oauth2_token(
                token_info['id_token'],
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
        except Exception as e:
            logger.error(f"ID token verification error: {str(e)}")
            return RedirectResponse(f"{FRONTEND_URL}/auth-error?message=Failed+to+verify+ID+token")

        # Extract user information from Google's response
        email = id_info.get('email')
        if not email:
            logger.error("Email not found in Google account")
            return RedirectResponse(f"{FRONTEND_URL}/auth-error?message=Email+not+found+in+Google+account")

        # Check if user exists in the database
        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            # Create a new user if they don't exist
            user = models.User(
                email=email,
                first_name=id_info.get('given_name', ''),
                last_name=id_info.get('family_name', ''),
                hashed_password='',  # No password for OAuth users
                is_verified=True,  # Google already verified the email
                is_google_auth=True,
                profile_photo=id_info.get('picture')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user from Google OAuth: {email}")
        elif not user.is_google_auth:
            # Update existing user to indicate they can now use Google auth
            user.is_google_auth = True

            # If user wasn't verified, verify them now (Google verified them)
            if not user.is_verified:
                user.is_verified = True

            # Update profile information if missing
            if not user.first_name:
                user.first_name = id_info.get('given_name', '')
            if not user.last_name:
                user.last_name = id_info.get('family_name', '')

            # Update profile photo if available
            if id_info.get('picture'):
                user.profile_photo = id_info.get('picture')

            db.commit()
            db.refresh(user)
            logger.info(f"Updated existing user with Google OAuth: {email}")

        # Record the login time
        user.last_login = datetime.now(UTC)
        db.commit()

        # Generate JWT token for the user
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        # Redirect to frontend with token
        redirect_url = f"{FRONTEND_URL}/auth-callback?token={access_token}"
        return RedirectResponse(redirect_url)

    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        # Redirect to frontend with error
        error_redirect = f"{FRONTEND_URL}/auth-error?message={str(e)}"
        return RedirectResponse(error_redirect)


@router.get("/session-test")
async def session_test(request: Request):
    """Test if sessions are working properly"""
    counter = request.session.get("counter", 0)
    counter += 1
    request.session["counter"] = counter
    return {
        "count": counter,
        "session_id": request.session.get("session"),
        "all_session_data": dict(request.session)
    }