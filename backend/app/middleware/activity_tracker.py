"""
Activity Tracking Middleware

This middleware automatically tracks user activity on all authenticated API requests.
It updates ONLY the last_activity timestamp, NOT last_login.

SECURITY:
- last_login should ONLY be updated on actual authentication (POST /api/auth/login)
- last_activity is updated on ANY authenticated request
- This allows proper tracking of:
  * Real login events (last_login)
  * User activity/presence (last_activity)
  * Security monitoring (detecting unauthorized logins)
"""

import re
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.database import SessionLocal
from app.services.user_service import update_last_activity
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class ActivityTrackerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track user activity on authenticated requests

    This middleware:
    1. Extracts JWT token from Authorization header
    2. Decodes the token to get user_id
    3. Updates last_activity timestamp in database
    4. Does NOT update last_login (security requirement)

    CRITICAL: Explicitly bypasses WebSocket connections in __call__
    to prevent BaseHTTPMiddleware from interfering with WS upgrade.

    Excluded paths:
    - /ws/* (WebSocket endpoints handle their own activity tracking)
    - /api/auth/login (handled explicitly in login endpoint)
    - /api/auth/logout (user is logging out, no need to track activity)
    - /api/auth/heartbeat (explicitly handles activity updates)
    - /docs, /redoc, /openapi.json (documentation endpoints)
    - / and /health (public endpoints)
    """

    # Paths that should NOT trigger activity tracking
    EXCLUDED_PATHS = [
        r'^/ws/.*',  # WebSocket endpoints
        r'^/api/auth/login$',  # Login endpoint
        r'^/api/auth/logout$',  # Logout endpoint
        r'^/api/auth/heartbeat$',  # Heartbeat endpoint
        r'^/docs$',  # OpenAPI docs
        r'^/redoc$',  # ReDoc
        r'^/openapi\.json$',  # OpenAPI schema
        r'^/$',  # Root endpoint
        r'^/health$',  # Health check
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_patterns = [re.compile(pattern) for pattern in self.EXCLUDED_PATHS]

    async def __call__(self, scope, receive, send):
        """
        CRITICAL: Explicitly bypass non-HTTP requests (WebSocket, lifespan).
        BaseHTTPMiddleware can interfere with WebSocket upgrade handshake.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

    def is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from activity tracking"""
        return any(pattern.match(path) for pattern in self.excluded_patterns)

    async def dispatch(self, request: Request, call_next):
        """Process the request and update user activity if authenticated"""

        # Check if path is excluded
        if self.is_excluded_path(request.url.path):
            return await call_next(request)

        # Try to extract user ID from JWT token
        user_id = None
        authorization = request.headers.get("Authorization")

        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                # Decode token to get user_id
                payload = decode_access_token(token)
                if payload:
                    user_id = int(payload.get("sub"))
            except Exception:
                # Invalid token or error decoding - continue without tracking
                pass

        # Process the request
        response = await call_next(request)

        # Update activity AFTER successful request (only for authenticated users)
        # We do this after the request to ensure the request was successful
        if user_id and response.status_code < 400:  # Only track on successful requests
            try:
                db = SessionLocal()
                try:
                    # SECURITY: Update ONLY last_activity, NOT last_login
                    update_last_activity(db, user_id)
                finally:
                    db.close()
            except Exception as e:
                # Don't fail the request if activity tracking fails
                logger.warning(f"Failed to update activity for user {user_id}: {e}")

        return response
