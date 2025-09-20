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


def test_apply_codec_preferences_matches_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = DummyMonitor()
    monkeypatch.setattr(agent, "monitor", monitor)

    class FakeInfo:
        def __init__(self, codec_id: str) -> None:
            self.codecId = codec_id

    class FakeEndpoint:
        def __init__(self) -> None:
            self.calls: list[tuple[str, int]] = []

        def codecEnum2(self):  # pragma: no cover - exercised in test
            return [FakeInfo("pcmu/8000/1"), FakeInfo("opus/48000/2")]

        def codecSetPriority(self, codec: str, priority: int) -> None:  # pragma: no cover - stub
            self.calls.append((codec, priority))

    endpoint = FakeEndpoint()

    agent._apply_codec_preferences(endpoint, ("PCMU", "OpUs", "g722"))

    assert endpoint.calls == [("pcmu/8000/1", 240), ("opus/48000/2", 230)]

    applied_logs = [fields for message, fields in monitor.logs if fields.get("event") == "codec_preference_applied"]
    assert applied_logs, "Expected applied codec log entry"
    assert applied_logs[0]["applied_codecs"][0]["codec_id"] == "pcmu/8000/1"

    missing_logs = [fields for message, fields in monitor.logs if fields.get("event") == "codec_preference_missing"]
    assert missing_logs, "Expected warning for unavailable codecs"
    assert missing_logs[0]["requested_codecs"] == ["g722"]
