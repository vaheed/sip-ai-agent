#!/usr/bin/env python3
import sys
import time
import json
import asyncio
import websockets
import threading
import base64
import queue
import contextlib
from typing import Callable, Optional, TYPE_CHECKING
import pjsua2 as pj

try:
    from pjsua2 import TimerEntry as _TimerEntryBase
except ImportError:  # pragma: no cover - fallback when direct import fails
    _TimerEntryBase = getattr(pj, "TimerEntry", object)

try:
    from .observability import (
        correlation_scope,
        generate_correlation_id,
        get_logger,
        metrics,
    )
except ImportError:  # pragma: no cover - script execution fallback
    from observability import (  # type: ignore
        correlation_scope,
        generate_correlation_id,
        get_logger,
        metrics,
    )

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from app.config import Settings as AppSettings
    from pjsua2 import TimerEntry as _TimerEntryBase

try:
    from .config import ConfigurationError, get_settings
except ImportError as exc:  # pragma: no cover - script execution fallback
    if "attempted relative import" in str(exc) or getattr(exc, "name", "") in {
        "config",
        "app.config",
    }:
        from config import ConfigurationError, get_settings  # type: ignore
    else:  # pragma: no cover - surface configuration import issues
        raise

from monitor import monitor

logger = get_logger(__name__)

SETTINGS: Optional["AppSettings"]
CONFIG_ERROR: Optional[ConfigurationError] = None
try:
    SETTINGS = get_settings()
except ConfigurationError as exc:  # pragma: no cover - exercised at runtime
    CONFIG_ERROR = exc
    SETTINGS = None
else:
    CONFIG_ERROR = None

# SIP Configuration
if SETTINGS is not None:
    SIP_DOMAIN = SETTINGS.sip_domain
    SIP_USER = SETTINGS.sip_user
    SIP_PASS = SETTINGS.sip_pass

    # OpenAI Configuration
    OPENAI_API_KEY = SETTINGS.openai_api_key
    AGENT_ID = SETTINGS.agent_id

    # Additional OpenAI settings
    OPENAI_MODE = SETTINGS.openai_mode
    OPENAI_MODEL = SETTINGS.openai_model
    OPENAI_VOICE = SETTINGS.openai_voice
    OPENAI_TEMPERATURE = SETTINGS.openai_temperature
    SYSTEM_PROMPT = SETTINGS.system_prompt

    ENABLE_SIP = SETTINGS.enable_sip
    ENABLE_AUDIO = SETTINGS.enable_audio

    # SIP media and transport tuning
    SIP_TRANSPORT_PORT = SETTINGS.sip_transport_port
    SIP_JB_MIN = SETTINGS.sip_jb_min
    SIP_JB_MAX = SETTINGS.sip_jb_max
    SIP_JB_MAX_PRE = SETTINGS.sip_jb_max_pre
    SIP_ENABLE_ICE = SETTINGS.sip_enable_ice
    SIP_ENABLE_TURN = SETTINGS.sip_enable_turn
    SIP_STUN_SERVER = SETTINGS.sip_stun_server or ""
    SIP_TURN_SERVER = SETTINGS.sip_turn_server or ""
    SIP_TURN_USER = SETTINGS.sip_turn_user or ""
    SIP_TURN_PASS = SETTINGS.sip_turn_pass or ""
    SIP_ENABLE_SRTP = SETTINGS.sip_enable_srtp
    SIP_SRTP_OPTIONAL = SETTINGS.sip_srtp_optional
    SIP_PREFERRED_CODECS = SETTINGS.sip_preferred_codecs

    # Retry behaviour
    SIP_REG_RETRY_BASE = SETTINGS.sip_reg_retry_base
    SIP_REG_RETRY_MAX = SETTINGS.sip_reg_retry_max
    SIP_INVITE_RETRY_BASE = SETTINGS.sip_invite_retry_base
    SIP_INVITE_RETRY_MAX = SETTINGS.sip_invite_retry_max
    SIP_INVITE_MAX_ATTEMPTS = SETTINGS.sip_invite_max_attempts
else:  # pragma: no cover - exercised when configuration is invalid
    SIP_DOMAIN = ""
    SIP_USER = ""
    SIP_PASS = ""
    OPENAI_API_KEY = ""
    AGENT_ID = ""
    OPENAI_MODE = "legacy"
    OPENAI_MODEL = "gpt-realtime"
    OPENAI_VOICE = "alloy"
    OPENAI_TEMPERATURE = 0.3
    SYSTEM_PROMPT = "You are a helpful voice assistant."
    ENABLE_SIP = True
    ENABLE_AUDIO = True
    SIP_TRANSPORT_PORT = 5060
    SIP_JB_MIN = 0
    SIP_JB_MAX = 0
    SIP_JB_MAX_PRE = 0
    SIP_ENABLE_ICE = False
    SIP_ENABLE_TURN = False
    SIP_STUN_SERVER = ""
    SIP_TURN_SERVER = ""
    SIP_TURN_USER = ""
    SIP_TURN_PASS = ""
    SIP_ENABLE_SRTP = False
    SIP_SRTP_OPTIONAL = True
    SIP_PREFERRED_CODECS = ()
    SIP_REG_RETRY_BASE = 2.0
    SIP_REG_RETRY_MAX = 60.0
    SIP_INVITE_RETRY_BASE = 1.0
    SIP_INVITE_RETRY_MAX = 30.0
    SIP_INVITE_MAX_ATTEMPTS = 5

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION = 20  # ms
PCM_WIDTH = 2  # 16-bit PCM
FRAME_BYTES = SAMPLE_RATE * FRAME_DURATION // 1000 * PCM_WIDTH
MAX_PENDING_FRAMES = 50



