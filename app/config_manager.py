"""
Configuration management module.

This module handles loading and saving configuration from .env files.
"""

import os
from typing import Dict, Any


def _env_path() -> str:
    """
    Return the absolute path to the .env file located two directories above
    this module. This function assumes the project structure of
    /project/sip-ai-agent-main/app/config_manager.py and returns
    /project/sip-ai-agent-main/.env.
    """
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )


def load_config() -> Dict[str, Any]:
    """
    Load key/value pairs from the project's .env file.

    The .env file stores configuration values used by the SIP agent. Lines
    starting with '#' are treated as comments and ignored. Values are
    returned as strings. If the file does not exist, an empty dict is
    returned. Unknown whitespace around keys/values is stripped.
    """
    config = {}
    env_path = _env_path()
    
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except Exception:
            # Silently ignore read errors; caller can handle missing keys
            pass
    
    return config


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration to the .env file.
    
    Args:
        config: Dictionary of configuration key-value pairs
        
    Returns:
        bool: True if successful, False otherwise
    """
    env_path = _env_path()
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        
        with open(env_path, "w", encoding="utf-8") as f:
            # Write header
            f.write("# SIP AI Agent Configuration\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            
            # Write configuration sections
            sections = {
                "SIP Configuration": ["SIP_DOMAIN", "SIP_USER", "SIP_PASS", "SIP_SRTP_ENABLED"],
                "OpenAI Configuration": ["OPENAI_API_KEY", "OPENAI_MODE", "OPENAI_MODEL", "OPENAI_VOICE"],
                "Audio Configuration": ["AUDIO_SAMPLE_RATE", "AUDIO_CHANNELS", "AUDIO_FRAME_DURATION"],
                "Monitoring Configuration": ["MONITOR_HOST", "MONITOR_PORT", "MONITOR_LOG_LEVEL"],
                "Web UI Configuration": ["WEB_UI_ENABLED", "WEB_UI_HOST", "WEB_UI_PORT"],
                "Security Configuration": ["ADMIN_USERNAME", "ADMIN_PASSWORD", "SESSION_SECRET"],
            }
            
            for section_name, keys in sections.items():
                f.write(f"# {section_name}\n")
                for key in keys:
                    if key in config:
                        f.write(f"{key}={config[key]}\n")
                f.write("\n")
            
            # Write any remaining keys not in sections
            written_keys = set()
            for keys in sections.values():
                written_keys.update(keys)
            
            remaining_keys = set(config.keys()) - written_keys
            if remaining_keys:
                f.write("# Other Configuration\n")
                for key in sorted(remaining_keys):
                    f.write(f"{key}={config[key]}\n")
                f.write("\n")
        
        return True
        
    except Exception as e:
        from .logging_config import get_logger
        logger = get_logger("config_manager")
        logger.error("Failed to save configuration", error=str(e))
        return False


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> bool:
    """
    Set a specific configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    config[key] = str(value)
    return save_config(config)
