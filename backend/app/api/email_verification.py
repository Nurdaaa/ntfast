import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
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
    Always returns the same response to prevent email enumeration.
    """
    # Check if a user with this email actually exists
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        # Return generic success — do NOT reveal that the email is unregistered
        logger.info(f"Verification requested for non-existent email (not sending)")
        return EmailVerificationResponse(
            message=_GENERIC_SEND_MESSAGE,
            success=True
        )

    try:
        code = EmailService.create_verification_code(db, request.email)
        EmailService.send_verification_code(request.email, code)
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
