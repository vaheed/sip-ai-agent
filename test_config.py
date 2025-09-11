#!/usr/bin/env python3
"""
Simple configuration test script for CI/CD validation.
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_config():
    """Test configuration loading and validation."""
    try:
        from config import Settings
        
        # Test with environment variables
        os.environ.setdefault('SIP_DOMAIN', 'test.example.com')
        os.environ.setdefault('SIP_USER', '1001')
        os.environ.setdefault('SIP_PASS', 'testpass')
        os.environ.setdefault('OPENAI_API_KEY', 'sk-test-key')
        os.environ.setdefault('AGENT_ID', 'va_test123')
        
        settings = Settings()
        print(f"✅ Configuration validation passed")
        print(f"   SIP Domain: {settings.sip_domain}")
        print(f"   OpenAI Mode: {settings.openai_mode.value}")
        print(f"   Metrics Enabled: {settings.metrics_enabled}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