class EndpointTimer(_TimerEntryBase):
    """Timer that adapts to the available ``pjsua2`` bindings."""

    def __init__(self, endpoint: pj.Endpoint, callback: Callable[[], None]) -> None:
        super().__init__()
        self._endpoint = endpoint
        self._callback = callback
        self._thread_timer: Optional[threading.Timer] = None
        self._thread_desc = None
        self._pj_thread = None

    def schedule(self, delay_seconds: float) -> None:
        """Schedule the timer to fire after ``delay_seconds``."""
        self.cancel()
        if delay_seconds < 0:
            delay_seconds = 0

        if hasattr(self._endpoint, "utilTimerSchedule") and hasattr(pj, "TimeVal"):
            try:
                seconds = int(delay_seconds)
                msec = int((delay_seconds - seconds) * 1000)
                time_val = pj.TimeVal()
                time_val.sec = seconds
                time_val.msec = msec
                self._endpoint.utilTimerSchedule(self, time_val)
                return
            except Exception as err:  # pragma: no cover - depends on runtime support
                monitor.add_log(f"Falling back to threading timer: {err}")

        # Fallback for environments where utilTimerSchedule is unavailable
        self._thread_timer = threading.Timer(delay_seconds, self._thread_timer_callback)
        self._thread_timer.daemon = True
        self._thread_timer.start()

    def cancel(self) -> None:
        """Cancel the scheduled timer if active."""
        try:
            if hasattr(self._endpoint, "utilTimerCancel"):
                self._endpoint.utilTimerCancel(self)
        except Exception:
            pass

        if self._thread_timer is not None:
            self._thread_timer.cancel()
            self._thread_timer = None

    def onTimeout(self) -> None:  # pragma: no cover - invoked by PJSIP runtime
        self._callback()

    def _thread_timer_callback(self) -> None:
        """Execute callback from fallback timer ensuring PJLIB thread registration."""
        self._register_thread_with_pjlib()
        self._callback()

    def _register_thread_with_pjlib(self) -> None:
        lib_cls = getattr(pj, "Lib", None)
        if lib_cls is None:
            return

        try:
            lib = lib_cls.instance()
        except Exception:
            return

        thread_register = getattr(lib, "threadRegister", None)
        if not callable(thread_register):
            return

        thread_is_registered = getattr(lib, "threadIsRegistered", None)
        if callable(thread_is_registered):
            try:
                if thread_is_registered():
                    return
            except Exception:
                pass

        thread_desc_cls = getattr(pj, "ThreadDesc", None)
        thread_cls = getattr(pj, "Thread", None)
        if thread_desc_cls is not None and thread_cls is not None:
            if self._thread_desc is None:
                try:
                    self._thread_desc = thread_desc_cls()
                except Exception:
                    self._thread_desc = None
            if self._pj_thread is None:
                try:
                    self._pj_thread = thread_cls()
                except Exception:
                    self._pj_thread = None

            if self._thread_desc is not None and self._pj_thread is not None:
                try:
                    thread_register("endpoint_timer", self._thread_desc, self._pj_thread)
                    return
                except TypeError:
                    pass
                except Exception:
                    return

        try:
            thread_register("endpoint_timer")
        except Exception:
            pass


