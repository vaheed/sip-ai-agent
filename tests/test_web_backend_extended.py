#!/usr/bin/env python3
"""
Extended tests for the web backend functionality including new components.
"""

import json
import time
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.call_history import CallHistoryItem
from app.web_backend import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_call_history_manager():
    """Mock call history manager with comprehensive data."""
    with patch("app.web_backend.call_history_manager") as mock:
        # Mock call history data
        mock_calls = [
            Mock(
                call_id="test-call-1",
                start=1640995200.0,
                end=1640995260.0,
                duration=60.0,
                status="completed",
                caller="+15551234567",
                callee="+15557654321",
                direction="incoming",
                tokens_used=150,
                cost=0.002,
                error_message=None,
            ),
            Mock(
                call_id="test-call-2",
                start=1640995300.0,
                end=None,
                duration=None,
                status="failed",
                caller="+15551234568",
                callee="+15557654322",
                direction="outgoing",
                tokens_used=0,
                cost=0.0,
                error_message="Connection timeout",
            ),
        ]
        
        mock.get_call_history.return_value = mock_calls
        mock.get_active_calls.return_value = ["test-call-2"]
        mock.get_call_statistics.return_value = {
            "total_calls": 2,
            "successful_calls": 1,
            "failed_calls": 1,
            "average_duration": 60.0,
            "longest_call": 60.0,
            "shortest_call": 60.0,
            "total_duration": 60.0,
            "total_tokens": 150,
            "average_tokens_per_call": 75.0,
            "max_tokens_used": 150,
            "total_cost": 0.002,
            "cost_per_token": 0.000013,
            "success_rate": 0.5,
            "calls_last_24h": 1,
            "calls_last_7d": 2,
            "calls_last_30d": 2,
        }
        yield mock


