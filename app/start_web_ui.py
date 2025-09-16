#!/usr/bin/env python3
"""
Startup script for SIP AI Agent with Web UI.

This script starts both the SIP agent and the web UI backend together,
providing a complete solution for monitoring and managing the SIP AI Agent.
"""

import asyncio
import signal
import sys
import threading
import time
from typing import Optional

from .agent import SIPAIAgent
from .config import get_settings
from .logging_config import get_logger, setup_logging
from .web_backend import start_web_backend

logger = get_logger("startup")


class WebUIService:
    """Service that manages both SIP agent and web UI."""

    def __init__(self):
        self.settings = get_settings()
        self.sip_agent: Optional[SIPAIAgent] = None
        self.web_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.shutdown_event = asyncio.Event()

    def start_web_backend_thread(self):
        """Start web backend in a separate thread."""
        try:
            logger.info("Starting web backend thread")
            start_web_backend(
                host=self.settings.monitor_host, port=self.settings.monitor_port
            )
        except Exception as e:
            logger.error("Failed to start web backend", error=str(e))

    async def start(self):
        """Start both SIP agent and web UI."""
        logger.info("Starting SIP AI Agent with Web UI")

        # Setup logging
        setup_logging()

        # Start web backend in a separate thread
        self.web_thread = threading.Thread(
            target=self.start_web_backend_thread, daemon=True
        )
        self.web_thread.start()

        # Give web backend time to start
        await asyncio.sleep(2)

        # Start SIP agent
        self.sip_agent = SIPAIAgent()
        await self.sip_agent.initialize()
        await self.sip_agent.start()

        self.is_running = True
        logger.info("SIP AI Agent with Web UI started successfully")

        # Keep running until shutdown
        try:
            await self.shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")

        await self.stop()

    async def stop(self):
        """Stop both SIP agent and web UI."""
        if not self.is_running:
            return

        logger.info("Stopping SIP AI Agent with Web UI")

        if self.sip_agent:
            await self.sip_agent.stop()

        self.is_running = False
        logger.info("SIP AI Agent with Web UI stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.shutdown_event.set())


async def main():
    """Main entry point."""
    # Setup signal handlers
    service = WebUIService()

    # Register signal handlers
    signal.signal(signal.SIGINT, service.signal_handler)
    signal.signal(signal.SIGTERM, service.signal_handler)

    try:
        await service.start()
    except Exception as e:
        logger.error("Failed to start service", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    # Check if we should run demo calls
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        logger.info("Running with demo call simulation")
        # Import and run demo calls in background
        from .demo_calls import CallSimulator

        async def run_demo():
            simulator = CallSimulator()
            # Create some demo calls
            await simulator.create_demo_calls(10)
            logger.info("Demo calls created")

        # Run demo calls
        asyncio.run(run_demo())

    # Start the main service
    asyncio.run(main())
