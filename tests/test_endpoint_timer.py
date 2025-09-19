import types

import pjsua2 as pj

from app import agent
from app.agent import EndpointTimer


class _FailingEndpoint(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.utilTimerSchedule = self._schedule
        self.utilTimerCancel = lambda timer: None

    def _schedule(self, timer, time_val):
        raise RuntimeError("utilTimerSchedule not available")


def test_endpoint_timer_registers_thread_on_fallback(monkeypatch):
    lib = pj.Lib.instance()
    if hasattr(lib, "reset"):
        lib.reset()

    callback_called = []

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