@pytest.fixture
def mock_monitor():
    """Mock monitor with comprehensive data."""
    with patch("app.web_backend.monitor") as mock:
        mock.sip_registered = True
        mock.active_calls = ["test-call-2"]
        mock.api_tokens_used = 150
        mock.logs = [
            "[2024-01-01 12:00:00] INFO: SIP registration successful",
            "[2024-01-01 12:01:00] ERROR: Call failed - Connection timeout",
            "[2024-01-01 12:02:00] WARNING: High token usage detected",
            "[2024-01-01 12:03:00] DEBUG: WebSocket connection established",
        ]
        mock.start_time = time.time() - 3600  # 1 hour ago
        mock.load_config.return_value = {
            "sip": {
                "domain": "test.sip.com",
                "username": "testuser",
                "password": "testpass",
            },
            "openai": {
                "mode": "realtime",
                "model": "gpt-4o-mini",
                "voice": "alloy",
                "max_tokens": 4096,
            },
            "audio": {
                "sample_rate": 16000,
            },
            "system": {
                "log_level": "INFO",
                "metrics_enabled": True,
            },
        }
        mock.save_config.return_value = None
        mock.add_log.return_value = None
        yield mock


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for protected endpoints."""
    login_response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_system_status_comprehensive(client, mock_call_history_manager, mock_monitor):
    """Test system status endpoint with comprehensive data."""
    response = client.get("/api/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["sip_registered"] is True
    assert data["active_calls"] == ["test-call-2"]
    assert data["api_tokens_used"] == 150
    assert data["uptime_seconds"] > 0
    assert "system_metrics" in data
    assert data["system_metrics"]["total_calls"] == 2
    assert data["system_metrics"]["active_calls_count"] == 1


def test_call_history_comprehensive(client, mock_call_history_manager):
    """Test call history endpoint with comprehensive data."""
    response = client.get("/api/call_history")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Check first call (completed)
    call1 = data[0]
    assert call1["call_id"] == "test-call-1"
    assert call1["status"] == "completed"
    assert call1["tokens_used"] == 150
    assert call1["cost"] == 0.002
    
    # Check second call (failed)
    call2 = data[1]
    assert call2["call_id"] == "test-call-2"
    assert call2["status"] == "failed"
    assert call2["tokens_used"] == 0
    assert call2["cost"] == 0.0


def test_call_history_csv_comprehensive(client, mock_call_history_manager):
    """Test call history CSV export with comprehensive data."""
    response = client.get("/api/call_history/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    csv_content = response.text
    assert "Call ID" in csv_content
    assert "test-call-1" in csv_content
    assert "test-call-2" in csv_content
    assert "completed" in csv_content
    assert "failed" in csv_content


def test_call_statistics_comprehensive(client, mock_call_history_manager):
    """Test call statistics endpoint with comprehensive data."""
    response = client.get("/api/call_history/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_calls"] == 2
    assert data["successful_calls"] == 1
    assert data["failed_calls"] == 1
    assert data["average_duration"] == 60.0
    assert data["longest_call"] == 60.0
    assert data["shortest_call"] == 60.0
    assert data["total_duration"] == 60.0
    assert data["total_tokens"] == 150
    assert data["average_tokens_per_call"] == 75.0
    assert data["max_tokens_used"] == 150
    assert data["total_cost"] == 0.002
    assert data["cost_per_token"] == 0.000013
    assert data["success_rate"] == 0.5
    assert data["calls_last_24h"] == 1
    assert data["calls_last_7d"] == 2
    assert data["calls_last_30d"] == 2


def test_logs_comprehensive(client, mock_monitor):
    """Test logs endpoint with comprehensive data."""
    response = client.get("/api/logs")
    assert response.status_code == 200
    
    data = response.json()
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)
    assert len(data["logs"]) == 4
    
    # Check log levels are present
    log_content = " ".join(data["logs"])
    assert "INFO" in log_content
    assert "ERROR" in log_content
    assert "WARNING" in log_content
    assert "DEBUG" in log_content


def test_logs_with_limit(client, mock_monitor):
    """Test logs endpoint with limit parameter."""
    response = client.get("/api/logs?limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["logs"]) == 2


def test_config_get_comprehensive(client, mock_monitor, auth_headers):
    """Test config endpoint with comprehensive data."""
    response = client.get("/api/config", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "sip" in data
    assert "openai" in data
    assert "audio" in data
    assert "system" in data
    
    # Check SIP config
    assert data["sip"]["domain"] == "test.sip.com"
    assert data["sip"]["username"] == "testuser"
    
    # Check OpenAI config
    assert data["openai"]["mode"] == "realtime"
    assert data["openai"]["model"] == "gpt-4o-mini"
    assert data["openai"]["voice"] == "alloy"
    assert data["openai"]["max_tokens"] == 4096
    
    # Check audio config
    assert data["audio"]["sample_rate"] == 16000
    
    # Check system config
    assert data["system"]["log_level"] == "INFO"
    assert data["system"]["metrics_enabled"] is True


def test_config_update_comprehensive(client, mock_monitor, auth_headers):
    """Test config update with comprehensive data."""
    new_config = {
        "sip": {
            "domain": "updated.sip.com",
            "username": "updateduser",
            "password": "updatedpass",
        },
        "openai": {
            "mode": "legacy",
            "model": "gpt-4",
            "voice": "nova",
            "max_tokens": 8192,
        },
        "audio": {
            "sample_rate": 48000,
        },
        "system": {
            "log_level": "DEBUG",
            "metrics_enabled": False,
        },
    }
    
    response = client.post("/api/config", json=new_config, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


def test_config_reload_comprehensive(client, mock_monitor, auth_headers):
    """Test config reload endpoint."""
    response = client.post("/api/config/reload", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


def test_websocket_endpoint(client):
    """Test WebSocket endpoint connection."""
    with client.websocket_connect("/ws/events") as websocket:
        # Send ping message
        websocket.send_json({"type": "ping"})
        
        # Receive pong response
        data = websocket.receive_json()
        assert data["type"] == "pong"


def test_websocket_system_updates(client, mock_monitor):
    """Test WebSocket system updates."""
    with client.websocket_connect("/ws/events") as websocket:
        # Wait for system update
        data = websocket.receive_json()
        assert data["type"] == "system_update"
        assert "data" in data
        assert "sip_registered" in data["data"]


def test_frontend_serving_success(client):
    """Test successful frontend serving."""
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "<html>Test</html>"
        response = client.get("/")
        assert response.status_code == 200
        assert "Test" in response.text


def test_health_check_detailed(client):
    """Test detailed health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert "checks" in data


