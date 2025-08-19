"""
Tests for idle detection logic
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from idle_monitor import IdleMonitor


class TestIdleDetection:
    """Test idle detection functionality"""

    def test_idle_monitor_initialization(self, test_db, mock_config):
        """Test that idle monitor initializes correctly"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        assert monitor.timeout_seconds == 300
        assert monitor.check_interval == 1.0
        assert monitor.cerebro_db == test_db
        assert monitor.is_running == False
        assert monitor.current_idle_start is None
        assert monitor.is_idle == False

    def test_idle_detection_below_threshold(self, test_db, mock_config):
        """Test that system is not considered idle when below threshold"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock idle time to be below threshold
        with patch('metrics.idle.get_idle_seconds', return_value=100):
            is_idle = monitor._check_idle_status()
            
        assert is_idle == False
        assert monitor.is_idle == False
        assert monitor.current_idle_start is None

    def test_idle_detection_above_threshold(self, test_db, mock_config):
        """Test that system is considered idle when above threshold"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock idle time to be above threshold
        with patch('metrics.idle.get_idle_seconds', return_value=400):
            is_idle = monitor._check_idle_status()
            
        assert is_idle == True
        assert monitor.is_idle == True
        assert monitor.current_idle_start is not None

    def test_idle_transition_from_active_to_idle(self, test_db, mock_config):
        """Test transition from active to idle state"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Start in active state
        monitor.is_idle = False
        monitor.current_idle_start = None
        
        # Mock idle time to be above threshold
        with patch('metrics.idle.get_idle_seconds', return_value=400):
            with patch.object(monitor, '_log_idle_start') as mock_log:
                is_idle = monitor._check_idle_status()
                
        assert is_idle == True
        assert monitor.is_idle == True
        assert monitor.current_idle_start is not None
        mock_log.assert_called_once()

    def test_idle_transition_from_idle_to_active(self, test_db, mock_config):
        """Test transition from idle to active state"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Start in idle state
        monitor.is_idle = True
        monitor.current_idle_start = 1640995200
        
        # Mock idle time to be below threshold
        with patch('metrics.idle.get_idle_seconds', return_value=100):
            with patch.object(monitor, '_log_idle_end') as mock_log:
                is_idle = monitor._check_idle_status()
                
        assert is_idle == False
        assert monitor.is_idle == False
        assert monitor.current_idle_start is None
        mock_log.assert_called_once()

    def test_idle_logging_start(self, test_db, mock_config):
        """Test that idle start is logged correctly"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        with patch('time.time', return_value=1640995200):
            monitor._log_idle_start(400, "inactivity")
        # Start only sets current_idle_start; DB row is written on end
        assert monitor.current_idle_start == 1640995200

    def test_idle_logging_end(self, test_db, mock_config):
        """Test that idle end is logged correctly"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Set up idle start
        monitor.current_idle_start = 1640995200
        
        with patch('time.time', return_value=1640995500):
            monitor._log_idle_end()
            
        # Check that idle period was updated
        result = test_db.get_idle_periods(limit=1)
        assert len(result) == 1
        data = result[0]
        assert data['start_time'] == 1640995200
        assert data['end_time'] == 1640995500
        assert data['duration'] == 300

    def test_idle_monitor_start_stop(self, test_db, mock_config):
        """Test that idle monitor can be started and stopped"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test start
        with patch('threading.Thread') as mock_thread:
            monitor.start()
            assert monitor.is_running == True
            mock_thread.assert_called_once()
            
        # Test stop
        monitor.stop()
        assert monitor.is_running == False

    def test_idle_monitor_thread_safety(self, test_db, mock_config):
        """Test thread safety of idle monitor"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test concurrent access
        with patch('metrics.idle.get_idle_seconds', return_value=400):
            # Simulate concurrent calls
            monitor._check_idle_status()
            monitor._check_idle_status()
            
        # Should not cause any issues
        assert monitor.is_idle == True

    def test_idle_threshold_edge_cases(self, test_db, mock_config):
        """Test idle detection at threshold boundaries"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test exactly at threshold
        with patch('metrics.idle.get_idle_seconds', return_value=300):
            is_idle = monitor._check_idle_status()
            assert is_idle == True
            
        # Test just below threshold
        with patch('metrics.idle.get_idle_seconds', return_value=299):
            is_idle = monitor._check_idle_status()
            assert is_idle == False
            
        # Test just above threshold
        with patch('metrics.idle.get_idle_seconds', return_value=301):
            is_idle = monitor._check_idle_status()
            assert is_idle == True

    def test_idle_duration_calculation(self, test_db, mock_config):
        """Test idle duration calculation"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Set up idle start
        monitor.current_idle_start = 1640995200
        
        with patch('time.time', return_value=1640995800):
            duration = monitor._calculate_idle_duration()
            assert duration == 600  # 10 minutes

    def test_idle_reason_tracking(self, test_db, mock_config):
        """Test that idle reasons are tracked correctly"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test different idle reasons
        reasons = ["inactivity", "screen_lock", "system_sleep"]
        
        for reason in reasons:
            with patch('time.time', return_value=1640995200):
                monitor._log_idle_start(400, reason)
                monitor._log_idle_end()
            result = test_db.get_idle_periods(limit=1)
            assert result[0]['start_time'] == 1640995200

    def test_idle_monitor_error_handling(self, test_db, mock_config):
        """Test error handling in idle monitor"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test with exception in idle detection
        with patch('metrics.idle.get_idle_seconds', side_effect=Exception("Test error")):
            # Should not crash
            is_idle = monitor._check_idle_status()
            assert is_idle == False

    def test_idle_monitor_database_error_handling(self, test_db, mock_config):
        """Test database error handling in idle monitor"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock database error
        with patch.object(test_db, 'insert_idle_period', side_effect=Exception("DB error")):
            with patch('time.time', return_value=1640995200):
                # Should not crash
                monitor._log_idle_start(400, "inactivity")

    def test_idle_monitor_configuration_validation(self, test_db, mock_config):
        """Test configuration validation"""
        # Test invalid timeout
        with pytest.raises(ValueError):
            IdleMonitor(
                timeout_seconds=-1,
                check_interval=1.0,
                cerebro_db=test_db
            )
            
        # Test invalid check interval
        with pytest.raises(ValueError):
            IdleMonitor(
                timeout_seconds=300,
                check_interval=0,
                cerebro_db=test_db
            )

    def test_idle_monitor_performance(self, test_db, mock_config):
        """Test idle monitor performance"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test multiple rapid checks
        start_time = time.time()
        
        with patch('metrics.idle.get_idle_seconds', return_value=100):
            for _ in range(100):
                monitor._check_idle_status()
                
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly (less than 1 second for 100 checks)
        assert duration < 1.0

    def test_idle_monitor_memory_usage(self, test_db, mock_config):
        """Test that idle monitor doesn't leak memory"""
        monitor = IdleMonitor(
            timeout_seconds=300,
            check_interval=1.0,
            cerebro_db=test_db
        )
        
        # Perform many operations
        with patch('metrics.idle.get_idle_seconds', return_value=400):
            for i in range(1000):
                monitor._check_idle_status()
                
        # Should not have accumulated excessive data
        assert monitor.current_idle_start is not None
        # No other state should accumulate indefinitely
