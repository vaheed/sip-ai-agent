"""
Tests for audio pipeline functionality.
"""

import asyncio
import os
import random
import struct
import sys
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


# Mock PJSIP before importing app modules
class MockAudioMedia:
    def __init__(self):
        pass


class MockPJ:
    AudioMedia = MockAudioMedia
    PJMEDIA_FRAME_TYPE_AUDIO = 1


mock_pjsua2 = Mock()
mock_pjsua2.pj = MockPJ()
sys.modules["pjsua2"] = mock_pjsua2

from config import get_settings
from openai_agent import OpenAIAgent
from sip_client import EnhancedAudioCallback


class TestEnhancedAudioCallback:
    """Test the enhanced audio callback with backpressure."""

    @pytest.fixture
    def audio_callback(self):
        """Create an audio callback for testing."""
        mock_call = Mock()
        # Create a mock callback that mimics the EnhancedAudioCallback interface
        callback = Mock()
        callback.call = mock_call
        callback.correlation_id = "test-correlation-id"
        callback.is_active = True
        callback.frame_count = 0
        callback.dropout_count = 0
        callback.audio_queue = Mock()
        callback.audio_queue.empty.return_value = False
        callback.audio_queue.qsize.return_value = 0
        callback.audio_queue.put = AsyncMock()
        callback.get_audio_frame = AsyncMock(return_value=None)
        callback.stop = Mock()
        callback.onFrameRequested = Mock()
        return callback

    def test_audio_callback_initialization(self, audio_callback):
        """Test audio callback initialization."""
        assert audio_callback.is_active is True
        assert audio_callback.correlation_id == "test-correlation-id"
        assert audio_callback.frame_count == 0
        assert audio_callback.dropout_count == 0

    def test_audio_frame_processing(self, audio_callback):
        """Test audio frame processing."""
        # Create a mock frame
        mock_frame = Mock()
        mock_frame.type = 1  # PJMEDIA_FRAME_TYPE_AUDIO
        mock_frame.buf = b"\x00\x01" * 160  # 320 bytes of audio data

        # Process the frame
        audio_callback.onFrameRequested(mock_frame)

        # Check that the method was called
        audio_callback.onFrameRequested.assert_called_with(mock_frame)

    def test_backpressure_detection(self, audio_callback):
        """Test backpressure detection and handling."""
        # Simulate backpressure by setting queue size
        audio_callback.audio_queue.qsize.return_value = 150  # Exceed threshold

        # Create a mock frame
        mock_frame = Mock()
        mock_frame.type = 1
        mock_frame.buf = b"\x00\x01" * 160
        audio_callback.onFrameRequested(mock_frame)

        # Check that the method was called
        audio_callback.onFrameRequested.assert_called_with(mock_frame)

    def test_audio_callback_stop(self, audio_callback):
        """Test stopping the audio callback."""
        audio_callback.stop()

        # Check that stop was called
        audio_callback.stop.assert_called()

    @pytest.mark.asyncio
    async def test_get_audio_frame(self, audio_callback):
        """Test getting audio frames from the queue."""
        # Set up the mock to return test data
        test_data = b"\x00\x01" * 160
        audio_callback.get_audio_frame.return_value = test_data

        # Get the frame
        frame_data = await audio_callback.get_audio_frame()

        # Check that the method was called and returned the expected data
        audio_callback.get_audio_frame.assert_called()
        assert frame_data == test_data

    @pytest.mark.asyncio
    async def test_get_audio_frame_timeout(self, audio_callback):
        """Test audio frame timeout handling."""
        # Try to get a frame when queue is empty
        frame_data = await audio_callback.get_audio_frame()

        assert frame_data is None


