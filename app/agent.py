#!/usr/bin/env python3
import os
import sys
import time
import json
import asyncio
import websockets
import threading
import base64
import queue
import contextlib
from typing import Optional, Sequence
from dotenv import load_dotenv
from openai import OpenAI
import pjsua2 as pj

from monitor import monitor

# Load environment variables
load_dotenv()

# SIP Configuration
SIP_DOMAIN = os.getenv('SIP_DOMAIN')
SIP_USER = os.getenv('SIP_USER')
SIP_PASS = os.getenv('SIP_PASS')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AGENT_ID = os.getenv('AGENT_ID')

# Additional OpenAI settings
#
# OPENAI_MODE controls which audio API to use. Valid values are:
#   "legacy"  - use the original audio/speech WebSocket API (default)
#   "realtime" - use the new Realtime API introduced in 2024/2025 for low
#                 latency speech‑to‑speech. See docs: "GPT‑realtime" for
#                 more information【214777425731610†L280-L310】.
OPENAI_MODE = os.getenv('OPENAI_MODE', 'legacy').lower()

# The model name to use when OPENAI_MODE is "realtime". Default to
# "gpt-realtime" which maps to OpenAI's realtime models. You may change
# this to newer models such as "gpt-realtime-latest" if available.
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-realtime')

# Preferred voice. The Realtime API supports voices like "alloy", "nova",
# "shimmer", and the newer "cedar" and "marin" voices【214777425731610†L304-L310】.
OPENAI_VOICE = os.getenv('OPENAI_VOICE', 'alloy')

# Temperature controls the randomness of the realtime model. Lower values
# produce more deterministic responses. Must be convertible to float.
try:
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
except ValueError:
    OPENAI_TEMPERATURE = 0.3

# System prompt for realtime sessions. This instructs the assistant on
# behaviour. Only used when OPENAI_MODE == "realtime". If not set,
# a generic helpful assistant prompt is used.
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'You are a helpful voice assistant.')

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION = 20  # ms
PCM_WIDTH = 2  # 16-bit PCM
FRAME_BYTES = SAMPLE_RATE * FRAME_DURATION // 1000 * PCM_WIDTH
MAX_PENDING_FRAMES = 50


def _env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean value from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    """Return a float value from environment variables with fallback."""
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    """Return an integer value from environment variables with fallback."""
    try:
        return int(float(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _parse_codec_prefs(raw: Optional[str]) -> Sequence[str]:
    """Parse the comma separated codec list from configuration."""
    if not raw:
        return ()
    codecs = []
    for item in raw.split(','):
        codec = item.strip()
        if codec:
            codecs.append(codec)
    return tuple(codecs)


# SIP media and transport tuning
SIP_TRANSPORT_PORT = _env_int('SIP_TRANSPORT_PORT', 5060)
SIP_JB_MIN = _env_int('SIP_JB_MIN', 0)
SIP_JB_MAX = _env_int('SIP_JB_MAX', 0)
SIP_JB_MAX_PRE = _env_int('SIP_JB_MAX_PRE', 0)
SIP_ENABLE_ICE = _env_bool('SIP_ENABLE_ICE', False)
SIP_ENABLE_TURN = _env_bool('SIP_ENABLE_TURN', False)
SIP_STUN_SERVER = os.getenv('SIP_STUN_SERVER', '').strip()
SIP_TURN_SERVER = os.getenv('SIP_TURN_SERVER', '').strip()
SIP_TURN_USER = os.getenv('SIP_TURN_USER', '').strip()
SIP_TURN_PASS = os.getenv('SIP_TURN_PASS', '').strip()
SIP_ENABLE_SRTP = _env_bool('SIP_ENABLE_SRTP', False)
SIP_SRTP_OPTIONAL = _env_bool('SIP_SRTP_OPTIONAL', True)
SIP_PREFERRED_CODECS = _parse_codec_prefs(os.getenv('SIP_PREFERRED_CODECS'))

# Retry behaviour
SIP_REG_RETRY_BASE = _env_float('SIP_REG_RETRY_BASE', 2.0)
SIP_REG_RETRY_MAX = _env_float('SIP_REG_RETRY_MAX', 60.0)
SIP_INVITE_RETRY_BASE = _env_float('SIP_INVITE_RETRY_BASE', 1.0)
SIP_INVITE_RETRY_MAX = _env_float('SIP_INVITE_RETRY_MAX', 30.0)
SIP_INVITE_MAX_ATTEMPTS = _env_int('SIP_INVITE_MAX_ATTEMPTS', 5)


class EndpointTimer(pj.TimerEntry):
    """Wrapper around ``pj.TimerEntry`` with automatic fallback."""

    def __init__(self, endpoint: pj.Endpoint, callback):
        super().__init__()
        self._endpoint = endpoint
        self._callback = callback
        self._thread_timer: Optional[threading.Timer] = None

    def schedule(self, delay_seconds: float) -> None:
        """Schedule the timer to fire after ``delay_seconds``."""
        self.cancel()
        if delay_seconds < 0:
            delay_seconds = 0

        if hasattr(self._endpoint, 'utilTimerSchedule') and hasattr(pj, 'TimeVal'):
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
        self._thread_timer = threading.Timer(delay_seconds, self._callback)
        self._thread_timer.daemon = True
        self._thread_timer.start()

    def cancel(self) -> None:
        """Cancel the scheduled timer if active."""
        try:
            if hasattr(self._endpoint, 'utilTimerCancel'):
                self._endpoint.utilTimerCancel(self)
        except Exception:
            pass

        if self._thread_timer is not None:
            self._thread_timer.cancel()
            self._thread_timer = None

    def onTimeout(self) -> None:  # pragma: no cover - invoked by PJSIP runtime
        self._callback()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

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
        self.openai_thread = None
        self.call_id = call_id
        self.target_uri = target_uri
        self._invite_attempts = 0
        self._invite_retry_timer = EndpointTimer(self.acc.ep, self._retry_invite)
        self._realtime_input_committed = False

    def onCallState(self, prm):
        ci = self.getInfo()
        print(f"Call state: {ci.stateText}")
        monitor.add_log(f"Call state: {ci.stateText}")
        
        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            # Call is established
            print("Call established, starting OpenAI Voice Agent")
            monitor.add_log("Call established, starting OpenAI Voice Agent")
            self._invite_attempts = 0
            self._invite_retry_timer.cancel()

            # Create audio callback and connect audio media
            self.audio_callback = AudioCallback(self)
            call_slot = self.getAudioMedia(-1)
            call_slot.startTransmit(self.audio_callback)
            self.audio_callback.startTransmit(call_slot)

            # Launch the appropriate OpenAI agent depending on the selected mode.
            # Using asyncio.create_task ensures the coroutine runs in the same event
            # loop instead of spawning a blocking thread. This improves speed and
            # reduces resource usage by leveraging async I/O for both SIP and
            # WebSocket handling.
            if OPENAI_MODE == 'realtime':
                # Start the Realtime agent
                print("Using OpenAI Realtime API")
                monitor.add_log("Using OpenAI Realtime API")
                self.openai_thread = threading.Thread(target=asyncio.run,
                                                     args=(self.start_openai_agent_realtime(),))
                self.openai_thread.start()
            else:
                # Fallback to legacy speech API
                print("Using legacy OpenAI Voice API")
                monitor.add_log("Using legacy OpenAI Voice API")
                self.openai_thread = threading.Thread(target=asyncio.run,
                                                     args=(self.start_openai_agent_legacy(),))
                self.openai_thread.start()
            
        elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            # Call ended
            print("Call disconnected")
            monitor.remove_call(f"Call-{self.call_id}")
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
        if self._invite_attempts >= SIP_INVITE_MAX_ATTEMPTS:
            monitor.add_log(
                f"Invite retry limit reached for {self.target_uri} (status {status_code})"
            )
            return
        delay = min(SIP_INVITE_RETRY_BASE * (2 ** self._invite_attempts), SIP_INVITE_RETRY_MAX)
        self._invite_attempts += 1
        monitor.add_log(
            f"Retrying INVITE to {self.target_uri} in {delay:.1f}s (attempt {self._invite_attempts})"
        )
        self._invite_retry_timer.schedule(delay)

    def _retry_invite(self) -> None:
        if not self.target_uri:
            return
        call_prm = pj.CallOpParam()
        if hasattr(call_prm, 'opt'):
            call_prm.opt.audioCount = 1
            call_prm.opt.videoCount = 0
        try:
            self.makeCall(self.target_uri, call_prm)
            monitor.add_log(f"Re-sending INVITE to {self.target_uri}")
        except Exception as err:
            monitor.add_log(f"INVITE retry failed: {err}")
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
        try:
            await self._ws_send(message)
            self._realtime_input_committed = True
        except Exception as err:
            monitor.add_log(f"Error committing realtime audio buffer: {err}")

    async def _close_websocket(self) -> None:
        if not self.ws:
            return
        with contextlib.suppress(Exception):
            await self.ws.close(code=1000, reason="call ended")
            await self.ws.wait_closed()
        self.ws = None
            
    async def start_openai_agent_legacy(self):
        """
        Start a connection to the original OpenAI Voice API via WebSocket.

        The legacy API expects raw 16‑bit PCM audio frames and returns
        synthesized audio as bytes. This method maintains backwards
        compatibility for environments where the newer Realtime API is not yet
        available. See OpenAI's voice documentation for details on the
        parameters used here【214777425731610†L286-L314】.
        """
        ws_url = "wss://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            self.ws = ws
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

    async def start_openai_agent_realtime(self):
        """
        Start a connection to the new OpenAI Realtime API via WebSocket.

        The Realtime API supports low‑latency speech‑to‑speech interactions and
        requires sending JSON messages with base64‑encoded audio. When
        connected, we immediately send a session.update message to configure
        the model, voice, audio formats and system instructions. The session
        remains active for the duration of the call. See the OpenAI
        Realtime API guide and examples【214777425731610†L286-L314】.
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
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            self.ws = ws
            self._realtime_input_committed = False
            # Build and send session.update message specifying audio formats
            # and system instructions. The audio formats must match the
            # inbound call. We use 16 kHz, 16‑bit PCM little endian audio (pcm16).
            session_update = {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": OPENAI_MODEL,
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm16", "sample_rate": SAMPLE_RATE},
                            # Enable server‑side VAD to allow the API to handle turn taking
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

            # Optionally send an initial conversation item so that the model
            # greets the caller. This can be controlled via an environment
            # variable or by modifying SYSTEM_PROMPT. Disabled by default.

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

    async def send_audio_to_openai_legacy(self):
        """
        Send raw audio frames from the SIP call to the legacy OpenAI voice API.
        Audio frames are taken from the AudioCallback queue and forwarded
        directly over the WebSocket connection. Token usage is estimated
        based on frame size to provide approximate cost tracking.
        """
        if not self.audio_callback:
            return
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
                        monitor.update_tokens(tokens_estimate)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = f"Error sending audio to OpenAI: {e}"
            print(error_msg)
            monitor.add_log(error_msg)

    async def send_audio_to_openai_realtime(self):
        """
        Send audio from the SIP call to the Realtime API. Audio frames are
        base64 encoded and wrapped in a JSON envelope with type
        "input_audio_buffer.append" as required by the Realtime API【826943400076790†L230-L249】. Token usage
        estimation is also updated.
        """
        if not self.audio_callback:
            return
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
                        monitor.update_tokens(tokens_estimate)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = f"Error sending audio to OpenAI (Realtime): {e}"
            print(error_msg)
            monitor.add_log(error_msg)

    async def receive_audio_from_openai_legacy(self):
        """
        Receive audio responses from the legacy voice API and play them back.
        The legacy API returns raw PCM frames. These are passed directly to
        playback_audio for synthesis over the SIP call. Any exceptions are
        logged and break the loop.
        """
        if not self.audio_callback:
            return
        try:
            while self.ws and not self.ws.closed:
                response = await self.ws.recv()
                if isinstance(response, bytes):
                    await self.audio_callback.queue_playback_frame(response)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = f"Error receiving audio from OpenAI: {e}"
            print(error_msg)
            monitor.add_log(error_msg)
        finally:
            if self.audio_callback:
                await self.audio_callback.flush_playback()

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
                        monitor.add_log(f"Error decoding audio delta: {decode_err}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = f"Error receiving audio from OpenAI (Realtime): {e}"
            print(error_msg)
            monitor.add_log(error_msg)
        finally:
            if self.audio_callback:
                await self.audio_callback.flush_playback()

# Account class for SIP registration
class Account(pj.Account):
    def __init__(self, ep):
        pj.Account.__init__(self)
        self.ep = ep
        self._reg_retry_attempts = 0
        self._reg_retry_timer = EndpointTimer(self.ep, self._retry_registration)

    def onRegState(self, prm):
        ai = self.getInfo()
        print(f"Registration state: {ai.regStatusText} ({ai.regStatus})")
        # Update monitor with registration status
        monitor.update_registration(ai.regStatus == 200)
        if ai.regStatus == 200:
            self._reg_retry_attempts = 0
            self._reg_retry_timer.cancel()
        elif 400 <= ai.regStatus < 600:
            self._schedule_registration_retry(ai.regStatus)

    def onIncomingCall(self, prm):
        print("Incoming call...")
        call = Call(self, prm.callId)
        call_prm = pj.CallOpParam()
        call_prm.statusCode = 200  # OK
        call.answer(call_prm)
        # Add call to monitor
        monitor.add_call(f"Call-{prm.callId}")

    def make_outgoing_call(self, uri: str) -> Call:
        call = Call(self, target_uri=uri)
        call_prm = pj.CallOpParam()
        if hasattr(call_prm, 'opt'):
            call_prm.opt.audioCount = 1
            call_prm.opt.videoCount = 0
        call.makeCall(uri, call_prm)
        return call

    def _schedule_registration_retry(self, status_code: int) -> None:
        delay = min(SIP_REG_RETRY_BASE * (2 ** self._reg_retry_attempts), SIP_REG_RETRY_MAX)
        self._reg_retry_attempts += 1
        monitor.add_log(
            f"Scheduling SIP registration retry in {delay:.1f}s after failure {status_code}"
        )
        self._reg_retry_timer.schedule(delay)

    def _retry_registration(self) -> None:
        try:
            monitor.add_log("Retrying SIP registration")
            self.setRegistration(True)
        except Exception as err:
            monitor.add_log(f"Registration retry failed: {err}")
            self._schedule_registration_retry(status_code=0)

# Main function
def main():
    # Start monitoring server
    monitor.start()
    
    # Check environment variables
    if not all([SIP_DOMAIN, SIP_USER, SIP_PASS, OPENAI_API_KEY, AGENT_ID]):
        error_msg = "Error: Missing environment variables. Please check your .env file."
        print(error_msg)
        monitor.add_log(error_msg)
        sys.exit(1)
        
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
    transport = ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)

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
    
    print(f"SIP client registered as {SIP_USER}@{SIP_DOMAIN}")
    print("Waiting for incoming calls...")
    
    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Shutdown
        ep.libDestroy()
        ep.libDelete()

if __name__ == "__main__":
    main()
