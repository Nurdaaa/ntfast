from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import secrets
import string


class EmailVerification(Base):
    """Email verification model"""
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String(6), nullable=False)  # 6-digit code
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def generate_code() -> str:
        """Generate a random 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
