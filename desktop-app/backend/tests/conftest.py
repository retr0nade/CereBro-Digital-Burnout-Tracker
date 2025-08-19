"""
Pytest configuration and fixtures for Mental Burnout Tracker V2 tests
"""

import pytest
import os
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cerebro_db import CerebroDB
from config_manager import ConfigManager


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup - close any connections first
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        # File might still be in use, ignore cleanup error
        pass


@pytest.fixture
def test_db(temp_db_path):
    """Create a test database instance"""
    db = CerebroDB(temp_db_path)
    return db


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
    config = Mock(spec=ConfigManager)
    config.get_database_path.return_value = ":memory:"
    config.get_api_config.return_value = {
        'host': 'localhost',
        'port': 5005,
        'debug': False
    }
    config.get_service_config.return_value = {
        'log_interval': 1.0,
        'timeout_seconds': 300,
        'check_interval': 1.0,
        'idle_threshold': 60,
        'enable_keyboard': True,
        'enable_mouse': True,
        'min_break_duration': 120,
        'max_break_duration': 900,
        'detect_lock_events': True
    }
    return config


@pytest.fixture
def sample_app_usage_data():
    """Sample app usage data for testing"""
    return {
        'app_name': 'test_app',
        'start_time': 1640995200,
        'end_time': 1640995260,
        'duration': 60
    }


@pytest.fixture
def sample_idle_data():
    """Sample idle data for testing"""
    return {
        'start_time': 1640995200,
        'end_time': 1640995500,
        'duration': 300
    }


@pytest.fixture
def sample_input_data():
    """Sample input activity data for testing"""
    return {
        'timestamp': 1640995200,
        'keypress_count': 15,
        'mouse_click_count': 8
    }


@pytest.fixture
def sample_focus_session_data():
    """Sample focus session data for testing"""
    return {
        'start_time': 1640995200,
        'end_time': 1640996700,
        'was_interrupted': False,
        'duration': 1500
    }


@pytest.fixture
def sample_break_data():
    """Sample break data for testing"""
    return {
        'start_time': 1640995200,
        'end_time': 1640995500,
        'break_type': 'inactivity'
    }


@pytest.fixture
def mock_time():
    """Mock time for consistent testing"""
    with patch('time.time') as mock_time:
        mock_time.return_value = 1640995200
        yield mock_time


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing"""
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = Mock(
            timestamp=lambda: 1640995200,
            isoformat=lambda: '2022-01-01T12:00:00'
        )
        yield mock_datetime
