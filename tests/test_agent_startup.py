import io
from types import SimpleNamespace

import pytest

from app.config import ConfigurationError
import app.agent as agent


class DummyMonitor:
    def __init__(self) -> None:
        self.started = False
        self.logs: list[tuple[str, dict]] = []

    def start(self) -> None:
        self.started = True

    def add_log(self, message: str, **fields) -> None:  # type: ignore[no-untyped-def]
        self.logs.append((message, fields))


def test_main_with_configuration_error_keeps_monitor_running(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = DummyMonitor()
    monkeypatch.setattr(agent, "monitor", monitor)

    logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
    monkeypatch.setattr(agent, "logger", logger)

    config_error = ConfigurationError("invalid", details=["SIP_DOMAIN missing"])
    monkeypatch.setattr(agent, "CONFIG_ERROR", config_error)

    idle_called = False

    def fake_idle() -> None:
        nonlocal idle_called
        idle_called = True

    monkeypatch.setattr(agent, "_idle_forever", fake_idle)

    stderr = io.StringIO()
    monkeypatch.setattr(agent.sys, "stderr", stderr)

    agent.main()

    assert monitor.started is True
    assert idle_called is True

    log_messages = [message for message, _ in monitor.logs]
    assert any("Configuration validation failed" in message for message in log_messages)
    assert any("SIP_DOMAIN missing" in message for message in log_messages)
    assert any("configuration fixes" in message for message in log_messages)
