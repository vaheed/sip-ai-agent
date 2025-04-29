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
            self.audio_callback = AudioCallback(self)
            
            # Connect call audio to our callback
            call_slot = self.getAudioMedia(-1)
            call_slot.startTransmit(self.audio_callback)
            
            # Start OpenAI Voice Agent in a separate thread
            self.openai_thread = threading.Thread(target=asyncio.run, 
                                                args=(self.start_openai_agent(),))
            self.openai_thread.start()
            
        elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            # Call ended
            print("Call disconnected")
            monitor.remove_call(f"Call-{self.call_id}")
            if self.audio_callback:
                self.audio_callback.stop()
            if self.ws and not self.ws.closed:
                asyncio.run(self.ws.close())
            
    async def start_openai_agent(self):
        # Connect to OpenAI Voice API via WebSocket
        ws_url = f"wss://api.openai.com/v1/audio/speech"
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
            
            # Start audio processing tasks
            await asyncio.gather(
                self.send_audio_to_openai(),
                self.receive_audio_from_openai()
            )
    
    async def send_audio_to_openai(self):
        # Send audio from the call to OpenAI
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
    
    async def receive_audio_from_openai(self):
        # Receive audio responses from OpenAI and play them back
        try:
            while self.ws and not self.ws.closed:
                response = await self.ws.recv()
                if isinstance(response, bytes):
                    # Play the audio response back to the caller
                    self.playback_audio(response)
        except Exception as e:
            print(f"Error receiving audio from OpenAI: {e}")
    
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
