import threading
import time

from app.monitor import Monitor


def _create_monitor() -> Monitor:
    monitor = Monitor()
    monitor._reload_poll_interval = 0.01  # type: ignore[attr-defined]
    monitor._reload_restart_delay = 0.0  # type: ignore[attr-defined]
    return monitor


def test_request_safe_reload_restarts_immediately(monkeypatch):
    monitor = _create_monitor()
    restart_event = threading.Event()

    def fake_restart() -> None:
        restart_event.set()

    monkeypatch.setattr(monitor, "_perform_process_restart", fake_restart)

    result = monitor.request_safe_reload()
    assert result["status"] == "restarting"
    assert result["active_calls"] == 0
    assert "restart" in result["message"].lower()

    assert restart_event.wait(timeout=1.0)
    if monitor._reload_thread is not None:  # type: ignore[attr-defined]
        monitor._reload_thread.join(timeout=1.0)  # type: ignore[attr-defined]


def test_request_safe_reload_waits_for_calls(monkeypatch):
    monitor = _create_monitor()
    monitor.active_calls.append("call-1")

    restart_event = threading.Event()

    def fake_restart() -> None:
        restart_event.set()

    monkeypatch.setattr(monitor, "_perform_process_restart", fake_restart)

    result = monitor.request_safe_reload()
    assert result["status"] == "waiting_for_calls"
    assert result["active_calls"] == 1
    assert "after" in result["message"].lower()

    pending = monitor.request_safe_reload()
    assert pending["status"] == "waiting_for_calls"

    time.sleep(0.05)
    assert not restart_event.is_set()

    monitor.active_calls.clear()
    assert restart_event.wait(timeout=1.0)
    if monitor._reload_thread is not None:  # type: ignore[attr-defined]
        monitor._reload_thread.join(timeout=1.0)  # type: ignore[attr-defined]
