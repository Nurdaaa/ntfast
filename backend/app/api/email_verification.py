import logging
from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post("/send-code", response_model=EmailVerificationResponse)
async def send_verification_code(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Send verification code to email.
    Works for both existing users (password reset) and new registrations.
    Always returns the same response to prevent email enumeration.
    """
    try:
        code = EmailService.create_verification_code(db, request.email)
        EmailService.send_verification_code(request.email, code)
        logger.info(f"Verification code sent to {request.email}")
    except Exception:
        # Log the error but still return the generic message
        logger.exception("Failed to send verification code")

    return EmailVerificationResponse(
        message=_GENERIC_SEND_MESSAGE,
        success=True
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
