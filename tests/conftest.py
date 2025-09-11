"""
Pytest configuration and fixtures for SIP AI Agent tests.
"""

import pytest
import asyncio
import os
import tempfile
import struct
import random
from unittest.mock import Mock, AsyncMock
import sys

# Mock PJSIP before importing app modules
sys.modules["pjsua2"] = Mock()
sys.modules["pjsua2"].pj = Mock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(
            """# Test configuration
SIP_DOMAIN=test.example.com
SIP_USER=1001
SIP_PASS=testpass
OPENAI_API_KEY=sk-test-key
AGENT_ID=va_test123
OPENAI_MODE=realtime
OPENAI_MODEL=gpt-realtime
OPENAI_VOICE=alloy
OPENAI_TEMPERATURE=0.3
SYSTEM_PROMPT=You are a test assistant.
SIP_SRTP_ENABLED=false
SIP_JITTER_BUFFER_SIZE=80
AUDIO_BACKPRESSURE_THRESHOLD=100
SIP_REGISTRATION_RETRY_MAX=3
SIP_REGISTRATION_RETRY_BACKOFF=2.0
DEBUG=true
STRUCTURED_LOGGING=false
METRICS_ENABLED=false
"""
        )
        temp_file = f.name

    yield temp_file

    # Cleanup
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def test_settings(temp_env_file):
    """Create test settings with temporary environment file."""
    # Set the env file path
    os.environ["ENV_FILE"] = temp_env_file

    # Create settings instance
    settings = Settings(_env_file=temp_env_file)
    return settings


@pytest.fixture
def mock_sip_client():
    """Create a mock SIP client for testing."""
    mock_client = Mock()
    mock_client.is_registered.return_value = True
    mock_client.initialize = Mock()
    mock_client.register = AsyncMock()
    mock_client.shutdown = Mock()
    return mock_client


@pytest.fixture
def mock_openai_agent():
    """Create a mock OpenAI agent for testing."""
    mock_agent = Mock()
    mock_agent.start = AsyncMock()
    mock_agent.stop = Mock()
    return mock_agent


@pytest.fixture
def mock_audio_callback():
    """Create a mock audio callback for testing."""
    mock_callback = Mock()
    mock_callback.is_active = True
    mock_callback.audio_queue = Mock()
    mock_callback.get_audio_frame = AsyncMock()
    mock_callback.stop = Mock()
    return mock_callback


@pytest.fixture
def sample_audio_frame():
    """Generate sample audio frame data for testing."""
    # 16-bit PCM, 16kHz, 20ms frame = 320 samples = 640 bytes
    samples = [random.randint(-32768, 32767) for _ in range(320)]
    audio_data = struct.pack("<" + "h" * len(samples), *samples)
    return audio_data


@pytest.fixture
def sample_rtp_frame():
    """Generate sample RTP frame data for testing."""
    # RTP header (12 bytes) + payload
    rtp_header = struct.pack(
        "!BBHII",
        0x80,  # Version, padding, extension, CSRC count
        0,  # Marker, payload type
        random.randint(1, 65535),  # Sequence number
        random.randint(1, 2**32 - 1),  # Timestamp
        random.randint(1, 2**32 - 1),
    )  # SSRC

    # Payload (320 samples = 640 bytes for 16-bit PCM)
    payload = struct.pack(
        "<" + "h" * 320, *[random.randint(-32768, 32767) for _ in range(320)]
    )

    return rtp_header + payload


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection for testing."""
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_metrics():
    """Create a mock metrics collector for testing."""
    mock_metrics = Mock()
    mock_metrics.record_call_start = Mock()
    mock_metrics.record_call_end = Mock()
    mock_metrics.record_audio_frame = Mock()
    mock_metrics.record_openai_request = Mock()
    mock_metrics.update_sip_registration_status = Mock()
    mock_metrics.start_metrics_server = Mock()
    mock_metrics.get_active_calls_count = Mock(return_value=0)
    return mock_metrics


@pytest.fixture
def mock_health_monitor():
    """Create a mock health monitor for testing."""
    mock_health = Mock()
    mock_health.run_health_checks = AsyncMock()
    mock_health.get_uptime = Mock(return_value=3600.0)
    mock_health.get_system_metrics = Mock(
        return_value={
            "cpu_percent": 25.0,
            "memory": {"percent": 50.0},
            "disk": {"percent": 30.0},
        }
    )
    return mock_health
