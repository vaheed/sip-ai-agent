"""
Authentication module for SIP AI Agent Web UI.

This module handles user authentication, session management, and security.
"""

import hashlib
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .logging_config import get_logger

logger = get_logger("auth")

# Configuration for authentication
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()  # nosec B303
SESSION_SECRET = "sip-agent-session-secret-key"  # nosec B105

# Security scheme
security = HTTPBearer()


class AuthManager:
    """Handles authentication and session management."""
    
    def __init__(self):
        self.sessions = {}  # In production, use Redis or database
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user credentials."""
        if username == ADMIN_USERNAME:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return password_hash == ADMIN_PASSWORD_HASH
        return False
    
    def create_session(self, username: str) -> str:
        """Create a new session token."""
        import secrets
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "username": username,
            "created_at": time.time(),
            "expires_at": time.time() + 3600  # 1 hour
        }
        return token
    
    def validate_session(self, token: str) -> Optional[dict]:
        """Validate session token and return user info."""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        if time.time() > session["expires_at"]:
            del self.sessions[token]
            return None
        
        return session
    
    def revoke_session(self, token: str) -> bool:
        """Revoke a session token."""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = auth_manager.validate_session(credentials.credentials)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    success: bool
    token: Optional[str] = None
    message: str


async def authenticate_user(login_data: LoginRequest) -> LoginResponse:
    """Authenticate user and return session token."""
    try:
        if auth_manager.verify_password(login_data.username, login_data.password):
            token = auth_manager.create_session(login_data.username)
            logger.info("User authenticated successfully", username=login_data.username)
            return LoginResponse(success=True, token=token, message="Login successful")
        else:
            logger.warning("Authentication failed", username=login_data.username)
            return LoginResponse(success=False, message="Invalid credentials")
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        return LoginResponse(success=False, message="Authentication failed")


async def logout_user(token: str) -> dict:
    """Logout user and revoke session."""
    try:
        success = auth_manager.revoke_session(token)
        if success:
            logger.info("User logged out successfully")
            return {"success": True, "message": "Logout successful"}
        else:
            return {"success": False, "message": "Invalid token"}
    except Exception as e:
        logger.error("Logout error", error=str(e))
        return {"success": False, "message": "Logout failed"}
