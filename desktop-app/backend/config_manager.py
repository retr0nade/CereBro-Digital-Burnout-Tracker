#!/usr/bin/env python3
"""
Configuration Manager for CereBro Mental Burnout Tracker
Handles loading and accessing configuration settings from config.json
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = {}
        self._load_config()
        self._ensure_directories()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Configuration file {self.config_path} not found, using defaults")
                self._create_default_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            "database": {
                "path": "./cerebro.db",
                "backup_path": "./backups/",
                "max_backups": 10
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "main_log": "./logs/cerebro.log",
                "service_manager_log": "./logs/service_manager.log",
                "window_tracker_log": "./logs/window_tracker.log",
                "idle_monitor_log": "./logs/idle_monitor.log",
                "input_logger_log": "./logs/input_logger.log",
                "screen_time_tracker_log": "./logs/screen_time_tracker.log",
                "break_monitor_log": "./logs/break_monitor.log",
                "focus_timer_log": "./logs/focus_timer.log"
            },
            "services": {
                "window_tracker": {
                    "enabled": True,
                    "log_interval": 1.0,
                    "max_restarts": 3,
                    "restart_delay": 5
                },
                "idle_monitor": {
                    "enabled": True,
                    "timeout_seconds": 300,
                    "check_interval": 1.0,
                    "max_restarts": 3,
                    "restart_delay": 5
                },
                "input_logger": {
                    "enabled": True,
                    "log_interval": 60,
                    "enable_keyboard": True,
                    "enable_mouse": True,
                    "max_restarts": 3,
                    "restart_delay": 5
                },
                "screen_time_tracker": {
                    "enabled": True,
                    "idle_threshold": 60,
                    "check_interval": 1.0,
                    "daily_reset_hour": 0,
                    "max_restarts": 3,
                    "restart_delay": 5
                },
                "break_monitor": {
                    "enabled": True,
                    "min_break_duration": 120,
                    "max_break_duration": 900,
                    "check_interval": 1.0,
                    "detect_lock_events": True,
                    "max_restarts": 3,
                    "restart_delay": 5
                },
                "focus_timer": {
                    "enabled": True,
                    "default_session_length": 1500,
                    "idle_threshold": 60,
                    "max_restarts": 3,
                    "restart_delay": 5
                }
            },
            "monitoring": {
                "check_interval": 10,
                "manager_check_interval": 30,
                "thread_timeout": 5
            },
            "api": {
                "host": "localhost",
                "port": 5005,
                "debug": False
            },
            "paths": {
                "logs_dir": "./logs",
                "backups_dir": "./backups",
                "data_dir": "./data",
                "extension_data_dir": "./extension_data"
            }
        }
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.get("paths.logs_dir"),
            self.get("paths.backups_dir"),
            self.get("paths.data_dir"),
            self.get("paths.extension_data_dir")
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation
        
        Args:
            key_path: Path to the configuration key (e.g., "database.path")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration dictionary
        """
        return self.get(f"services.{service_name}", {})
    
    def get_log_config(self, service_name: str = None) -> Dict[str, Any]:
        """
        Get logging configuration
        
        Args:
            service_name: Optional service name for specific log file
            
        Returns:
            Logging configuration dictionary
        """
        log_config = {
            "level": self.get("logging.level", "INFO"),
            "format": self.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        }
        
        if service_name:
            log_file = self.get(f"logging.{service_name}_log")
            if log_file:
                log_config["file"] = log_file
        
        return log_config
    
    def get_database_path(self) -> str:
        """Get the database path"""
        return self.get("database.path", "./cerebro.db")
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.get("api", {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.get("monitoring", {})
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration with new values
        
        Args:
            updates: Dictionary of configuration updates
        """
        def update_nested_dict(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    update_nested_dict(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        update_nested_dict(self.config, updates)
        self.save_config()
    
    def validate_config(self) -> bool:
        """
        Validate the configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_keys = [
            "database.path",
            "logging.level",
            "services.window_tracker.enabled",
            "services.idle_monitor.enabled",
            "services.input_logger.enabled"
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                print(f"Missing required configuration key: {key}")
                return False
        
        return True

# Global configuration instance
config = ConfigManager()
