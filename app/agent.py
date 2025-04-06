import os
import pjsua as pj
import threading
import sounddevice as sd
import numpy as np
import asyncio
import websockets

SIP_DOMAIN = os.getenv("SIP_DOMAIN")
SIP_USER = os.getenv("SIP_USER")
SIP_PASS = os.getenv("SIP_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")

WS_URL = f"wss://api.openai.com/v1/voice/agents/{AGENT_ID}/interact"
HEADERS = { "Authorization": f"Bearer {OPENAI_API_KEY}" }

class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)
        self.call = call

    def on_state(self):
        print(f"Call is {self.call.info().state_text}")
        if self.call.info().state == pj.CallState.CONFIRMED:
            threading.Thread(target=self.stream_audio).start()

    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            call_slot = self.call.info().conf_slot
            pj.Lib.instance().conf_connect(call_slot, 0)
            pj.Lib.instance().conf_connect(0, call_slot)

    def stream_audio(self):
        async def send_audio():
            async with websockets.connect(WS_URL, extra_headers=HEADERS) as ws:
                with sd.InputStream(samplerate=16000, channels=1) as stream:
                    while True:
                        data, _ = stream.read(1024)
                        audio_data = np.frombuffer(data, dtype=np.int16).tobytes()
                        await ws.send(audio_data)
                        response = await ws.recv()
                        pj.Lib.instance().conf_playback(0, response)

        asyncio.run(send_audio())

class MyAccountCallback(pj.AccountCallback):
    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)

    def on_incoming_call(self, call):
        print(f"Incoming call from {call.info().remote_uri}")
        call_cb = MyCallCallback(call)
        call.set_callback(call_cb)
        call.answer(200)

lib = pj.Lib()

try:
    lib.init(log_cfg=pj.LogConfig(level=3))
    transport = lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(5060))
    lib.start()

    acc_cfg = pj.AccountConfig(domain=SIP_DOMAIN, username=SIP_USER, password=SIP_PASS)
    acc = lib.create_account(acc_cfg)
    acc_cb = MyAccountCallback(acc)
    acc.set_callback(acc_cb)

    print("SIP Agent is running. Press Ctrl+C to quit.")
    threading.Event().wait()

except KeyboardInterrupt:
    print("Exiting...")
finally:
    lib.destroy()
