"""
System monitoring module.

This module provides system status monitoring and health checks.
"""

import asyncio
import time
from typing import Dict, Any, List

from .call_history import get_call_history_manager
from .config import get_settings
from .health import HealthStatus, get_health_monitor
from .logging_config import get_logger

logger = get_logger("system_monitor")


class SystemMonitor:
    """Monitors system status and health."""
    
    def __init__(self):
        self.start_time = time.time()
        self.logs = []
        self.max_logs = 1000
        self.call_history_manager = get_call_history_manager()
        self.health_monitor = get_health_monitor()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get health status
            health_report = await self.health_monitor.run_health_checks()
            
            # Get call history statistics
            call_stats = self.call_history_manager.get_call_statistics()
            
            # Get current settings
            settings = get_settings()
            
            # Extract SIP registration status from health report
            sip_registered = False
            if hasattr(health_report, 'checks'):
                for check in health_report.checks:
                    if check.name == "sip_registration" and check.status.value == "healthy":
                        sip_registered = True
                        break
            elif isinstance(health_report, dict):
                sip_registration = health_report.get("sip_registration", {})
                if isinstance(sip_registration, dict):
                    sip_registered = sip_registration.get("status") == "healthy"
                else:
                    sip_registered = sip_registration == "healthy"
            
            return {
                "timestamp": time.time(),
                "uptime_seconds": time.time() - self.start_time,
                "sip_registered": sip_registered,
                "active_calls": self._get_active_calls(),
                "api_tokens_used": call_stats.get("total_tokens", 0),
                "total_calls": call_stats.get("total_calls", 0),
                "successful_calls": call_stats.get("completed_calls", 0),
                "failed_calls": call_stats.get("failed_calls", 0),
                "average_call_duration": call_stats.get("average_duration", 0.0),
                "total_cost": call_stats.get("total_cost", 0.0),
                "health_status": health_report,
                "configuration": {
                    "sip_domain": settings.sip_domain,
                    "openai_mode": settings.openai_mode.value if hasattr(settings.openai_mode, 'value') else str(settings.openai_mode),
                    "openai_model": settings.openai_model,
                    "audio_sample_rate": settings.audio_sample_rate,
                }
            }
        except Exception as e:
            logger.error("Failed to get system status", error=str(e))
            return {
                "timestamp": time.time(),
                "uptime_seconds": time.time() - self.start_time,
                "sip_registered": False,
                "active_calls": [],
                "api_tokens_used": 0,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "average_call_duration": 0.0,
                "total_cost": 0.0,
                "error": str(e)
            }
    
    def _get_active_calls(self) -> List[Dict[str, Any]]:
        """Get list of currently active calls."""
        # This would integrate with the SIP client to get active calls
        # For now, return empty list
        return []
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add a log message to the system logs."""
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        }
        
        self.logs.append(log_entry)
        
        # Keep only the last max_logs entries
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Also log to the main logger
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "INFO":
            logger.info(message)
        else:
            logger.debug(message)
    
    def get_logs(self) -> List[str]:
        """Get formatted log messages."""
        return [
            f"[{log['formatted_time']}] {log['level']}: {log['message']}"
            for log in self.logs
        ]
    
    def clear_logs(self):
        """Clear all system logs."""
        self.logs.clear()
        logger.info("System logs cleared")
    
    async def start(self):
        """Start the system monitor."""
        logger.info("Starting system monitor")
        self.add_log("System monitor started", "INFO")
    
    async def stop(self):
        """Stop the system monitor."""
        logger.info("Stopping system monitor")
        self.add_log("System monitor stopped", "INFO")


# Global system monitor instance
_system_monitor = None


def get_system_monitor() -> SystemMonitor:
    """Get or create system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor
