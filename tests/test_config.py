import textwrap
from pathlib import Path

import pytest

from app import config


@pytest.fixture()
def valid_env(tmp_path: Path) -> Path:
    lines = config.generate_env_example_lines()
    path = tmp_path / ".env"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_validate_env_map_accepts_valid_values():
    values = {
        "SIP_DOMAIN": "example.com",
        "SIP_USER": "1001",
        "SIP_PASS": "secret",
        "OPENAI_API_KEY": "sk-test",
        "AGENT_ID": "va_test",
    }
    settings = config.validate_env_map(values)
    assert settings.sip_domain == "example.com"
    assert settings.enable_sip is True


def test_validate_env_map_handles_comma_separated_codecs():
    values = {
        "SIP_DOMAIN": "example.com",
        "SIP_USER": "1001",
        "SIP_PASS": "secret",
        "OPENAI_API_KEY": "sk-test",
        "AGENT_ID": "va_test",
        "SIP_PREFERRED_CODECS": "PCMU,PCMA,opus",
    }
    settings = config.validate_env_map(values)
    assert settings.sip_preferred_codecs == ("PCMU", "PCMA", "opus")


def test_validate_env_map_handles_blank_codecs():
    values = {
        "SIP_DOMAIN": "example.com",
        "SIP_USER": "1001",
        "SIP_PASS": "secret",
        "OPENAI_API_KEY": "sk-test",
        "AGENT_ID": "va_test",
        "SIP_PREFERRED_CODECS": "",
    }
    settings = config.validate_env_map(values)
    assert settings.sip_preferred_codecs == ()


def test_validate_env_map_raises_for_bad_values():
    with pytest.raises(config.ConfigurationError) as excinfo:
        config.validate_env_map({"SIP_TRANSPORT_PORT": "not-a-number"})
    assert "SIP_TRANSPORT_PORT" in "\n".join(excinfo.value.details)


def test_generate_env_example_lines_structure():
    lines = config.generate_env_example_lines()
    assert lines[0] == "# PBX"
    assert "SIP_DOMAIN=your.asterisk.ip.or.domain" in lines
    comment_count = sum(1 for line in lines if line.startswith("#"))
    assert lines.count("") == max(comment_count - 1, 0)


def test_cli_validate_success(valid_env: Path, capsys):
    exit_code = config.main(["validate", "--path", str(valid_env)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"{valid_env}" in captured.out


def test_cli_validate_failure(tmp_path: Path, capsys):
    env_path = tmp_path / ".env"
    env_path.write_text(
        textwrap.dedent(
            """
            SIP_DOMAIN=example.com
            SIP_USER=1001
            SIP_PASS=secret
            OPENAI_API_KEY=sk-test
            AGENT_ID=va_test
            SIP_TRANSPORT_PORT=not-a-number
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    exit_code = config.main(["validate", "--path", str(env_path)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Invalid environment configuration" in captured.err
    assert "SIP_TRANSPORT_PORT" in captured.err


def test_cli_sample_write(tmp_path: Path, capsys):
    example_path = tmp_path / "env.sample"
    exit_code = config.main(["sample", "--write", "--path", str(example_path), "--no-print"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert example_path.read_text(encoding="utf-8") == ("\n".join(config.generate_env_example_lines()) + "\n")
    assert "Sample environment written" in captured.out
