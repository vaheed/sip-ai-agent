"""
Tests for OpenAI agent functionality.
"""

import base64
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from unittest.mock import AsyncMock, Mock, patch

from config import OpenAIAPIMode, OpenAIVoice
from openai_agent import OpenAIAgent


class TestOpenAIAgent:
    """Test the OpenAI agent functionality."""

    @pytest.fixture
    def agent_config(self, test_settings):
        """Create agent configuration for testing."""
        return {"correlation_id": "test-correlation-id", "settings": test_settings}

    @pytest.fixture
    def mock_agent(self, agent_config):
        """Create a mock OpenAI agent."""
        with patch("openai_agent.get_settings") as mock_get_settings:
            mock_get_settings.return_value = agent_config["settings"]
            agent = OpenAIAgent(agent_config["correlation_id"])
            return agent

    def test_agent_initialization(self, mock_agent):
        """Test agent initialization."""
        assert mock_agent.correlation_id == "test-correlation-id"
        assert mock_agent.is_active is False
        assert mock_agent.ws is None

    def test_configuration_validation_realtime(self, test_settings):
        """Test configuration validation for realtime mode."""
        with patch("openai_agent.get_settings") as mock_get_settings:
            mock_get_settings.return_value = test_settings
            agent = OpenAIAgent("test-correlation-id")

            # Should not raise an exception for valid realtime config
            assert agent.settings.openai_mode == OpenAIAPIMode.REALTIME

    def test_configuration_validation_invalid_voice(self, test_settings):
        """Test configuration validation with invalid voice."""
        # Create invalid settings
        test_settings.openai_voice = "invalid_voice"

        with patch("openai_agent.get_settings") as mock_get_settings:
            mock_get_settings.return_value = test_settings
            with pytest.raises(ValueError, match="Voice invalid_voice not supported"):
                OpenAIAgent("test-correlation-id")

    @pytest.mark.asyncio
    async def test_session_update_message(self, mock_agent):
        """Test session.update message generation."""
        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()

        # Call the method
        await mock_agent._send_session_update()

        # Verify send was called
        mock_ws.send.assert_called_once()

        # Verify message content
        call_args = mock_ws.send.call_args[0][0]
        message = json.loads(call_args)

        assert message["type"] == "session.update"
        assert message["session"]["type"] == "realtime"
        assert message["session"]["model"] == mock_agent.settings.openai_model
        assert message["session"]["audio"]["input"]["format"]["sample_rate"] == 16000
        assert message["session"]["audio"]["output"]["format"]["sample_rate"] == 16000

    @pytest.mark.asyncio
    async def test_realtime_audio_sending(
        self, mock_agent, mock_call, sample_audio_frame
    ):
        """Test sending audio to realtime API."""
        # Setup mock call
        mock_call.audio_callback.get_audio_frame.return_value = sample_audio_frame

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Mock the loop to run only once
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, Exception("Stop loop")]

            try:
                await mock_agent._send_audio_realtime(mock_call)
            except Exception:
                pass

        # Verify WebSocket send was called
        assert mock_ws.send.called

        # Verify message format
        call_args = mock_ws.send.call_args[0][0]
        message = json.loads(call_args)

        assert message["type"] == "input_audio_buffer.append"
        assert "audio" in message

        # Verify audio is base64 encoded
        audio_data = base64.b64decode(message["audio"])
        assert len(audio_data) == len(sample_audio_frame)

    @pytest.mark.asyncio
    async def test_realtime_audio_receiving(self, mock_agent, mock_call):
        """Test receiving audio from realtime API."""
        # Mock WebSocket responses
        mock_responses = [
            json.dumps(
                {
                    "type": "response.output_audio.delta",
                    "delta": base64.b64encode(b"\x00\x01" * 160).decode("utf-8"),
                }
            ),
            json.dumps(
                {"type": "response.audio_transcript.delta", "delta": "Hello world"}
            ),
            None,  # End of stream
        ]

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv = AsyncMock(side_effect=mock_responses)
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Mock playback
        mock_call.playback_audio = Mock()

        # Run the receiver
        await mock_agent._receive_audio_realtime(mock_call)

        # Verify audio was played back
        mock_call.playback_audio.assert_called_once()

        # Verify audio data
        call_args = mock_call.playback_audio.call_args[0][0]
        assert len(call_args) == 320  # 160 samples * 2 bytes

    @pytest.mark.asyncio
    async def test_legacy_audio_sending(
        self, mock_agent, mock_call, sample_audio_frame
    ):
        """Test sending audio to legacy API."""
        # Setup mock call
        mock_call.audio_callback.get_audio_frame.return_value = sample_audio_frame

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Mock the loop to run only once
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, Exception("Stop loop")]

            try:
                await mock_agent._send_audio_legacy(mock_call)
            except Exception:
                pass

        # Verify WebSocket send was called with raw audio data
        assert mock_ws.send.called
        call_args = mock_ws.send.call_args[0][0]
        assert call_args == sample_audio_frame

    @pytest.mark.asyncio
    async def test_legacy_audio_receiving(self, mock_agent, mock_call):
        """Test receiving audio from legacy API."""
        # Mock WebSocket responses
        mock_responses = [b"\x00\x01" * 160, b"\x02\x03" * 160, None]

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv = AsyncMock(side_effect=mock_responses)
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Mock playback
        mock_call.playback_audio = Mock()

        # Run the receiver
        await mock_agent._receive_audio_legacy(mock_call)

        # Verify audio was played back twice
        assert mock_call.playback_audio.call_count == 2

    @pytest.mark.asyncio
    async def test_websocket_connection_handling(self, mock_agent):
        """Test WebSocket connection handling."""
        # Mock WebSocket connection
        with patch("openai_agent.websockets.connect") as mock_connect:
            mock_ws = AsyncMock()
            mock_ws.closed = False
            mock_connect.return_value.__aenter__.return_value = mock_ws

            # Mock call
            mock_call = Mock()
            mock_call.audio_callback = Mock()
            mock_call.audio_callback.is_active = True
            mock_call.audio_callback.get_audio_frame = AsyncMock(return_value=None)

            # Start agent
            mock_agent.is_active = True

            # Mock the audio processing to complete quickly
            with (
                patch.object(mock_agent, "_send_audio_realtime") as mock_send,
                patch.object(mock_agent, "_receive_audio_realtime") as mock_receive,
            ):

                mock_send.return_value = None
                mock_receive.return_value = None

                await mock_agent._start_realtime_agent(mock_call)

            # Verify WebSocket was used
            assert mock_ws.send.called

    @pytest.mark.asyncio
    async def test_error_handling_in_audio_processing(self, mock_agent, mock_call):
        """Test error handling in audio processing."""
        # Setup mock call that raises an exception
        mock_call.audio_callback.get_audio_frame.side_effect = Exception("Audio error")

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Should handle exception gracefully
        await mock_agent._send_audio_realtime(mock_call)

        # Agent should still be active (not crashed)
        assert mock_agent.is_active

    def test_agent_stop(self, mock_agent):
        """Test agent stop functionality."""
        mock_agent.is_active = True
        mock_agent.ws = AsyncMock()
        mock_agent.ws.closed = False
        mock_agent.ws.close = AsyncMock()

        mock_agent.stop()

        assert mock_agent.is_active is False
        assert mock_agent.ws.close.called


