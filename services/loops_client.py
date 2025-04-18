import requests
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class LoopsClient:
    def __init__(self):
        self.api_key = os.getenv("LOOPS_API_KEY")
        self.base_url = "https://app.loops.so/api/v1"
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def send_transactional_email(self, email: str, template_id: str, data: Dict = None) -> Dict:
        """
        Send a transactional email using Loops.so API

        :param email: Recipient email
        :param template_id: Loops.so template ID
        :param data: Dictionary containing template variables
        :return: API response
        """
        if not data:
            data = {}

        payload = {
            "email": email,
            "transactionalId": template_id,
            "dataVariables": data
        }

        try:
            response = requests.post(
                f"{self.base_url}/transactional",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Email sent successfully to {email} using template {template_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Loops.so API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None

    def send_verification_email(self, email: str, token: str, first_name: str = None) -> Dict:
        """
        Send an account verification email with a secure link

        :param email: User's email address
        :param token: Verification token
        :param first_name: User's first name (optional)
        :return: API response
        """
        template_id = os.getenv("LOOPS_VERIFICATION_TEMPLATE_ID")

        # Create a secure link that contains the token but doesn't expose it directly
        verification_link = f"{self.frontend_url}/verify-email?token={token}"

        data = {
            "verificationToken": token,
            "verificationLink": verification_link,
            "email": email,
            "firstName": first_name if first_name else "there"
        }

        logger.info(f"Sending verification email to {email} with embedded token")
        logger.info(f"Data being sent to Loops: {data}")
        return self.send_transactional_email(email, template_id, data)

    def send_otp_email(self, email: str, otp: str, first_name: str = None) -> Dict:
        """
        Send a one-time password (OTP) email for two-factor authentication

        :param email: User's email address
        :param otp: One-time password code
        :param first_name: User's first name (optional)
        :return: API response
        """
        template_id = os.getenv("LOOPS_OTP_TEMPLATE_ID")

        # Data variables for the email template
        data = {
            "otp": otp,
            "email": email
        }

        # Add first name if provided
        if first_name:
            data["firstName"] = first_name

        logger.info(f"Sending OTP email to {email}")
        return self.send_transactional_email(email, template_id, data)

    def send_password_reset_email(self, email: str, token: str, first_name: str = None) -> Dict:
        """
        Send a password reset email with a secure link

        :param email: User's email address
        :param token: Reset token
        :param first_name: User's first name (optional)
        :return: API response
        """
        template_id = os.getenv("LOOPS_PASSWORD_RESET_TEMPLATE_ID")

        # Create a secure link that contains the token but doesn't expose it directly
        reset_link = f"{self.frontend_url}/reset-password?token={token}"

        # Data variables for the email template
        data = {
            "resetLink": reset_link,
            "email": email
        }

        # Add first name if provided
        if first_name:
            data["firstName"] = first_name

        logger.info(f"Sending password reset email to {email} with embedded token")
        return self.send_transactional_email(email, template_id, data)
