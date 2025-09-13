#!/usr/bin/env python3
"""
Enhanced SIP AI Agent with comprehensive reliability and observability.

This is the new main agent that integrates all the enhanced modules:
- Typed configuration with Pydantic
- Structured logging with correlation IDs
- Comprehensive metrics and health monitoring
- Enhanced SIP client with reconnection and NAT traversal
- Improved OpenAI integration with realtime API support
- Audio pipeline with backpressure and error handling
"""

import asyncio
import signal
import sys
from typing import Optional

from config import get_settings, reload_settings
from health import get_health_monitor
from logging_config import (
    generate_correlation_id,
    get_logger,
    setup_logging,
    with_correlation_id,
)
from metrics import get_metrics
from monitor import monitor
from call_history import get_call_history_manager

# OpenAIAgent is imported by SIPClient when needed
from sip_client import SIPClient, SIPRegistrationError


class SIPAIAgent:
    """Enhanced SIP AI Agent with comprehensive reliability features."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("agent")
        self.metrics = get_metrics()
        self.health_monitor = get_health_monitor()
        self.call_history_manager = get_call_history_manager()
        self.sip_client: Optional[SIPClient] = None
        self.is_running = False
        self.correlation_id = generate_correlation_id()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(self.shutdown())

    async def initialize(self) -> None:
        """Initialize the agent with all components."""
        with with_correlation_id(self.correlation_id):
            try:
                self.logger.info(
                    "Initializing SIP AI Agent",
                    version="2.1.0",
                    openai_mode=self.settings.openai_mode.value,
                    sip_domain=self.settings.sip_domain,
                )

                # Validate configuration
                self._validate_configuration()

                # Initialize SIP client
                self.sip_client = SIPClient()
                self.sip_client.initialize()

                # Start monitoring
                monitor.start()

                self.logger.info("Agent initialization completed successfully")

            except Exception as e:
                self.logger.error("Failed to initialize agent", error=str(e))
                raise

    def _validate_configuration(self) -> None:
        """Validate agent configuration."""
        # Check required settings
        required_settings = [
            "sip_domain",
            "sip_user",
            "sip_pass",
            "openai_api_key",
            "agent_id",
        ]

        missing_settings = []
        for setting in required_settings:
            if not getattr(self.settings, setting, None):
                missing_settings.append(setting)

        if missing_settings:
            raise ValueError(
                f"Missing required settings: {', '.join(missing_settings)}"
            )

        # Validate SIP configuration
        if not self.settings.sip_domain or not self.settings.sip_user:
            raise ValueError("SIP domain and user must be configured")

        # Validate OpenAI configuration
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key must be configured")

        # Validate audio configuration
        if self.settings.audio_sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError(
                f"Unsupported sample rate: {self.settings.audio_sample_rate}"
            )

        self.logger.info("Configuration validation passed")

    async def start(self) -> None:
        """Start the agent and begin SIP registration."""
        with with_correlation_id(self.correlation_id):
            try:
                self.is_running = True
                self.logger.info("Starting SIP AI Agent")

                # Register with SIP server
                await self._register_sip()

                # Start health monitoring loop
                asyncio.create_task(self._health_monitoring_loop())

                self.logger.info(
                    "SIP AI Agent started successfully",
                    sip_domain=self.settings.sip_domain,
                    sip_user=self.settings.sip_user,
                    openai_mode=self.settings.openai_mode.value,
                )

                # Keep the agent running
                await self._run_forever()

            except Exception as e:
                self.logger.error("Failed to start agent", error=str(e))
                await self.shutdown()
                raise

    async def _register_sip(self) -> None:
        """Register with the SIP server with retry logic."""
        max_retries = self.settings.sip_registration_retry_max
        retry_count = 0

        while retry_count < max_retries and self.is_running:
            try:
                self.logger.info(
                    "Attempting SIP registration",
                    attempt=retry_count + 1,
                    max_retries=max_retries,
                )

                if self.sip_client is None:
                    raise SIPRegistrationError("SIP client not initialized")

                await self.sip_client.register()

                # Wait for registration to complete
                await asyncio.sleep(2)

                if self.sip_client.is_registered():
                    self.logger.info("SIP registration successful")
                    monitor.update_registration(True)
                    return
                else:
                    raise SIPRegistrationError("Registration failed")

            except SIPRegistrationError as e:
                retry_count += 1
                self.logger.warning(
                    "SIP registration failed",
                    attempt=retry_count,
                    max_retries=max_retries,
                    error=str(e),
                )

                if retry_count < max_retries:
                    backoff_time = (
                        self.settings.sip_registration_retry_backoff**retry_count
                    )
                    self.logger.info(
                        "Retrying SIP registration", retry_in_seconds=backoff_time
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    self.logger.error("SIP registration failed after all retries")
                    monitor.update_registration(False)
                    raise

    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop."""
        while self.is_running:
            try:
                await asyncio.sleep(self.settings.health_check_interval)

                if self.is_running:
                    # Run health checks
                    report = await self.health_monitor.run_health_checks()

                    # Log health status
                    if report.overall_status.value in ["unhealthy", "critical"]:
                        self.logger.warning(
                            "Health check failed",
                            overall_status=report.overall_status.value,
                            failed_checks=[
                                check.name
                                for check in report.checks
                                if check.status.value in ["unhealthy", "critical"]
                            ],
                        )
                    else:
                        self.logger.debug(
                            "Health check passed",
                            overall_status=report.overall_status.value,
                        )

            except Exception as e:
                self.logger.error("Health monitoring error", error=str(e))

    async def _run_forever(self) -> None:
        """Keep the agent running until shutdown is requested."""
        try:
            while self.is_running:
                await asyncio.sleep(1)

                # Check SIP registration status periodically
                if self.sip_client and not self.sip_client.is_registered():
                    self.logger.warning(
                        "SIP registration lost, attempting to re-register"
                    )
                    monitor.update_registration(False)
                    try:
                        await self._register_sip()
                    except Exception as e:
                        self.logger.error("Failed to re-register SIP", error=str(e))

        except asyncio.CancelledError:
            self.logger.info("Agent run loop cancelled")
        except Exception as e:
            self.logger.error("Unexpected error in run loop", error=str(e))
            raise

    async def shutdown(self) -> None:
        """Gracefully shutdown the agent."""
        with with_correlation_id(self.correlation_id):
            self.logger.info("Shutting down SIP AI Agent")
            self.is_running = False

        try:
            # Shutdown SIP client
            if self.sip_client:
                self.sip_client.shutdown()

            # Final health report
            report = await self.health_monitor.run_health_checks()
            self.logger.info(
                "Final health report",
                overall_status=report.overall_status.value,
                uptime_seconds=report.uptime_seconds,
            )

            self.logger.info("SIP AI Agent shutdown completed")

        except Exception as e:
            self.logger.error("Error during shutdown", error=str(e))

    def reload_configuration(self) -> None:
        """Reload configuration from environment."""
        try:
            new_settings = reload_settings()
            self.settings = new_settings

            self.logger.info("Configuration reloaded successfully")

        except Exception as e:
            self.logger.error("Failed to reload configuration", error=str(e))


async def main():
    """Main entry point for the enhanced SIP AI Agent."""
    # Setup structured logging
    setup_logging()

    # Create and start the agent
    agent = SIPAIAgent()

    try:
        await agent.initialize()
        await agent.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    # Run the agent
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
    except Exception as e:
        print(f"Failed to start agent: {e}")
        sys.exit(1)
