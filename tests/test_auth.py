"""
Tests for authentication module.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.auth import AuthManager, authenticate_user, get_current_user, LoginRequest, LoginResponse


class TestAuthManager:
    """Test AuthManager class."""
    
    def test_init(self):
        """Test AuthManager initialization."""
        auth_manager = AuthManager()
        assert auth_manager.sessions == {}
    
    def test_verify_password_correct(self):
        """Test password verification with correct credentials."""
        auth_manager = AuthManager()
        assert auth_manager.verify_password("admin", "admin123") is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect credentials."""
        auth_manager = AuthManager()
        assert auth_manager.verify_password("admin", "wrongpassword") is False
        assert auth_manager.verify_password("wronguser", "admin123") is False
    
    def test_create_session(self):
        """Test session creation."""
        auth_manager = AuthManager()
        token = auth_manager.create_session("admin")
        
        assert token is not None
        assert len(token) > 0
        assert token in auth_manager.sessions
        
        session = auth_manager.sessions[token]
        assert session["username"] == "admin"
        assert "created_at" in session
        assert "expires_at" in session
    
    def test_validate_session_valid(self):
        """Test session validation with valid session."""
        auth_manager = AuthManager()
        token = auth_manager.create_session("admin")
        
        user_info = auth_manager.validate_session(token)
        assert user_info is not None
        assert user_info["username"] == "admin"
    
    def test_validate_session_invalid(self):
        """Test session validation with invalid session."""
        auth_manager = AuthManager()
        user_info = auth_manager.validate_session("invalid_token")
        assert user_info is None
    
    def test_revoke_session(self):
        """Test session revocation."""
        auth_manager = AuthManager()
        token = auth_manager.create_session("admin")
        
        assert token in auth_manager.sessions
        success = auth_manager.revoke_session(token)
        
        assert success is True
        assert token not in auth_manager.sessions
    
    def test_revoke_session_invalid(self):
        """Test session revocation with invalid token."""
        auth_manager = AuthManager()
        success = auth_manager.revoke_session("invalid_token")
        assert success is False


class TestAuthenticateUser:
    """Test authenticate_user function."""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        login_data = LoginRequest(username="admin", password="admin123")
        result = await authenticate_user(login_data)
        
        assert isinstance(result, LoginResponse)
        assert result.success is True
        assert result.token is not None
        assert result.message == "Login successful"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self):
        """Test failed user authentication."""
        login_data = LoginRequest(username="admin", password="wrongpassword")
        result = await authenticate_user(login_data)
        
        assert isinstance(result, LoginResponse)
        assert result.success is False
        assert result.token is None
        assert result.message == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username."""
        login_data = LoginRequest(username="invaliduser", password="admin123")
        result = await authenticate_user(login_data)
        
        assert isinstance(result, LoginResponse)
        assert result.success is False
        assert result.token is None
        assert result.message == "Invalid credentials"


class TestGetCurrentUser:
    """Test get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid token."""
        from app.auth import HTTPAuthorizationCredentials, auth_manager
        
        # Create a valid session first
        token = auth_manager.create_session("admin")
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user_info = await get_current_user(credentials)
        assert user_info["username"] == "admin"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        from app.auth import HTTPAuthorizationCredentials, HTTPException
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test get_current_user with no credentials."""
        from app.auth import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)
        
        assert exc_info.value.status_code == 401
