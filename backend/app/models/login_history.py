from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class LoginHistory(Base):
    """
    Login history model for tracking all user login events
    Used for security monitoring and detecting unauthorized access
    """

    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    login_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)  # When user logged out or session expired
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/device info
    location = Column(String(200), nullable=True)  # City/Country (if available)
    session_duration = Column(Integer, nullable=True)  # Duration in seconds
    is_suspicious = Column(Boolean, default=False)  # Flag for suspicious login attempts

    # Relationship to User model
    user = relationship("User", backref="login_history")

    def __repr__(self):
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, login_time='{self.login_time}')>"