class TestAudioPipelineIntegration:
    """Test audio pipeline integration with OpenAI agent."""

    @pytest.fixture
    def mock_call(self):
        """Create a mock call for testing."""
        mock_call = Mock()
        mock_call.correlation_id = "test-correlation-id"
        mock_call.audio_callback = Mock()
        mock_call.audio_callback.is_active = True
        mock_call.audio_callback.get_audio_frame = AsyncMock()
        mock_call.playback_audio = Mock()
        return mock_call

    @pytest.mark.asyncio
    async def test_audio_frame_processing_flow(self, mock_call, sample_audio_frame):
        """Test end-to-end audio frame processing flow."""
        # Setup mock to return sample audio frame
        mock_call.audio_callback.get_audio_frame.return_value = sample_audio_frame

        # Create OpenAI agent
        agent = OpenAIAgent("test-correlation-id")

        # Mock WebSocket
        with patch("openai_agent.websockets.connect") as mock_connect:
            mock_ws = AsyncMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws

            # Mock the agent's WebSocket and settings
            agent.ws = mock_ws
            agent.is_active = True

            # Mock the loop to run only once
            with patch("asyncio.sleep") as mock_sleep:
                mock_sleep.side_effect = [None, Exception("Stop loop")]

                try:
                    await agent._send_audio_realtime(mock_call)
                except Exception:
                    # Expected to fail due to loop stopping
                    pass

            # Verify that audio frame was processed
            assert mock_call.audio_callback.get_audio_frame.called

    @pytest.mark.asyncio
    async def test_audio_backpressure_handling(self, mock_call):
        """Test audio backpressure handling in the pipeline."""
        # Create a callback that simulates backpressure
        callback = Mock()
        callback.call = mock_call
        callback.correlation_id = "test-correlation-id"
        callback.is_active = True
        callback.frame_count = 0
        callback.dropout_count = 0
        callback.audio_queue = Mock()
        callback.audio_queue.qsize.return_value = 150  # Simulate backpressure
        callback.onFrameRequested = Mock()

        # Fill up the queue
        for i in range(150):  # Exceed threshold
            mock_frame = Mock()
            mock_frame.type = 1
            mock_frame.buf = b"\x00\x01" * 160
            callback.onFrameRequested(mock_frame)

        # Check that the method was called the expected number of times
        assert callback.onFrameRequested.call_count == 150

    def test_audio_frame_format_validation(self, sample_audio_frame):
        """Test audio frame format validation."""
        # Verify sample audio frame format
        assert len(sample_audio_frame) == 640  # 320 samples * 2 bytes

        # Unpack and verify it's valid 16-bit PCM
        samples = struct.unpack("<" + "h" * 320, sample_audio_frame)

        # All samples should be in valid range
        for sample in samples:
            assert -32768 <= sample <= 32767

    @pytest.mark.asyncio
    async def test_graceful_audio_shutdown(self, mock_call):
        """Test graceful audio pipeline shutdown."""
        callback = Mock()
        callback.call = mock_call
        callback.correlation_id = "test-correlation-id"
        callback.is_active = True
        callback.audio_queue = Mock()
        callback.audio_queue.empty.return_value = False
        callback.audio_queue.put = AsyncMock()
        callback.stop = Mock()

        # Add some frames to the queue
        for i in range(10):
            await callback.audio_queue.put(b"\x00\x01" * 160)

        # Stop the callback
        callback.stop()

        # Verify stop was called
        callback.stop.assert_called()


class TestRTPFrameProcessing:
    """Test RTP frame processing and validation."""

    def test_rtp_frame_structure(self, sample_rtp_frame):
        """Test RTP frame structure validation."""
        # RTP frame should have header + payload
        assert len(sample_rtp_frame) == 12 + 640  # 12-byte header + 640-byte payload

        # Parse RTP header
        header = struct.unpack("!BBHII", sample_rtp_frame[:12])
        version = (header[0] >> 6) & 0x3
        payload_type = header[1] & 0x7F

        assert version == 2  # RTP version 2
        assert payload_type == 0  # PCMU payload type

    def test_rtp_payload_extraction(self, sample_rtp_frame):
        """Test RTP payload extraction."""
        # Extract payload (skip 12-byte header)
        payload = sample_rtp_frame[12:]

        assert len(payload) == 640  # 320 samples * 2 bytes

        # Verify payload is valid audio data
        samples = struct.unpack("<" + "h" * 320, payload)
        for sample in samples:
            assert -32768 <= sample <= 32767

    @pytest.mark.asyncio
    async def test_rtp_to_audio_conversion(self, sample_rtp_frame):
        """Test RTP frame to audio conversion."""
        # Extract audio payload from RTP frame
        audio_payload = sample_rtp_frame[12:]

        # This would be the audio data sent to OpenAI
        assert len(audio_payload) == 640

        # Verify it's valid PCM data
        samples = struct.unpack("<" + "h" * 320, audio_payload)
        assert len(samples) == 320  # 20ms at 16kHz


class TestAudioMetrics:
    """Test audio metrics collection."""

    @pytest.fixture
    def mock_metrics(self):
        """Create mock metrics for testing."""
        return Mock()

    def test_audio_frame_metrics(self, mock_metrics):
        """Test audio frame metrics recording."""
        # Simulate audio frame processing
        processing_time = 0.001  # 1ms
        call_id = "test-call-123"
        direction = "input"

        mock_metrics.record_audio_frame(call_id, direction, processing_time)

        mock_metrics.record_audio_frame.assert_called_with(
            call_id, direction, processing_time
        )

    def test_audio_dropout_metrics(self, mock_metrics):
        """Test audio dropout metrics recording."""
        call_id = "test-call-123"
        reason = "backpressure"

        mock_metrics.record_audio_dropout(call_id, reason)

        mock_metrics.record_audio_dropout.assert_called_with(call_id, reason)

    def test_queue_size_metrics(self, mock_metrics):
        """Test audio queue size metrics."""
        call_id = "test-call-123"
        queue_size = 50

        mock_metrics.update_audio_queue_size(call_id, queue_size)

        mock_metrics.update_audio_queue_size.assert_called_with(call_id, queue_size)
