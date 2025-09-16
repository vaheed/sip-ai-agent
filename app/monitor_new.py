#!/usr/bin/env python3
"""
Monitoring module for SIP AI Agent.

This module provides the main monitoring interface and coordinates
between different monitoring components.
"""

import asyncio
from typing import Dict, Any

from .config_manager import load_config, save_config
from .logging_config import get_logger
from .system_monitor import get_system_monitor

logger = get_logger("monitor")


class Monitor:
    """Main monitoring class that coordinates all monitoring activities."""
    
    def __init__(self):
        self.system_monitor = get_system_monitor()
        self.start_time = None
    
    async def start(self):
        """Start all monitoring services."""
        logger.info("Starting monitor")
        self.start_time = asyncio.get_event_loop().time()
        await self.system_monitor.start()
    
    async def stop(self):
        """Stop all monitoring services."""
        logger.info("Stopping monitor")
        await self.system_monitor.stop()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return await self.system_monitor.get_system_status()
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add a log message."""
        self.system_monitor.add_log(message, level)
    
    def get_logs(self) -> list:
        """Get system logs."""
        return self.system_monitor.get_logs()
    
    def clear_logs(self):
        """Clear system logs."""
        self.system_monitor.clear_logs()


# Global monitor instance
_monitor = None


def get_monitor() -> Monitor:
    """Get or create monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = Monitor()
    return _monitor


# Backward compatibility functions
def load_config() -> dict:
    """Load configuration from .env file."""
    from .config_manager import load_config as _load_config
    return _load_config()


def save_config(config: dict) -> bool:
    """Save configuration to .env file."""
    from .config_manager import save_config as _save_config
    return _save_config(config)
