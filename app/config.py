"""Centralised configuration loading and validation utilities."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, cast

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class ConfigurationError(RuntimeError):
    """Raised when the environment configuration cannot be validated."""

    def __init__(self, message: str, *, details: List[str] | None = None):
        super().__init__(message)
        self.details: List[str] = details or []


class Settings(BaseSettings):
    """Typed representation of the agent configuration."""

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
    )

    sip_domain: str = Field(..., alias="SIP_DOMAIN", min_length=1)
    sip_user: str = Field(..., alias="SIP_USER", min_length=1)
    sip_pass: str = Field(..., alias="SIP_PASS", min_length=1)

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY", min_length=1)
    agent_id: str = Field(..., alias="AGENT_ID", min_length=1)

    openai_mode: str = Field("legacy", alias="OPENAI_MODE")
    openai_model: str = Field("gpt-realtime", alias="OPENAI_MODEL")
    openai_voice: str = Field("alloy", alias="OPENAI_VOICE")
    openai_temperature: float = Field(0.3, alias="OPENAI_TEMPERATURE", ge=0.0, le=2.0)
    system_prompt: str = Field(
        "You are a helpful voice assistant.", alias="SYSTEM_PROMPT"
    )

    enable_sip: bool = Field(True, alias="ENABLE_SIP")
    enable_audio: bool = Field(True, alias="ENABLE_AUDIO")

    sip_transport_port: int = Field(5060, alias="SIP_TRANSPORT_PORT", ge=0, le=65535)
    sip_jb_min: int = Field(0, alias="SIP_JB_MIN", ge=0)
    sip_jb_max: int = Field(0, alias="SIP_JB_MAX", ge=0)
    sip_jb_max_pre: int = Field(0, alias="SIP_JB_MAX_PRE", ge=0)
    sip_enable_ice: bool = Field(False, alias="SIP_ENABLE_ICE")
    sip_enable_turn: bool = Field(False, alias="SIP_ENABLE_TURN")
    sip_stun_server: str | None = Field(None, alias="SIP_STUN_SERVER")
    sip_turn_server: str | None = Field(None, alias="SIP_TURN_SERVER")
    sip_turn_user: str | None = Field(None, alias="SIP_TURN_USER")
    sip_turn_pass: str | None = Field(None, alias="SIP_TURN_PASS")
    sip_enable_srtp: bool = Field(False, alias="SIP_ENABLE_SRTP")
    sip_srtp_optional: bool = Field(True, alias="SIP_SRTP_OPTIONAL")
    sip_preferred_codecs: Tuple[str, ...] = Field(
        (), alias="SIP_PREFERRED_CODECS"
    )

    sip_reg_retry_base: float = Field(2.0, alias="SIP_REG_RETRY_BASE", ge=0.0)
    sip_reg_retry_max: float = Field(60.0, alias="SIP_REG_RETRY_MAX", ge=0.0)
    sip_invite_retry_base: float = Field(1.0, alias="SIP_INVITE_RETRY_BASE", ge=0.0)
    sip_invite_retry_max: float = Field(30.0, alias="SIP_INVITE_RETRY_MAX", ge=0.0)
    sip_invite_max_attempts: int = Field(5, alias="SIP_INVITE_MAX_ATTEMPTS", ge=0)

    @field_validator(
        "sip_domain",
        "sip_user",
        "sip_pass",
        "openai_api_key",
        "agent_id",
        mode="before",
    )
    @classmethod
    def _strip_and_validate_required(cls, value: object) -> object:
        if value is None:
            return value
        text = str(value).strip()
        if not text:
            raise ValueError("must not be empty")
        return text

    @field_validator(
        "openai_mode",
        mode="before",
    )
    @classmethod
    def _normalise_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator(
        "sip_stun_server",
        "sip_turn_server",
        "sip_turn_user",
        "sip_turn_pass",
        mode="before",
    )
    @classmethod
    def _blank_string_to_none(cls, value: object) -> object:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("sip_preferred_codecs", mode="before")
    @classmethod
    def _parse_codecs(cls, value: object) -> Tuple[str, ...]:
        if value in (None, "", ()):  # type: ignore[comparison-overlap]
            return ()
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
            return tuple(item for item in items if item)
        if isinstance(value, Iterable):
            return tuple(str(item).strip() for item in value if str(item).strip())
        raise TypeError("SIP_PREFERRED_CODECS must be a comma-separated string")

    def as_env(self) -> Dict[str, str]:
        """Return the configuration as ``KEY=value`` style strings."""

        env: Dict[str, str] = {}
        for field_name, field in self.model_fields.items():
            alias = field.alias or field_name
            value = getattr(self, field_name)
            if value is None:
                env[alias] = ""
            elif isinstance(value, tuple):
                env[alias] = ",".join(value)
            elif isinstance(value, bool):
                env[alias] = "true" if value else "false"
            else:
                env[alias] = str(value)
        return env


_FIELD_ALIAS: Dict[str, str] = {
    name: field.alias or name for name, field in Settings.model_fields.items()
}
_ALIAS_FIELD: Dict[str, str] = {alias: name for name, alias in _FIELD_ALIAS.items()}


def _format_validation_errors(exc: ValidationError) -> List[str]:
    details: List[str] = []
    for error in exc.errors():
        if not error.get("loc"):
            details.append(error.get("msg", "Invalid configuration"))
            continue
        field_name = str(error["loc"][-1])
        alias = _FIELD_ALIAS.get(field_name, field_name)
        details.append(f"{alias}: {error.get('msg', 'invalid value')}")
    return details


@lru_cache()
def get_settings() -> Settings:
    """Load settings from the environment and ``.env`` file."""

    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:  # pragma: no cover - exercised at runtime
        details = _format_validation_errors(exc)
        message = "Invalid environment configuration:\n" + "\n".join(
            f"  - {item}" for item in details
        )
        raise ConfigurationError(message, details=details) from exc


def env_file_path() -> Path:
    """Return the path to the runtime ``.env`` file."""

    return ENV_FILE


def read_env_file(path: Path | None = None) -> Dict[str, str]:
    """Read key/value pairs from ``path`` and return them as a dictionary."""

    target = path or env_file_path()
    if not target.exists():
        return {}
    data: Dict[str, str] = {}
    for line in target.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def merge_env(base: Dict[str, str], overrides: Dict[str, str]) -> Dict[str, str]:
    """Merge two ``KEY=value`` mappings, returning a new dictionary."""

    merged = dict(base)
    for key, value in overrides.items():
        merged[key] = "" if value is None else str(value)
    return merged


def validate_env_map(
    values: Dict[str, str], *, include_os_environ: bool = False
) -> Settings:
    """Validate a raw mapping of environment variables."""

    combined: Dict[str, str] = {}
    if include_os_environ:
        for key, value in os.environ.items():
            if key in _ALIAS_FIELD and key not in values:
                combined[key] = value
    combined.update(values)
    settings_payload = cast(
        Dict[str, Any],
        {
            _ALIAS_FIELD[key]: combined[key]
            for key in combined
            if key in _ALIAS_FIELD
        },
    )
    try:
        return Settings(**settings_payload)
    except ValidationError as exc:
        details = _format_validation_errors(exc)
        message = "Invalid environment configuration:\n" + "\n".join(
            f"  - {item}" for item in details
        )
        raise ConfigurationError(message, details=details) from exc


def write_env_file(values: Dict[str, str], path: Path | None = None) -> None:
    """Persist ``values`` to ``path`` as ``KEY=value`` lines."""

    target = path or env_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in sorted(values.items())]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
