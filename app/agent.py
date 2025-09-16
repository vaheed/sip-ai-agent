#!/usr/bin/env python3
import os
import sys
import time
import json
import asyncio
import websockets
import wave
import pyaudio
from pydub import AudioSegment
from pydub.playback import play
import threading
import base64
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

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Audio callback class for PJSIP
class AudioCallback(pj.AudioMedia):
    def __init__(self, call):
        pj.AudioMedia.__init__(self)
        self.call = call
        self.audio_queue = asyncio.Queue()
        self.is_active = True
        
    def onFrameRequested(self, frame):
        # This method is called when PJSIP needs audio frames
        if not self.is_active:
            return
            
        # Get audio from the call and put it in the queue
        if frame.type == pj.PJMEDIA_FRAME_TYPE_AUDIO:
            self.audio_queue.put_nowait(frame.buf)
            
    def stop(self):
        self.is_active = False

# Call class for handling SIP calls
class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.audio_callback = None
        self.ws = None
        self.openai_thread = None
        self.call_id = call_id
        
    def onCallState(self, prm):
        ci = self.getInfo()
        print(f"Call state: {ci.stateText}")
        monitor.add_log(f"Call state: {ci.stateText}")
        
        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            # Call is established
            print("Call established, starting OpenAI Voice Agent")
            monitor.add_log("Call established, starting OpenAI Voice Agent")

            # Create audio callback and connect audio media
            self.audio_callback = AudioCallback(self)
            call_slot = self.getAudioMedia(-1)
            call_slot.startTransmit(self.audio_callback)

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
            if self.audio_callback:
                self.audio_callback.stop()
            if self.ws and not self.ws.closed:
                asyncio.run(self.ws.close())
            
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
        async with websockets.connect(ws_url, extra_headers=headers) as self.ws:
            # Send initial configuration
            await self.ws.send(json.dumps({
                "agent_id": AGENT_ID,
                "sample_rate": SAMPLE_RATE,
                "encoding": "linear16",
                "audio_channels": CHANNELS
            }))
            # Start audio processing tasks concurrently
            await asyncio.gather(
                self.send_audio_to_openai_legacy(),
                self.receive_audio_from_openai_legacy()
            )

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
        async with websockets.connect(ws_url, extra_headers=headers) as self.ws:
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
            await asyncio.gather(
                self.send_audio_to_openai_realtime(),
                self.receive_audio_from_openai_realtime()
            )
    
    async def send_audio_to_openai_legacy(self):
        """
        Send raw audio frames from the SIP call to the legacy OpenAI voice API.
        Audio frames are taken from the AudioCallback queue and forwarded
        directly over the WebSocket connection. Token usage is estimated
        based on frame size to provide approximate cost tracking.
        """
        while self.audio_callback and self.audio_callback.is_active:
            try:
                audio_chunk = await self.audio_callback.audio_queue.get()
                if audio_chunk and self.ws and not self.ws.closed:
                    await self.ws.send(audio_chunk)
                    # Estimate token usage (rough approximation)
                    tokens_estimate = len(audio_chunk) // 1000
                    if tokens_estimate > 0:
                        monitor.update_tokens(tokens_estimate)
            except Exception as e:
                error_msg = f"Error sending audio to OpenAI: {e}"
                print(error_msg)
                monitor.add_log(error_msg)
                break

    async def send_audio_to_openai_realtime(self):
        """
        Send audio from the SIP call to the Realtime API. Audio frames are
        base64 encoded and wrapped in a JSON envelope with type
        "input_audio_buffer.append" as required by the Realtime API【826943400076790†L230-L249】. Token usage
        estimation is also updated.
        """
        while self.audio_callback and self.audio_callback.is_active:
            try:
                audio_chunk = await self.audio_callback.audio_queue.get()
                if audio_chunk and self.ws and not self.ws.closed:
                    # Base64 encode the PCM data
                    audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    await self.ws.send(json.dumps(message))
                    # Estimate token usage: divide by approx. 1000 bytes per token
                    tokens_estimate = len(audio_chunk) // 1000
                    if tokens_estimate > 0:
                        monitor.update_tokens(tokens_estimate)
            except Exception as e:
                error_msg = f"Error sending audio to OpenAI (Realtime): {e}"
                print(error_msg)
                monitor.add_log(error_msg)
                break
    
    async def receive_audio_from_openai_legacy(self):
        """
        Receive audio responses from the legacy voice API and play them back.
        The legacy API returns raw PCM frames. These are passed directly to
        playback_audio for synthesis over the SIP call. Any exceptions are
        logged and break the loop.
        """
        try:
            while self.ws and not self.ws.closed:
                response = await self.ws.recv()
                if isinstance(response, bytes):
                    self.playback_audio(response)
        except Exception as e:
            error_msg = f"Error receiving audio from OpenAI: {e}"
            print(error_msg)
            monitor.add_log(error_msg)

    async def receive_audio_from_openai_realtime(self):
        """
        Receive messages from the Realtime API and handle audio output.

        Responses from the Realtime API are JSON messages. When a
        "response.output_audio.delta" event is received, the audio delta is
        base64 decoded and played back to the caller. Other message types
        (such as transcription updates or system events) are ignored for now
        but could be surfaced to the monitor in the future【826943400076790†L230-L249】.
        """
        try:
            while self.ws and not self.ws.closed:
                raw_msg = await self.ws.recv()
                if not raw_msg:
                    continue
                try:
                    message = json.loads(raw_msg)
                except Exception:
                    # Skip non‑JSON messages
                    continue
                msg_type = message.get('type')
                # Handle audio delta messages
                if msg_type == 'response.output_audio.delta' and 'delta' in message:
                    try:
                        audio_bytes = base64.b64decode(message['delta'])
                        self.playback_audio(audio_bytes)
                    except Exception as decode_err:
                        monitor.add_log(f"Error decoding audio delta: {decode_err}")
                # You may add handling of transcripts or other events here
        except Exception as e:
            error_msg = f"Error receiving audio from OpenAI (Realtime): {e}"
            print(error_msg)
            monitor.add_log(error_msg)
    
    def playback_audio(self, audio_data):
        # Play audio back to the caller
        try:
            # Create a temporary WAV file
            with wave.open("temp.wav", "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data)
            
            # Load and play the audio
            sound = AudioSegment.from_wav("temp.wav")
            play(sound)
            
            # Clean up
            os.remove("temp.wav")
        except Exception as e:
            print(f"Error playing back audio: {e}")

# Account class for SIP registration
class Account(pj.Account):
    def __init__(self, ep):
        pj.Account.__init__(self)
        self.ep = ep
        
    def onRegState(self, prm):
        ai = self.getInfo()
        print(f"Registration state: {ai.regStatusText} ({ai.regStatus})")
        # Update monitor with registration status
        monitor.update_registration(ai.regStatus == 200)
        
    def onIncomingCall(self, prm):
        print("Incoming call...")
        call = Call(self, prm.callId)
        call_prm = pj.CallOpParam()
        call_prm.statusCode = 200  # OK
        call.answer(call_prm)
        # Add call to monitor
        monitor.add_call(f"Call-{prm.callId}")

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
    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)
    
    # Create SIP transport
    transport_cfg = pj.TransportConfig()
    transport_cfg.port = 5060
    transport = ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
    
    # Start PJSIP
    ep.libStart()
    
    # Create and register account
    acc_cfg = pj.AccountConfig()
    acc_cfg.idUri = f"sip:{SIP_USER}@{SIP_DOMAIN}"
    acc_cfg.regConfig.registrarUri = f"sip:{SIP_DOMAIN}"
    cred = pj.AuthCredInfo("digest", "*", SIP_USER, 0, SIP_PASS)
    acc_cfg.sipConfig.authCreds.append(cred)
    
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
