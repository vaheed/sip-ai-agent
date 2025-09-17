import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _FakeAudioMedia:
    def __init__(self):
        self._transmit = []

    def startTransmit(self, other):  # pragma: no cover - behaviour tested via agent
        self._transmit.append(other)

    def stopTransmit(self, other):  # pragma: no cover - compatibility shim
        if other in self._transmit:
            self._transmit.remove(other)


class _FakeCall:
    def __init__(self, acc=None, call_id=0):
        self.acc = acc
        self.call_id = call_id
        self._audio_media = _FakeAudioMedia()
        self._info = types.SimpleNamespace(
            stateText="", state=0, role=0, lastStatusCode=0
        )

    def getAudioMedia(self, index):
        return self._audio_media

    def getInfo(self):
        return self._info

    def makeCall(self, target_uri, call_prm):  # pragma: no cover - stub
        self._last_invite = (target_uri, call_prm)


class _FakeAccount:
    def __init__(self, ep=None):
        self.ep = ep

    def create(self, cfg):  # pragma: no cover - stub
        self.cfg = cfg

    def setRegistration(self, value):  # pragma: no cover - stub
        self.registered = value


class _FakeEndpoint:
    def __init__(self):
        self.transport = None

    def utilTimerSchedule(self, timer, time_val):  # pragma: no cover - stub
        timer._callback()

    def utilTimerCancel(self, timer):  # pragma: no cover - stub
        pass

    def libCreate(self):  # pragma: no cover - stub
        pass

    def libInit(self, cfg):  # pragma: no cover - stub
        self.cfg = cfg

    def libStart(self):  # pragma: no cover - stub
        pass

    def libDestroy(self):  # pragma: no cover - stub
        pass

    def libDelete(self):  # pragma: no cover - stub
        pass

    def transportCreate(self, transport_type, cfg):  # pragma: no cover - stub
        self.transport = cfg
        return types.SimpleNamespace()

    def codecEnum2(self):  # pragma: no cover - stub
        return []

    def codecSetPriority(self, codec, priority):  # pragma: no cover - stub
        pass


class _FakeEpConfig:
    def __init__(self):
        self.medConfig = types.SimpleNamespace(jbMin=0, jbMax=0, jbMaxPre=0)
        self.uaConfig = types.SimpleNamespace(stunServer=[])


class _FakeCallOpParam:
    def __init__(self):
        self.opt = types.SimpleNamespace(audioCount=0, videoCount=0)
        self.statusCode = 0


class _FakeTimeVal:
    def __init__(self):
        self.sec = 0
        self.msec = 0


class _FakeAccountConfig:
    def __init__(self):
        self.idUri = ""
        self.regConfig = types.SimpleNamespace(registrarUri="")
        self.sipConfig = types.SimpleNamespace(authCreds=[])
        self.mediaConfig = types.SimpleNamespace()
        self.natConfig = types.SimpleNamespace(
            iceEnabled=False,
            turnEnabled=False,
            stunServer="",
            turnServer="",
            turnUserName="",
            turnPassword="",
        )


class _FakeTransportConfig:
    def __init__(self):
        self.port = 0


_fake_pj = types.ModuleType("pjsua2")
_fake_pj.AudioMedia = _FakeAudioMedia
_fake_pj.Call = _FakeCall
_fake_pj.Account = _FakeAccount
_fake_pj.Endpoint = _FakeEndpoint
_fake_pj.EpConfig = _FakeEpConfig
_fake_pj.AccountConfig = _FakeAccountConfig
_fake_pj.TransportConfig = _FakeTransportConfig
_fake_pj.CallOpParam = _FakeCallOpParam
_fake_pj.TimerEntry = type("TimerEntry", (), {})
_fake_pj.AuthCredInfo = lambda *args, **kwargs: types.SimpleNamespace(args=args, kwargs=kwargs)
_fake_pj.TimeVal = _FakeTimeVal
_fake_pj.PJMEDIA_FRAME_TYPE_AUDIO = 0
_fake_pj.PJMEDIA_FRAME_TYPE_NONE = 1
_fake_pj.PJSUA_INVALID_ID = -1
_fake_pj.PJSIP_INV_STATE_CONFIRMED = 1
_fake_pj.PJSIP_INV_STATE_DISCONNECTED = 2
_fake_pj.PJSIP_ROLE_UAC = 3
_fake_pj.PJSIP_TRANSPORT_UDP = 0
_fake_pj.PJSUA_SRTP_DISABLED = 0
_fake_pj.PJSUA_SRTP_OPTIONAL = 1
_fake_pj.PJSUA_SRTP_MANDATORY = 2

sys.modules.setdefault("pjsua2", _fake_pj)

_fake_openai = types.ModuleType("openai")


class _FakeOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key


_fake_openai.OpenAI = _FakeOpenAI
sys.modules.setdefault("openai", _fake_openai)

_fake_websockets = types.ModuleType("websockets")


async def _fake_connect(*args, **kwargs):  # pragma: no cover - stub
    raise RuntimeError("websockets.connect stub")


_fake_websockets.connect = _fake_connect
sys.modules.setdefault("websockets", _fake_websockets)

_fake_flask = types.ModuleType("flask")


class _FakeFlask:
    def __init__(self, name):
        self.name = name

    def route(self, *args, **kwargs):  # pragma: no cover - stub
        def decorator(func):
            return func

        return decorator


_fake_flask.Flask = _FakeFlask
_fake_flask.jsonify = lambda *args, **kwargs: {}
_fake_flask.render_template_string = lambda *args, **kwargs: ""
_fake_flask.request = types.SimpleNamespace(method="GET", form={}, json={})
sys.modules.setdefault("flask", _fake_flask)

_fake_dotenv = types.ModuleType("dotenv")
_fake_dotenv.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", _fake_dotenv)


class _FakeMonitor:
    def __init__(self):
        self.logs = []

    def add_log(self, message):  # pragma: no cover - stub
        self.logs.append(message)

    def remove_call(self, *args, **kwargs):  # pragma: no cover - stub
        pass

    def update_tokens(self, *args, **kwargs):  # pragma: no cover - stub
        pass

    def update_registration(self, *args, **kwargs):  # pragma: no cover - stub
        pass

    def start(self):  # pragma: no cover - stub
        pass


sys.modules.setdefault("monitor", types.SimpleNamespace(monitor=_FakeMonitor()))
