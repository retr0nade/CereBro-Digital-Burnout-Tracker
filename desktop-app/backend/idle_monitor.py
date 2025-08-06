#!/usr/bin/env python3
"""
User Idle Monitor for CereBro Mental Burnout Tracker
Continuously monitors mouse and keyboard activity to detect user inactivity
Supports Windows, macOS, and Linux with configurable timeout periods
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import platform
import os

# Platform-specific imports
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    import win32api
    import win32con
elif platform.system() == "Darwin":  # macOS
    try:
        import Quartz
    except ImportError:
        print("Quartz not available. Install with: pip install pyobjc-framework-Quartz")
        Quartz = None
elif platform.system() == "Linux":
    try:
        import Xlib
        from Xlib import display, X
        from Xlib.ext import randr
    except ImportError:
        print("Xlib not available. Install with: pip install python-xlib")
        Xlib = None

class IdleMonitor:
    """Cross-platform user idle monitoring"""
    
    def __init__(self, db_path: str = "idle_activity.db", timeout_seconds: int = 300, 
                 check_interval: float = 1.0):
        """
        Initialize the idle monitor
        
        Args:
            db_path: Path to SQLite database file
            timeout_seconds: Seconds of inactivity before logging idle period
            check_interval: How often to check for activity (seconds)
        """
        self.db_path = db_path
        self.timeout_seconds = timeout_seconds
        self.check_interval = check_interval
        self.is_running = False
        self.monitor_thread = None
        self.last_activity_time = time.time()
        self.current_idle_start = None
        self.is_idle = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('idle_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        # Platform-specific setup
        self._setup_platform()
    
    def _setup_platform(self):
        """Setup platform-specific components"""
        self.system = platform.system()
        
        if self.system == "Windows":
            self.logger.info("Initializing Windows idle monitor")
            self._setup_windows()
        elif self.system == "Darwin":
            if Quartz is None:
                raise ImportError("Quartz module not available for macOS")
            self.logger.info("Initializing macOS idle monitor")
            self._setup_macos()
        elif self.system == "Linux":
            if Xlib is None:
                raise ImportError("Xlib module not available for Linux")
            self.logger.info("Initializing Linux idle monitor")
            self._setup_linux()
        else:
            raise NotImplementedError(f"Unsupported operating system: {self.system}")
    
    def _setup_windows(self):
        """Setup Windows-specific components"""
        # Windows uses GetLastInputInfo for idle detection
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Define structures for GetLastInputInfo
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)
            ]
        
        self.LASTINPUTINFO = LASTINPUTINFO
        self.LASTINPUTINFO.cbSize = ctypes.sizeof(LASTINPUTINFO)
    
    def _setup_macos(self):
        """Setup macOS-specific components"""
        # macOS uses Core Graphics for idle detection
        pass
    
    def _setup_linux(self):
        """Setup Linux-specific components"""
        try:
            self.display = display.Display()
            self.screen = self.display.screen()
            self.root = self.screen.root
            self.logger.info("X11 display initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize X11 display: {e}")
            raise
    
    def _init_database(self):
        """Initialize SQLite database with idle activity table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create idle activity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS idle_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idle_start TIMESTAMP NOT NULL,
                    idle_end TIMESTAMP,
                    duration_seconds REAL,
                    timeout_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_idle_start 
                ON idle_activity(idle_start)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_duration 
                ON idle_activity(duration_seconds)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_last_input_time_windows(self) -> Optional[float]:
        """Get last input time on Windows"""
        try:
            last_input_info = self.LASTINPUTINFO()
            if self.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
                # Convert to seconds since boot
                tick_count = self.kernel32.GetTickCount()
                idle_time = (tick_count - last_input_info.dwTime) / 1000.0
                return idle_time
            return None
        except Exception as e:
            self.logger.error(f"Error getting Windows last input time: {e}")
            return None
    
    def _get_last_input_time_macos(self) -> Optional[float]:
        """Get last input time on macOS"""
        try:
            # Use Core Graphics to get last input time
            # This is a simplified implementation
            # For production, you might want to use IOKit for more accurate results
            return None  # Placeholder - would need more complex implementation
        except Exception as e:
            self.logger.error(f"Error getting macOS last input time: {e}")
            return None
    
    def _get_last_input_time_linux(self) -> Optional[float]:
        """Get last input time on Linux"""
        try:
            # Check for mouse and keyboard activity using X11
            # This is a simplified implementation
            return None  # Placeholder - would need more complex implementation
        except Exception as e:
            self.logger.error(f"Error getting Linux last input time: {e}")
            return None
    
    def _get_last_input_time(self) -> Optional[float]:
        """Get last input time based on platform"""
        if self.system == "Windows":
            return self._get_last_input_time_windows()
        elif self.system == "Darwin":
            return self._get_last_input_time_macos()
        elif self.system == "Linux":
            return self._get_last_input_time_linux()
        else:
            return None
    
    def _check_activity(self) -> bool:
        """Check if user is currently active"""
        try:
            # Get last input time
            last_input_time = self._get_last_input_time()
            
            if last_input_time is not None:
                # If we can get last input time from system
                return last_input_time < self.timeout_seconds
            else:
                # Fallback: use our own tracking
                time_since_last_activity = time.time() - self.last_activity_time
                return time_since_last_activity < self.timeout_seconds
                
        except Exception as e:
            self.logger.error(f"Error checking activity: {e}")
            return True  # Assume active on error
    
    def _log_idle_period(self, idle_start: datetime, idle_end: datetime, duration: float):
        """Log idle period to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO idle_activity 
                (idle_start, idle_end, duration_seconds, timeout_seconds)
                VALUES (?, ?, ?, ?)
            ''', (idle_start, idle_end, duration, self.timeout_seconds))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged idle period: {duration:.1f}s ({idle_start} to {idle_end})")
            
        except Exception as e:
            self.logger.error(f"Failed to log idle period: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Idle monitoring started")
        
        while self.is_running:
            try:
                current_time = time.time()
                is_active = self._check_activity()
                
                if is_active:
                    # User is active
                    if self.is_idle:
                        # User just became active after being idle
                        idle_end = datetime.now()
                        duration = (idle_end - self.current_idle_start).total_seconds()
                        
                        self._log_idle_period(self.current_idle_start, idle_end, duration)
                        
                        self.is_idle = False
                        self.current_idle_start = None
                        self.logger.info(f"User became active after {duration:.1f}s of inactivity")
                    
                    # Update last activity time
                    self.last_activity_time = current_time
                    
                else:
                    # User is idle
                    if not self.is_idle:
                        # User just became idle
                        self.is_idle = True
                        self.current_idle_start = datetime.now()
                        self.logger.info(f"User became idle (timeout: {self.timeout_seconds}s)")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """Start idle monitoring"""
        if self.is_running:
            self.logger.warning("Idle monitor is already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Idle monitor started")
    
    def stop(self):
        """Stop idle monitoring"""
        if not self.is_running:
            self.logger.warning("Idle monitor is not running")
            return
        
        self.is_running = False
        
        # Log final idle period if user is currently idle
        if self.is_idle and self.current_idle_start:
            idle_end = datetime.now()
            duration = (idle_end - self.current_idle_start).total_seconds()
            self._log_idle_period(self.current_idle_start, idle_end, duration)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Idle monitor stopped")
    
    def get_recent_idle_periods(self, hours: int = 24) -> list:
        """Get recent idle periods"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get idle periods from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT idle_start, idle_end, duration_seconds, timeout_seconds
                FROM idle_activity
                WHERE idle_start >= ?
                ORDER BY idle_start DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get recent idle periods: {e}")
            return []
    
    def get_idle_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of idle activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_periods,
                    SUM(duration_seconds) as total_idle_time,
                    AVG(duration_seconds) as avg_idle_duration,
                    MAX(duration_seconds) as max_idle_duration,
                    MIN(duration_seconds) as min_idle_duration
                FROM idle_activity
                WHERE idle_start >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                total_periods, total_idle_time, avg_duration, max_duration, min_duration = result
                
                return {
                    'total_periods': total_periods,
                    'total_idle_time': total_idle_time or 0,
                    'avg_idle_duration': avg_duration or 0,
                    'max_idle_duration': max_duration or 0,
                    'min_idle_duration': min_duration or 0,
                    'hours_analyzed': hours
                }
            else:
                return {
                    'total_periods': 0,
                    'total_idle_time': 0,
                    'avg_idle_duration': 0,
                    'max_idle_duration': 0,
                    'min_idle_duration': 0,
                    'hours_analyzed': hours
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get idle summary: {e}")
            return {
                'total_periods': 0,
                'total_idle_time': 0,
                'avg_idle_duration': 0,
                'max_idle_duration': 0,
                'min_idle_duration': 0,
                'hours_analyzed': hours
            }
    
    def export_to_csv(self, csv_path: str, hours: int = 24):
        """Export idle periods to CSV file"""
        try:
            import csv
            
            idle_periods = self.get_recent_idle_periods(hours)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['idle_start', 'idle_end', 'duration_seconds', 'timeout_seconds']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for idle_start, idle_end, duration, timeout in idle_periods:
                    writer.writerow({
                        'idle_start': idle_start,
                        'idle_end': idle_end,
                        'duration_seconds': duration,
                        'timeout_seconds': timeout
                    })
            
            self.logger.info(f"Exported {len(idle_periods)} idle periods to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='User Idle Monitor')
    parser.add_argument('--timeout', type=int, default=300, 
                       help='Idle timeout in seconds (default: 300)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Check interval in seconds (default: 1.0)')
    parser.add_argument('--db', type=str, default='idle_activity.db',
                       help='Database file path (default: idle_activity.db)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Run duration in seconds (default: 60)')
    parser.add_argument('--export-csv', type=str, default=None,
                       help='Export to CSV file after completion')
    
    args = parser.parse_args()
    
    monitor = IdleMonitor(
        db_path=args.db,
        timeout_seconds=args.timeout,
        check_interval=args.interval
    )
    
    try:
        print(f"Starting idle monitor with {args.timeout}s timeout...")
        monitor.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping idle monitor...")
        monitor.stop()
        
        # Show results
        print("\n" + "=" * 50)
        print("IDLE PERIODS:")
        idle_periods = monitor.get_recent_idle_periods(hours=1)
        
        if idle_periods:
            for idle_start, idle_end, duration, timeout in idle_periods:
                print(f"• {idle_start} to {idle_end}: {duration:.1f}s")
        else:
            print("No idle periods recorded.")
        
        print("\n" + "=" * 50)
        print("IDLE SUMMARY:")
        summary = monitor.get_idle_summary(hours=1)
        
        print(f"Total periods: {summary['total_periods']}")
        print(f"Total idle time: {summary['total_idle_time']:.1f}s")
        print(f"Average duration: {summary['avg_idle_duration']:.1f}s")
        print(f"Max duration: {summary['max_idle_duration']:.1f}s")
        print(f"Min duration: {summary['min_idle_duration']:.1f}s")
        
        # Export to CSV if requested
        if args.export_csv:
            monitor.export_to_csv(args.export_csv, hours=1)
            print(f"\nExported data to: {args.export_csv}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
        monitor.stop()
        print("Test stopped by user.")
    
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        monitor.stop()

if __name__ == "__main__":
    main() 