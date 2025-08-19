"""
Tests for focus session timer logic
"""

import pytest
import time
import uuid
from unittest.mock import Mock, patch, MagicMock
from focus_timer import FocusTimer


class TestFocusTimer:
    """Test focus timer functionality"""

    def test_focus_timer_initialization(self, test_db, mock_config):
        """Test that focus timer initializes correctly"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        assert timer.idle_threshold == 60
        assert timer.cerebro_db == test_db
        assert timer.current_session is None
        assert timer.session_start_time is None

    def test_start_focus_session(self, test_db, mock_config):
        """Test starting a focus session"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Test session")
            
        assert session_id is not None
        assert timer.current_session is not None
        assert timer.session_start_time == 1640995200
        assert timer.current_session['duration_minutes'] == 25
        assert timer.current_session['notes'] == "Test session"

    def test_start_focus_session_with_defaults(self, test_db, mock_config):
        """Test starting a focus session with default values"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session()
            
        assert session_id is not None
        assert timer.current_session['duration_minutes'] == 25  # Default
        assert timer.current_session['notes'] == ""  # Default

    def test_cannot_start_session_when_already_running(self, test_db, mock_config):
        """Test that cannot start a session when one is already running"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start first session
        with patch('time.time', return_value=1640995200):
            timer.start_session(25, "First session")
            
        # Try to start second session
        with pytest.raises(RuntimeError):
            timer.start_session(30, "Second session")

    def test_stop_focus_session(self, test_db, mock_config):
        """Test stopping a focus session"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start session
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Test session")
            
        # Stop session
        with patch('time.time', return_value=1640996700):
            result = timer.stop_session("Session completed")
            
        assert result is not None
        assert timer.current_session is None
        assert timer.session_start_time is None
        assert result['session_id'] == session_id
        assert result['duration'] == 1500  # 25 minutes in seconds
        assert result['was_interrupted'] == False

    def test_cannot_stop_session_when_none_running(self, test_db, mock_config):
        """Test that cannot stop a session when none is running"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        with pytest.raises(RuntimeError):
            timer.stop_session("No session to stop")

    def test_get_session_status(self, test_db, mock_config):
        """Test getting current session status"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # No session running
        status = timer.get_session_status()
        assert status['is_running'] == False
        assert status['session_id'] is None
        
        # Start session
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Test session")
            
        # Check status
        with patch('time.time', return_value=1640995800):
            status = timer.get_session_status()
            
        assert status['is_running'] == True
        assert status['session_id'] == session_id
        assert status['elapsed_seconds'] == 600  # 10 minutes
        assert status['remaining_seconds'] == 900  # 15 minutes remaining

    def test_session_interruption_detection(self, test_db, mock_config):
        """Test that sessions are marked as interrupted when idle"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start session
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Test session")
            
        # Simulate idle period
        with patch('metrics.idle.get_idle_seconds', return_value=120):
            timer._check_idle_interruption()
            
        # Stop session
        with patch('time.time', return_value=1640996700):
            result = timer.stop_session("Session completed")
            
        assert result['was_interrupted'] == True

    def test_session_not_interrupted_when_active(self, test_db, mock_config):
        """Test that sessions are not marked as interrupted when active"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start session
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Test session")
            
        # Simulate active period
        with patch('metrics.idle.get_idle_seconds', return_value=30):
            timer._check_idle_interruption()
            
        # Stop session
        with patch('time.time', return_value=1640996700):
            result = timer.stop_session("Session completed")
            
        assert result['was_interrupted'] == False

    def test_session_duration_calculation(self, test_db, mock_config):
        """Test session duration calculation"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start session
        with patch('time.time', return_value=1640995200):
            timer.start_session(25, "Test session")
            
        # Calculate duration after 10 minutes
        with patch('time.time', return_value=1640995800):
            duration = timer._calculate_session_duration()
            assert duration == 600  # 10 minutes

    def test_session_completion_detection(self, test_db, mock_config):
        """Test that sessions are marked as completed when duration is reached"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start session for 1 minute
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(1, "Short session")
            
        # Check after 1 minute
        with patch('time.time', return_value=1640995260):
            is_completed = timer._is_session_completed()
            assert is_completed == True

    def test_session_not_completed_before_duration(self, test_db, mock_config):
        """Test that sessions are not marked as completed before duration"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start session for 25 minutes
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Long session")
            
        # Check after 10 minutes
        with patch('time.time', return_value=1640995800):
            is_completed = timer._is_session_completed()
            assert is_completed == False

    def test_session_id_generation(self, test_db, mock_config):
        """Test that session IDs are unique"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        session_ids = set()
        
        for i in range(10):
            with patch('time.time', return_value=1640995200 + i):
                session_id = timer.start_session(1, f"Session {i}")
                session_ids.add(session_id)
                timer.stop_session("Completed")
                
        # All session IDs should be unique
        assert len(session_ids) == 10

    def test_session_database_logging(self, test_db, mock_config):
        """Test that sessions are logged to database"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Start and stop session
        with patch('time.time', return_value=1640995200):
            session_id = timer.start_session(25, "Test session")
            
        with patch('time.time', return_value=1640996700):
            result = timer.stop_session("Session completed")
            
        # Check database
        sessions = test_db.get_focus_sessions(limit=1)
        assert len(sessions) == 1
        session_data = sessions[0]
        assert session_data['session_id'] == session_id
        assert session_data['duration'] == 1500
        assert session_data['was_interrupted'] == False
        assert session_data['notes'] == "Session completed"

    def test_session_statistics(self, test_db, mock_config):
        """Test session statistics calculation"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Create multiple sessions
        for i in range(5):
            with patch('time.time', return_value=1640995200 + i * 1500):
                session_id = timer.start_session(25, f"Session {i}")
                
            with patch('time.time', return_value=1640995200 + (i + 1) * 1500):
                timer.stop_session("Completed")
                
        # Get statistics
        stats = timer.get_session_statistics(days=7)
        assert stats['total_sessions'] == 5
        assert stats['total_duration'] == 7500  # 5 * 25 minutes
        assert stats['avg_duration'] == 1500  # 25 minutes
        assert stats['completed_sessions'] == 5
        assert stats['interrupted_sessions'] == 0

    def test_session_history(self, test_db, mock_config):
        """Test session history retrieval"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Create sessions
        for i in range(3):
            with patch('time.time', return_value=1640995200 + i * 1500):
                session_id = timer.start_session(25, f"Session {i}")
                
            with patch('time.time', return_value=1640995200 + (i + 1) * 1500):
                timer.stop_session("Completed")
                
        # Get history
        history = timer.get_session_history(days=7)
        assert len(history) == 3
        assert history[0]['notes'] == "Completed"
        assert history[1]['notes'] == "Completed"
        assert history[2]['notes'] == "Completed"

    def test_focus_timer_error_handling(self, test_db, mock_config):
        """Test error handling in focus timer"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Test with database error
        with patch.object(test_db, 'insert_focus_session', side_effect=Exception("DB error")):
            with patch('time.time', return_value=1640995200):
                # Should not crash
                session_id = timer.start_session(25, "Test session")
                assert session_id is not None

    def test_focus_timer_configuration_validation(self, test_db, mock_config):
        """Test configuration validation"""
        # Test invalid idle threshold
        with pytest.raises(ValueError):
            FocusTimer(
                idle_threshold=-1,
                cerebro_db=test_db
            )
            
        # Test invalid session duration
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        with pytest.raises(ValueError):
            timer.start_session(-1, "Invalid session")

    def test_focus_timer_performance(self, test_db, mock_config):
        """Test focus timer performance"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Test multiple rapid operations
        start_time = time.time()
        
        for i in range(100):
            with patch('time.time', return_value=1640995200 + i):
                session_id = timer.start_session(1, f"Session {i}")
                timer.stop_session("Completed")
                
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly
        assert duration < 2.0

    def test_focus_timer_memory_usage(self, test_db, mock_config):
        """Test that focus timer doesn't leak memory"""
        timer = FocusTimer(
            idle_threshold=60,
            cerebro_db=test_db
        )
        
        # Perform many operations
        for i in range(1000):
            with patch('time.time', return_value=1640995200 + i):
                session_id = timer.start_session(1, f"Session {i}")
                timer.stop_session("Completed")
                
        # Should not have accumulated excessive data
        assert timer.current_session is None
        assert timer.session_start_time is None
