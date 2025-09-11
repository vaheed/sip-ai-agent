#!/usr/bin/env python3
"""
Metrics collection for the SIP AI Agent.

This module provides Prometheus metrics for monitoring call performance,
SIP registration status, audio pipeline health, and OpenAI API usage.
"""

import time
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from config import get_settings
from logging_config import get_logger

logger = get_logger("metrics")

# SIP Metrics
sip_registration_status = Gauge(
    'sip_registration_status',
    'SIP registration status (1=registered, 0=not registered)',
    ['domain', 'user']
)

sip_registration_attempts = Counter(
    'sip_registration_attempts_total',
    'Total number of SIP registration attempts',
    ['domain', 'user', 'result']
)

sip_registration_duration = Histogram(
    'sip_registration_duration_seconds',
    'Time taken for SIP registration',
    ['domain', 'user']
)

sip_calls_total = Counter(
    'sip_calls_total',
    'Total number of SIP calls',
    ['direction', 'result']
)

sip_call_duration = Histogram(
    'sip_call_duration_seconds',
    'Duration of SIP calls',
    ['result']
)

# Audio Metrics
audio_frames_processed = Counter(
    'audio_frames_processed_total',
    'Total number of audio frames processed',
    ['direction', 'call_id']
)

audio_frame_processing_time = Histogram(
    'audio_frame_processing_time_seconds',
    'Time taken to process audio frames',
    ['direction']
)

audio_queue_size = Gauge(
    'audio_queue_size',
    'Current size of audio queue',
    ['call_id']
)

audio_dropouts = Counter(
    'audio_dropouts_total',
    'Total number of audio dropouts',
    ['call_id', 'reason']
)

# OpenAI API Metrics
openai_requests_total = Counter(
    'openai_requests_total',
    'Total number of OpenAI API requests',
    ['api_mode', 'model', 'voice', 'result']
)

openai_request_duration = Histogram(
    'openai_request_duration_seconds',
    'Duration of OpenAI API requests',
    ['api_mode', 'model']
)

openai_tokens_used = Counter(
    'openai_tokens_used_total',
    'Total number of OpenAI tokens used',
    ['api_mode', 'model']
)

openai_websocket_connections = Gauge(
    'openai_websocket_connections',
    'Number of active OpenAI WebSocket connections'
)

# System Metrics
active_calls = Gauge(
    'active_calls',
    'Number of currently active calls'
)

system_info = Info(
    'system_info',
    'System information'
)

# Performance Metrics
call_setup_time = Histogram(
    'call_setup_time_seconds',
    'Time taken to set up a call',
    ['result']
)

end_to_end_latency = Histogram(
    'end_to_end_latency_seconds',
    'End-to-end audio latency',
    ['call_id']
)


