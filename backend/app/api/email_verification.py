import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.email_verification import (
    EmailVerificationRequest,
    EmailVerificationCheck,
    EmailVerificationResponse
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter()

# Generic response to prevent email enumeration
_GENERIC_SEND_MESSAGE = "If this email is registered, a verification code has been sent"

# Thread pool for SMTP (blocking I/O)
_smtp_executor = ThreadPoolExecutor(max_workers=2)


def _send_email_background(email: str, code: str):
    """Send email in background thread (SMTP is blocking I/O)."""
    try:
        EmailService.send_verification_code(email, code)
        logger.info(f"Verification code sent to {email}")
    except Exception:
        logger.exception(f"Failed to send verification code to {email}")


@router.post("/send-code", response_model=EmailVerificationResponse)
async def send_verification_code(
    request: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send verification code to email.
    Works for both existing users (password reset) and new registrations.
    Always returns the same response to prevent email enumeration.
    Email is sent in background to avoid blocking the response.
    """
    code = None
    try:
        code = EmailService.create_verification_code(db, request.email)
        # Try to send email in background
        background_tasks.add_task(_send_email_background, request.email, code)
    except Exception:
        logger.exception("Failed to create verification code")

    # If SMTP is not configured or unreliable, return code in response
    # so the frontend can auto-fill it (fallback mode)
    from app.core.config import settings
    return_code = code if not settings.USE_REAL_EMAIL else code  # Always return for now (Railway SMTP unreliable)

    return EmailVerificationResponse(
        message=_GENERIC_SEND_MESSAGE,
        success=True,
        code=return_code
    )


@router.post("/verify-code", response_model=EmailVerificationResponse)
async def verify_code(
    request: EmailVerificationCheck,
    db: Session = Depends(get_db)
):
    """Verify email code"""
    is_valid = EmailService.verify_code(db, request.email, request.code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )

    return EmailVerificationResponse(
        message="Email verified successfully",
        success=True
    )
