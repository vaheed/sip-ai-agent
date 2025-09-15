"""
WebSocket handler module for SIP AI Agent Web UI.

This module handles WebSocket connections for real-time updates.
"""

import asyncio
import json
import time
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect

from .logging_config import get_logger

logger = get_logger("websocket")


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.message_queue = asyncio.Queue()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected", total_connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected", total_connections=len(self.active_connections))
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        # Send message to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_system_update(self, update_type: str, data: Dict):
        """Send system update to all connected clients."""
        message = {
            "type": update_type,
            "data": data,
            "timestamp": time.time()
        }
        await self.broadcast(json.dumps(message))


# Global connection manager
manager = ConnectionManager()


class WebSocketHandler:
    """Handles WebSocket connections and real-time updates."""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.connection_manager = manager
    
    async def websocket_endpoint(self, websocket: WebSocket):
        """Handle WebSocket connections."""
        await self.connection_manager.connect(websocket)
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await self.handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await self.connection_manager.send_personal_message(
                        json.dumps({"error": "Invalid JSON format"}), websocket
                    )
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error("WebSocket error", error=str(e))
            self.connection_manager.disconnect(websocket)
    
    async def handle_client_message(self, websocket: WebSocket, message: Dict):
        """Handle incoming messages from WebSocket clients."""
        message_type = message.get("type")
        
        if message_type == "ping":
            await self.connection_manager.send_personal_message(
                json.dumps({"type": "pong", "timestamp": time.time()}), websocket
            )
        
        elif message_type == "get_status":
            try:
                status = await self.monitor.get_system_status()
                await self.connection_manager.send_personal_message(
                    json.dumps({"type": "status_update", "data": status}), websocket
                )
            except Exception as e:
                logger.error("Failed to get status for WebSocket", error=str(e))
                await self.connection_manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Failed to get status"}), websocket
                )
        
        else:
            await self.connection_manager.send_personal_message(
                json.dumps({"type": "error", "message": f"Unknown message type: {message_type}"}), websocket
            )
    
    async def send_system_updates(self):
        """Periodically send system updates to all connected clients."""
        while True:
            try:
                # Get system status
                status = await self.monitor.get_system_status()
                
                # Send update to all connected clients
                await self.connection_manager.send_system_update("system_status", status)
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error("Failed to send system updates", error=str(e))
                await asyncio.sleep(10)  # Wait longer on error
    
    async def start_update_loop(self):
        """Start the system update loop."""
        asyncio.create_task(self.send_system_updates())


# Global WebSocket handler instance
websocket_handler = None


def get_websocket_handler(monitor):
    """Get or create WebSocket handler instance."""
    global websocket_handler
    if websocket_handler is None:
        websocket_handler = WebSocketHandler(monitor)
    return websocket_handler
