import importlib
import sys
import types

if "pydantic" not in sys.modules:
    _fake_pydantic = types.ModuleType("pydantic")
    class _FakeFieldInfo:
        def __init__(self, default=..., **kwargs):
            self.default = default
            self.alias = kwargs.get("alias")

    def _fake_field(default=..., **kwargs):
        return _FakeFieldInfo(default, **kwargs)

    class _FakeValidationError(Exception):
        def errors(self):
            return []

    def _fake_field_validator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    _fake_pydantic.Field = _fake_field
    _fake_pydantic.ValidationError = _FakeValidationError
    _fake_pydantic.field_validator = _fake_field_validator
    sys.modules["pydantic"] = _fake_pydantic

if "pydantic_settings" not in sys.modules:
    _fake_pydantic_settings = types.ModuleType("pydantic_settings")

    class _FakeBaseSettings:
        model_config = {}
        model_fields = {}

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _FakeEnvSettingsSource:
        def __init__(self, *args, **kwargs):
            pass

    class _FakeDotEnvSettingsSource(_FakeEnvSettingsSource):
        pass

    _fake_pydantic_settings.BaseSettings = _FakeBaseSettings
    _fake_pydantic_settings.SettingsConfigDict = dict
    _fake_sources = types.ModuleType("pydantic_settings.sources")
    _fake_sources.EnvSettingsSource = _FakeEnvSettingsSource
    _fake_sources.DotEnvSettingsSource = _FakeDotEnvSettingsSource
    sys.modules["pydantic_settings.sources"] = _fake_sources
    _fake_pydantic_settings.DotEnvSettingsSource = _FakeDotEnvSettingsSource
    _fake_pydantic_settings.EnvSettingsSource = _FakeEnvSettingsSource
    sys.modules["pydantic_settings"] = _fake_pydantic_settings

import app.config as config


class _StubSettings:
    sip_domain = "example.com"
    sip_user = "1001"
    sip_pass = "secret"
    openai_api_key = "test-key"
    agent_id = "test-agent"
    openai_mode = "legacy"
    openai_model = "gpt-realtime"
    openai_voice = "alloy"
    openai_temperature = 0.3
    system_prompt = "You are a helpful voice assistant."
    enable_sip = True
    enable_audio = True
    sip_transport_port = 5060
    sip_jb_min = 0
    sip_jb_max = 0
    sip_jb_max_pre = 0
    sip_enable_ice = False
    sip_enable_turn = False
    sip_stun_server = ""
    sip_turn_server = ""
    sip_turn_user = ""
    sip_turn_pass = ""
    sip_enable_srtp = False
    sip_srtp_optional = True
    sip_preferred_codecs = ()
    sip_reg_retry_base = 2.0
    sip_reg_retry_max = 60.0
    sip_invite_retry_base = 1.0
    sip_invite_retry_max = 30.0
    sip_invite_max_attempts = 5


config.get_settings = lambda: _StubSettings()

agent = importlib.import_module("app.agent")
EndpointTimer = agent.EndpointTimer
pj = importlib.import_module("pjsua2")


class _MsecEndpoint:
    def __init__(self):
        self.calls = []

    def utilTimerSchedule(self, timer, value):
        self.calls.append(value)
        timer._callback()

    @staticmethod
    def utilTimerCancel(timer):
        pass


class _TimeValEndpoint:
    def __init__(self):
        self.calls = []

    def utilTimerSchedule(self, timer, value):
        if isinstance(value, int):
            raise TypeError("TimeVal overload only")
        self.calls.append((value.sec, value.msec))
        timer._callback()

    @staticmethod
    def utilTimerCancel(timer):
        pass


class _MsecEndpoint:
    def __init__(self):
        self.calls = []

    def utilTimerSchedule(self, timer, value):
        self.calls.append(value)
        timer._callback()

    @staticmethod
    def utilTimerCancel(timer):
        pass


class _TimeValEndpoint:
    def __init__(self):
        self.calls = []

    def utilTimerSchedule(self, timer, value):
        if isinstance(value, int):
            raise TypeError("TimeVal overload only")
        self.calls.append((value.sec, value.msec))
        timer._callback()

    @staticmethod
    def utilTimerCancel(timer):
        pass


class _FailingEndpoint(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.utilTimerSchedule = self._schedule
        self.utilTimerCancel = lambda timer: None

    def _schedule(self, timer, time_val):
        raise RuntimeError("utilTimerSchedule not available")


def test_endpoint_timer_prefers_msec_variant():
    agent.monitor.logs.clear()
    endpoint = _MsecEndpoint()
    callback_called = []
    timer = EndpointTimer(endpoint, lambda: callback_called.append(True))

    timer.schedule(0.5)

    assert callback_called == [True]
    assert endpoint.calls == [500]
    assert agent.monitor.logs == []


def test_endpoint_timer_uses_timeval_when_int_overload_missing():
    agent.monitor.logs.clear()
    endpoint = _TimeValEndpoint()
    callback_called = []
    timer = EndpointTimer(endpoint, lambda: callback_called.append(True))

    timer.schedule(1.25)

    assert callback_called == [True]
    assert endpoint.calls == [(1, 250)]
    assert agent.monitor.logs == []


def test_endpoint_timer_registers_thread_on_fallback(monkeypatch):
    lib = pj.Lib.instance()
    if hasattr(lib, "reset"):
        lib.reset()

    callback_called = []

    agent.monitor.logs.clear()

    class _ImmediateTimer:
        def __init__(self, delay, func):
            self.delay = delay
            self.func = func
            self.daemon = False

        def start(self):
            self.func()

        def cancel(self):
            pass

    monkeypatch.setattr(agent.threading, "Timer", _ImmediateTimer)

    timer = EndpointTimer(_FailingEndpoint(), lambda: callback_called.append(True))
    timer.schedule(0.5)

    assert callback_called == [True]
    assert getattr(lib, "registered", [])
    name, *_ = lib.registered[-1]
    assert name == "endpoint_timer"
    assert any(
        log == "EndpointTimer fallback thread executing callback"
        for log in agent.monitor.logs
    )
