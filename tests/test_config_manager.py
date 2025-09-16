"""
Tests for configuration manager module.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from app.config_manager import (
    load_config, save_config, get_config_value, set_config_value,
    _env_path
)


class TestConfigManager:
    """Test configuration manager functions."""
    
    def test_env_path(self):
        """Test _env_path function."""
        expected_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            ".env"
        )
        actual_path = _env_path()
        assert actual_path == expected_path
    
    @patch('app.config_manager._env_path')
    @patch('os.path.exists')
    def test_load_config_file_exists(self, mock_exists, mock_env_path):
        """Test loading configuration when file exists."""
        mock_env_path.return_value = "/tmp/test.env"
        mock_exists.return_value = True
        
        env_content = """# Test configuration
SIP_DOMAIN=test.com
SIP_USER=testuser
SIP_PASS=testpass
# Comment line
OPENAI_API_KEY=sk-test123
"""
        
        with patch("builtins.open", mock_open(read_data=env_content)):
            config = load_config()
        
        assert config["SIP_DOMAIN"] == "test.com"
        assert config["SIP_USER"] == "testuser"
        assert config["SIP_PASS"] == "testpass"
        assert config["OPENAI_API_KEY"] == "sk-test123"
        assert "# Comment line" not in config
    
    @patch('app.config_manager._env_path')
    def test_load_config_file_not_exists(self, mock_env_path):
        """Test loading configuration when file doesn't exist."""
        mock_env_path.return_value = "/nonexistent/path/.env"
        
        with patch("os.path.exists", return_value=False):
            config = load_config()
        
        assert config == {}
    
    @patch('app.config_manager._env_path')
    def test_load_config_read_error(self, mock_env_path):
        """Test loading configuration with read error."""
        mock_env_path.return_value = "/tmp/test.env"
        
        with patch("builtins.open", side_effect=IOError("Read error")):
            config = load_config()
        
        assert config == {}
    
    @patch('app.config_manager._env_path')
    def test_save_config_success(self, mock_env_path):
        """Test saving configuration successfully."""
        mock_env_path.return_value = "/tmp/test.env"
        
        config = {
            "SIP_DOMAIN": "test.com",
            "SIP_USER": "testuser",
            "OPENAI_API_KEY": "sk-test123"
        }
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs"):
                result = save_config(config)
        
        assert result is True
        mock_file.assert_called_once_with("/tmp/test.env", "w", encoding="utf-8")
    
    @patch('app.config_manager._env_path')
    def test_save_config_error(self, mock_env_path):
        """Test saving configuration with error."""
        mock_env_path.return_value = "/tmp/test.env"
        
        config = {"SIP_DOMAIN": "test.com"}
        
        with patch("builtins.open", side_effect=IOError("Write error")):
            result = save_config(config)
        
        assert result is False
    
    @patch('app.config_manager.load_config')
    def test_get_config_value_exists(self, mock_load_config):
        """Test getting existing configuration value."""
        mock_load_config.return_value = {
            "SIP_DOMAIN": "test.com",
            "SIP_USER": "testuser"
        }
        
        value = get_config_value("SIP_DOMAIN")
        assert value == "test.com"
        
        value = get_config_value("SIP_USER", "default")
        assert value == "testuser"
    
    @patch('app.config_manager.load_config')
    def test_get_config_value_not_exists(self, mock_load_config):
        """Test getting non-existing configuration value."""
        mock_load_config.return_value = {"SIP_DOMAIN": "test.com"}
        
        value = get_config_value("NONEXISTENT_KEY")
        assert value is None
        
        value = get_config_value("NONEXISTENT_KEY", "default")
        assert value == "default"
    
    @patch('app.config_manager.save_config')
    @patch('app.config_manager.load_config')
    def test_set_config_value(self, mock_load_config, mock_save_config):
        """Test setting configuration value."""
        mock_load_config.return_value = {"SIP_DOMAIN": "old.com"}
        mock_save_config.return_value = True
        
        result = set_config_value("SIP_DOMAIN", "new.com")
        
        assert result is True
        mock_load_config.assert_called_once()
        mock_save_config.assert_called_once_with({"SIP_DOMAIN": "new.com"})
    
    @patch('app.config_manager.save_config')
    @patch('app.config_manager.load_config')
    def test_set_config_value_save_error(self, mock_load_config, mock_save_config):
        """Test setting configuration value with save error."""
        mock_load_config.return_value = {"SIP_DOMAIN": "old.com"}
        mock_save_config.return_value = False
        
        result = set_config_value("SIP_DOMAIN", "new.com")
        
        assert result is False
