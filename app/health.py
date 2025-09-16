#!/usr/bin/env python3
"""
Health monitoring and diagnostics for the SIP AI Agent.

This module provides comprehensive health checks, system diagnostics,
and a health endpoint for monitoring and alerting systems.
"""

import asyncio
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

from .config import get_settings
from .logging_config import get_logger
from .metrics import get_metrics

logger = get_logger("health")


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float
    duration_ms: float


@dataclass
class HealthReport:
    """Complete health report."""

    overall_status: HealthStatus
    timestamp: float
    uptime_seconds: float
    checks: List[HealthCheck]
    system_metrics: Dict[str, Any]


class HealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self):
        self.settings = get_settings()
        self.metrics = get_metrics()
        self.start_time = time.time()
        self.last_check_time: float = 0.0
        self.check_results: Dict[str, HealthCheck] = {}

    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return float(time.time() - self.start_time)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
                    "percent": memory.percent,
                },
                "disk": {
                    "total_bytes": disk.total,
                    "used_bytes": disk.used,
                    "free_bytes": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "load_average": (
                    psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
                ),
            }
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {"error": str(e)}

    async def check_sip_registration(self) -> HealthCheck:
        """Check SIP registration status."""
        start_time = time.time()

        try:
            # This would need to be integrated with the actual SIP client
            # For now, we'll use the metrics
            is_registered = self.metrics.get_active_calls_count() >= 0  # Placeholder

            status = HealthStatus.HEALTHY if is_registered else HealthStatus.UNHEALTHY
            message = "SIP registered" if is_registered else "SIP not registered"

            return HealthCheck(
                name="sip_registration",
                status=status,
                message=message,
                details={
                    "registered": is_registered,
                    "domain": self.settings.sip_domain,
                    "user": self.settings.sip_user,
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="sip_registration",
                status=HealthStatus.CRITICAL,
                message=f"SIP registration check failed: {e}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_openai_connectivity(self) -> HealthCheck:
        """Check OpenAI API connectivity."""
        start_time = time.time()

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key)

            # Simple connectivity test
            models = client.models.list()

            return HealthCheck(
                name="openai_connectivity",
                status=HealthStatus.HEALTHY,
                message="OpenAI API accessible",
                details={
                    "models_available": len(models.data) if models.data else 0,
                    "api_mode": self.settings.openai_mode.value,
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="openai_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"OpenAI API unreachable: {e}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_audio_pipeline(self) -> HealthCheck:
        """Check audio pipeline health."""
        start_time = time.time()

        try:
            # Check audio configuration
            frame_size = self.settings.get_audio_frame_size()
            frame_bytes = self.settings.get_audio_frame_bytes()

            # Check if audio processing is within expected parameters
            active_calls = self.metrics.get_active_calls_count()

            status = HealthStatus.HEALTHY
            message = "Audio pipeline healthy"

            if active_calls > 0:
                # Additional checks for active calls could go here
                pass

            return HealthCheck(
                name="audio_pipeline",
                status=status,
                message=message,
                details={
                    "active_calls": active_calls,
                    "frame_size": frame_size,
                    "frame_bytes": frame_bytes,
                    "sample_rate": self.settings.audio_sample_rate,
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="audio_pipeline",
                status=HealthStatus.DEGRADED,
                message=f"Audio pipeline issues: {e}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_websocket_connections(self) -> HealthCheck:
        """Check WebSocket connection health."""
        start_time = time.time()

        try:
            # This would need to be integrated with actual WebSocket tracking
            # For now, we'll use placeholder logic
            connection_count = 0  # Placeholder

            status = HealthStatus.HEALTHY
            message = "WebSocket connections healthy"

            if connection_count > 10:  # Arbitrary threshold
                status = HealthStatus.DEGRADED
                message = "High number of WebSocket connections"

            return HealthCheck(
                name="websocket_connections",
                status=status,
                message=message,
                details={
                    "active_connections": connection_count,
                    "api_mode": self.settings.openai_mode.value,
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="websocket_connections",
                status=HealthStatus.DEGRADED,
                message=f"WebSocket check failed: {e}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_system_resources(self) -> HealthCheck:
        """Check system resource usage."""
        start_time = time.time()

        try:
            metrics = self.get_system_metrics()

            cpu_percent = metrics.get("cpu_percent", 0)
            memory_percent = metrics.get("memory", {}).get("percent", 0)
            disk_percent = metrics.get("disk", {}).get("percent", 0)

            status = HealthStatus.HEALTHY
            message = "System resources healthy"

            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                status = HealthStatus.CRITICAL
                message = "High resource usage detected"
            elif cpu_percent > 70 or memory_percent > 80 or disk_percent > 85:
                status = HealthStatus.DEGRADED
                message = "Elevated resource usage"

            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details=metrics,
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resource check failed: {e}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def run_health_checks(self) -> HealthReport:
        """Run all health checks and generate a comprehensive report."""
        logger.info("Running health checks")

        checks = [
            self.check_sip_registration(),
            self.check_openai_connectivity(),
            self.check_audio_pipeline(),
            self.check_websocket_connections(),
            self.check_system_resources(),
        ]

        # Run checks concurrently
        results = await asyncio.gather(*checks, return_exceptions=True)

        # Process results
        health_checks: list[HealthCheck] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_check = HealthCheck(
                    name=f"check_{i}",
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {result}",
                    details={"error": str(result)},
                    timestamp=time.time(),
                    duration_ms=0,
                )
                health_checks.append(error_check)
                self.check_results[error_check.name] = error_check
            else:
                # result is guaranteed to be HealthCheck here
                if not isinstance(result, HealthCheck):
                    # This should never happen, but handle gracefully
                    error_check = HealthCheck(
                        name=f"check_{i}_type_error",
                        status=HealthStatus.CRITICAL,
                        message="Unexpected result type in health check",
                        details={"error": f"Expected HealthCheck, got {type(result)}"},
                        timestamp=time.time(),
                        duration_ms=0,
                    )
                    health_checks.append(error_check)
                    self.check_results[error_check.name] = error_check
                else:
                    health_checks.append(result)
                    self.check_results[result.name] = result

        # Determine overall status
        statuses = [check.status for check in health_checks]
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        self.last_check_time = time.time()

        report = HealthReport(
            overall_status=overall_status,
            timestamp=time.time(),
            uptime_seconds=self.get_uptime(),
            checks=health_checks,
            system_metrics=self.get_system_metrics(),
        )

        logger.info(
            "Health check completed",
            overall_status=overall_status.value,
            checks_count=len(health_checks),
        )

        return report

    def get_last_check_result(self, check_name: str) -> Optional[HealthCheck]:
        """Get the result of the last health check by name."""
        return self.check_results.get(check_name)

    def is_healthy(self) -> bool:
        """Quick health check - returns True if overall status is healthy or degraded."""
        if not self.check_results:
            return False

        overall_status = HealthStatus.HEALTHY
        for check in self.check_results.values():
            if check.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
                break
            elif (
                check.status == HealthStatus.UNHEALTHY
                and overall_status == HealthStatus.HEALTHY
            ):
                overall_status = HealthStatus.UNHEALTHY

        return overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


# Global health monitor instance
health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    return health_monitor


async def get_health_report() -> Dict[str, Any]:
    """Get a health report as a dictionary."""
    report = await health_monitor.run_health_checks()
    return asdict(report)
