#!/usr/bin/env python3
"""
Structured logging configuration for the SIP AI Agent.

This module provides JSON-structured logging with correlation IDs,
performance metrics, and integration with the monitoring system.
"""

import sys
import json
import time
import uuid
import structlog
from typing import Any, Dict, Optional
from config import get_settings


class CorrelationIDProcessor:
    """Add correlation ID to log records."""

    def __init__(self):
        self._correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the current correlation ID."""
        self._correlation_id = correlation_id

    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
        self._correlation_id = None

    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID."""
        return self._correlation_id

    def __call__(self, logger, method_name, event_dict):
        """Add correlation ID to log record."""
        if self._correlation_id:
            event_dict["correlation_id"] = self._correlation_id
        return event_dict


class CallMetricsProcessor:
    """Add call metrics to log records."""

    def __init__(self):
        self._call_start_times: Dict[str, float] = {}

    def start_call(self, call_id: str) -> None:
        """Record call start time."""
        self._call_start_times[call_id] = time.time()

    def end_call(self, call_id: str) -> Optional[float]:
        """Record call end time and return duration."""
        if call_id in self._call_start_times:
            duration = time.time() - self._call_start_times[call_id]
            del self._call_start_times[call_id]
            return duration
        return None

    def __call__(self, logger, method_name, event_dict):
        """Add call metrics to log record."""
        # Add active call count
        event_dict["active_calls"] = len(self._call_start_times)

        # Add call duration if available
        call_id = event_dict.get("call_id")
        if call_id and call_id in self._call_start_times:
            event_dict["call_duration"] = time.time() - self._call_start_times[call_id]

        return event_dict


class JSONFormatter:
    """Custom JSON formatter for structured logs."""

    def __call__(self, logger, method_name, event_dict):
        """Format log record as JSON."""
        # Add timestamp
        event_dict["timestamp"] = time.time()

        # Add level
        event_dict["level"] = method_name.upper()

        # Add logger name
        event_dict["logger"] = logger.name

        # Format as JSON string
        return json.dumps(event_dict, separators=(",", ":"), ensure_ascii=False)


# Global processors
correlation_processor = CorrelationIDProcessor()
metrics_processor = CallMetricsProcessor()


def setup_logging() -> None:
    """Setup structured logging configuration."""
    settings = get_settings()

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        correlation_processor,
        metrics_processor,
    ]

    if settings.structured_logging:
        processors.append(JSONFormatter())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.monitor_log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def with_correlation_id(correlation_id: str):
    """Context manager for correlation ID."""
    correlation_processor.set_correlation_id(correlation_id)
    try:
        yield
    finally:
        correlation_processor.clear_correlation_id()


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def log_call_event(event_type: str, call_id: str, **kwargs) -> None:
    """Log a call-related event with metrics."""
    logger = get_logger("call")

    if event_type == "call_start":
        metrics_processor.start_call(call_id)
        logger.info("Call started", event_type=event_type, call_id=call_id, **kwargs)
    elif event_type == "call_end":
        duration = metrics_processor.end_call(call_id)
        if duration is not None:
            kwargs["duration"] = duration
        logger.info("Call ended", event_type=event_type, call_id=call_id, **kwargs)
    else:
        logger.info("Call event", event_type=event_type, call_id=call_id, **kwargs)


def log_sip_event(event_type: str, **kwargs) -> None:
    """Log a SIP-related event."""
    logger = get_logger("sip")
    logger.info("SIP event", event_type=event_type, **kwargs)


def log_openai_event(event_type: str, **kwargs) -> None:
    """Log an OpenAI API event."""
    logger = get_logger("openai")
    logger.info("OpenAI event", event_type=event_type, **kwargs)


def log_audio_event(event_type: str, call_id: str, **kwargs) -> None:
    """Log an audio processing event."""
    logger = get_logger("audio")
    logger.info("Audio event", event_type=event_type, call_id=call_id, **kwargs)


def log_performance_metric(metric_name: str, value: float, **kwargs) -> None:
    """Log a performance metric."""
    logger = get_logger("performance")
    logger.info("Performance metric", metric_name=metric_name, value=value, **kwargs)
