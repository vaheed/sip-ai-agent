import asyncio
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import ConfigurationError, read_env_file as config_read_env_file, write_env_file as config_write_env_file
from app.monitor import Monitor


@pytest.fixture
def monitor(tmp_path: Path) -> Monitor:
    monitor = Monitor()
    monitor._reload_poll_interval = 0.01  # type: ignore[attr-defined]
    monitor._reload_restart_delay = 0.0  # type: ignore[attr-defined]
    monitor.dashboard_dir = tmp_path
    return monitor


@pytest.fixture
def client(monitor: Monitor):
    with TestClient(monitor.app) as test_client:
        # Ensure the startup hook has a chance to populate the event loop reference.
        if monitor._loop is None:  # type: ignore[attr-defined]
            monitor._loop = asyncio.get_event_loop()  # type: ignore[attr-defined]
        yield test_client


def _login(client: TestClient, username: str = "admin", password: str = "admin") -> None:
    response = client.post(
        "/login",
        data={"username": username, "password": password, "next": "/dashboard"},
        allow_redirects=False,
    )
    assert response.status_code == 303


def test_login_logout_and_dashboard_protection(client: TestClient, monitor: Monitor) -> None:
    response = client.get("/dashboard", allow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")

    invalid = client.post(
        "/login",
        data={"username": "wrong", "password": "bad", "next": "/dashboard"},
        allow_redirects=False,
    )
    assert invalid.status_code == 200
    assert "Invalid username or password" in invalid.text

    _login(client)
    assert monitor.session_cookie in client.cookies

    dashboard = client.get("/dashboard", allow_redirects=False)
    assert dashboard.status_code == 503
    assert "Dashboard assets unavailable" in dashboard.text

    logout = client.post("/logout", allow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"

    follow_up = client.get("/dashboard", allow_redirects=False)
    assert follow_up.status_code == 303
    assert follow_up.headers["location"].startswith("/login")


def test_update_config_validation_error(
    client: TestClient, monitor: Monitor, monkeypatch: pytest.MonkeyPatch
) -> None:
    _login(client)

    validate_called = False
    reload_called = False
    write_called = False

    def fake_validate(values, include_os_environ):
        nonlocal validate_called
        validate_called = True
        raise ConfigurationError("bad config", details=["SIP_DOMAIN: invalid"])

    def fake_reload():
        nonlocal reload_called
        reload_called = True
        return {"status": "noop"}

    def fake_write(values):
        nonlocal write_called
        write_called = True

    monkeypatch.setattr("app.monitor.validate_env_map", fake_validate)
    monkeypatch.setattr(monitor, "request_safe_reload", fake_reload)
    monkeypatch.setattr("app.monitor.write_env_file", fake_write)

    response = client.post(
        "/api/update_config",
        json={"SIP_DOMAIN": "bad.example.com"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "bad config"
    assert payload["details"] == ["SIP_DOMAIN: invalid"]

    assert validate_called is True
    assert reload_called is False
    assert write_called is False


def test_update_config_json_persists_and_returns_reload(
    client: TestClient, monitor: Monitor, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _login(client)

    env_path = tmp_path / ".env"
    baseline = {
        "SIP_DOMAIN": "example.com",
        "SIP_USER": "1001",
        "SIP_PASS": "secret",
        "OPENAI_API_KEY": "sk-test",
        "AGENT_ID": "agent-1",
    }
    config_write_env_file(baseline, path=env_path)

    monkeypatch.setattr(
        "app.monitor.read_env_file", lambda: config_read_env_file(env_path)
    )
    monkeypatch.setattr(
        "app.monitor.write_env_file",
        lambda values: config_write_env_file(values, path=env_path),
    )

    reload_payload = {
        "status": "restarting",
        "active_calls": 0,
        "message": "Configuration saved.",
    }

    monkeypatch.setattr(monitor, "request_safe_reload", lambda: reload_payload)

    response = client.post(
        "/api/update_config",
        json={
            "SIP_DOMAIN": "new.example.com",
            "SYSTEM_PROMPT": "Be helpful.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["reload"] == reload_payload

    result = config_read_env_file(env_path)
    assert result["SIP_DOMAIN"] == "new.example.com"
    assert result["SYSTEM_PROMPT"] == "Be helpful."
    assert result["SIP_USER"] == "1001"


def test_websocket_events_and_call_history_csv(
    client: TestClient, monitor: Monitor
) -> None:
    _login(client)

    monitor.call_history = [
        {
            "call_id": "call-1",
            "correlation_id": "corr-1",
            "start": 1700000000.0,
            "end": 1700000005.0,
        }
    ]

    with client.websocket_connect("/ws/events") as websocket:
        initial_status = websocket.receive_json()
        assert initial_status["type"] == "status"
        assert "sip_registered" in initial_status["payload"]

        initial_history = websocket.receive_json()
        assert initial_history["type"] == "call_history"
        assert initial_history["payload"] == monitor.call_history

        monitor.update_registration(True)

        received_types = set()
        deadline = time.time() + 2.0
        while time.time() < deadline and {"status", "metrics"} - received_types:
            message = websocket.receive_json()
            received_types.add(message["type"])
            if message["type"] == "status":
                assert message["payload"]["sip_registered"] is True
            if message["type"] == "metrics":
                assert "active_calls" in message["payload"]

        assert "status" in received_types
        assert "metrics" in received_types

    response = client.get("/api/call_history.csv")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith(
        "attachment; filename=\"call_history.csv\""
    )

    csv_body = "".join(response.iter_text())
    lines = [line for line in csv_body.strip().splitlines() if line]
    assert lines[0] == "call_id,correlation_id,start,end,duration_seconds"
    assert lines[1].startswith("call-1,corr-1,")
