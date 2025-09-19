import asyncio
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_login_logout_and_dashboard_protection(client: TestClient, monitor: Monitor) -> None:
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")

    invalid = client.post(
        "/login",
        data={"username": "wrong", "password": "bad", "next": "/dashboard"},
        follow_redirects=False,
    )
    assert invalid.status_code == 200
    assert "Invalid username or password" in invalid.text

    _login(client)
    assert monitor.session_cookie in client.cookies

    dashboard = client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 503
    assert "Dashboard assets unavailable" in dashboard.text

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"

    follow_up = client.get("/dashboard", follow_redirects=False)
    assert follow_up.status_code == 303
    assert follow_up.headers["location"].startswith("/login")


def test_login_uses_env_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "app.monitor.read_env_file",
        lambda: {
            "MONITOR_ADMIN_USERNAME": "env-admin",
            "MONITOR_ADMIN_PASSWORD": "env-secret",
        },
    )

    monitor = Monitor()
    monitor.dashboard_dir = tmp_path

    with TestClient(monitor.app) as client:
        if monitor._loop is None:  # type: ignore[attr-defined]
            monitor._loop = asyncio.get_event_loop()  # type: ignore[attr-defined]

        invalid = client.post(
            "/login",
            data={"username": "admin", "password": "admin", "next": "/dashboard"},
            follow_redirects=False,
        )
        assert invalid.status_code == 200
        assert "Invalid username or password" in invalid.text

        response = client.post(
            "/login",
            data={
                "username": "env-admin",
                "password": "env-secret",
                "next": "/dashboard",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303


def test_configuration_routes_removed(client: TestClient) -> None:
    _login(client)

    config_get = client.get("/api/config")
    assert config_get.status_code == 404

    config_post = client.post("/api/update_config", json={"SIP_DOMAIN": "example.com"})
    assert config_post.status_code == 404


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
