from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.core.database import Base


class User(Base):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="analyst")  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)  # Online status tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)  # ONLY updated on actual login (POST /api/auth/login)
    last_activity = Column(DateTime, nullable=True)  # Updated on ANY user activity (heartbeat, API calls)
    previous_login = Column(DateTime, nullable=True)  # Previous login for security tracking
    session_start = Column(DateTime, nullable=True)  # Current session start time
    total_online_time = Column(Integer, default=0)  # Total time online in seconds

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