# Audio callback class for PJSIP
class AudioCallback(pj.AudioMedia):
    """Bidirectional PCM media adapter between PJSIP and asyncio code."""

    def __init__(self, call):
        super().__init__()
        self.call = call
        self.is_active = True
        self.capture_queue: queue.Queue[bytes] = queue.Queue(maxsize=MAX_PENDING_FRAMES)
        self.playback_queue: queue.Queue[bytes] = queue.Queue(maxsize=MAX_PENDING_FRAMES)
        self._capture_buffer = bytearray()
        self._playback_buffer = bytearray()
        self._stop_event = threading.Event()

    # --- Internal helpers -------------------------------------------------

    def _blocking_put(self, target_queue: queue.Queue, data: bytes) -> None:
        """Put ``data`` into ``target_queue`` applying backpressure."""
        while self.is_active:
            try:
                target_queue.put(data, timeout=0.1)
                return
            except queue.Full:
                if self._stop_event.is_set():
                    break
        with contextlib.suppress(queue.Full):
            target_queue.put_nowait(data)

    def _normalize_chunk(self, data: bytes) -> bytes:
        if not data:
            return b"\x00" * FRAME_BYTES
        if len(data) < FRAME_BYTES:
            return data + b"\x00" * (FRAME_BYTES - len(data))
        if len(data) > FRAME_BYTES:
            return data[:FRAME_BYTES]
        return data

    # --- Capture path -----------------------------------------------------

    def putFrame(self, frame):  # pragma: no cover - invoked by PJSIP runtime
        if not self.is_active or frame is None:
            return
        if getattr(frame, 'type', None) != pj.PJMEDIA_FRAME_TYPE_AUDIO:
            return
        data = bytes(getattr(frame, 'buf', b''))
        if not data:
            return
        self._capture_buffer.extend(data)
        while len(self._capture_buffer) >= FRAME_BYTES:
            chunk = bytes(self._capture_buffer[:FRAME_BYTES])
            del self._capture_buffer[:FRAME_BYTES]
            self._blocking_put(self.capture_queue, chunk)

    async def get_capture_frame(self) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._capture_queue_get)

    def _capture_queue_get(self) -> bytes:
        while self.is_active or not self.capture_queue.empty():
            try:
                data = self.capture_queue.get(timeout=0.1)
                self.capture_queue.task_done()
                return data
            except queue.Empty:
                if not self.is_active:
                    break
        return b''

    # --- Playback path ----------------------------------------------------

    async def queue_playback_frame(self, data: bytes) -> None:
        if not data:
            return
        self._playback_buffer.extend(data)
        loop = asyncio.get_running_loop()
        while len(self._playback_buffer) >= FRAME_BYTES:
            chunk = bytes(self._playback_buffer[:FRAME_BYTES])
            del self._playback_buffer[:FRAME_BYTES]
            await loop.run_in_executor(None, self._blocking_put, self.playback_queue, chunk)

    async def flush_playback(self) -> None:
        if not self._playback_buffer:
            return
        loop = asyncio.get_running_loop()
        data = self._normalize_chunk(bytes(self._playback_buffer))
        self._playback_buffer.clear()
        await loop.run_in_executor(None, self._blocking_put, self.playback_queue, data)

    def _flush_playback_sync(self) -> None:
        if self._playback_buffer:
            data = self._normalize_chunk(bytes(self._playback_buffer))
            self._playback_buffer.clear()
            self._blocking_put(self.playback_queue, data)

    def onFrameRequested(self, frame):  # pragma: no cover - invoked by PJSIP runtime
        if frame is None:
            return
        if not self.is_active:
            frame.type = pj.PJMEDIA_FRAME_TYPE_NONE
            frame.buf = b''
            frame.size = 0
            return
        try:
            chunk = self.playback_queue.get(timeout=FRAME_DURATION / 1000)
            self.playback_queue.task_done()
        except queue.Empty:
            chunk = b''
        if not chunk and self._playback_buffer:
            chunk = self._normalize_chunk(bytes(self._playback_buffer))
            self._playback_buffer.clear()
        frame.type = pj.PJMEDIA_FRAME_TYPE_AUDIO
        normalized = self._normalize_chunk(chunk)
        frame.buf = normalized
        frame.size = len(normalized)

    def wait_for_playback_drain(self, timeout: float = 1.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.playback_queue.empty() and not self._playback_buffer:
                return
            time.sleep(0.01)

    def stop(self):
        if not self.is_active:
            return
        self._flush_playback_sync()
        self.is_active = False
        self._stop_event.set()
        for q in (self.capture_queue, self.playback_queue):
            with contextlib.suppress(queue.Full):
                q.put_nowait(b'')

# Call class for handling SIP calls
class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID, target_uri: Optional[str] = None):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.audio_callback = None
        self.ws = None
        self.openai_thread: Optional[threading.Thread] = None
        self.call_id = call_id
        self.target_uri = target_uri
        self._invite_attempts = 0
        self._invite_retry_timer = EndpointTimer(self.acc.ep, self._retry_invite)
        self._realtime_input_committed = False
        self.correlation_id = generate_correlation_id()
        self.monitor_call_id: Optional[str] = None

    def call_label(self) -> str:
        existing = getattr(self, 'monitor_call_id', None)
        if existing:
            return existing
        call_identifier = getattr(self, 'call_id', pj.PJSUA_INVALID_ID)
        if call_identifier != pj.PJSUA_INVALID_ID:
            derived = f"Call-{call_identifier}"
        else:
            target_uri = getattr(self, 'target_uri', None)
            if target_uri:
                derived = f"Call-{target_uri}"
            else:
                derived = f"Call-{id(self)}"
        self.monitor_call_id = derived
        return derived

    def _ensure_correlation_id(self) -> str:
        correlation_id = getattr(self, 'correlation_id', None)
        if not correlation_id:
            correlation_id = generate_correlation_id()
            setattr(self, 'correlation_id', correlation_id)
        return correlation_id

    @contextlib.contextmanager
    def _correlation_context(self):
        with correlation_scope(self._ensure_correlation_id()):
            yield

    def _log_event(self, message: str, level: str = 'info', **fields) -> None:
        fields.setdefault('call_id', self.call_label())
        with self._correlation_context():
            monitor.add_log(message, level=level, **fields)

    def _start_async_agent(self, coroutine_fn, mode: str) -> None:
        correlation_id = self._ensure_correlation_id()

        def runner():
            try:
                with correlation_scope(correlation_id):
                    asyncio.run(coroutine_fn())
            except Exception as err:  # pragma: no cover - defensive logging
                with correlation_scope(correlation_id):
                    self._log_event(
                        "OpenAI agent thread crashed",
                        level='error',
                        event='openai_agent_error',
                        mode=mode,
                        error=str(err),
                    )
                raise

        thread_name = f"OpenAI-{mode}-{self.call_label()}"
        self.openai_thread = threading.Thread(target=runner, name=thread_name, daemon=True)
        self.openai_thread.start()

    def onCallState(self, prm):
        ci = self.getInfo()
        call_id = self.call_label()
        with self._correlation_context():
            self._log_event(
                "Call state changed",
                event="sip_call_state",
                sip_state=ci.stateText,
                sip_state_code=getattr(ci, 'state', None),
            )

            if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
                # Call is established
                self._invite_attempts = 0
                self._invite_retry_timer.cancel()
                self._log_event(
                    "Call established, starting OpenAI Voice Agent",
                    event="call_established",
                )
                monitor.record_audio_event('call_established', call_id=call_id)

                if not ENABLE_AUDIO:
                    self._log_event(
                        "Audio bridge disabled by configuration",
                        level='warning',
                        event='audio_disabled',
                    )
                    monitor.record_audio_event('audio_disabled', call_id=call_id)
                    return

                # Create audio callback and connect audio media
                self.audio_callback = AudioCallback(self)
                call_slot = self.getAudioMedia(-1)
                call_slot.startTransmit(self.audio_callback)
                self.audio_callback.startTransmit(call_slot)
                monitor.record_audio_event('audio_bridge_connected', call_id=call_id)

                # Launch the appropriate OpenAI agent depending on the selected mode.
                if OPENAI_MODE == 'realtime':
                    self._log_event(
                        "Using OpenAI Realtime API",
                        event="openai_mode",
                        mode='realtime',
                    )
                    monitor.record_audio_event('openai_mode_realtime', call_id=call_id)
                    self._start_async_agent(self.start_openai_agent_realtime, 'realtime')
                else:
                    self._log_event(
                        "Using legacy OpenAI Voice API",
                        event="openai_mode",
                        mode='legacy',
                    )
                    monitor.record_audio_event('openai_mode_legacy', call_id=call_id)
                    self._start_async_agent(self.start_openai_agent_legacy, 'legacy')

            elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
                # Call ended
                self._log_event(
                    "Call disconnected",
                    event="call_disconnected",
                    disconnect_code=ci.lastStatusCode,
                )
                monitor.record_audio_event('call_disconnected', call_id=call_id)
                monitor.remove_call(call_id)
                self._invite_retry_timer.cancel()
                if self.audio_callback:
                    self.audio_callback.wait_for_playback_drain()
                    self.audio_callback.stop()
                if self.openai_thread and self.openai_thread.is_alive():
                    self.openai_thread.join(timeout=5)
                status_code = ci.lastStatusCode
                if (self.target_uri and ci.role == pj.PJSIP_ROLE_UAC and status_code
                        and 400 <= status_code < 600):
                    self._schedule_invite_retry(status_code)

    def _schedule_invite_retry(self, status_code: int) -> None:
        with self._correlation_context():
            if self._invite_attempts >= SIP_INVITE_MAX_ATTEMPTS:
                self._log_event(
                    "Invite retry limit reached",
                    event='invite_retry_limit',
                    status_code=status_code,
                    target_uri=self.target_uri,
                    max_attempts=SIP_INVITE_MAX_ATTEMPTS,
                )
                return
            delay = min(SIP_INVITE_RETRY_BASE * (2 ** self._invite_attempts), SIP_INVITE_RETRY_MAX)
            self._invite_attempts += 1
            metrics.record_invite_retry()
            self._log_event(
                "Scheduling INVITE retry",
                event='invite_retry_scheduled',
                target_uri=self.target_uri,
                delay_seconds=delay,
                attempt=self._invite_attempts,
                status_code=status_code,
            )
            self._invite_retry_timer.schedule(delay)

    def _retry_invite(self) -> None:
        if not self.target_uri:
            return
        call_prm = pj.CallOpParam()
        if hasattr(call_prm, 'opt'):
            call_prm.opt.audioCount = 1
            call_prm.opt.videoCount = 0
        with self._correlation_context():
            try:
                self.makeCall(self.target_uri, call_prm)
                self._log_event(
                    "Re-sending INVITE",
                    event='invite_retry_send',
                    target_uri=self.target_uri,
                )
            except Exception as err:
                self._log_event(
                    "INVITE retry failed",
                    level='error',
                    event='invite_retry_failed',
                    target_uri=self.target_uri,
                    error=str(err),
                )
                if self._invite_attempts < SIP_INVITE_MAX_ATTEMPTS:
                    self._schedule_invite_retry(status_code=0)

    async def _ws_send(self, payload):
        if not self.ws or self.ws.closed:
            return
        await self.ws.send(payload)
        await self._ws_drain()

    async def _ws_drain(self) -> None:
        if not self.ws:
            return
        # websockets>=11 returns a protocol object with a writer implementing drain.
        transport = getattr(self.ws, 'transport', None)
        if transport is None or transport.is_closing():
            return
        # websockets.legacy.client.WebSocketClientProtocol exposes ``connection``
        # containing the underlying StreamWriter.
        candidates = [
            getattr(self.ws, 'drain', None),
            getattr(getattr(self.ws, 'connection', None), 'drain', None),
            getattr(getattr(getattr(self.ws, 'connection', None), 'writer', None), 'drain', None),
            getattr(getattr(getattr(self.ws, 'connection', None), '_writer', None), 'drain', None),
        ]
        for maybe_drain in candidates:
            if callable(maybe_drain):
                result = maybe_drain()
                if asyncio.iscoroutine(result):
                    with contextlib.suppress(Exception):
                        await result
                break

    async def _send_realtime_commit(self) -> None:
        if self._realtime_input_committed or not self.ws or self.ws.closed:
            return
        message = json.dumps({"type": "input_audio_buffer.commit"})
        with self._correlation_context():
            try:
                await self._ws_send(message)
                self._realtime_input_committed = True
                monitor.record_audio_event('realtime_commit', call_id=self.call_label())
                self._log_event(
                    "Realtime audio buffer committed",
                    event='realtime_commit',
                )
            except Exception as err:
                self._log_event(
                    "Error committing realtime audio buffer",
                    level='error',
                    event='realtime_commit_error',
                    error=str(err),
                )

    async def _close_websocket(self) -> None:
        if not self.ws:
            return
        call_id = self.call_label()
        with self._correlation_context():
            try:
                await self.ws.close(code=1000, reason="call ended")
                await self.ws.wait_closed()
                monitor.record_audio_event('openai_ws_closed', call_id=call_id)
                monitor.update_realtime_ws(True, 'connection closed', call_id=call_id)
                self._log_event(
                    "Realtime WebSocket closed",
                    event='realtime_ws_closed',
                )
            except Exception as err:
                self._log_event(
                    "Error closing OpenAI WebSocket",
                    level='error',
                    event='realtime_ws_close_error',
                    error=str(err),
                )
                monitor.update_realtime_ws(False, f'close error: {err}', call_id=call_id)
            finally:
                self.ws = None
            
    async def start_openai_agent_legacy(self):
        """
        Start a connection to the original OpenAI Voice API via WebSocket.

        The legacy API expects raw 16‑bit PCM audio frames and returns
        synthesized audio as bytes. This method maintains backwards
        compatibility for environments where the newer Realtime API is not yet
        available. Refer to the OpenAI voice API documentation for details on
        the configuration parameters used here.
        """
        call_id = self.call_label()
        ws_url = "wss://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        with self._correlation_context():
            monitor.record_audio_event('legacy_ws_connecting', call_id=call_id)
            self._log_event(
                "Connecting to legacy OpenAI voice API",
                event='openai_ws_connecting',
                mode='legacy',
            )
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                self.ws = ws
                with self._correlation_context():
                    monitor.update_realtime_ws(True, 'legacy connected', call_id=call_id)
                    monitor.record_audio_event('legacy_ws_connected', call_id=call_id)
                    self._log_event(
                        "Connected to legacy OpenAI voice API",
                        event='openai_ws_connected',
                        mode='legacy',
                    )
                # Send initial configuration
                await self.ws.send(json.dumps({
                    "agent_id": AGENT_ID,
                    "sample_rate": SAMPLE_RATE,
                    "encoding": "linear16",
                    "audio_channels": CHANNELS
                }))
                # Start audio processing tasks concurrently
                send_task = asyncio.create_task(self.send_audio_to_openai_legacy())
                recv_task = asyncio.create_task(self.receive_audio_from_openai_legacy())

                def _cancel_sender(_):
                    if not send_task.done():
                        send_task.cancel()

                recv_task.add_done_callback(_cancel_sender)

                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
                await self._close_websocket()
                with contextlib.suppress(asyncio.CancelledError):
                    await recv_task
        except Exception as err:
            with self._correlation_context():
                monitor.update_realtime_ws(False, f'legacy connect error: {err}', call_id=call_id)
                self._log_event(
                    "Legacy OpenAI connection failed",
                    level='error',
                    event='openai_ws_error',
                    mode='legacy',
                    error=str(err),
                )
            raise

    async def start_openai_agent_realtime(self):
        """
        Start a connection to the new OpenAI Realtime API via WebSocket.

        The Realtime API supports low‑latency speech‑to‑speech interactions and
        requires sending JSON messages with base64‑encoded audio. When
        connected, we immediately send a session.update message to configure
        the model, voice, audio formats and system instructions. The session
        remains active for the duration of the call. Consult the OpenAI
        Realtime API guide for the full set of options and examples.
        """
        # Compose the query string with model, voice and temperature. These
        # parameters are documented in the realtime API. Additional query
        # parameters can be added as needed (e.g. for turn detection).
        ws_url = (
            f"wss://api.openai.com/v1/realtime?"
            f"model={OPENAI_MODEL}&voice={OPENAI_VOICE}&temperature={OPENAI_TEMPERATURE}"
        )
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            # Realtime API may require this beta header; included for
            # completeness. Remove or adjust once API stabilises.
            "OpenAI-Beta": "realtime=v1"
        }
        call_id = self.call_label()
        with self._correlation_context():
            monitor.record_audio_event('realtime_ws_connecting', call_id=call_id)
            self._log_event(
                "Connecting to realtime OpenAI voice API",
                event='openai_ws_connecting',
                mode='realtime',
            )
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                self.ws = ws
                self._realtime_input_committed = False
                with self._correlation_context():
                    monitor.update_realtime_ws(True, 'realtime connected', call_id=call_id)
                    monitor.record_audio_event('realtime_ws_connected', call_id=call_id)
                    self._log_event(
                        "Connected to realtime OpenAI voice API",
                        event='openai_ws_connected',
                        mode='realtime',
                    )
                # Build and send session.update message specifying audio formats
                session_update = {
                    "type": "session.update",
                    "session": {
                        "type": "realtime",
                        "model": OPENAI_MODEL,
                        "output_modalities": ["audio"],
                        "audio": {
                            "input": {
                                "format": {"type": "audio/pcm16", "sample_rate": SAMPLE_RATE},
                                "turn_detection": {"type": "server_vad"}
                            },
                            "output": {
                                "format": {"type": "audio/pcm16", "sample_rate": SAMPLE_RATE}
                            }
                        },
                        "instructions": SYSTEM_PROMPT
                    }
                }
                await self.ws.send(json.dumps(session_update))

                # Start concurrent audio sending/receiving tasks
                send_task = asyncio.create_task(self.send_audio_to_openai_realtime())
                recv_task = asyncio.create_task(self.receive_audio_from_openai_realtime())

                def _cancel_sender(_):
                    if not send_task.done():
                        send_task.cancel()

                recv_task.add_done_callback(_cancel_sender)

                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
                finally:
                    await self._send_realtime_commit()
                await self._close_websocket()
                with contextlib.suppress(asyncio.CancelledError):
                    await recv_task
        except Exception as err:
            with self._correlation_context():
                monitor.update_realtime_ws(False, f'realtime connect error: {err}', call_id=call_id)
                self._log_event(
                    "Realtime OpenAI connection failed",
                    level='error',
                    event='openai_ws_error',
                    mode='realtime',
                    error=str(err),
                )
            raise

    async def send_audio_to_openai_legacy(self):
        """
        Send raw audio frames from the SIP call to the legacy OpenAI voice API.
        Audio frames are taken from the AudioCallback queue and forwarded
        directly over the WebSocket connection. Token usage is estimated
        based on frame size to provide approximate cost tracking.
        """
        if not self.audio_callback:
            return
        call_id = self.call_label()
        with self._correlation_context():
            monitor.record_audio_event('legacy_stream_started', call_id=call_id)
            self._log_event(
                "Starting legacy audio stream",
                event='audio_stream_start',
                mode='legacy',
            )
        try:
            while self.audio_callback.is_active:
                audio_chunk = await self.audio_callback.get_capture_frame()
                if not audio_chunk:
                    if not self.audio_callback.is_active:
                        break
                    continue
                if self.ws and not self.ws.closed:
                    await self._ws_send(audio_chunk)
                    tokens_estimate = len(audio_chunk) // 1000
                    if tokens_estimate > 0:
                        monitor.update_tokens(tokens_estimate, call_id=call_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            with self._correlation_context():
                self._log_event(
                    "Error sending audio to OpenAI",
                    level='error',
                    event='audio_stream_error',
                    mode='legacy',
                    error=str(e),
                )
        finally:
            with self._correlation_context():
                monitor.record_audio_event('legacy_stream_stopped', call_id=call_id)
                self._log_event(
                    "Legacy audio stream stopped",
                    event='audio_stream_stop',
                    mode='legacy',
                )

    async def send_audio_to_openai_realtime(self):
        """
        Send audio from the SIP call to the Realtime API. Audio frames are
        base64 encoded and wrapped in a JSON envelope with type
        "input_audio_buffer.append" as required by the Realtime API
        specification. Token usage estimation is also updated.
        """
        if not self.audio_callback:
            return
        call_id = self.call_label()
        with self._correlation_context():
            monitor.record_audio_event('realtime_stream_started', call_id=call_id)
            self._log_event(
                "Starting realtime audio stream",
                event='audio_stream_start',
                mode='realtime',
            )
        try:
            while self.audio_callback.is_active:
                audio_chunk = await self.audio_callback.get_capture_frame()
                if not audio_chunk:
                    if not self.audio_callback.is_active:
                        break
                    continue
                if self.ws and not self.ws.closed:
                    audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                    message = {"type": "input_audio_buffer.append", "audio": audio_b64}
                    await self._ws_send(json.dumps(message))
                    tokens_estimate = len(audio_chunk) // 1000
                    if tokens_estimate > 0:
                        monitor.update_tokens(tokens_estimate, call_id=call_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            with self._correlation_context():
                self._log_event(
                    "Error sending audio to OpenAI (Realtime)",
                    level='error',
                    event='audio_stream_error',
                    mode='realtime',
                    error=str(e),
                )
        finally:
            with self._correlation_context():
                monitor.record_audio_event('realtime_stream_stopped', call_id=call_id)
                self._log_event(
                    "Realtime audio stream stopped",
                    event='audio_stream_stop',
                    mode='realtime',
                )

    async def receive_audio_from_openai_legacy(self):
        """
        Receive audio responses from the legacy voice API and play them back.
        The legacy API returns raw PCM frames. These are passed directly to
        playback_audio for synthesis over the SIP call. Any exceptions are
        logged and break the loop.
        """
        if not self.audio_callback:
            return
        call_id = self.call_label()
        with self._correlation_context():
            monitor.record_audio_event('legacy_receive_started', call_id=call_id)
            self._log_event(
                "Starting legacy audio receive loop",
                event='audio_receive_start',
                mode='legacy',
            )
        try:
            while self.ws and not self.ws.closed:
                response = await self.ws.recv()
                if isinstance(response, bytes):
                    await self.audio_callback.queue_playback_frame(response)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            with self._correlation_context():
                self._log_event(
                    "Error receiving audio from OpenAI",
                    level='error',
                    event='audio_receive_error',
                    mode='legacy',
                    error=str(e),
                )
        finally:
            if self.audio_callback:
                await self.audio_callback.flush_playback()
            with self._correlation_context():
                monitor.record_audio_event('legacy_receive_stopped', call_id=call_id)
                self._log_event(
                    "Legacy audio receive loop stopped",
                    event='audio_receive_stop',
                    mode='legacy',
                )

    async def receive_audio_from_openai_realtime(self):
        """
        Receive messages from the Realtime API and handle audio output.

        Responses from the Realtime API are JSON messages. When a
        "response.output_audio.delta" event is received, the audio delta is
        base64 decoded and played back to the caller. Other message types
        (such as transcription updates or system events) are ignored for now
        but could be surfaced to the monitor in the future【826943400076790†L230-L249】.
        """
        if not self.audio_callback:
            return
        call_id = self.call_label()
        with self._correlation_context():
            monitor.record_audio_event('realtime_receive_started', call_id=call_id)
            self._log_event(
                "Starting realtime audio receive loop",
                event='audio_receive_start',
                mode='realtime',
            )
        try:
            while self.ws and not self.ws.closed:
                raw_msg = await self.ws.recv()
                if not raw_msg:
                    continue
                try:
                    message = json.loads(raw_msg)
                except Exception:
                    continue
                msg_type = message.get('type')
                if msg_type == 'response.output_audio.delta' and 'delta' in message:
                    try:
                        audio_bytes = base64.b64decode(message['delta'])
                        await self.audio_callback.queue_playback_frame(audio_bytes)
                    except Exception as decode_err:
                        with self._correlation_context():
                            self._log_event(
                                "Error decoding realtime audio delta",
                                level='error',
                                event='audio_receive_decode_error',
                                mode='realtime',
                                error=str(decode_err),
                            )
                elif msg_type == 'response.completed':
                    await self._send_realtime_commit()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            with self._correlation_context():
                self._log_event(
                    "Error receiving audio from OpenAI (Realtime)",
                    level='error',
                    event='audio_receive_error',
                    mode='realtime',
                    error=str(e),
                )
        finally:
            if self.audio_callback:
                await self.audio_callback.flush_playback()
            with self._correlation_context():
                monitor.record_audio_event('realtime_receive_stopped', call_id=call_id)
                self._log_event(
                    "Realtime audio receive loop stopped",
                    event='audio_receive_stop',
                    mode='realtime',
                )

# Account class for SIP registration
class Account(pj.Account):
    def __init__(self, ep):
        pj.Account.__init__(self)
        self.ep = ep
        self._reg_retry_attempts = 0
        self._reg_retry_timer = EndpointTimer(self.ep, self._retry_registration)

    def onRegState(self, prm):
        ai = self.getInfo()
        monitor.add_log(
            "Registration state updated",
            event='sip_registration_state',
            status_text=ai.regStatusText,
            status_code=ai.regStatus,
        )
        monitor.update_registration(ai.regStatus == 200)
        if ai.regStatus == 200:
            self._reg_retry_attempts = 0
            self._reg_retry_timer.cancel()
        elif 400 <= ai.regStatus < 600:
            self._schedule_registration_retry(ai.regStatus)

    def onIncomingCall(self, prm):
        call = Call(self, prm.callId)
        call_id = call.call_label()
        correlation_id = monitor.add_call(call_id, correlation_id=call.correlation_id)
        call.correlation_id = correlation_id
        with correlation_scope(correlation_id):
            monitor.record_audio_event('incoming_call', call_id=call_id)
            monitor.add_log(
                "Incoming call",
                event='incoming_call',
                call_id=call_id,
            )
        call_prm = pj.CallOpParam()
        call_prm.statusCode = 200  # OK
        call.answer(call_prm)

    def make_outgoing_call(self, uri: str) -> Call:
        call = Call(self, target_uri=uri)
        call.monitor_call_id = f"Outbound-{int(time.time() * 1000)}"
        correlation_id = monitor.add_call(call.monitor_call_id, correlation_id=call.correlation_id)
        call.correlation_id = correlation_id
        with correlation_scope(correlation_id):
            monitor.record_audio_event('outgoing_call', call_id=call.monitor_call_id)
            monitor.add_log(
                "Placing outgoing call",
                event='outgoing_call',
                call_id=call.monitor_call_id,
                target_uri=uri,
            )
        call_prm = pj.CallOpParam()
        if hasattr(call_prm, 'opt'):
            call_prm.opt.audioCount = 1
            call_prm.opt.videoCount = 0
        call.makeCall(uri, call_prm)
        return call

    def _schedule_registration_retry(self, status_code: int) -> None:
        delay = min(SIP_REG_RETRY_BASE * (2 ** self._reg_retry_attempts), SIP_REG_RETRY_MAX)
        self._reg_retry_attempts += 1
        metrics.record_register_retry()
        monitor.add_log(
            "Scheduling SIP registration retry",
            event='registration_retry_scheduled',
            delay_seconds=delay,
            attempt=self._reg_retry_attempts,
            status_code=status_code,
        )
        self._reg_retry_timer.schedule(delay)

    def _retry_registration(self) -> None:
        try:
            monitor.add_log(
                "Retrying SIP registration",
                event='registration_retry_send',
                attempt=self._reg_retry_attempts,
            )
            self.setRegistration(True)
        except Exception as err:
            monitor.add_log(
                "Registration retry failed",
                level='error',
                event='registration_retry_failed',
                error=str(err),
            )
            self._schedule_registration_retry(status_code=0)

# Main function
def main():
    # Start monitoring server
    monitor.start()
    logger.info("SIP AI agent starting", extra={"event": "agent_start"})

    if CONFIG_ERROR is not None:
        error_msg = "Configuration validation failed"
        monitor.add_log(
            error_msg,
            level='error',
            event='configuration_error',
        )
        for detail in CONFIG_ERROR.details:
            monitor.add_log(
                detail,
                level='error',
                event='configuration_error_detail',
            )
        logger.error(
            error_msg,
            extra={"event": "configuration_error", "details": CONFIG_ERROR.details},
        )
        print(CONFIG_ERROR, file=sys.stderr)
        sys.exit(1)

    if not ENABLE_SIP:
        warning_msg = (
            "SIP stack disabled via ENABLE_SIP=0. Monitoring server will stay active."
        )
        monitor.add_log(
            warning_msg,
            level='warning',
            event='sip_disabled',
        )
        logger.warning(warning_msg, extra={"event": "sip_disabled"})
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.add_log("Exiting on keyboard interrupt", event='agent_shutdown')
        return

    # Create and initialize PJSIP library
    ep_cfg = pj.EpConfig()
    # Apply jitter buffer preferences when provided
    med_cfg = getattr(ep_cfg, 'medConfig', None)
    if med_cfg is not None:
        if SIP_JB_MIN > 0 and hasattr(med_cfg, 'jbMin'):
            med_cfg.jbMin = SIP_JB_MIN
        if SIP_JB_MAX > 0 and hasattr(med_cfg, 'jbMax'):
            med_cfg.jbMax = SIP_JB_MAX
        if SIP_JB_MAX_PRE > 0 and hasattr(med_cfg, 'jbMaxPre'):
            med_cfg.jbMaxPre = SIP_JB_MAX_PRE

    ua_cfg = getattr(ep_cfg, 'uaConfig', None)
    if ua_cfg is not None and SIP_STUN_SERVER:
        try:
            stun_servers = getattr(ua_cfg, 'stunServer')
            if stun_servers is not None:
                if hasattr(stun_servers, 'clear'):
                    stun_servers.clear()
                stun_servers.append(SIP_STUN_SERVER)
        except Exception:
            pass

    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)

    # Create SIP transport
    transport_cfg = pj.TransportConfig()
    transport_cfg.port = SIP_TRANSPORT_PORT
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)

    # Start PJSIP
    ep.libStart()

    # Apply codec preferences
    if SIP_PREFERRED_CODECS:
        try:
            codec_infos = ep.codecEnum2()
            available = {info.codecId: info for info in codec_infos}
            priority = 240
            for codec in SIP_PREFERRED_CODECS:
                if codec in available:
                    ep.codecSetPriority(codec, priority)
                    priority = max(priority - 10, 0)
                else:
                    monitor.add_log(f"Requested codec {codec} not available")
        except Exception as err:
            monitor.add_log(f"Unable to set codec preferences: {err}")

    # Create and register account
    acc_cfg = pj.AccountConfig()
    acc_cfg.idUri = f"sip:{SIP_USER}@{SIP_DOMAIN}"
    acc_cfg.regConfig.registrarUri = f"sip:{SIP_DOMAIN}"
    cred = pj.AuthCredInfo("digest", "*", SIP_USER, 0, SIP_PASS)
    acc_cfg.sipConfig.authCreds.append(cred)

    nat_cfg = getattr(acc_cfg, 'natConfig', None)
    if nat_cfg is not None:
        if hasattr(nat_cfg, 'iceEnabled'):
            nat_cfg.iceEnabled = SIP_ENABLE_ICE
        if hasattr(nat_cfg, 'turnEnabled'):
            nat_cfg.turnEnabled = SIP_ENABLE_TURN
        if SIP_STUN_SERVER and hasattr(nat_cfg, 'stunServer'):
            nat_cfg.stunServer = SIP_STUN_SERVER
        if SIP_TURN_SERVER and hasattr(nat_cfg, 'turnServer'):
            nat_cfg.turnServer = SIP_TURN_SERVER
        if SIP_TURN_USER and hasattr(nat_cfg, 'turnUserName'):
            nat_cfg.turnUserName = SIP_TURN_USER
        if SIP_TURN_PASS and hasattr(nat_cfg, 'turnPassword'):
            nat_cfg.turnPassword = SIP_TURN_PASS

    media_cfg = getattr(acc_cfg, 'mediaConfig', None)
    if media_cfg is not None:
        disabled = getattr(pj, 'PJSUA_SRTP_DISABLED', 0)
        optional = getattr(pj, 'PJSUA_SRTP_OPTIONAL', 1)
        mandatory = getattr(pj, 'PJSUA_SRTP_MANDATORY', 2)
        if hasattr(media_cfg, 'srtpUse'):
            if SIP_ENABLE_SRTP:
                media_cfg.srtpUse = optional if SIP_SRTP_OPTIONAL else mandatory
            else:
                media_cfg.srtpUse = disabled
        if hasattr(media_cfg, 'srtpSecureSignaling'):
            media_cfg.srtpSecureSignaling = SIP_ENABLE_SRTP

    acc = Account(ep)
    acc.create(acc_cfg)
    
    monitor.add_log(
        "SIP client registered",
        event='sip_registration_complete',
        sip_user=SIP_USER,
        sip_domain=SIP_DOMAIN,
    )
    monitor.add_log("Waiting for incoming calls...", event='agent_idle')
    
    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.add_log("Exiting on keyboard interrupt", event='agent_shutdown')
    finally:
        # Shutdown
        ep.libDestroy()
        ep.libDelete()
        monitor.add_log("PJSIP shutdown complete", event='agent_shutdown_complete')

if __name__ == "__main__":
    main()
