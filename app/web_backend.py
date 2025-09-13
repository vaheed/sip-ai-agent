#!/usr/bin/env python3
"""
FastAPI backend for SIP AI Agent Web UI.

This module provides a comprehensive REST API and WebSocket interface for
the web dashboard, including authentication, configuration management,
real-time monitoring, and call history tracking.
"""

import asyncio
import csv
import hashlib
import io
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import get_settings, reload_settings
from logging_config import get_logger
from monitor import Monitor
from call_history import get_call_history_manager

logger = get_logger("web_backend")

# Configuration for authentication
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()  # Default password
SESSION_SECRET = "sip-agent-session-secret-key"  # In production, use env variable

# Global instances
settings = get_settings()
monitor = Monitor()
call_history_manager = get_call_history_manager()
security = HTTPBearer(auto_error=False)

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected", connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected", connections=len(self.active_connections))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Failed to send WebSocket message", error=str(e))
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]

class ConfigReloadResponse(BaseModel):
    success: bool
    message: str

class CallHistoryItem(BaseModel):
    call_id: str
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    caller: Optional[str] = None
    callee: Optional[str] = None
    status: str = "completed"

class SystemStatus(BaseModel):
    sip_registered: bool
    active_calls: List[str]
    api_tokens_used: int
    uptime_seconds: float
    system_metrics: Dict[str, Any]

# Authentication functions
def verify_password(password: str) -> bool:
    """Verify admin password."""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == ADMIN_PASSWORD_HASH

def create_session_token() -> str:
    """Create a session token."""
    timestamp = str(int(time.time()))
    token_data = f"{ADMIN_USERNAME}:{timestamp}:{SESSION_SECRET}"
    return hashlib.sha256(token_data.encode()).hexdigest()

def verify_session_token(token: str) -> bool:
    """Verify session token."""
    # For simplicity, we'll use a basic token validation
    # In production, use JWT or similar
    return token == create_session_token()

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current authenticated user."""
    if not credentials or not verify_session_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": ADMIN_USERNAME}

# FastAPI app
app = FastAPI(
    title="SIP AI Agent Web UI",
    description="Web interface for SIP AI Agent monitoring and configuration",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (React frontend)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend."""
    try:
        with open("web/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>SIP AI Agent Web UI</h1><p>Frontend not found. Please build the React app.</p>",
            status_code=404
        )

@app.post("/api/auth/login")
async def login(request: LoginRequest, response: Response):
    """Authenticate user and create session."""
    if request.username == ADMIN_USERNAME and verify_password(request.password):
        token = create_session_token()
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return {"success": True, "token": token}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

@app.post("/api/auth/logout")
async def logout(response: Response):
    """Logout user and clear session."""
    response.delete_cookie(key="session_token")
    return {"success": True}

@app.get("/api/auth/status")
async def auth_status(current_user: dict = Depends(get_current_user)):
    """Check authentication status."""
    return {"authenticated": True, "username": current_user["username"]}

@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status."""
    try:
        # Get system metrics from monitor
        uptime = time.time() - monitor.start_time if hasattr(monitor, 'start_time') else 0
        
        # Get active calls from call history manager
        active_calls = [call.call_id for call in call_history_manager.get_active_calls()]
        
        # Get total tokens from call history
        total_tokens = sum(call.tokens_used for call in call_history_manager.get_call_history())
        
        return SystemStatus(
            sip_registered=monitor.sip_registered,
            active_calls=active_calls,
            api_tokens_used=total_tokens,
            uptime_seconds=uptime,
            system_metrics={
                "cpu_usage": 0.0,  # Placeholder - implement actual system metrics
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "total_calls": len(call_history_manager.get_call_history()),
                "active_calls_count": len(active_calls),
            }
        )
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Get recent logs."""
    try:
        logs = monitor.logs[-limit:] if monitor.logs else []
        return {"logs": logs, "total": len(monitor.logs)}
    except Exception as e:
        logger.error("Failed to get logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get logs")

@app.get("/api/call_history", response_model=List[CallHistoryItem])
async def get_call_history():
    """Get call history."""
    try:
        # Get history from call history manager
        history_items = call_history_manager.get_call_history()
        
        # Convert to response model
        history = []
        for item in history_items:
            history.append(CallHistoryItem(
                call_id=item.call_id,
                start_time=item.start_time,
                end_time=item.end_time,
                duration=item.duration,
                status=item.status
            ))
        
        # Also include active calls
        active_calls = call_history_manager.get_active_calls()
        for item in active_calls:
            history.append(CallHistoryItem(
                call_id=item.call_id,
                start_time=item.start_time,
                end_time=item.end_time,
                duration=item.duration,
                status=item.status
            ))
        
        return history
    except Exception as e:
        logger.error("Failed to get call history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get call history")

