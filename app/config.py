#!/usr/bin/env python3
"""
Configuration management for the SIP AI Agent.

This module provides typed configuration using Pydantic with validation
and environment variable support. All configuration is centralized here
for maintainability and type safety.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class OpenAIAPIMode(str, Enum):
    """OpenAI API modes."""

    LEGACY = "legacy"
    REALTIME = "realtime"


class SIPCodec(str, Enum):
    """Supported SIP codecs."""

    PCMU = "PCMU"  # G.711 μ-law
    PCMA = "PCMA"  # G.711 A-law
    G722 = "G.722"  # G.722
    L16 = "L16"  # Linear PCM 16-bit


class OpenAIVoice(str, Enum):
    """Supported OpenAI voices."""

    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"
    CEDAR = "cedar"
    MARIN = "marin"


class OpenAIRealtimeModel(str, Enum):
    """Supported OpenAI realtime models."""

    GPT_REALTIME = "gpt-realtime"
    GPT_REALTIME_LATEST = "gpt-realtime-latest"


class Settings(BaseSettings):
    """Application settings with validation."""

    # SIP Configuration
    sip_domain: str = Field(default="", description="SIP domain or IP address")
    sip_user: str = Field(default="", description="SIP username")
    sip_pass: str = Field(default="", description="SIP password")
    sip_port: int = Field(default=5060, description="SIP signaling port")
    sip_transport: str = Field(default="UDP", description="SIP transport protocol")

    # SIP Advanced Configuration
    sip_jitter_buffer_size: int = Field(
        default=80, ge=20, le=400, description="Jitter buffer size in ms"
    )
    sip_srtp_enabled: bool = Field(default=False, description="Enable SRTP encryption")
    sip_srtp_secure_signaling: bool = Field(
        default=False, description="Enable secure SIP signaling (TLS)"
    )
    sip_nat_type: Optional[str] = Field(
        default=None, description="NAT type: STUN, TURN, or ICE"
    )
    sip_stun_server: Optional[str] = Field(
        default=None, description="STUN server address"
    )
    sip_turn_server: Optional[str] = Field(
        default=None, description="TURN server address"
    )
    sip_turn_user: Optional[str] = Field(default=None, description="TURN username")
    sip_turn_pass: Optional[str] = Field(default=None, description="TURN password")
    sip_codecs: List[SIPCodec] = Field(
        default=[SIPCodec.PCMU, SIPCodec.PCMA], description="Preferred codecs"
    )
    sip_registration_timeout: int = Field(
        default=30, ge=5, le=300, description="Registration timeout in seconds"
    )
    sip_registration_retry_max: int = Field(
        default=5, ge=1, le=20, description="Max registration retries"
    )
    sip_registration_retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Registration retry backoff multiplier",
    )

    # RTP Configuration
    rtp_port_range_start: int = Field(
        default=16000, ge=1024, le=65535, description="Start of RTP port range"
    )
    rtp_port_range_end: int = Field(
        default=16100, ge=1024, le=65535, description="End of RTP port range"
    )

    # Audio Configuration
    audio_sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    audio_channels: int = Field(
        default=1, ge=1, le=2, description="Number of audio channels"
    )
    audio_frame_duration: int = Field(
        default=20, ge=10, le=100, description="Audio frame duration in ms"
    )
    audio_backpressure_threshold: int = Field(
        default=100, ge=10, le=1000, description="WebSocket backpressure threshold"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    agent_id: str = Field(default="", description="OpenAI agent ID")
    openai_mode: OpenAIAPIMode = Field(
        default=OpenAIAPIMode.LEGACY, description="OpenAI API mode"
    )
    openai_model: str = Field(default="gpt-realtime", description="OpenAI model name")
    openai_voice: OpenAIVoice = Field(
        default=OpenAIVoice.ALLOY, description="OpenAI voice"
    )
    openai_temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="OpenAI temperature"
    )
    system_prompt: str = Field(
        default="You are a helpful voice assistant.", description="System prompt"
    )
    openai_timeout: int = Field(
        default=30, ge=5, le=300, description="OpenAI API timeout in seconds"
    )
    openai_retry_max: int = Field(
        default=3, ge=1, le=10, description="Max OpenAI API retries"
    )
    openai_retry_backoff: float = Field(
        default=1.5, ge=1.0, le=10.0, description="OpenAI retry backoff multiplier"
    )

    # Monitoring Configuration
    monitor_host: str = Field(
        default="0.0.0.0", description="Monitor server host"  # nosec B104
    )
    monitor_port: int = Field(
        default=8080, ge=1024, le=65535, description="Monitor server port"
    )
    monitor_log_level: str = Field(default="INFO", description="Log level")
    monitor_max_logs: int = Field(
        default=1000, ge=100, le=10000, description="Maximum number of logs to keep"
    )
    health_check_interval: int = Field(
        default=30, ge=5, le=300, description="Health check interval in seconds"
    )

    # Observability Configuration
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(
        default=9090, ge=1024, le=65535, description="Metrics server port"
    )
    structured_logging: bool = Field(
        default=True, description="Enable structured JSON logging"
    )
    correlation_id_header: str = Field(
        default="X-Correlation-ID", description="Correlation ID header name"
    )

    # Development Configuration
    debug: bool = Field(default=False, description="Enable debug mode")
    log_sip_messages: bool = Field(
        default=False, description="Log SIP messages for debugging"
    )
    log_audio_samples: bool = Field(
        default=False, description="Log audio sample data for debugging"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @field_validator("rtp_port_range_end")
    @classmethod
    def validate_rtp_port_range(cls, v, info):
        """Validate that RTP port range end is greater than start."""
        if hasattr(info, "data") and "rtp_port_range_start" in info.data:
            if v <= info.data["rtp_port_range_start"]:
                raise ValueError("RTP port range end must be greater than start")
        return v

    @field_validator("sip_codecs", mode="before")
    @classmethod
    def parse_codecs(cls, v):
        """Parse codec list from string or list."""
        if isinstance(v, str):
            return [SIPCodec(codec.strip()) for codec in v.split(",")]
        return v

    @field_validator("openai_voice")
    @classmethod
    def validate_voice_for_mode(cls, v, info):
        """Validate voice selection for realtime mode."""
        if (
            hasattr(info, "data")
            and info.data.get("openai_mode") == OpenAIAPIMode.REALTIME
        ):
            # Realtime API supports newer voices
            supported_voices = {
                OpenAIVoice.ALLOY,
                OpenAIVoice.ECHO,
                OpenAIVoice.FABLE,
                OpenAIVoice.ONYX,
                OpenAIVoice.NOVA,
                OpenAIVoice.SHIMMER,
                OpenAIVoice.CEDAR,
                OpenAIVoice.MARIN,
            }
            if v not in supported_voices:
                raise ValueError(f"Voice {v} not supported in realtime mode")
        return v

    @field_validator("openai_model")
    @classmethod
    def validate_model_for_mode(cls, v, info):
        """Validate model selection for realtime mode."""
        if (
            hasattr(info, "data")
            and info.data.get("openai_mode") == OpenAIAPIMode.REALTIME
        ):
            supported_models = {
                OpenAIRealtimeModel.GPT_REALTIME,
                OpenAIRealtimeModel.GPT_REALTIME_LATEST,
            }
            if v not in [model.value for model in supported_models]:
                raise ValueError(f"Model {v} not supported in realtime mode")
        return v

    def get_sip_codec_list(self) -> List[str]:
        """Get codec list as strings for PJSIP."""
        return [codec.value for codec in self.sip_codecs]

    def get_rtp_port_range(self) -> tuple[int, int]:
        """Get RTP port range as tuple."""
        return (self.rtp_port_range_start, self.rtp_port_range_end)

    def get_audio_frame_size(self) -> int:
        """Calculate audio frame size in samples."""
        return int(self.audio_sample_rate * self.audio_frame_duration / 1000)

    def get_audio_frame_bytes(self) -> int:
        """Calculate audio frame size in bytes."""
        return self.get_audio_frame_size() * self.audio_channels * 2  # 16-bit = 2 bytes

    def is_srtp_enabled(self) -> bool:
        """Check if SRTP is enabled."""
        return self.sip_srtp_enabled

    def get_nat_config(self) -> Dict[str, Any]:
        """Get NAT traversal configuration."""
        config = {}
        if self.sip_nat_type:
            config["type"] = self.sip_nat_type.upper()
        if self.sip_stun_server:
            config["stun_server"] = self.sip_stun_server
        if self.sip_turn_server:
            config["turn_server"] = self.sip_turn_server
            if self.sip_turn_user:
                config["turn_user"] = self.sip_turn_user
            if self.sip_turn_pass:
                config["turn_pass"] = self.sip_turn_pass
        return config


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings
