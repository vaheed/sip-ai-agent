"""
Tests for configuration management.
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from config import Settings, OpenAIAPIMode, OpenAIVoice, SIPCodec


def test_settings_validation():
    """Test settings validation with valid configuration."""
    settings = Settings(
        sip_domain="test.example.com",
        sip_user="1001",
        sip_pass="testpass",
        openai_api_key="sk-test-key",
        agent_id="va_test123"
    )
    
    assert settings.sip_domain == "test.example.com"
    assert settings.sip_user == "1001"
    assert settings.openai_mode == OpenAIAPIMode.LEGACY


def test_settings_defaults():
    """Test that default values are set correctly."""
    settings = Settings(
        sip_domain="test.example.com",
        sip_user="1001",
        sip_pass="testpass",
        openai_api_key="sk-test-key",
        agent_id="va_test123"
    )
    
    assert settings.sip_port == 5060
    assert settings.audio_sample_rate == 16000
    assert settings.audio_channels == 1
    assert settings.openai_temperature == 0.3
    assert settings.metrics_enabled is True


def test_settings_validation_errors():
    """Test settings validation with invalid configuration."""
    with pytest.raises(ValueError):
        Settings(
            sip_domain="",  # Empty domain should fail
            sip_user="1001",
            sip_pass="testpass",
            openai_api_key="sk-test-key",
            agent_id="va_test123"
        )


def test_realtime_voice_validation():
    """Test voice validation for realtime mode."""
    # Valid voice for realtime
    settings = Settings(
        sip_domain="test.example.com",
        sip_user="1001",
        sip_pass="testpass",
        openai_api_key="sk-test-key",
        agent_id="va_test123",
        openai_mode=OpenAIAPIMode.REALTIME,
        openai_voice=OpenAIVoice.CEDAR
    )
    
    assert settings.openai_voice == OpenAIVoice.CEDAR


def test_rtp_port_range_validation():
    """Test RTP port range validation."""
    with pytest.raises(ValueError):
        Settings(
            sip_domain="test.example.com",
            sip_user="1001",
            sip_pass="testpass",
            openai_api_key="sk-test-key",
            agent_id="va_test123",
            rtp_port_range_start=16000,
            rtp_port_range_end=16000  # End must be greater than start
        )


def test_codec_parsing():
    """Test codec list parsing."""
    settings = Settings(
        sip_domain="test.example.com",
        sip_user="1001",
        sip_pass="testpass",
        openai_api_key="sk-test-key",
        agent_id="va_test123",
        sip_codecs="PCMU,PCMA,G.722"
    )
    
    assert len(settings.sip_codecs) == 3
    assert SIPCodec.PCMU in settings.sip_codecs
    assert SIPCodec.PCMA in settings.sip_codecs
    assert SIPCodec.G722 in settings.sip_codecs


def test_audio_frame_calculations():
    """Test audio frame size calculations."""
    settings = Settings(
        sip_domain="test.example.com",
        sip_user="1001",
        sip_pass="testpass",
        openai_api_key="sk-test-key",
        agent_id="va_test123",
        audio_sample_rate=16000,
        audio_frame_duration=20,
        audio_channels=1
    )
    
    frame_size = settings.get_audio_frame_size()
    frame_bytes = settings.get_audio_frame_bytes()
    
    assert frame_size == 320  # 16000 * 20ms / 1000 = 320 samples
    assert frame_bytes == 640  # 320 samples * 1 channel * 2 bytes = 640 bytes


def test_nat_config():
    """Test NAT configuration."""
    settings = Settings(
        sip_domain="test.example.com",
        sip_user="1001",
        sip_pass="testpass",
        openai_api_key="sk-test-key",
        agent_id="va_test123",
        sip_nat_type="STUN",
        sip_stun_server="stun.example.com:3478",
        sip_turn_server="turn.example.com:3478",
        sip_turn_user="turnuser",
        sip_turn_pass="turnpass"
    )
    
    nat_config = settings.get_nat_config()
    
    assert nat_config["type"] == "STUN"
    assert nat_config["stun_server"] == "stun.example.com:3478"
    assert nat_config["turn_server"] == "turn.example.com:3478"
    assert nat_config["turn_user"] == "turnuser"
    assert nat_config["turn_pass"] == "turnpass"


def test_settings_from_env_file(test_settings):
    """Test loading settings from environment file."""
    assert test_settings.sip_domain == "test.example.com"
    assert test_settings.sip_user == "1001"
    assert test_settings.openai_mode == OpenAIAPIMode.REALTIME
    assert test_settings.debug is True
    assert test_settings.structured_logging is False


def test_pydantic_v2_compatibility():
    """Test Pydantic v2 compatibility."""
    from pydantic import ValidationError
    
    # Test validation error handling
    with pytest.raises(ValidationError):
        Settings(
            sip_domain="",  # Empty domain should fail
            sip_user="1001",
            sip_pass="testpass",
            openai_api_key="sk-test-key",
            agent_id="va_test123"
        )