@app.get("/api/call_history/csv")
async def export_call_history_csv():
    """Export call history as CSV."""
    try:
        # Get history from call history manager
        history_items = call_history_manager.get_call_history()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Call ID", "Caller", "Callee", "Direction", "Start Time", "End Time", 
            "Duration (seconds)", "Status", "Tokens Used", "Cost", "Error Message"
        ])
        
        # Write data
        for item in history_items:
            start_time = datetime.fromtimestamp(item.start_time).strftime("%Y-%m-%d %H:%M:%S")
            end_time = datetime.fromtimestamp(item.end_time).strftime("%Y-%m-%d %H:%M:%S") if item.end_time else ""
            
            writer.writerow([
                item.call_id,
                item.caller or "",
                item.callee or "",
                item.direction,
                start_time,
                end_time,
                item.duration or "",
                item.status,
                item.tokens_used,
                item.cost,
                item.error_message or ""
            ])
        
        # Return CSV file
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=call_history.csv"}
        )
    except Exception as e:
        logger.error("Failed to export call history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export call history")

@app.get("/api/call_history/statistics")
async def get_call_statistics():
    """Get call statistics for analytics."""
    try:
        statistics = call_history_manager.get_call_statistics()
        return statistics
    except Exception as e:
        logger.error("Failed to get call statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get call statistics")

@app.get("/api/config")
async def get_configuration(current_user: dict = Depends(get_current_user)):
    """Get current configuration."""
    try:
        # Load config from .env file
        config = monitor.load_config()
        return {"config": config}
    except Exception as e:
        logger.error("Failed to get configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get configuration")

@app.post("/api/config", response_model=ConfigReloadResponse)
async def update_configuration(
    request: ConfigUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update configuration and reload settings."""
    try:
        # Update config file
        monitor.save_config(request.config)
        
        # Reload settings
        reload_settings()
        
        # Log the update
        monitor.add_log(f"Configuration updated by {current_user['username']}")
        
        # Broadcast config update to WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "config_updated",
            "message": "Configuration updated successfully"
        }))
        
        return ConfigReloadResponse(
            success=True,
            message="Configuration updated successfully. Some changes may require a restart."
        )
    except Exception as e:
        logger.error("Failed to update configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@app.post("/api/config/reload", response_model=ConfigReloadResponse)
async def reload_configuration(current_user: dict = Depends(get_current_user)):
    """Reload configuration from environment."""
    try:
        # Reload settings
        reload_settings()
        
        # Log the reload
        monitor.add_log(f"Configuration reloaded by {current_user['username']}")
        
        # Broadcast reload to WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "config_reloaded",
            "message": "Configuration reloaded successfully"
        }))
        
        return ConfigReloadResponse(
            success=True,
            message="Configuration reloaded successfully"
        )
    except Exception as e:
        logger.error("Failed to reload configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reload configuration")

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}), websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(websocket)

# Background task to broadcast system updates
async def broadcast_system_updates():
    """Background task to broadcast system updates via WebSocket."""
    while True:
        try:
            if manager.active_connections:
                # Get current system status
                status_data = {
                    "type": "system_update",
                    "data": {
                        "sip_registered": monitor.sip_registered,
                        "active_calls": monitor.active_calls,
                        "api_tokens_used": monitor.api_tokens_used,
                        "timestamp": time.time()
                    }
                }
                
                await manager.broadcast(json.dumps(status_data))
        except Exception as e:
            logger.error("Failed to broadcast system updates", error=str(e))
        
        # Wait before next update
        await asyncio.sleep(5)

@app.get("/healthz")
async def health_check():
    """Health check endpoint for container orchestration."""
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "services": {
                "web_backend": "healthy",
                "monitor": "healthy",
                "call_history": "healthy"
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}, 503

@app.on_event("startup")
async def startup_event():
    """Initialize the web backend on startup."""
    logger.info("Starting SIP AI Agent Web Backend")
    
    # Set monitor start time
    monitor.start_time = time.time()
    
    # Start background task for system updates
    asyncio.create_task(broadcast_system_updates())
    
    logger.info("Web backend started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down SIP AI Agent Web Backend")

def start_web_backend(host: str = "0.0.0.0", port: int = 8080):
    """Start the web backend server."""
    logger.info("Starting web backend server", host=host, port=port)
    
    uvicorn.run(
        "web_backend:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    start_web_backend()
