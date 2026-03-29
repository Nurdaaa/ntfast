from pydantic import BaseModel, EmailStr, Field, field_serializer, model_serializer
from datetime import datetime
from typing import Optional, Any


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(BaseModel):
    """Schema for user creation"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="analyst", pattern="^(admin|analyst|viewer)$")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: str
    is_active: bool
    is_online: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    previous_login: Optional[datetime] = None  # For security: shows REAL last login before current
    session_start: Optional[datetime] = None  # Current session start time
    total_online_time: Optional[int] = 0  # Total time online in seconds

    # Pydantic v2: model serializer to ensure datetime with 'Z' suffix
    @model_serializer(mode='wrap', when_used='json')
    def serialize_model(self, serializer: Any, info: Any) -> Any:
        data = serializer(self)
        # Add 'Z' suffix to all datetime fields
        datetime_fields = ['created_at', 'last_login', 'previous_login', 'session_start']
        for field in datetime_fields:
            if field in data and data[field] is not None:
                # Remove existing timezone info and add 'Z'
                if isinstance(data[field], str):
                    # Already serialized by default serializer
                    if not data[field].endswith('Z'):
                        # VALIDATION: Check if timestamp is valid ISO format
                        # Valid format must contain 'T': "2025-11-23T17:26:41.080090"
                        # Invalid formats like "2025Z" should be set to None
                        if 'T' not in data[field]:
                            pass  # Invalid timestamp format, set to None below
                            data[field] = None
                            continue

                        # FIXED: Remove timezone by splitting on '+' only (not '-')
                        # ISO format: "2025-11-23T17:26:41.080090" or "2025-11-23T17:26:41.080090+00:00"
                        # We want to preserve the date part before 'T'
                        timestamp = data[field].split('+')[0]  # Remove +XX:XX timezone if present

                        # Handle UTC offset with minus: "2025-11-23T17:26:41-05:00"
                        # Split by T, then check if time part has timezone
                        date_part, time_part = timestamp.split('T', 1)
                        # Remove any timezone offset after the time (e.g., "-05:00")
                        # Look for timezone pattern like "-05:00" or "-0500" at the end
                        if time_part.count('-') > 0:
                            # Check if the last dash is part of a timezone (has digits after it)
                            parts = time_part.rsplit('-', 1)
                            if len(parts) == 2 and parts[1].replace(':', '').isdigit():
                                # This is a timezone offset, remove it
                                time_part = parts[0]

                        timestamp = f"{date_part}T{time_part}"
                        data[field] = timestamp + 'Z'
        return data

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    """Schema for updating user role"""
    role: str = Field(..., pattern="^(admin|analyst|viewer)$")


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    active_sessions_count: Optional[int] = None  # Number of active sessions
    session_start: Optional[str] = None  # Backend timestamp - single source of truth


class TokenData(BaseModel):
    """Schema for token data"""
    user_id: Optional[int] = None


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for reset password with code"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)


class UserAnalysisStats(BaseModel):
    """Schema for user analysis statistics"""
    total_analyses: int = 0
    pending_analyses: int = 0
    in_progress_analyses: int = 0
    completed_analyses: int = 0
    average_risk_score: Optional[float] = None


class UserDetailedProfile(UserResponse):
    """Schema for detailed user profile with activity history and analysis stats"""
    analysis_stats: UserAnalysisStats

    # Inherits field_serializer from UserResponse
    class Config:
        from_attributes = True
