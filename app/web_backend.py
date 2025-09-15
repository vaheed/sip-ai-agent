#!/usr/bin/env python3
"""
FastAPI backend for SIP AI Agent Web UI.

This module provides a comprehensive REST API and WebSocket interface for
the web dashboard, including authentication, configuration management,
real-time monitoring, and call history tracking.
"""

import os
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api_routes import APIHandler, ConfigUpdateRequest
from .auth import LoginRequest, LoginResponse, authenticate_user, get_current_user, logout_user
from .logging_config import get_logger
from .monitor import Monitor
from .websocket_handler import get_websocket_handler

logger = get_logger("web_backend")

# Global instances
monitor = None
api_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global monitor, api_handler
    
    # Startup
    logger.info("Starting SIP AI Agent Web Backend")
    
    # Initialize monitor
    monitor = Monitor()
    await monitor.start()
    
    # Initialize API handler
    api_handler = APIHandler(monitor)
    
    # Initialize WebSocket handler
    websocket_handler = get_websocket_handler(monitor)
    await websocket_handler.start_update_loop()
    
    logger.info("Web Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SIP AI Agent Web Backend")
    if monitor:
        await monitor.stop()


# Create FastAPI app
app = FastAPI(
    title="SIP AI Agent Web Backend",
    description="REST API and WebSocket interface for SIP AI Agent dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.exists(web_dir):
    app.mount("/js", StaticFiles(directory=os.path.join(web_dir, "js")), name="js")
    app.mount("/favicon.ico", StaticFiles(directory=web_dir), name="favicon")
    app.mount("/favicon.svg", StaticFiles(directory=web_dir), name="favicon-svg")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    try:
        frontend_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        if os.path.exists(frontend_path):
            with open(frontend_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(
                content="<h1>SIP AI Agent</h1><p>Frontend not found. Please check deployment.</p>",
                status_code=404
            )
    except Exception as e:
        logger.error("Failed to serve frontend", error=str(e))
        return HTMLResponse(
            content="<h1>Error</h1><p>Failed to load frontend.</p>",
            status_code=500
        )


# Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return session token."""
    result = await authenticate_user(login_data)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.message)
    return result


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and revoke session."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return await logout_user(token)
    return {"success": False, "message": "No token provided"}


@app.get("/api/auth/status")
async def auth_status(current_user: dict = Depends(get_current_user)):
    """Check authentication status."""
    return {"authenticated": True, "username": current_user["username"]}


# System status endpoints
@app.get("/api/status")
async def get_system_status():
    """Get current system status."""
    global api_handler
    if api_handler is None:
        # Initialize for testing
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.get_system_status()


@app.options("/api/status")
async def options_system_status():
    """Handle CORS preflight for system status."""
    from fastapi.responses import Response
    response = Response(content="OK")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.get("/api/logs")
async def get_logs():
    """Get system logs."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.get_logs()


# Call history endpoints
@app.get("/api/call_history")
async def get_call_history():
    """Get call history."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.get_call_history()


@app.get("/api/call_history/csv")
async def export_call_history_csv():
    """Export call history as CSV."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.export_call_history_csv()


@app.get("/api/call_history/statistics")
async def get_call_statistics():
    """Get call statistics for analytics."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.get_call_statistics()


# Configuration endpoints
@app.get("/api/config")
async def get_configuration(current_user: dict = Depends(get_current_user)):
    """Get current configuration."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.get_configuration(current_user)


@app.post("/api/config")
async def update_configuration(
    config_data: ConfigUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update configuration."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.update_configuration(config_data, current_user)


@app.post("/api/config/reload")
async def reload_configuration(current_user: dict = Depends(get_current_user)):
    """Reload configuration."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.reload_configuration(current_user)


# System metrics endpoint
@app.get("/api/system/metrics")
async def get_system_metrics():
    """Get real-time system metrics for admin dashboard."""
    global api_handler
    if api_handler is None:
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
        api_handler = APIHandler(monitor)
    return await api_handler.get_system_metrics()


# WebSocket endpoint
@app.websocket("/ws/events")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time updates."""
    global monitor
    if monitor is None:
        # Initialize for testing
        from .monitor import Monitor
        monitor = Monitor()
        await monitor.start()
    
    websocket_handler = get_websocket_handler(monitor)
    await websocket_handler.websocket_endpoint(websocket)


# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint for container orchestration."""
    try:
        # Get health report from health monitor
        from .health import get_health_monitor
        health_monitor = get_health_monitor()
        health_report = await health_monitor.run_health_checks()
        
        return {
            "status": health_report.overall_status.value,
            "timestamp": health_report.timestamp,
            "uptime_seconds": health_report.uptime_seconds,
            "version": "1.0.0",
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details
                } for check in health_report.checks
            },
            "services": {
                "web_backend": "healthy",
                "monitor": "healthy" if monitor else "unhealthy",
                "call_history": "healthy",
            },
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}, 503


def start_web_backend(host: str = "0.0.0.0", port: int = 8080):  # nosec B104
    """Start the web backend server."""
    logger.info("Starting web backend server", host=host, port=port)
    uvicorn.run("app.web_backend:app", host=host, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    start_web_backend()
