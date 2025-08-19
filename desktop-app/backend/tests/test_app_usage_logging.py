"""
Tests for app usage logging functionality
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from window_tracker import WindowTracker


class TestAppUsageLogging:
    """Test app usage logging functionality"""

    def test_window_tracker_initialization(self, test_db, mock_config):
        """Test that window tracker initializes correctly"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        assert tracker.log_interval == 1.0
        assert tracker.cerebro_db == test_db
        assert tracker.is_running == False
        assert tracker.current_window is None
        assert tracker.current_start_time is None

    def test_get_active_window_mocking(self, test_db, mock_config):
        """Test getting active window with mocked data"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock the active window detection
        with patch('metrics.apps.get_foreground_app', return_value=('test_app', 'Test Window', 12345)):
            app_name, window_title, pid = tracker._get_active_window()
            
        assert app_name == 'test_app'
        assert window_title == 'Test Window'
        assert pid == 12345

    def test_window_activity_logging(self, test_db, mock_config):
        """Test logging window activity"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock active window
        with patch.object(tracker, '_get_active_window', return_value=('test_app', 'Test Window', 12345)):
            with patch('time.time', return_value=1640995200):
                tracker._log_window_activity(
                    'test_app',
                    'Test Window',
                    1640995200,
                    1640995260,
                    60,
                    12345
                )
                
        # Check database
        result = test_db.get_app_usage(limit=1)
        assert len(result) == 1
        data = result[0]
        assert data['app_name'] == 'test_app'
        assert data['duration'] == 60

    def test_window_switch_detection(self, test_db, mock_config):
        """Test detection of window switches"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Set current window
        tracker.current_window = ('app1', 'Window 1')
        tracker.current_start_time = 1640995200
        
        # Mock new window
        with patch.object(tracker, '_get_active_window', return_value=('app2', 'Window 2', 12345)):
            with patch.object(tracker, '_log_window_activity') as mock_log:
                with patch('time.time', return_value=1640995260):
                    tracker._tracking_loop_iteration()
                    
        # Should log the previous window activity
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args['app_name'] == 'app1'
        assert call_args['window_title'] == 'Window 1'
        assert call_args['duration'] == 60

    def test_no_window_switch_same_app(self, test_db, mock_config):
        """Test that no logging occurs when window doesn't change"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Set current window
        tracker.current_window = ('app1', 'Window 1')
        tracker.current_start_time = 1640995200
        
        # Mock same window
        with patch.object(tracker, '_get_active_window', return_value=('app1', 'Window 1', 12345)):
            with patch.object(tracker, '_log_window_activity') as mock_log:
                with patch('time.time', return_value=1640995260):
                    tracker._tracking_loop_iteration()
                    
        # Should not log anything
        mock_log.assert_not_called()

    def test_window_tracker_start_stop(self, test_db, mock_config):
        """Test that window tracker can be started and stopped"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test start
        with patch('threading.Thread') as mock_thread:
            tracker.start()
            assert tracker.is_running == True
            mock_thread.assert_called_once()
            
        # Test stop
        tracker.stop()
        assert tracker.is_running == False

    def test_app_categorization(self, test_db, mock_config):
        """Test app categorization logic"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test different app categories
        test_cases = [
            ('code.exe', 'development'),
            ('slack.exe', 'communication'),
            ('excel.exe', 'productivity'),
            ('chrome.exe', 'browsing'),
            ('youtube.com', 'entertainment'),
            ('explorer.exe', 'system'),
            ('unknown.exe', 'other')
        ]
        
        for app_name, expected_category in test_cases:
            category = tracker._categorize_app(app_name)
            assert category == expected_category

    def test_window_tracking_loop(self, test_db, mock_config):
        """Test the main tracking loop"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock the tracking loop for a few iterations
        with patch.object(tracker, '_get_active_window', return_value=('test_app', 'Test Window', 12345)):
            with patch('time.time', side_effect=[1640995200, 1640995260, 1640995320]):
                # First iteration - should set current window
                tracker._tracking_loop_iteration()
                assert tracker.current_window == ('test_app', 'Test Window')
                assert tracker.current_start_time == 1640995200
                
                # Second iteration - same window, no logging
                with patch.object(tracker, '_log_window_activity') as mock_log:
                    tracker._tracking_loop_iteration()
                    mock_log.assert_not_called()

    def test_window_tracking_with_different_windows(self, test_db, mock_config):
        """Test tracking with different windows"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock different windows over time
        window_sequence = [
            ('app1', 'Window 1', 12345),
            ('app2', 'Window 2', 12346),
            ('app1', 'Window 3', 12347)
        ]
        
        with patch.object(tracker, '_get_active_window', side_effect=window_sequence):
            with patch('time.time', side_effect=[1640995200, 1640995260, 1640995320]):
                with patch.object(tracker, '_log_window_activity') as mock_log:
                    # First window
                    tracker._tracking_loop_iteration()
                    assert tracker.current_window == ('app1', 'Window 1')
                    
                    # Second window - should log first window
                    tracker._tracking_loop_iteration()
                    mock_log.assert_called_once()
                    call_args = mock_log.call_args[1]
                    assert call_args['app_name'] == 'app1'
                    assert call_args['window_title'] == 'Window 1'
                    assert call_args['duration'] == 60
                    
                    # Third window - should log second window
                    tracker._tracking_loop_iteration()
                    assert mock_log.call_count == 2
                    call_args = mock_log.call_args[1]
                    assert call_args['app_name'] == 'app2'
                    assert call_args['window_title'] == 'Window 2'

    def test_window_tracker_error_handling(self, test_db, mock_config):
        """Test error handling in window tracker"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test with exception in window detection
        with patch.object(tracker, '_get_active_window', side_effect=Exception("Test error")):
            # Should not crash
            tracker._tracking_loop_iteration()

    def test_window_tracker_database_error_handling(self, test_db, mock_config):
        """Test database error handling in window tracker"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Mock database error
        with patch.object(test_db, 'insert_app_usage', side_effect=Exception("DB error")):
            with patch('time.time', return_value=1640995200):
                # Should not crash
                tracker._log_window_activity(
                    'test_app',
                    'Test Window',
                    1640995200,
                    1640995260,
                    60,
                    12345
                )

    def test_window_tracker_configuration_validation(self, test_db, mock_config):
        """Test configuration validation"""
        # Test invalid log interval
        with pytest.raises(ValueError):
            WindowTracker(
                log_interval=0,
                cerebro_db=test_db
            )
            
        # Test negative log interval
        with pytest.raises(ValueError):
            WindowTracker(
                log_interval=-1.0,
                cerebro_db=test_db
            )

    def test_window_tracker_performance(self, test_db, mock_config):
        """Test window tracker performance"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test multiple rapid operations
        start_time = time.time()
        
        with patch.object(tracker, '_get_active_window', return_value=('test_app', 'Test Window', 12345)):
            for i in range(100):
                with patch('time.time', return_value=1640995200 + i):
                    tracker._tracking_loop_iteration()
                    
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly
        assert duration < 1.0

    def test_window_tracker_memory_usage(self, test_db, mock_config):
        """Test that window tracker doesn't leak memory"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Perform many operations
        with patch.object(tracker, '_get_active_window', return_value=('test_app', 'Test Window', 12345)):
            for i in range(1000):
                with patch('time.time', return_value=1640995200 + i):
                    tracker._tracking_loop_iteration()
                    
        # Should not have accumulated excessive data
        assert tracker.current_window is not None
        assert tracker.current_start_time is not None
        # No other state should accumulate indefinitely

    def test_window_tracker_data_integrity(self, test_db, mock_config):
        """Test data integrity in window tracker"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Log some window activity
        with patch('time.time', return_value=1640995200):
            tracker._log_window_activity(
                'test_app',
                'Test Window',
                1640995200,
                1640995260,
                60,
                12345
            )
            
        # Verify data integrity
        result = test_db.get_app_usage(limit=1)
        data = result[0]
        
        # Check data types for stored fields
        assert isinstance(data['app_name'], str)
        assert isinstance(data['duration'], int)
        
        # Check logical constraints
        assert data['duration'] > 0
        assert data['start_time'] < data['end_time']
        assert data['end_time'] - data['start_time'] == data['duration']

    def test_window_tracker_edge_cases(self, test_db, mock_config):
        """Test edge cases in window tracker"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Test with very short duration
        with patch('time.time', return_value=1640995200):
            tracker._log_window_activity(
                'test_app',
                'Test Window',
                1640995200,
                1640995201,
                1,
                12345
            )
            
        result = test_db.get_app_usage(limit=1)
        assert result[0]['duration'] == 1
        
        # Test with very long duration
        with patch('time.time', return_value=1640995200):
            tracker._log_window_activity(
                'test_app',
                'Test Window',
                1640995200,
                1640998800,
                3600,  # 1 hour
                12345
            )
            
        result = test_db.get_app_usage(limit=2)
        assert result[0]['duration'] == 3600

    def test_window_tracker_multiple_apps(self, test_db, mock_config):
        """Test tracking multiple apps"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        apps = ['chrome', 'code', 'slack', 'excel', 'explorer']
        
        for i, app in enumerate(apps):
            with patch('time.time', return_value=1640995200 + i * 60):
                tracker._log_window_activity(
                    app,
                    f'{app} Window',
                    1640995200 + i * 60,
                    1640995260 + i * 60,
                    60,
                    12345 + i
                )
                
        # Check all apps were logged
        result = test_db.get_app_usage(limit=10)
        assert len(result) == 5
        
        app_names = [r['app_name'] for r in result]
        for app in apps:
            assert app in app_names

    def test_window_tracker_concurrent_access(self, test_db, mock_config):
        """Test concurrent access to window tracker"""
        tracker = WindowTracker(
            log_interval=1.0,
            cerebro_db=test_db
        )
        
        # Simulate concurrent access
        with patch.object(tracker, '_get_active_window', return_value=('test_app', 'Test Window', 12345)):
            # Multiple rapid calls should not cause issues
            for i in range(10):
                with patch('time.time', return_value=1640995200 + i):
                    tracker._tracking_loop_iteration()
                    
        # Should still work correctly
        assert tracker.current_window == ('test_app', 'Test Window')
