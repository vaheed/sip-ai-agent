"""
API routes module for SIP AI Agent Web UI.

This module contains all the REST API endpoints for the web dashboard.
"""

import csv
import io
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .auth import get_current_user
from .call_history import get_call_history_manager
from .config import get_settings, reload_settings
from .logging_config import get_logger
from .monitor import Monitor, load_config, save_config

logger = get_logger("api_routes")


class ConfigUpdateRequest(BaseModel):
    """Configuration update request model."""
    sip: Optional[Dict[str, Any]] = None
    openai: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    system: Optional[Dict[str, Any]] = None


class APIHandler:
    """Handles API route logic."""
    
    def __init__(self, monitor: Monitor):
        self.monitor = monitor
        self.call_history_manager = get_call_history_manager()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            status_data = await self.monitor.get_system_status()
            return status_data
        except Exception as e:
            logger.error("Failed to get system status", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get system status")
    
    async def get_call_history(self) -> List[Dict[str, Any]]:
        """Get call history."""
        try:
            history = self.call_history_manager.get_call_history()
            return history
        except Exception as e:
            logger.error("Failed to get call history", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get call history")
    
    async def export_call_history_csv(self) -> FileResponse:
        """Export call history as CSV."""
        try:
            history = self.call_history_manager.get_call_history()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Call ID", "Start Time", "End Time", "Duration", 
                "Status", "Tokens Used", "Cost"
            ])
            
            # Write data
            for call in history:
                start_time = datetime.fromtimestamp(call.get("start", 0)).isoformat() if call.get("start") else ""
                end_time = datetime.fromtimestamp(call.get("end", 0)).isoformat() if call.get("end") else ""
                duration = call.get("end", 0) - call.get("start", 0) if call.get("start") and call.get("end") else 0
                
                writer.writerow([
                    call.get("call_id", ""),
                    start_time,
                    end_time,
                    duration,
                    call.get("status", ""),
                    call.get("tokens_used", ""),
                    call.get("cost", "")
                ])
            
            # Prepare response
            csv_content = output.getvalue()
            output.close()
            
            response = Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=call_history.csv"}
            )
            return response
            
        except Exception as e:
            logger.error("Failed to export call history", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to export call history")
    
    async def get_call_statistics(self) -> Dict[str, Any]:
        """Get call statistics for analytics."""
        try:
            # Get statistics from call history manager
            stats = self.call_history_manager.get_call_statistics()
            
            # Calculate additional metrics
            total_calls = stats.get("total_calls", 0)
            successful_calls = stats.get("completed_calls", 0)
            failed_calls = stats.get("failed_calls", 0)
            total_tokens = stats.get("total_tokens", 0)
            
            return {
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "average_duration": stats.get("average_duration", 0.0),
                "longest_call": stats.get("longest_call", 0.0),
                "shortest_call": stats.get("shortest_call", 0.0),
                "total_duration": stats.get("total_duration", 0.0),
                "total_tokens": total_tokens,
                "average_tokens_per_call": total_tokens / total_calls if total_calls > 0 else 0,
                "max_tokens_used": stats.get("max_tokens_used", 0),
                "total_cost": stats.get("total_cost", 0.0),
                "cost_per_token": stats.get("total_cost", 0.0) / total_tokens if total_tokens > 0 else 0,
                "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
                "calls_last_24h": stats.get("calls_last_24h", 0),
                "calls_last_7d": stats.get("calls_last_7d", 0),
                "calls_last_30d": stats.get("calls_last_30d", 0),
            }
        except Exception as e:
            logger.error("Failed to get call statistics", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get call statistics")
    
    async def get_logs(self) -> Dict[str, Any]:
        """Get system logs."""
        try:
            logs = self.monitor.get_logs()
            return {"logs": logs}
        except Exception as e:
            logger.error("Failed to get logs", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get logs")
    
    async def get_configuration(self, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
        """Get current configuration."""
        try:
            config = load_config()
            return config
        except Exception as e:
            logger.error("Failed to get configuration", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    async def update_configuration(
        self, 
        config_data: ConfigUpdateRequest, 
        current_user: dict = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Update configuration."""
        try:
            # Load current config
            current_config = load_config()
            
            # Update with new values
            if config_data.sip:
                current_config["sip"].update(config_data.sip)
            if config_data.openai:
                current_config["openai"].update(config_data.openai)
            if config_data.audio:
                current_config["audio"].update(config_data.audio)
            if config_data.system:
                current_config["system"].update(config_data.system)
            
            # Save configuration
            save_config(current_config)
            
            logger.info("Configuration updated successfully", user=current_user["username"])
            return {"success": True, "message": "Configuration updated successfully"}
            
        except Exception as e:
            logger.error("Failed to update configuration", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    
    async def reload_configuration(self, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
        """Reload configuration."""
        try:
            reload_settings()
            logger.info("Configuration reloaded successfully", user=current_user["username"])
            return {"success": True, "message": "Configuration reloaded successfully"}
        except Exception as e:
            logger.error("Failed to reload configuration", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to reload configuration")
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics for admin dashboard."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network stats
            network = psutil.net_io_counters()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "pid": os.getpid(),
                    "threads": psutil.Process().num_threads(),
                    "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
                }
            }
        except ImportError:
            # Fallback if psutil is not available
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {"usage_percent": 0, "count": 1, "frequency": 0},
                "memory": {"total": 0, "available": 0, "used": 0, "usage_percent": 0},
                "disk": {"total": 0, "used": 0, "free": 0, "usage_percent": 0},
                "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
                "process": {"pid": os.getpid(), "threads": 1, "memory_mb": 0}
            }
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get system metrics")
