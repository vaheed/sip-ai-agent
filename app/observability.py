#!/usr/bin/env python3
"""Shared observability helpers for structured logging and metrics."""
from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import math
import os
import sys
import threading
import time
import uuid
from collections import Counter
from typing import Any, Dict, Iterable, Iterator, Optional

__all__ = [
    "correlation_scope",
    "current_correlation_id",
    "generate_correlation_id",
    "get_logger",
    "metrics",
]

# ---------------------------------------------------------------------------
# Correlation ID handling
# ---------------------------------------------------------------------------

_correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def current_correlation_id() -> Optional[str]:
    """Return the correlation ID associated with the current context."""

    return _correlation_id_var.get()


@contextlib.contextmanager
def correlation_scope(correlation_id: Optional[str]) -> Iterator[None]:
    """Context manager that sets the correlation ID for nested log records."""

    if correlation_id is None:
        yield
        return

    token = _correlation_id_var.set(correlation_id)
    try:
        yield
    finally:
        _correlation_id_var.reset(token)


def generate_correlation_id() -> str:
    """Generate a new random correlation identifier."""

    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Structured logging configuration
# ---------------------------------------------------------------------------

_LOGGING_CONFIGURED = False

# Attributes defined by the logging system that should not be emitted as part
# of the structured payload. This list mirrors ``logging.LogRecord`` fields.
_RESERVED_LOG_ATTRIBUTES = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


def _json_default(value: Any) -> Any:
    """Fallback JSON serialiser that stringifies unsupported values."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_default(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _json_default(v) for k, v in value.items()}
    return str(value)


class _JsonFormatter(logging.Formatter):
    """Format log records as structured JSON lines."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - override
        payload: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = getattr(record, "correlation_id", None) or current_correlation_id()
        if correlation_id:
            payload["correlation_id"] = correlation_id

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_ATTRIBUTES or key.startswith("_"):
                continue
            if key == "correlation_id":
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=_json_default)


class _CorrelationIdFilter(logging.Filter):
    """Attach the active correlation ID to log records when missing."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 - override
        if getattr(record, "correlation_id", None) is None:
            record.correlation_id = current_correlation_id()
        return True


def _configure_logging() -> None:
    """Configure root logging to emit JSON structured logs once."""

    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    root_logger.addFilter(_CorrelationIdFilter())

    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for structured JSON output."""

    _configure_logging()
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Metrics collection
# ---------------------------------------------------------------------------


def _percentile(samples: Iterable[float], percentile: float) -> Optional[float]:
    """Compute an interpolated percentile for the provided samples."""

    data = sorted(samples)
    if not data:
        return None
    if len(data) == 1:
        return data[0]

    percentile = max(0.0, min(100.0, percentile))
    rank = (len(data) - 1) * (percentile / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return data[int(rank)]
    lower_value = data[low]
    upper_value = data[high]
    return lower_value + (upper_value - lower_value) * (rank - low)


class Metrics:
    """In-memory metrics collector exposed via the monitoring API."""

    MAX_LATENCY_SAMPLES = 1000

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_calls: Dict[str, float] = {}
        self._call_correlation: Dict[str, str] = {}
        self._latency_samples: list[float] = []
        self._token_usage = 0
        self._total_calls = 0
        self._register_retries = 0
        self._invite_retries = 0
        self._audio_events: Counter[str] = Counter()

    # ---- Call lifecycle -------------------------------------------------

    def call_started(self, call_id: str, correlation_id: str) -> None:
        with self._lock:
            self._active_calls[call_id] = time.time()
            self._call_correlation[call_id] = correlation_id
            self._total_calls += 1

    def call_ended(self, call_id: str) -> Optional[float]:
        with self._lock:
            start_ts = self._active_calls.pop(call_id, None)
            self._call_correlation.pop(call_id, None)
            if start_ts is None:
                return None
            duration = max(time.time() - start_ts, 0.0)
            self._record_latency_locked(duration)
            return duration

    def _record_latency_locked(self, duration: float) -> None:
        self._latency_samples.append(duration)
        if len(self._latency_samples) > self.MAX_LATENCY_SAMPLES:
            self._latency_samples = self._latency_samples[-self.MAX_LATENCY_SAMPLES :]

    def record_latency(self, duration: float) -> None:
        with self._lock:
            self._record_latency_locked(duration)

    # ---- Token usage ----------------------------------------------------

    def record_token_usage(self, tokens: int) -> None:
        if tokens <= 0:
            return
        with self._lock:
            self._token_usage += tokens

    # ---- Retry counters -------------------------------------------------

    def record_register_retry(self) -> None:
        with self._lock:
            self._register_retries += 1

    def record_invite_retry(self) -> None:
        with self._lock:
            self._invite_retries += 1

    # ---- Audio pipeline events -----------------------------------------

    def record_audio_event(self, name: str) -> None:
        if not name:
            return
        with self._lock:
            self._audio_events[name] += 1

    # ---- Snapshot -------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            active_calls = len(self._active_calls)
            token_usage = self._token_usage
            total_calls = self._total_calls
            register_retries = self._register_retries
            invite_retries = self._invite_retries
            audio_events = dict(self._audio_events)
            latencies = list(self._latency_samples)

        latency_percentiles: Dict[str, float] = {}
        for pct in (50, 90, 95, 99):
            value = _percentile(latencies, pct)
            if value is not None:
                latency_percentiles[f"p{pct}"] = value

        return {
            "active_calls": active_calls,
            "total_calls": total_calls,
            "token_usage_total": token_usage,
            "latency_seconds": latency_percentiles,
            "register_retries": register_retries,
            "invite_retries": invite_retries,
            "audio_pipeline_events": audio_events,
        }


metrics = Metrics()