class TestOpenAIAgentIntegration:
    """Test OpenAI agent integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_call_flow_realtime(self, test_settings, sample_audio_frame):
        """Test full call flow with realtime API."""
        with patch("openai_agent.get_settings") as mock_get_settings:
            mock_get_settings.return_value = test_settings

            agent = OpenAIAgent("test-correlation-id")

            # Mock call
            mock_call = Mock()
            mock_call.correlation_id = "test-correlation-id"
            mock_call.audio_callback = Mock()
            mock_call.audio_callback.is_active = True
            mock_call.audio_callback.get_audio_frame = AsyncMock(
                return_value=sample_audio_frame
            )
            mock_call.playback_audio = Mock()

            # Mock WebSocket connection
            with patch("openai_agent.websockets.connect") as mock_connect:
                mock_ws = AsyncMock()
                mock_ws.closed = False
                mock_ws.send = AsyncMock()
                mock_ws.recv = AsyncMock(
                    return_value=json.dumps(
                        {
                            "type": "response.output_audio.delta",
                            "delta": base64.b64encode(b"\x00\x01" * 160).decode(
                                "utf-8"
                            ),
                        }
                    )
                )
                mock_connect.return_value.__aenter__.return_value = mock_ws

                # Mock async gather to prevent infinite loops
                with patch("asyncio.gather") as mock_gather:
                    mock_gather.return_value = None

                    await agent._start_realtime_agent(mock_call)

                # Verify session update was sent
                assert mock_ws.send.called

    @pytest.mark.asyncio
    async def test_token_usage_tracking(
        self, mock_agent, mock_call, sample_audio_frame
    ):
        """Test token usage tracking."""
        # Setup mock call
        mock_call.audio_callback.get_audio_frame.return_value = sample_audio_frame

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Mock metrics
        with patch("openai_agent.get_metrics") as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics

            # Mock the loop to run once
            with patch("asyncio.sleep") as mock_sleep:
                mock_sleep.side_effect = [None, Exception("Stop loop")]

                try:
                    await mock_agent._send_audio_realtime(mock_call)
                except Exception:
                    pass

            # Verify metrics were recorded
            mock_metrics.record_openai_request.assert_called()

    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self, mock_agent, mock_call):
        """Test concurrent audio sending and receiving."""
        # Setup mocks
        mock_call.audio_callback.get_audio_frame.return_value = b"\x00\x01" * 160
        mock_call.playback_audio = Mock()

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "response.output_audio.delta",
                    "delta": base64.b64encode(b"\x00\x01" * 160).decode("utf-8"),
                }
            )
        )
        mock_agent.ws = mock_ws
        mock_agent.is_active = True

        # Run both send and receive concurrently
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, None, Exception("Stop loop")]

            try:
                await asyncio.gather(
                    mock_agent._send_audio_realtime(mock_call),
                    mock_agent._receive_audio_realtime(mock_call),
                    return_exceptions=True,
                )
            except Exception:
                pass

        # Verify both operations occurred
        assert mock_ws.send.called
        assert mock_call.playback_audio.called
