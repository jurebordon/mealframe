"""Email service using Resend for transactional emails."""
import logging

import resend

from app.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str) -> bool:
    """Send an email via Resend. Returns True on success, False on failure."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — printing email to console")
        logger.info("TO: %s | SUBJECT: %s\n%s", to, subject, html)
        return True

    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {
                "from": settings.email_from,
                "to": [to],
                "subject": subject,
                "html": html,
            }
        )
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def send_verification_email(to: str, token: str) -> bool:
    """Send email verification link."""
    link = f"{settings.frontend_url}/verify-email?token={token}"
    html = f"""
    <h2>Verify your email</h2>
    <p>Click the link below to verify your MealFrame account:</p>
    <p><a href="{link}">Verify Email</a></p>
    <p>This link expires in 24 hours.</p>
    <p>If you didn't create an account, you can safely ignore this email.</p>
    """
    return _send(to, "Verify your MealFrame email", html)


def send_password_reset_email(to: str, token: str) -> bool:
    """Send password reset link."""
    link = f"{settings.frontend_url}/reset-password?token={token}"
    html = f"""
    <h2>Reset your password</h2>
    <p>Click the link below to reset your MealFrame password:</p>
    <p><a href="{link}">Reset Password</a></p>
    <p>This link expires in 1 hour.</p>
    <p>If you didn't request a password reset, you can safely ignore this email.</p>
    """
    return _send(to, "Reset your MealFrame password", html)
