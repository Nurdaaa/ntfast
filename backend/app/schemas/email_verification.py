from pydantic import BaseModel, EmailStr


class EmailVerificationRequest(BaseModel):
    """Request to send verification code"""
    email: EmailStr


class EmailVerificationCheck(BaseModel):
    """Request to verify code"""
    email: EmailStr
    code: str


class EmailVerificationResponse(BaseModel):
    """Response for verification operations"""
    message: str
    success: bool
