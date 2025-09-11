#!/usr/bin/env python3
"""
Enhanced OpenAI agent with improved error handling and realtime configuration.

This module provides robust integration with OpenAI's API, including
the legacy speech API and the new realtime API with proper session management.
"""

import json
import base64
import asyncio
import time
import websockets
from typing import Optional, Dict, Any, AsyncGenerator
from openai import OpenAI
from config import get_settings, OpenAIAPIMode, OpenAIVoice, OpenAIRealtimeModel
from logging_config import get_logger, log_openai_event, with_correlation_id
from metrics import get_metrics

logger = get_logger("openai_agent")
metrics = get_metrics()


class OpenAIAgent:
    """Enhanced OpenAI agent with comprehensive error handling and metrics."""

    def __init__(self, correlation_id: str):
        self.settings = get_settings()
        self.correlation_id = correlation_id
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.ws = None
        self.is_active = False
        self.start_time = time.time()

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate OpenAI configuration."""
        if self.settings.openai_mode == OpenAIAPIMode.REALTIME:
            # Validate voice for realtime mode
            if self.settings.openai_voice not in [
                OpenAIVoice.ALLOY,
                OpenAIVoice.ECHO,
                OpenAIVoice.FABLE,
                OpenAIVoice.ONYX,
                OpenAIVoice.NOVA,
                OpenAIVoice.SHIMMER,
                OpenAIVoice.CEDAR,
                OpenAIVoice.MARIN,
            ]:
                raise ValueError(
                    f"Voice {self.settings.openai_voice} not supported in realtime mode"
                )

            # Validate model for realtime mode
            if self.settings.openai_model not in [
                model.value for model in OpenAIRealtimeModel
            ]:
                raise ValueError(
                    f"Model {self.settings.openai_model} not supported in realtime mode"
                )

        logger.info(
            "OpenAI configuration validated",
            correlation_id=self.correlation_id,
            mode=self.settings.openai_mode.value,
            model=self.settings.openai_model,
            voice=self.settings.openai_voice.value,
        )

    async def start(self, call) -> None:
        """Start the OpenAI agent for the given call."""
        with with_correlation_id(self.correlation_id):
            try:
                self.is_active = True

                if self.settings.openai_mode == OpenAIAPIMode.REALTIME:
                    await self._start_realtime_agent(call)
                else:
                    await self._start_legacy_agent(call)

            except Exception as e:
                logger.error(
                    "Failed to start OpenAI agent",
                    correlation_id=self.correlation_id,
                    error=str(e),
                )
                metrics.record_openai_request(
                    self.settings.openai_mode.value,
                    self.settings.openai_model,
                    self.settings.openai_voice.value,
                    False,
                    time.time() - self.start_time,
                )
                raise

    async def _start_legacy_agent(self, call) -> None:
        """Start the legacy OpenAI speech API agent."""
        logger.info("Starting legacy OpenAI agent", correlation_id=self.correlation_id)

        ws_url = "wss://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with websockets.connect(ws_url, extra_headers=headers) as self.ws:
                metrics.record_websocket_connection(self.settings.openai_mode.value)

                # Send initial configuration
                config = {
                    "agent_id": self.settings.agent_id,
                    "sample_rate": self.settings.audio_sample_rate,
                    "encoding": "linear16",
                    "audio_channels": self.settings.audio_channels,
                }
                await self.ws.send(json.dumps(config))

                log_openai_event(
                    "legacy_session_started",
                    correlation_id=self.correlation_id,
                    config=config,
                )

                # Start concurrent audio processing
                await asyncio.gather(
                    self._send_audio_legacy(call),
                    self._receive_audio_legacy(call),
                    return_exceptions=True,
                )

        except Exception as e:
            logger.error(
                "Legacy agent error", correlation_id=self.correlation_id, error=str(e)
            )
            raise
        finally:
            if self.ws:
                metrics.record_websocket_disconnection(self.settings.openai_mode.value)

    async def _start_realtime_agent(self, call) -> None:
        """Start the realtime OpenAI API agent with proper session configuration."""
        logger.info(
            "Starting realtime OpenAI agent", correlation_id=self.correlation_id
        )

        # Build WebSocket URL with parameters
        ws_url = (
            f"wss://api.openai.com/v1/realtime?"
            f"model={self.settings.openai_model}&"
            f"voice={self.settings.openai_voice.value}&"
            f"temperature={self.settings.openai_temperature}"
        )

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        try:
            async with websockets.connect(ws_url, extra_headers=headers) as self.ws:
                metrics.record_websocket_connection(self.settings.openai_mode.value)

                # Send session.update with proper configuration
                await self._send_session_update()

                log_openai_event(
                    "realtime_session_started",
                    correlation_id=self.correlation_id,
                    model=self.settings.openai_model,
                    voice=self.settings.openai_voice.value,
                )

                # Start concurrent audio processing
                await asyncio.gather(
                    self._send_audio_realtime(call),
                    self._receive_audio_realtime(call),
                    return_exceptions=True,
                )

        except Exception as e:
            logger.error(
                "Realtime agent error", correlation_id=self.correlation_id, error=str(e)
            )
            raise
        finally:
            if self.ws:
                metrics.record_websocket_disconnection(self.settings.openai_mode.value)

    async def _send_session_update(self) -> None:
        """Send session.update message for realtime API."""
        session_update = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "model": self.settings.openai_model,
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "format": {
                            "type": "audio/pcm16",
                            "sample_rate": self.settings.audio_sample_rate,
                        },
                        "turn_detection": {"type": "server_vad"},
                    },
                    "output": {
                        "format": {
                            "type": "audio/pcm16",
                            "sample_rate": self.settings.audio_sample_rate,
                        }
                    },
                },
                "instructions": self.settings.system_prompt,
            },
        }

        await self.ws.send(json.dumps(session_update))

        log_openai_event(
            "session_update_sent",
            correlation_id=self.correlation_id,
            session_config=session_update,
        )

    async def _send_audio_legacy(self, call) -> None:
        """Send audio to legacy OpenAI API."""
        logger.info("Starting legacy audio sender", correlation_id=self.correlation_id)

        frame_count = 0
        total_bytes = 0

        try:
            while (
                self.is_active and call.audio_callback and call.audio_callback.is_active
            ):
                audio_chunk = await call.audio_callback.get_audio_frame()

                if audio_chunk and self.ws and not self.ws.closed:
                    frame_start = time.time()

                    await self.ws.send(audio_chunk)

                    frame_count += 1
                    total_bytes += len(audio_chunk)

                    # Record metrics
                    processing_time = time.time() - frame_start
                    metrics.record_audio_frame(
                        self.correlation_id, "input", processing_time
                    )

                    # Estimate token usage
                    tokens_estimate = len(audio_chunk) // 1000
                    if tokens_estimate > 0:
                        metrics.record_openai_request(
                            self.settings.openai_mode.value,
                            self.settings.openai_model,
                            self.settings.openai_voice.value,
                            True,
                            0,
                            tokens_estimate,
                        )

                    if frame_count % 100 == 0:  # Log every 100 frames
                        logger.debug(
                            "Legacy audio progress",
                            correlation_id=self.correlation_id,
                            frames=frame_count,
                            total_bytes=total_bytes,
                        )

                await asyncio.sleep(0.001)  # Small delay to prevent busy waiting

        except Exception as e:
            logger.error(
                "Legacy audio sender error",
                correlation_id=self.correlation_id,
                error=str(e),
            )
        finally:
            logger.info(
                "Legacy audio sender completed",
                correlation_id=self.correlation_id,
                total_frames=frame_count,
                total_bytes=total_bytes,
            )

    async def _send_audio_realtime(self, call) -> None:
        """Send audio to realtime OpenAI API."""
        logger.info(
            "Starting realtime audio sender", correlation_id=self.correlation_id
        )

        frame_count = 0
        total_bytes = 0

        try:
            while (
                self.is_active and call.audio_callback and call.audio_callback.is_active
            ):
                audio_chunk = await call.audio_callback.get_audio_frame()

                if audio_chunk and self.ws and not self.ws.closed:
                    frame_start = time.time()

                    # Base64 encode the PCM data
                    audio_b64 = base64.b64encode(audio_chunk).decode("utf-8")
                    message = {"type": "input_audio_buffer.append", "audio": audio_b64}

                    await self.ws.send(json.dumps(message))

                    frame_count += 1
                    total_bytes += len(audio_chunk)

                    # Record metrics
                    processing_time = time.time() - frame_start
                    metrics.record_audio_frame(
                        self.correlation_id, "input", processing_time
                    )

                    # Estimate token usage
                    tokens_estimate = len(audio_chunk) // 1000
                    if tokens_estimate > 0:
                        metrics.record_openai_request(
                            self.settings.openai_mode.value,
                            self.settings.openai_model,
                            self.settings.openai_voice.value,
                            True,
                            0,
                            tokens_estimate,
                        )

                    if frame_count % 100 == 0:  # Log every 100 frames
                        logger.debug(
                            "Realtime audio progress",
                            correlation_id=self.correlation_id,
                            frames=frame_count,
                            total_bytes=total_bytes,
                        )

                await asyncio.sleep(0.001)  # Small delay to prevent busy waiting

        except Exception as e:
            logger.error(
                "Realtime audio sender error",
                correlation_id=self.correlation_id,
                error=str(e),
            )
        finally:
            logger.info(
                "Realtime audio sender completed",
                correlation_id=self.correlation_id,
                total_frames=frame_count,
                total_bytes=total_bytes,
            )

    async def _receive_audio_legacy(self, call) -> None:
        """Receive audio from legacy OpenAI API."""
        logger.info(
            "Starting legacy audio receiver", correlation_id=self.correlation_id
        )

        frame_count = 0
        total_bytes = 0

        try:
            while self.is_active and self.ws and not self.ws.closed:
                response = await self.ws.recv()

                if isinstance(response, bytes):
                    frame_start = time.time()

                    call.playback_audio(response)

                    frame_count += 1
                    total_bytes += len(response)

                    # Record metrics
                    processing_time = time.time() - frame_start
                    metrics.record_audio_frame(
                        self.correlation_id, "output", processing_time
                    )

                    if frame_count % 10 == 0:  # Log every 10 frames
                        logger.debug(
                            "Legacy audio playback progress",
                            correlation_id=self.correlation_id,
                            frames=frame_count,
                            total_bytes=total_bytes,
                        )

        except Exception as e:
            logger.error(
                "Legacy audio receiver error",
                correlation_id=self.correlation_id,
                error=str(e),
            )
        finally:
            logger.info(
                "Legacy audio receiver completed",
                correlation_id=self.correlation_id,
                total_frames=frame_count,
                total_bytes=total_bytes,
            )

    async def _receive_audio_realtime(self, call) -> None:
        """Receive audio from realtime OpenAI API."""
        logger.info(
            "Starting realtime audio receiver", correlation_id=self.correlation_id
        )

        frame_count = 0
        total_bytes = 0

        try:
            while self.is_active and self.ws and not self.ws.closed:
                raw_msg = await self.ws.recv()

                if not raw_msg:
                    continue

                try:
                    message = json.loads(raw_msg)
                except json.JSONDecodeError:
                    logger.warning(
                        "Received non-JSON message", correlation_id=self.correlation_id
                    )
                    continue

                msg_type = message.get("type")

                if msg_type == "response.output_audio.delta" and "delta" in message:
                    frame_start = time.time()

                    try:
                        audio_bytes = base64.b64decode(message["delta"])
                        call.playback_audio(audio_bytes)

                        frame_count += 1
                        total_bytes += len(audio_bytes)

                        # Record metrics
                        processing_time = time.time() - frame_start
                        metrics.record_audio_frame(
                            self.correlation_id, "output", processing_time
                        )

                        if frame_count % 10 == 0:  # Log every 10 frames
                            logger.debug(
                                "Realtime audio playback progress",
                                correlation_id=self.correlation_id,
                                frames=frame_count,
                                total_bytes=total_bytes,
                            )

                    except Exception as decode_err:
                        logger.error(
                            "Error decoding audio delta",
                            correlation_id=self.correlation_id,
                            error=str(decode_err),
                        )

                elif msg_type == "response.audio_transcript.delta":
                    # Log transcription updates (optional)
                    transcript = message.get("delta", "")
                    if transcript.strip():
                        logger.debug(
                            "Transcription update",
                            correlation_id=self.correlation_id,
                            transcript=transcript,
                        )

                elif msg_type == "error":
                    # Handle API errors
                    error_info = message.get("error", {})
                    logger.error(
                        "OpenAI API error",
                        correlation_id=self.correlation_id,
                        error=error_info,
                    )
                    break

        except Exception as e:
            logger.error(
                "Realtime audio receiver error",
                correlation_id=self.correlation_id,
                error=str(e),
            )
        finally:
            logger.info(
                "Realtime audio receiver completed",
                correlation_id=self.correlation_id,
                total_frames=frame_count,
                total_bytes=total_bytes,
            )

    def stop(self) -> None:
        """Stop the OpenAI agent."""
        self.is_active = False

        if self.ws and not self.ws.closed:
            asyncio.create_task(self.ws.close())

        duration = time.time() - self.start_time
        logger.info(
            "OpenAI agent stopped",
            correlation_id=self.correlation_id,
            duration=duration,
        )
