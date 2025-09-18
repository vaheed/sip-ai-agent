"""Centralised configuration loading and validation utilities."""

from __future__ import annotations

import argparse
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple, cast

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE_FILE = BASE_DIR / "env.example"

_ENV_EXAMPLE_TEMPLATE: List[Tuple[str | None, Dict[str, str]]] = [
    (
        "# PBX",
        {
            "SIP_DOMAIN": "your.asterisk.ip.or.domain",
            "SIP_USER": "1001",
            "SIP_PASS": "yourpassword",
        },
    ),
    (
        "# OpenAI",
        {
            "OPENAI_API_KEY": "sk-...",
            "AGENT_ID": "va_...",
        },
    ),
    (
        "# Feature toggles & realtime session",
        {
            "ENABLE_SIP": "true",
            "ENABLE_AUDIO": "true",
            "OPENAI_MODE": "legacy",
            "OPENAI_MODEL": "gpt-realtime",
            "OPENAI_VOICE": "alloy",
            "OPENAI_TEMPERATURE": "0.3",
            "SYSTEM_PROMPT": "You are a helpful voice assistant.",
        },
    ),
    (
        "# Audio pipeline",
        {
            "SIP_TRANSPORT_PORT": "5060",
            "SIP_PREFERRED_CODECS": "PCMU,PCMA,opus",
            "SIP_JB_MIN": "0",
            "SIP_JB_MAX": "0",
            "SIP_JB_MAX_PRE": "0",
        },
    ),
    (
        "# NAT traversal & media security",
        {
            "SIP_ENABLE_ICE": "false",
            "SIP_ENABLE_TURN": "false",
            "SIP_STUN_SERVER": "",
            "SIP_TURN_SERVER": "",
            "SIP_TURN_USER": "",
            "SIP_TURN_PASS": "",
            "SIP_ENABLE_SRTP": "false",
            "SIP_SRTP_OPTIONAL": "true",
        },
    ),
    (
        "# Retry behaviour (seconds)",
        {
            "SIP_REG_RETRY_BASE": "2.0",
            "SIP_REG_RETRY_MAX": "60.0",
            "SIP_INVITE_RETRY_BASE": "1.0",
            "SIP_INVITE_RETRY_MAX": "30.0",
            "SIP_INVITE_MAX_ATTEMPTS": "5",
        },
    ),
]


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
    system_prompt: str = Field("You are a helpful voice assistant.", alias="SYSTEM_PROMPT")

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
    sip_preferred_codecs: Tuple[str, ...] = Field((), alias="SIP_PREFERRED_CODECS")

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


_FIELD_ALIAS: Dict[str, str] = {name: field.alias or name for name, field in Settings.model_fields.items()}
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
        message = "Invalid environment configuration:\n" + "\n".join(f"  - {item}" for item in details)
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


def generate_env_example_lines() -> List[str]:
    """Return the canonical ``.env`` example as a list of lines."""

    lines: List[str] = []
    for section_index, (header, values) in enumerate(_ENV_EXAMPLE_TEMPLATE):
        if section_index > 0:
            lines.append("")
        if header:
            lines.append(header)
        for key, value in values.items():
            lines.append(f"{key}={value}")
    return lines


def write_env_example(path: Path | None = None) -> Path:
    """Write the canonical ``.env`` example to ``path``.

    Parameters
    ----------
    path:
        Target file. Defaults to :data:`ENV_EXAMPLE_FILE` when not provided.
    """

    target = path or ENV_EXAMPLE_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(generate_env_example_lines()) + "\n"
    target.write_text(content, encoding="utf-8")
    return target


def merge_env(base: Dict[str, str], overrides: Dict[str, str]) -> Dict[str, str]:
    """Merge two ``KEY=value`` mappings, returning a new dictionary."""

    merged = dict(base)
    for key, value in overrides.items():
        merged[key] = "" if value is None else str(value)
    return merged


def validate_env_map(values: Dict[str, str], *, include_os_environ: bool = False) -> Settings:
    """Validate a raw mapping of environment variables."""

    combined: Dict[str, str] = {}
    if include_os_environ:
        for key, value in os.environ.items():
            if key in _ALIAS_FIELD and key not in values:
                combined[key] = value
    combined.update(values)
    settings_payload = cast(
        Dict[str, Any],
        {_ALIAS_FIELD[key]: combined[key] for key in combined if key in _ALIAS_FIELD},
    )
    try:
        return Settings(**settings_payload)
    except ValidationError as exc:
        details = _format_validation_errors(exc)
        message = "Invalid environment configuration:\n" + "\n".join(f"  - {item}" for item in details)
        raise ConfigurationError(message, details=details) from exc


def validate_env_file(path: Path | None = None, *, include_os_environ: bool = False) -> Settings:
    """Validate the ``.env`` file located at ``path`` and return the settings."""

    target = path or env_file_path()
    if not target.exists():
        raise FileNotFoundError(target)
    values = read_env_file(target)
    return validate_env_map(values, include_os_environ=include_os_environ)


def write_env_file(values: Dict[str, str], path: Path | None = None) -> None:
    """Persist ``values`` to ``path`` as ``KEY=value`` lines."""

    target = path or env_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in sorted(values.items())]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or generate environment files for the SIP AI agent.",
    )
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate", help="Validate a .env file using the Settings schema.")
    validate_parser.add_argument(
        "--path",
        type=Path,
        default=env_file_path(),
        help="Path to the .env file (defaults to the repository root .env)",
    )
    validate_parser.add_argument(
        "--include-os",
        action="store_true",
        help="Merge matching keys from the current process environment before validation.",
    )

    sample_parser = subparsers.add_parser(
        "sample",
        help="Print or regenerate the canonical env.example file.",
    )
    sample_parser.add_argument(
        "--write",
        action="store_true",
        help="Write the sample to disk instead of printing to stdout.",
    )
    sample_parser.add_argument(
        "--path",
        type=Path,
        default=ENV_EXAMPLE_FILE,
        help="Destination path when using --write (defaults to env.example).",
    )
    sample_parser.add_argument(
        "--no-print",
        action="store_true",
        help="Suppress printing the sample contents when --write is supplied.",
    )

    return parser


def _emit_configuration_error(exc: ConfigurationError) -> None:
    print("Invalid environment configuration:", file=sys.stderr)
    for detail in exc.details:
        print(f"  - {detail}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``python -m app.config`` CLI invocations."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        target_path: Path = args.path
        try:
            validate_env_file(target_path, include_os_environ=args.include_os)
        except FileNotFoundError:
            print(f"Environment file not found: {target_path}", file=sys.stderr)
            return 1
        except ConfigurationError as exc:
            _emit_configuration_error(exc)
            return 1
        else:
            print(f"{target_path} is valid.")
            return 0

    if args.command == "sample":
        lines = generate_env_example_lines()
        if args.write:
            destination: Path = args.path
            write_env_example(destination)
            if not args.no_print:
                print("\n".join(lines))
            print(f"Sample environment written to {destination}")
        else:
            print("\n".join(lines))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI
    raise SystemExit(main())
