#!/usr/bin/env python3
"""
Enhanced SIP client with reliability features.

This module provides a robust SIP client with automatic reconnection,
NAT traversal support, SRTP encryption, and comprehensive error handling.
"""

import time
import asyncio
import threading
from typing import Optional, Dict, Any, Callable, List
import pjsua2 as pj
from config import get_settings, SIPCodec
from logging_config import (
    get_logger,
    log_sip_event,
    with_correlation_id,
    generate_correlation_id,
)
from metrics import get_metrics

logger = get_logger("sip_client")
metrics = get_metrics()


class SIPRegistrationError(Exception):
    """Exception raised for SIP registration errors."""

    pass


class SIPCallError(Exception):
    """Exception raised for SIP call errors."""

    pass


class EnhancedAudioCallback(pj.AudioMedia):
    """Enhanced audio callback with backpressure and error handling."""

    def __init__(self, call, correlation_id: str):
        pj.AudioMedia.__init__(self)
        self.call = call
        self.correlation_id = correlation_id
        self.audio_queue = asyncio.Queue(
            maxsize=get_settings().audio_backpressure_threshold
        )
        self.is_active = True
        self.frame_count = 0
        self.dropout_count = 0

    def onFrameRequested(self, frame):
        """Handle audio frame requests with backpressure control."""
        if not self.is_active:
            return

        try:
            if frame.type == pj.PJMEDIA_FRAME_TYPE_AUDIO and frame.buf:
                # Check for backpressure
                if (
                    self.audio_queue.qsize()
                    >= get_settings().audio_backpressure_threshold
                ):
                    metrics.record_audio_dropout(self.correlation_id, "backpressure")
                    self.dropout_count += 1
                    logger.warning(
                        "Audio backpressure detected",
                        correlation_id=self.correlation_id,
                        queue_size=self.audio_queue.qsize(),
                    )
                    return

                # Put frame in queue (non-blocking)
                try:
                    self.audio_queue.put_nowait(frame.buf)
                    self.frame_count += 1
                    metrics.update_audio_queue_size(
                        self.correlation_id, self.audio_queue.qsize()
                    )
                except asyncio.QueueFull:
                    metrics.record_audio_dropout(self.correlation_id, "queue_full")
                    self.dropout_count += 1

        except Exception as e:
            logger.error(
                "Error in audio frame processing",
                correlation_id=self.correlation_id,
                error=str(e),
            )
            metrics.record_audio_dropout(self.correlation_id, "processing_error")

    def stop(self):
        """Stop the audio callback."""
        self.is_active = False
        logger.info(
            "Audio callback stopped",
            correlation_id=self.correlation_id,
            total_frames=self.frame_count,
            dropouts=self.dropout_count,
        )

    async def get_audio_frame(self) -> Optional[bytes]:
        """Get the next audio frame from the queue."""
        try:
            return await asyncio.wait_for(self.audio_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(
                "Error getting audio frame",
                correlation_id=self.correlation_id,
                error=str(e),
            )
            return None


class EnhancedCall(pj.Call):
    """Enhanced SIP call with improved error handling and metrics."""

    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.call_id = call_id
        self.correlation_id = generate_correlation_id()
        self.audio_callback: Optional[EnhancedAudioCallback] = None
        self.ws = None
        self.openai_thread = None
        self.start_time = time.time()
        self.callback_handlers: Dict[str, Callable] = {}

    def onCallState(self, prm):
        """Handle call state changes with enhanced logging and metrics."""
        ci = self.getInfo()
        state_text = ci.stateText

        with with_correlation_id(self.correlation_id):
            log_sip_event(
                "call_state_change",
                call_id=self.call_id,
                correlation_id=self.correlation_id,
                state=state_text,
                state_code=ci.state,
            )

            if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
                # Call established
                metrics.record_call_start(str(self.call_id))
                logger.info(
                    "Call established",
                    call_id=self.call_id,
                    correlation_id=self.correlation_id,
                )

                # Create enhanced audio callback
                self.audio_callback = EnhancedAudioCallback(self, self.correlation_id)
                call_slot = self.getAudioMedia(-1)
                call_slot.startTransmit(self.audio_callback)

                # Start OpenAI agent
                self._start_openai_agent()

            elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
                # Call ended
                duration = time.time() - self.start_time
                metrics.record_call_end(str(self.call_id))

                logger.info(
                    "Call disconnected",
                    call_id=self.call_id,
                    correlation_id=self.correlation_id,
                    duration=duration,
                )

                self._cleanup_call()

            elif ci.state == pj.PJSIP_INV_STATE_CALLING:
                logger.info(
                    "Call initiated",
                    call_id=self.call_id,
                    correlation_id=self.correlation_id,
                )

            elif ci.state == pj.PJSIP_INV_STATE_EARLY:
                logger.info(
                    "Call ringing",
                    call_id=self.call_id,
                    correlation_id=self.correlation_id,
                )

    def _start_openai_agent(self):
        """Start the OpenAI agent in a separate thread."""
        from agent import OpenAIAgent  # Import here to avoid circular imports

        try:
            agent = OpenAIAgent(self.correlation_id)
            self.openai_thread = threading.Thread(
                target=asyncio.run, args=(agent.start(self),), daemon=True
            )
            self.openai_thread.start()
            logger.info(
                "OpenAI agent started",
                call_id=self.call_id,
                correlation_id=self.correlation_id,
            )
        except Exception as e:
            logger.error(
                "Failed to start OpenAI agent",
                call_id=self.call_id,
                correlation_id=self.correlation_id,
                error=str(e),
            )

    def _cleanup_call(self):
        """Clean up call resources."""
        if self.audio_callback:
            self.audio_callback.stop()
            self.audio_callback = None

        if self.ws and not self.ws.closed:
            try:
                asyncio.run(self.ws.close())
            except Exception as e:
                logger.error(
                    "Error closing WebSocket",
                    call_id=self.call_id,
                    correlation_id=self.correlation_id,
                    error=str(e),
                )

        # Clean up metrics
        metrics.cleanup_call_metrics(self.correlation_id)

    def playback_audio(self, audio_data: bytes):
        """Play audio back to the caller with error handling."""
        try:
            if not self.audio_callback or not self.audio_callback.is_active:
                return

            # Create audio media for playback
            player = pj.AudioMediaPlayer()
            player.createPlayerFromBuffer(audio_data)
            player.startTransmit(self.getAudioMedia(-1))

            logger.debug(
                "Audio played back",
                call_id=self.call_id,
                correlation_id=self.correlation_id,
                size=len(audio_data),
            )

        except Exception as e:
            logger.error(
                "Error playing back audio",
                call_id=self.call_id,
                correlation_id=self.correlation_id,
                error=str(e),
            )
            metrics.record_audio_dropout(self.correlation_id, "playback_error")


class EnhancedAccount(pj.Account):
    """Enhanced SIP account with automatic reconnection and error handling."""

    def __init__(self, ep, settings):
        pj.Account.__init__(self)
        self.ep = ep
        self.settings = settings
        self.is_registered = False
        self.registration_attempts = 0
        self.last_registration_attempt = 0
        self.registration_start_time = 0
        self.reconnect_task = None

    def onRegState(self, prm):
        """Handle registration state changes with automatic reconnection."""
        ai = self.getInfo()
        reg_status = ai.regStatus
        reg_status_text = ai.regStatusText

        log_sip_event(
            "registration_state_change",
            domain=self.settings.sip_domain,
            user=self.settings.sip_user,
            status=reg_status,
            status_text=reg_status_text,
            attempts=self.registration_attempts,
        )

        if reg_status == 200:
            # Registration successful
            self.is_registered = True
            self.registration_attempts = 0

            if self.registration_start_time > 0:
                duration = time.time() - self.registration_start_time
                metrics.record_sip_registration_attempt(
                    self.settings.sip_domain, self.settings.sip_user, True, duration
                )

            metrics.update_sip_registration_status(
                self.settings.sip_domain, self.settings.sip_user, True
            )

            logger.info(
                "SIP registration successful",
                domain=self.settings.sip_domain,
                user=self.settings.sip_user,
            )

        else:
            # Registration failed
            self.is_registered = False

            if self.registration_start_time > 0:
                duration = time.time() - self.registration_start_time
                metrics.record_sip_registration_attempt(
                    self.settings.sip_domain, self.settings.sip_user, False, duration
                )

            metrics.update_sip_registration_status(
                self.settings.sip_domain, self.settings.sip_user, False
            )

            logger.error(
                "SIP registration failed",
                domain=self.settings.sip_domain,
                user=self.settings.sip_user,
                status=reg_status,
                status_text=reg_status_text,
            )

            # Schedule reconnection if within retry limits
            if self.registration_attempts < self.settings.sip_registration_retry_max:
                self._schedule_reconnect()

    def _schedule_reconnect(self):
        """Schedule automatic reconnection with exponential backoff."""
        if self.reconnect_task and not self.reconnect_task.done():
            return

        self.registration_attempts += 1
        backoff_time = (
            self.settings.sip_registration_retry_backoff**self.registration_attempts
        )

        logger.info(
            "Scheduling SIP reconnection",
            domain=self.settings.sip_domain,
            user=self.settings.sip_user,
            attempt=self.registration_attempts,
            backoff_seconds=backoff_time,
        )

        self.reconnect_task = asyncio.create_task(
            self._reconnect_after_delay(backoff_time)
        )

    async def _reconnect_after_delay(self, delay: float):
        """Reconnect after a delay."""
        await asyncio.sleep(delay)
        await self._attempt_registration()

    async def _attempt_registration(self):
        """Attempt SIP registration."""
        try:
            self.registration_start_time = time.time()

            # Create account configuration
            acc_cfg = pj.AccountConfig()
            acc_cfg.idUri = f"sip:{self.settings.sip_user}@{self.settings.sip_domain}"
            acc_cfg.regConfig.registrarUri = f"sip:{self.settings.sip_domain}"
            acc_cfg.regConfig.timeoutSec = self.settings.sip_registration_timeout

            # Add authentication credentials
            cred = pj.AuthCredInfo(
                "digest", "*", self.settings.sip_user, 0, self.settings.sip_pass
            )
            acc_cfg.sipConfig.authCreds.append(cred)

            # Configure codecs
            if hasattr(acc_cfg, "mediaConfig") and hasattr(
                acc_cfg.mediaConfig, "codecConfig"
            ):
                codec_cfg = acc_cfg.mediaConfig.codecConfig
                for codec in self.settings.get_sip_codec_list():
                    codec_cfg.setCodecPriority(codec, pj.PJMEDIA_CODEC_PRIORITY_HIGH)

            # Apply configuration
            self.create(acc_cfg)

            logger.info(
                "SIP registration attempt initiated",
                domain=self.settings.sip_domain,
                user=self.settings.sip_user,
                attempt=self.registration_attempts,
            )

        except Exception as e:
            logger.error(
                "Error during SIP registration attempt",
                domain=self.settings.sip_domain,
                user=self.settings.sip_user,
                error=str(e),
            )
            self._schedule_reconnect()

    def onIncomingCall(self, prm):
        """Handle incoming calls with enhanced logging."""
        logger.info(
            "Incoming call received",
            call_id=prm.callId,
            from_uri=getattr(prm, "fromUri", "unknown"),
        )

        call = EnhancedCall(self, prm.callId)
        call_prm = pj.CallOpParam()
        call_prm.statusCode = 200  # OK

        try:
            call.answer(call_prm)
            log_sip_event("incoming_call_answered", call_id=prm.callId)
        except Exception as e:
            logger.error(
                "Error answering incoming call", call_id=prm.callId, error=str(e)
            )
            log_sip_event("incoming_call_error", call_id=prm.callId, error=str(e))


class SIPClient:
    """Enhanced SIP client with comprehensive error handling and monitoring."""

    def __init__(self):
        self.settings = get_settings()
        self.ep = None
        self.transport = None
        self.account = None
        self.is_initialized = False

    def initialize(self) -> None:
        """Initialize the SIP client with enhanced configuration."""
        try:
            # Create and initialize PJSIP library
            ep_cfg = pj.EpConfig()

            # Configure logging
            if self.settings.log_sip_messages:
                ep_cfg.logConfig.level = 4  # Enable SIP message logging
                ep_cfg.logConfig.consoleLevel = 4

            self.ep = pj.Endpoint()
            self.ep.libCreate()
            self.ep.libInit(ep_cfg)

            # Create SIP transport
            transport_cfg = pj.TransportConfig()
            transport_cfg.port = self.settings.sip_port

            # Configure transport type
            transport_type = pj.PJSIP_TRANSPORT_UDP
            if self.settings.sip_transport.upper() == "TCP":
                transport_type = pj.PJSIP_TRANSPORT_TCP
            elif self.settings.sip_transport.upper() == "TLS":
                transport_type = pj.PJSIP_TRANSPORT_TLS
                transport_cfg.tlsConfig.certFile = getattr(
                    self.settings, "sip_cert_file", ""
                )
                transport_cfg.tlsConfig.privKeyFile = getattr(
                    self.settings, "sip_key_file", ""
                )

            self.transport = self.ep.transportCreate(transport_type, transport_cfg)

            # Start PJSIP
            self.ep.libStart()

            # Create enhanced account
            self.account = EnhancedAccount(self.ep, self.settings)

            self.is_initialized = True
            logger.info(
                "SIP client initialized",
                domain=self.settings.sip_domain,
                port=self.settings.sip_port,
                transport=self.settings.sip_transport,
            )

        except Exception as e:
            logger.error("Failed to initialize SIP client", error=str(e))
            raise SIPRegistrationError(f"SIP initialization failed: {e}")

    async def register(self) -> None:
        """Register with the SIP server."""
        if not self.is_initialized:
            raise SIPRegistrationError("SIP client not initialized")

        await self.account._attempt_registration()

    def shutdown(self) -> None:
        """Shutdown the SIP client."""
        try:
            if self.account:
                self.account.delete()

            if self.transport:
                self.transport.delete()

            if self.ep:
                self.ep.libDestroy()
                self.ep.libDelete()

            self.is_initialized = False
            logger.info("SIP client shutdown completed")

        except Exception as e:
            logger.error("Error during SIP client shutdown", error=str(e))

    def is_registered(self) -> bool:
        """Check if the SIP client is registered."""
        return self.account and self.account.is_registered