class MetricsCollector:
    """Centralized metrics collection and management."""
    
    def __init__(self):
        self.settings = get_settings()
        self._call_start_times: Dict[str, float] = {}
        self._audio_start_times: Dict[str, float] = {}
        self._setup_start_times: Dict[str, float] = {}
        
        # Set system info
        system_info.info({
            'version': '2.1.0',
            'openai_mode': self.settings.openai_mode.value,
            'sip_domain': self.settings.sip_domain,
        })
    
    def start_metrics_server(self) -> None:
        """Start the Prometheus metrics server."""
        if self.settings.metrics_enabled:
            try:
                start_http_server(self.settings.metrics_port)
                logger.info("Metrics server started", port=self.settings.metrics_port)
            except Exception as e:
                logger.error("Failed to start metrics server", error=str(e))
    
    # SIP Metrics
    def update_sip_registration_status(self, domain: str, user: str, registered: bool) -> None:
        """Update SIP registration status."""
        sip_registration_status.labels(domain=domain, user=user).set(1 if registered else 0)
        logger.info("SIP registration status updated", domain=domain, user=user, registered=registered)
    
    def record_sip_registration_attempt(self, domain: str, user: str, success: bool, duration: float) -> None:
        """Record a SIP registration attempt."""
        result = "success" if success else "failure"
        sip_registration_attempts.labels(domain=domain, user=user, result=result).inc()
        sip_registration_duration.labels(domain=domain, user=user).observe(duration)
        logger.info("SIP registration attempt recorded", 
                   domain=domain, user=user, success=success, duration=duration)
    
    def record_call_start(self, call_id: str, direction: str = "incoming") -> None:
        """Record the start of a call."""
        self._call_start_times[call_id] = time.time()
        self._setup_start_times[call_id] = time.time()
        sip_calls_total.labels(direction=direction, result="started").inc()
        active_calls.inc()
        logger.info("Call started", call_id=call_id, direction=direction)
    
    def record_call_end(self, call_id: str, result: str = "completed") -> None:
        """Record the end of a call."""
        if call_id in self._call_start_times:
            duration = time.time() - self._call_start_times[call_id]
            sip_call_duration.labels(result=result).observe(duration)
            del self._call_start_times[call_id]
        
        if call_id in self._setup_start_times:
            setup_time = time.time() - self._setup_start_times[call_id]
            call_setup_time.labels(result=result).observe(setup_time)
            del self._setup_start_times[call_id]
        
        sip_calls_total.labels(direction="incoming", result=result).inc()
        active_calls.dec()
        logger.info("Call ended", call_id=call_id, result=result)
    
    # Audio Metrics
    def record_audio_frame(self, call_id: str, direction: str, processing_time: float) -> None:
        """Record an audio frame being processed."""
        audio_frames_processed.labels(direction=direction, call_id=call_id).inc()
        audio_frame_processing_time.labels(direction=direction).observe(processing_time)
    
    def update_audio_queue_size(self, call_id: str, size: int) -> None:
        """Update the audio queue size for a call."""
        audio_queue_size.labels(call_id=call_id).set(size)
    
    def record_audio_dropout(self, call_id: str, reason: str) -> None:
        """Record an audio dropout."""
        audio_dropouts.labels(call_id=call_id, reason=reason).inc()
        logger.warning("Audio dropout recorded", call_id=call_id, reason=reason)
    
    def start_audio_latency_measurement(self, call_id: str) -> None:
        """Start measuring end-to-end audio latency."""
        self._audio_start_times[call_id] = time.time()
    
    def record_audio_latency(self, call_id: str) -> None:
        """Record end-to-end audio latency."""
        if call_id in self._audio_start_times:
            latency = time.time() - self._audio_start_times[call_id]
            end_to_end_latency.labels(call_id=call_id).observe(latency)
            del self._audio_start_times[call_id]
    
    # OpenAI Metrics
    def record_openai_request(self, api_mode: str, model: str, voice: str, 
                            success: bool, duration: float, tokens: int = 0) -> None:
        """Record an OpenAI API request."""
        result = "success" if success else "failure"
        openai_requests_total.labels(
            api_mode=api_mode, model=model, voice=voice, result=result
        ).inc()
        openai_request_duration.labels(api_mode=api_mode, model=model).observe(duration)
        
        if tokens > 0:
            openai_tokens_used.labels(api_mode=api_mode, model=model).inc(tokens)
    
    def update_websocket_connections(self, count: int) -> None:
        """Update the number of active WebSocket connections."""
        openai_websocket_connections.set(count)
    
    def record_websocket_connection(self, api_mode: str) -> None:
        """Record a WebSocket connection."""
        openai_websocket_connections.inc()
        logger.info("WebSocket connection established", api_mode=api_mode)
    
    def record_websocket_disconnection(self, api_mode: str) -> None:
        """Record a WebSocket disconnection."""
        openai_websocket_connections.dec()
        logger.info("WebSocket connection closed", api_mode=api_mode)
    
    # Utility Methods
    def get_active_calls_count(self) -> int:
        """Get the current number of active calls."""
        return len(self._call_start_times)
    
    def get_call_duration(self, call_id: str) -> Optional[float]:
        """Get the current duration of a call."""
        if call_id in self._call_start_times:
            return time.time() - self._call_start_times[call_id]
        return None
    
    def cleanup_call_metrics(self, call_id: str) -> None:
        """Clean up metrics for a completed call."""
        self._call_start_times.pop(call_id, None)
        self._audio_start_times.pop(call_id, None)
        self._setup_start_times.pop(call_id, None)
        audio_queue_size.remove(call_id)


# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics
