import asyncio
import base64
import json
import types
import contextlib

import app.agent as agent


class DummyWriter:
    def __init__(self):
        self.calls = 0

    async def drain(self):
        self.calls += 1


class DummyTransport:
    def __init__(self):
        self._closing = False

    def is_closing(self):
        return self._closing


class DummyWebSocket:
    def __init__(self, incoming=None):
        self.sent = []
        self.closed = False
        self.transport = DummyTransport()
        self._writer = DummyWriter()
        self.connection = types.SimpleNamespace(
            drain=self._writer.drain,
            writer=self._writer,
            _writer=self._writer,
        )
        self._incoming = asyncio.Queue()
        if incoming:
            for item in incoming:
                self._incoming.put_nowait(item)

    async def send(self, payload):
        self.sent.append(payload)

    async def recv(self):
        return await self._incoming.get()

    async def close(self, code=1000, reason=""):
        self.closed = True
        self.transport._closing = True

    async def wait_closed(self):
        return


def test_audio_callback_frame_alignment():
    async def main():
        callback = agent.AudioCallback(call=None)
        samples = bytes(range(256)) * 10
        payload_length = agent.FRAME_BYTES * 2 + agent.FRAME_BYTES // 2
        frame_payload = samples[:payload_length]
        frame = types.SimpleNamespace(
            type=agent.pj.PJMEDIA_FRAME_TYPE_AUDIO,
            buf=frame_payload,
        )
        callback.putFrame(frame)

        collected = [await asyncio.wait_for(callback.get_capture_frame(), timeout=0.1) for _ in range(2)]
        assert all(len(chunk) == agent.FRAME_BYTES for chunk in collected)
        assert len(callback._capture_buffer) == agent.FRAME_BYTES // 2

    asyncio.run(main())


def test_realtime_send_and_commit(monkeypatch):
    async def main():
        callback = agent.AudioCallback(call=None)
        call = agent.Call.__new__(agent.Call)
        call.audio_callback = callback
        ws = DummyWebSocket()
        call.ws = ws
        call._realtime_input_committed = False

        recorded_tokens = []
        monkeypatch.setattr(agent.monitor, "update_tokens", recorded_tokens.append)

        frame = b"\x01\x02" * (agent.FRAME_BYTES // 2)
        callback.capture_queue.put_nowait(frame)
        callback.capture_queue.put_nowait(frame)

        async def stop_soon():
            await asyncio.sleep(0.01)
            callback.is_active = False

        asyncio.create_task(stop_soon())
        await call.send_audio_to_openai_realtime()

        assert len(ws.sent) == 2
        for payload in ws.sent:
            message = json.loads(payload)
            assert message["type"] == "input_audio_buffer.append"
            assert base64.b64decode(message["audio"]) == frame
        assert ws.connection.writer.calls == 2
        assert call._realtime_input_committed is False
        assert recorded_tokens == []

        await call._send_realtime_commit()
        assert call._realtime_input_committed is True
        assert json.loads(ws.sent[-1]) == {"type": "input_audio_buffer.commit"}

        await call._close_websocket()
        assert ws.closed is True
        assert call.ws is None

    asyncio.run(main())


def test_realtime_receive_streams_to_playback():
    async def main():
        callback = agent.AudioCallback(call=None)
        call = agent.Call.__new__(agent.Call)
        call.audio_callback = callback

        frame = b"\x03\x04" * (agent.FRAME_BYTES // 2)
        message = json.dumps({
            "type": "response.output_audio.delta",
            "delta": base64.b64encode(frame).decode("utf-8"),
        })
        ws = DummyWebSocket(incoming=[message])
        call.ws = ws

        task = asyncio.create_task(call.receive_audio_from_openai_realtime())
        await asyncio.sleep(0.05)
        assert not callback.playback_queue.empty()
        queued = callback.playback_queue.get_nowait()
        callback.playback_queue.task_done()
        assert queued == frame

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(main())


def test_legacy_send_and_receive(monkeypatch):
    async def main():
        callback = agent.AudioCallback(call=None)
        call = agent.Call.__new__(agent.Call)
        call.audio_callback = callback

        incoming_frame = b"\x05\x06" * (agent.FRAME_BYTES // 2)
        ws = DummyWebSocket(incoming=[incoming_frame])
        call.ws = ws

        monkeypatch.setattr(agent.monitor, "update_tokens", lambda *args, **kwargs: None)

        frame = b"\x07\x08" * (agent.FRAME_BYTES // 2)
        callback.capture_queue.put_nowait(frame)

        async def stop_later():
            await asyncio.sleep(0.01)
            callback.is_active = False

        asyncio.create_task(stop_later())
        send_task = asyncio.create_task(call.send_audio_to_openai_legacy())
        recv_task = asyncio.create_task(call.receive_audio_from_openai_legacy())

        await asyncio.sleep(0.05)
        await send_task
        assert ws.sent == [frame]
        assert ws.connection.writer.calls == 1

        assert not callback.playback_queue.empty()
        queued = callback.playback_queue.get_nowait()
        callback.playback_queue.task_done()
        assert queued == incoming_frame

        recv_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await recv_task

    asyncio.run(main())
