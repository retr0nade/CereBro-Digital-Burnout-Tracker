#!/usr/bin/env python3
"""
Service Manager for CereBro Mental Burnout Tracker
Manages all tracking services with monitoring, restart capabilities, and clean shutdown
"""

import time
import threading
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Import all trackers
from cerebro_db import CerebroDB
from window_tracker import WindowTracker
from idle_monitor import IdleMonitor
from input_logger import InputLogger
from screen_time_tracker import ScreenTimeTracker
from break_monitor import BreakMonitor
from config_manager import config

class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RESTARTING = "restarting"

@dataclass
class ServiceInfo:
    """Information about a service"""
    name: str
    status: ServiceStatus
    start_time: Optional[datetime] = None
    last_error: Optional[str] = None
    restart_count: int = 0
    max_restarts: int = 3
    restart_delay: int = 5  # seconds

class ServiceManager:
    """Manages all tracking services with monitoring and restart capabilities"""
    
    def __init__(self, cerebro_db: CerebroDB = None, custom_config: Dict[str, Any] = None):
        """
        Initialize the service manager
        
        Args:
            cerebro_db: Unified CerebroDB instance for all services
            custom_config: Optional custom configuration dictionary (overrides config.json)
        """
        self.cerebro_db = cerebro_db or CerebroDB(config.get_database_path())
        self.config = custom_config or config.config
        
        # Service management
        self.services: Dict[str, Any] = {}
        self.service_info: Dict[str, ServiceInfo] = {}
        self.service_threads: Dict[str, threading.Thread] = {}
        self.monitor_threads: Dict[str, threading.Thread] = {}
        
        # Manager state
        self.is_running = False
        self.shutdown_event = threading.Event()
        self.manager_thread = None
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize services
        self._initialize_services()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = config.get_log_config('service_manager')
        handlers = [logging.StreamHandler()]
        
        if 'file' in log_config:
            handlers.append(logging.FileHandler(log_config['file']))
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=handlers
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for all services"""
        return config.config
    
    def _initialize_services(self):
        """Initialize all services based on configuration"""
        self.logger.info("Initializing services...")
        
        # Window Tracker
        service_config = self.config['services']['window_tracker']
        if service_config['enabled']:
            try:
                self.services['window_tracker'] = WindowTracker(
                    log_interval=service_config['log_interval'],
                    cerebro_db=self.cerebro_db
                )
                self.service_info['window_tracker'] = ServiceInfo(
                    name='Window Tracker',
                    status=ServiceStatus.STOPPED,
                    max_restarts=service_config['max_restarts'],
                    restart_delay=service_config['restart_delay']
                )
                self.logger.info("Window tracker initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize window tracker: {e}")
        
        # Idle Monitor
        service_config = self.config['services']['idle_monitor']
        if service_config['enabled']:
            try:
                self.services['idle_monitor'] = IdleMonitor(
                    timeout_seconds=service_config['timeout_seconds'],
                    check_interval=service_config['check_interval'],
                    cerebro_db=self.cerebro_db
                )
                self.service_info['idle_monitor'] = ServiceInfo(
                    name='Idle Monitor',
                    status=ServiceStatus.STOPPED,
                    max_restarts=service_config['max_restarts'],
                    restart_delay=service_config['restart_delay']
                )
                self.logger.info("Idle monitor initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize idle monitor: {e}")
        
        # Input Logger
        service_config = self.config['services']['input_logger']
        if service_config['enabled']:
            try:
                self.services['input_logger'] = InputLogger(
                    log_interval=service_config['log_interval'],
                    enable_keyboard=service_config['enable_keyboard'],
                    enable_mouse=service_config['enable_mouse'],
                    cerebro_db=self.cerebro_db
                )
                self.service_info['input_logger'] = ServiceInfo(
                    name='Input Logger',
                    status=ServiceStatus.STOPPED,
                    max_restarts=service_config['max_restarts'],
                    restart_delay=service_config['restart_delay']
                )
                self.logger.info("Input logger initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize input logger: {e}")
        
        # Screen Time Tracker
        service_config = self.config['services']['screen_time_tracker']
        if service_config['enabled']:
            try:
                self.services['screen_time_tracker'] = ScreenTimeTracker(
                    idle_threshold=service_config['idle_threshold'],
                    check_interval=service_config['check_interval'],
                    daily_reset_hour=service_config['daily_reset_hour']
                )
                self.service_info['screen_time_tracker'] = ServiceInfo(
                    name='Screen Time Tracker',
                    status=ServiceStatus.STOPPED,
                    max_restarts=service_config['max_restarts'],
                    restart_delay=service_config['restart_delay']
                )
                self.logger.info("Screen time tracker initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize screen time tracker: {e}")
        
        # Break Monitor
        service_config = self.config['services']['break_monitor']
        if service_config['enabled']:
            try:
                self.services['break_monitor'] = BreakMonitor(
                    min_break_duration=service_config['min_break_duration'],
                    max_break_duration=service_config['max_break_duration'],
                    check_interval=service_config['check_interval'],
                    detect_lock_events=service_config['detect_lock_events']
                )
                self.service_info['break_monitor'] = ServiceInfo(
                    name='Break Monitor',
                    status=ServiceStatus.STOPPED,
                    max_restarts=service_config['max_restarts'],
                    restart_delay=service_config['restart_delay']
                )
                self.logger.info("Break monitor initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize break monitor: {e}")
        
        self.logger.info(f"Initialized {len(self.services)} services")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def _start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        service = self.services[service_name]
        service_info = self.service_info[service_name]
        
        try:
            self.logger.info(f"Starting {service_info.name}...")
            service_info.status = ServiceStatus.STARTING
            
            # Start the service
            service.start()
            
            # Update service info
            service_info.status = ServiceStatus.RUNNING
            service_info.start_time = datetime.now()
            service_info.last_error = None
            
            self.logger.info(f"{service_info.name} started successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start {service_info.name}: {e}"
            self.logger.error(error_msg)
            service_info.status = ServiceStatus.ERROR
            service_info.last_error = error_msg
            return False
    
    def _stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        service = self.services[service_name]
        service_info = self.service_info[service_name]
        
        try:
            self.logger.info(f"Stopping {service_info.name}...")
            
            # Stop the service
            service.stop()
            
            # Update service info
            service_info.status = ServiceStatus.STOPPED
            service_info.start_time = None
            
            self.logger.info(f"{service_info.name} stopped successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to stop {service_info.name}: {e}"
            self.logger.error(error_msg)
            service_info.last_error = error_msg
            return False
    
    def _restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        service_info = self.service_info[service_name]
        
        # Check if we've exceeded max restarts
        if service_info.restart_count >= service_info.max_restarts:
            error_msg = f"Max restarts ({service_info.max_restarts}) exceeded for {service_info.name}"
            self.logger.error(error_msg)
            service_info.status = ServiceStatus.ERROR
            service_info.last_error = error_msg
            return False
        
        try:
            self.logger.info(f"Restarting {service_info.name} (attempt {service_info.restart_count + 1}/{service_info.max_restarts})...")
            service_info.status = ServiceStatus.RESTARTING
            service_info.restart_count += 1
            
            # Stop the service first
            self._stop_service(service_name)
            
            # Wait before restarting
            time.sleep(service_info.restart_delay)
            
            # Start the service
            success = self._start_service(service_name)
            
            if success:
                self.logger.info(f"{service_info.name} restarted successfully")
            else:
                self.logger.error(f"Failed to restart {service_info.name}")
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to restart {service_info.name}: {e}"
            self.logger.error(error_msg)
            service_info.status = ServiceStatus.ERROR
            service_info.last_error = error_msg
            return False
    
    def _monitor_service(self, service_name: str):
        """Monitor a specific service for crashes and restart if needed"""
        service = self.services[service_name]
        service_info = self.service_info[service_name]
        
        self.logger.info(f"Starting monitor for {service_info.name}")
        
        while not self.shutdown_event.is_set():
            try:
                # Check if service is still running
                if hasattr(service, 'is_running') and not service.is_running:
                    if service_info.status == ServiceStatus.RUNNING:
                        self.logger.warning(f"{service_info.name} appears to have crashed")
                        self._restart_service(service_name)
                
                # Check if service thread is alive (if applicable)
                if hasattr(service, 'tracker_thread') and service.tracker_thread:
                    if not service.tracker_thread.is_alive():
                        self.logger.warning(f"{service_info.name} thread is not alive")
                        self._restart_service(service_name)
                
                # Sleep before next check
                check_interval = config.get_monitoring_config().get('check_interval', 10)
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring {service_info.name}: {e}")
                time.sleep(5)
        
        self.logger.info(f"Monitor for {service_info.name} stopped")
    
    def _manager_loop(self):
        """Main manager loop"""
        self.logger.info("Service manager started")
        
        while not self.shutdown_event.is_set():
            try:
                # Check all services
                for service_name in self.services.keys():
                    if self.shutdown_event.is_set():
                        break
                    
                    service_info = self.service_info[service_name]
                    
                    # If service is in error state and we haven't exceeded restarts, try to restart
                    if (service_info.status == ServiceStatus.ERROR and 
                        service_info.restart_count < service_info.max_restarts):
                        self._restart_service(service_name)
                
                # Sleep before next check
                check_interval = config.get_monitoring_config().get('manager_check_interval', 30)
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in manager loop: {e}")
                time.sleep(5)
        
        self.logger.info("Service manager stopped")
    
    def start_all(self) -> bool:
        """Start all services"""
        if self.is_running:
            self.logger.warning("Service manager is already running")
            return False
        
        self.logger.info("Starting all services...")
        self.is_running = True
        self.shutdown_event.clear()
        
        # Start all services
        for service_name in self.services.keys():
            if not self._start_service(service_name):
                self.logger.error(f"Failed to start {service_name}")
        
        # Start monitor threads for each service
        for service_name in self.services.keys():
            monitor_thread = threading.Thread(
                target=self._monitor_service,
                args=(service_name,),
                daemon=True
            )
            monitor_thread.start()
            self.monitor_threads[service_name] = monitor_thread
        
        # Start manager thread
        self.manager_thread = threading.Thread(target=self._manager_loop, daemon=True)
        self.manager_thread.start()
        
        self.logger.info("All services started")
        return True
    
    def stop_all(self) -> bool:
        """Stop all services"""
        if not self.is_running:
            self.logger.warning("Service manager is not running")
            return False
        
        self.logger.info("Stopping all services...")
        self.is_running = False
        self.shutdown_event.set()
        
        # Stop all services
        for service_name in self.services.keys():
            self._stop_service(service_name)
        
        # Wait for monitor threads to finish
        thread_timeout = config.get_monitoring_config().get('thread_timeout', 5)
        for service_name, monitor_thread in self.monitor_threads.items():
            if monitor_thread.is_alive():
                monitor_thread.join(timeout=thread_timeout)
        
        # Wait for manager thread to finish
        if self.manager_thread and self.manager_thread.is_alive():
            self.manager_thread.join(timeout=thread_timeout)
        
        self.logger.info("All services stopped")
        return True
    
    def shutdown(self):
        """Graceful shutdown of all services"""
        self.logger.info("Shutting down service manager...")
        self.stop_all()
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        status = {}
        
        for service_name, service_info in self.service_info.items():
            status[service_name] = {
                'name': service_info.name,
                'status': service_info.status.value,
                'start_time': service_info.start_time.isoformat() if service_info.start_time else None,
                'last_error': service_info.last_error,
                'restart_count': service_info.restart_count,
                'max_restarts': service_info.max_restarts,
                'uptime': None
            }
            
            # Calculate uptime if service is running
            if service_info.start_time and service_info.status == ServiceStatus.RUNNING:
                uptime = datetime.now() - service_info.start_time
                status[service_name]['uptime'] = str(uptime).split('.')[0]  # Remove microseconds
        
        return status
    
    def restart_service(self, service_name: str) -> bool:
        """Manually restart a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        self.logger.info(f"Manual restart requested for {service_name}")
        return self._restart_service(service_name)
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> List[str]:
        """Get recent logs for a specific service"""
        try:
            log_file = config.get(f"logging.{service_name}_log", f"{service_name}.log")
            with open(log_file, 'r') as f:
                lines_list = f.readlines()
                return lines_list[-lines:] if len(lines_list) > lines else lines_list
        except FileNotFoundError:
            return [f"Log file not found for {service_name}"]
        except Exception as e:
            return [f"Error reading logs for {service_name}: {e}"]

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CereBro Service Manager')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--duration', type=int, default=300, help='Run duration in seconds (default: 300)')
    parser.add_argument('--status', action='store_true', help='Show service status and exit')
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        try:
            import json
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return
    
    # Create service manager
    manager = ServiceManager(config=config)
    
    if args.status:
        # Show status and exit
        status = manager.get_service_status()
        print("\nService Status:")
        print("=" * 80)
        for service_name, info in status.items():
            print(f"{info['name']:20} | {info['status']:12} | Restarts: {info['restart_count']}/{info['max_restarts']}")
            if info['uptime']:
                print(f"{'':20} | Uptime: {info['uptime']}")
            if info['last_error']:
                print(f"{'':20} | Error: {info['last_error']}")
        return
    
    try:
        print("Starting CereBro Service Manager...")
        manager.start_all()
        
        # Run for specified duration
        print(f"Running for {args.duration} seconds...")
        time.sleep(args.duration)
        
        print("Shutting down...")
        manager.shutdown()
        
        # Show final status
        status = manager.get_service_status()
        print("\nFinal Service Status:")
        print("=" * 80)
        for service_name, info in status.items():
            print(f"{info['name']:20} | {info['status']:12} | Restarts: {info['restart_count']}/{info['max_restarts']}")
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        manager.shutdown()
    except Exception as e:
        print(f"\nError: {e}")
        manager.shutdown()

if __name__ == "__main__":
    main()
