import os
import json
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Constants
SETTINGS_PATH = "settings.json"
DEFAULT_SETTINGS = {
    "track_apps": True,
    "track_idle": True,
    "idle_threshold": 180,
    "track_screenshots": False,
    "track_audio": False,
    "track_windows": True,
    "track_idle_detailed": True,
    "track_input": True,
    "track_screen_time": True,
    "track_focus_sessions": True,
    "track_breaks": True
}

class Config:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "cerebro.db"
        self.settings_path = self.base_dir / SETTINGS_PATH
        
        # Ensure settings exist
        if not self.settings_path.exists():
            self.save_settings(DEFAULT_SETTINGS)

    def get_database_path(self) -> str:
        return str(self.db_path)

    def load_settings(self) -> Dict[str, Any]:
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            return DEFAULT_SETTINGS
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS

    def save_settings(self, settings: Dict[str, Any]):
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        # TODO: Implement per-service config in settings.json
        # For now return defaults based on service name
        defaults = {
            'window_tracker': {'log_interval': 1.0},
            'idle_monitor': {'timeout_seconds': 300, 'check_interval': 1.0},
            'input_logger': {'log_interval': 60, 'enable_keyboard': True, 'enable_mouse': True},
            'screen_time_tracker': {'idle_threshold': 60, 'check_interval': 1.0, 'daily_reset_hour': 0},
            'focus_timer': {'idle_threshold': 60},
            'break_monitor': {'min_break_duration': 120, 'max_break_duration': 900, 'check_interval': 1.0, 'detect_lock_events': True}
        }
        return defaults.get(service_name, {})

# Global config instance
settings = Config()
