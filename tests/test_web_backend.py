#!/usr/bin/env python3
"""
Tests for the web backend functionality.
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.web_backend import app
from app.call_history import CallHistoryItem


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_call_history_manager():
    """Mock call history manager."""
    with patch("app.web_backend.call_history_manager") as mock:
        mock.get_call_history.return_value = []
        mock.get_active_calls.return_value = []
        mock.get_call_statistics.return_value = {
            "total_calls": 0,
            "completed_calls": 0,
            "failed_calls": 0,
            "average_duration": 0.0,
            "total_duration": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }
        yield mock


@pytest.fixture
def mock_monitor():
    """Mock monitor."""
    with patch("app.web_backend.monitor") as mock:
        mock.sip_registered = True
        mock.active_calls = []
        mock.api_tokens_used = 0
        mock.logs = []
        mock.load_config.return_value = {}
        mock.save_config.return_value = None
        mock.add_log.return_value = None
        yield mock


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_frontend_serving(client):
    """Test frontend serving."""
    with patch("builtins.open", Mock(side_effect=FileNotFoundError)):
        response = client.get("/")
        assert response.status_code == 404


def test_login(client):
    """Test authentication login."""
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_logout(client):
    """Test logout."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_system_status(client, mock_call_history_manager, mock_monitor):
    """Test system status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "sip_registered" in data
    assert "active_calls" in data
    assert "api_tokens_used" in data
    assert "uptime_seconds" in data


def test_call_history(client, mock_call_history_manager):
    """Test call history endpoint."""
    # Mock call history data
    mock_call_history_manager.get_call_history.return_value = [
        Mock(
            call_id="test-call-1",
            start_time=1640995200.0,
            end_time=1640995260.0,
            duration=60.0,
            status="completed",
        )
    ]

    response = client.get("/api/call_history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_call_history_csv(client, mock_call_history_manager):
    """Test call history CSV export."""
    mock_call_history_manager.get_call_history.return_value = [
        Mock(
            call_id="test-call-1",
            start_time=1640995200.0,
            end_time=1640995260.0,
            duration=60.0,
            status="completed",
            caller="+15551234567",
            callee="+15557654321",
            direction="incoming",
            tokens_used=100,
            cost=0.001,
            error_message=None,
        )
    ]

    response = client.get("/api/call_history/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Call ID" in response.text


def test_call_statistics(client, mock_call_history_manager):
    """Test call statistics endpoint."""
    response = client.get("/api/call_history/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "completed_calls" in data
    assert "failed_calls" in data


def test_logs(client, mock_monitor):
    """Test logs endpoint."""
    mock_monitor.logs = ["[2024-01-01 12:00:00] Test log message"]

    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)


def test_config_get_unauthorized(client):
    """Test config endpoint without authentication."""
    response = client.get("/api/config")
    assert response.status_code == 401


def test_config_get_authorized(client, mock_monitor):
    """Test config endpoint with authentication."""
    # First login to get a token
    login_response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Use token in Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/config", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "config" in data


def test_config_update_unauthorized(client):
    """Test config update without authentication."""
    response = client.post("/api/config", json={"config": {"TEST": "value"}})
    assert response.status_code == 401


def test_config_update_authorized(client, mock_monitor):
    """Test config update with authentication."""
    # First login to get a token
    login_response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Use token in Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/config", json={"config": {"TEST": "value"}}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_config_reload_unauthorized(client):
    """Test config reload without authentication."""
    response = client.post("/api/config/reload")
    assert response.status_code == 401


def test_config_reload_authorized(client, mock_monitor):
    """Test config reload with authentication."""
    # First login to get a token
    login_response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Use token in Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/config/reload", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_auth_status_unauthorized(client):
    """Test auth status without authentication."""
    response = client.get("/api/auth/status")
    assert response.status_code == 401


def test_auth_status_authorized(client):
    """Test auth status with authentication."""
    # First login to get a token
    login_response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Use token in Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["username"] == "admin"
