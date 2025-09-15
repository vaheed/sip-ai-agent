"""
Tests for system monitor module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.system_monitor import SystemMonitor, get_system_monitor


class TestSystemMonitor:
    """Test SystemMonitor class."""
    
    @pytest.fixture
    def system_monitor(self):
        """Create SystemMonitor instance for testing."""
        return SystemMonitor()
    
    @pytest.fixture
    def mock_call_history_manager(self):
        """Mock call history manager."""
        mock_manager = MagicMock()
        mock_manager.get_call_statistics.return_value = {
            "total_calls": 10,
            "completed_calls": 8,
            "failed_calls": 2,
            "total_tokens": 5000,
            "average_duration": 45.0,
            "total_cost": 0.015
        }
        return mock_manager
    
    @pytest.fixture
    def mock_health_monitor(self):
        """Mock health monitor."""
        mock_monitor = AsyncMock()
        mock_monitor.run_health_checks.return_value = {
            "sip_registration": {"status": "healthy"},
            "openai_connection": {"status": "healthy"}
        }
        return mock_monitor
    
    def test_init(self, system_monitor):
        """Test SystemMonitor initialization."""
        assert system_monitor.start_time is not None
        assert system_monitor.logs == []
        assert system_monitor.max_logs == 1000
        assert system_monitor.call_history_manager is not None
        assert system_monitor.health_monitor is not None
    
    @pytest.mark.asyncio
    async def test_get_system_status_success(self, system_monitor, mock_call_history_manager, mock_health_monitor):
        """Test getting system status successfully."""
        with patch.object(system_monitor, 'call_history_manager', mock_call_history_manager), \
             patch.object(system_monitor, 'health_monitor', mock_health_monitor):
            
            status = await system_monitor.get_system_status()
            
            assert "timestamp" in status
            assert "uptime_seconds" in status
            assert "sip_registered" in status
            assert "active_calls" in status
            assert "api_tokens_used" in status
            assert "total_calls" in status
            assert "successful_calls" in status
            assert "failed_calls" in status
            assert "average_call_duration" in status
            assert "total_cost" in status
            assert "health_status" in status
            assert "configuration" in status
            
            assert status["total_calls"] == 10
            assert status["successful_calls"] == 8
            assert status["failed_calls"] == 2
            assert status["api_tokens_used"] == 5000
    
    @pytest.mark.asyncio
    async def test_get_system_status_error(self, system_monitor):
        """Test getting system status with error."""
        # Mock the health_monitor.run_health_checks to raise an exception
        mock_health_monitor = AsyncMock()
        mock_health_monitor.run_health_checks.side_effect = Exception("Test error")
        
        with patch.object(system_monitor, 'health_monitor', mock_health_monitor):
            status = await system_monitor.get_system_status()
            
            assert "error" in status
            assert "Test error" in str(status["error"])
    
    def test_add_log(self, system_monitor):
        """Test adding log messages."""
        system_monitor.add_log("Test log message", "INFO")
        
        assert len(system_monitor.logs) == 1
        log_entry = system_monitor.logs[0]
        assert log_entry["message"] == "Test log message"
        assert log_entry["level"] == "INFO"
        assert "timestamp" in log_entry
        assert "formatted_time" in log_entry
    
    def test_add_log_different_levels(self, system_monitor):
        """Test adding log messages with different levels."""
        system_monitor.add_log("Error message", "ERROR")
        system_monitor.add_log("Warning message", "WARNING")
        system_monitor.add_log("Info message", "INFO")
        system_monitor.add_log("Debug message", "DEBUG")
        
        assert len(system_monitor.logs) == 4
        assert system_monitor.logs[0]["level"] == "ERROR"
        assert system_monitor.logs[1]["level"] == "WARNING"
        assert system_monitor.logs[2]["level"] == "INFO"
        assert system_monitor.logs[3]["level"] == "DEBUG"
    
    def test_add_log_max_logs(self, system_monitor):
        """Test adding logs when max_logs limit is reached."""
        system_monitor.max_logs = 3
        
        # Add more logs than max_logs
        for i in range(5):
            system_monitor.add_log(f"Log message {i}", "INFO")
        
        assert len(system_monitor.logs) == 3
        # Should keep the last 3 logs
        assert system_monitor.logs[0]["message"] == "Log message 2"
        assert system_monitor.logs[1]["message"] == "Log message 3"
        assert system_monitor.logs[2]["message"] == "Log message 4"
    
    def test_get_logs(self, system_monitor):
        """Test getting formatted log messages."""
        system_monitor.add_log("Test message", "INFO")
        system_monitor.add_log("Error message", "ERROR")
        
        logs = system_monitor.get_logs()
        
        assert len(logs) == 2
        assert "INFO: Test message" in logs[0]
        assert "ERROR: Error message" in logs[1]
        assert all("[20" in log for log in logs)  # Check timestamp format
    
    def test_clear_logs(self, system_monitor):
        """Test clearing logs."""
        system_monitor.add_log("Test message", "INFO")
        system_monitor.add_log("Another message", "ERROR")
        
        assert len(system_monitor.logs) == 2
        
        system_monitor.clear_logs()
        
        assert len(system_monitor.logs) == 0
    
    def test_get_active_calls(self, system_monitor):
        """Test getting active calls."""
        active_calls = system_monitor._get_active_calls()
        
        # Currently returns empty list
        assert isinstance(active_calls, list)
        assert len(active_calls) == 0
    
    @pytest.mark.asyncio
    async def test_start(self, system_monitor):
        """Test starting the system monitor."""
        await system_monitor.start()
        
        # Should add a log entry
        assert len(system_monitor.logs) >= 1
        assert any("System monitor started" in log["message"] for log in system_monitor.logs)
    
    @pytest.mark.asyncio
    async def test_stop(self, system_monitor):
        """Test stopping the system monitor."""
        await system_monitor.stop()
        
        # Should add a log entry
        assert len(system_monitor.logs) >= 1
        assert any("System monitor stopped" in log["message"] for log in system_monitor.logs)


class TestGetSystemMonitor:
    """Test get_system_monitor function."""
    
    def test_get_system_monitor_singleton(self):
        """Test that get_system_monitor returns singleton instance."""
        monitor1 = get_system_monitor()
        monitor2 = get_system_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, SystemMonitor)