def test_auth_flow_comprehensive(client):
    """Test comprehensive authentication flow."""
    # Test login
    login_response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    assert token is not None
    
    # Test auth status
    headers = {"Authorization": f"Bearer {token}"}
    status_response = client.get("/api/auth/status", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["authenticated"] is True
    
    # Test logout
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["success"] is True


def test_error_handling_invalid_endpoints(client):
    """Test error handling for invalid endpoints."""
    # Test non-existent endpoint
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    
    # Test invalid method
    response = client.delete("/api/status")
    assert response.status_code == 405


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/api/status")
    assert response.status_code == 200
    
    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers


def test_rate_limiting_behavior(client):
    """Test rate limiting behavior (if implemented)."""
    # Make multiple rapid requests
    responses = []
    for _ in range(10):
        response = client.get("/api/status")
        responses.append(response.status_code)
    
    # All should succeed (no rate limiting implemented yet)
    assert all(status == 200 for status in responses)


def test_concurrent_requests(client, mock_call_history_manager, mock_monitor):
    """Test handling of concurrent requests."""
    import threading
    import time
    
    results = []
    errors = []
    
    def make_request():
        try:
            response = client.get("/api/status")
            results.append(response.status_code)
        except Exception as e:
            errors.append(str(e))
    
    # Create multiple threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All requests should succeed
    assert len(errors) == 0
    assert all(status == 200 for status in results)
    assert len(results) == 5


def test_system_metrics_endpoint(client):
    """Test system metrics endpoint."""
    response = client.get("/api/system/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "timestamp" in data
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data
    assert "process" in data
    
    # Check CPU data structure
    assert "usage_percent" in data["cpu"]
    assert "count" in data["cpu"]
    
    # Check memory data structure
    assert "total" in data["memory"]
    assert "usage_percent" in data["memory"]
    
    # Check disk data structure
    assert "total" in data["disk"]
    assert "usage_percent" in data["disk"]
    
    # Check network data structure
    assert "bytes_sent" in data["network"]
    assert "bytes_recv" in data["network"]
    
    # Check process data structure
    assert "pid" in data["process"]
    assert "threads" in data["process"]


def test_admin_dashboard_data_integration(client, mock_call_history_manager, mock_monitor):
    """Test integration of all data sources for admin dashboard."""
    # Test all endpoints that admin dashboard uses
    endpoints = [
        "/api/status",
        "/api/call_history/statistics", 
        "/healthz",
        "/api/system/metrics"
    ]
    
    responses = {}
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        responses[endpoint] = response.json()
    
    # Verify data consistency
    status_data = responses["/api/status"]
    stats_data = responses["/api/call_history/statistics"]
    health_data = responses["/healthz"]
    metrics_data = responses["/api/system/metrics"]
    
    # Status data should have required fields
    assert "sip_registered" in status_data
    assert "active_calls" in status_data
    assert "api_tokens_used" in status_data
    
    # Statistics data should have required fields
    assert "total_calls" in stats_data
    assert "success_rate" in stats_data
    assert "total_cost" in stats_data
    
    # Health data should have required fields
    assert "status" in health_data
    assert "timestamp" in health_data
    
    # Metrics data should have required fields
    assert "cpu" in metrics_data
    assert "memory" in metrics_data
    assert "disk" in metrics_data


def test_enhanced_call_statistics(client, mock_call_history_manager):
    """Test enhanced call statistics with new fields."""
    mock_call_history_manager.get_call_statistics.return_value = {
        "total_calls": 10,
        "completed_calls": 8,
        "failed_calls": 2,
        "average_duration": 45.5,
        "longest_call": 120.0,
        "shortest_call": 5.0,
        "total_duration": 455.0,
        "total_tokens": 5000,
        "max_tokens_used": 800,
        "total_cost": 0.015,
        "calls_last_24h": 3,
        "calls_last_7d": 8,
        "calls_last_30d": 10,
    }
    
    response = client.get("/api/call_history/statistics")
    assert response.status_code == 200
    
    data = response.json()
    
    # Test calculated fields
    assert data["total_calls"] == 10
    assert data["successful_calls"] == 8
    assert data["failed_calls"] == 2
    assert data["success_rate"] == 0.8  # 8/10
    assert data["average_tokens_per_call"] == 500  # 5000/10
    assert data["cost_per_token"] == 0.000003  # 0.015/5000
    assert data["longest_call"] == 120.0
    assert data["shortest_call"] == 5.0
    assert data["calls_last_24h"] == 3
    assert data["calls_last_7d"] == 8
    assert data["calls_last_30d"] == 10
