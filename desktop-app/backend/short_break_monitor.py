#!/usr/bin/env python3
"""
Short Break Monitor for Mental Burnout Tracker
Monitors user inactivity over short durations (2-15 minutes) and logs them as breaks.
Optionally detects system lock/unlock events.
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import platform
import os
import json

# Platform-specific imports
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    import win32api
    import win32con
    import win32gui
    import win32process
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

class ShortBreakMonitor:
    """Monitor short breaks (2-15 minutes of inactivity)"""
    
    def __init__(self, db_path: str = "short_breaks.db", 
                 min_break_seconds: int = 120,  # 2 minutes
                 max_break_seconds: int = 900,  # 15 minutes
                 check_interval: float = 1.0,
                 enable_lock_detection: bool = True):
        """
        Initialize the short break monitor
        
        Args:
            db_path: Path to SQLite database file
            min_break_seconds: Minimum seconds of inactivity to consider a break
            max_break_seconds: Maximum seconds before considering it a long idle period
            check_interval: How often to check for activity (seconds)
            enable_lock_detection: Whether to detect system lock/unlock events
        """
        self.db_path = db_path
        self.min_break_seconds = min_break_seconds
        self.max_break_seconds = max_break_seconds
        self.check_interval = check_interval
        self.enable_lock_detection = enable_lock_detection
        self.is_running = False
        self.monitor_thread = None
        self.last_activity_time = time.time()
        self.current_break_start = None
        self.is_in_break = False
        self.system_locked = False
        self.last_lock_state = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('short_break_monitor.log'),
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
            self.logger.info("Initializing Windows short break monitor")
            self._setup_windows()
        elif self.system == "Darwin":
            if Quartz is None:
                raise ImportError("Quartz module not available for macOS")
            self.logger.info("Initializing macOS short break monitor")
            self._setup_macos()
        elif self.system == "Linux":
            if Xlib is None:
                raise ImportError("Xlib module not available for Linux")
            self.logger.info("Initializing Linux short break monitor")
            self._setup_linux()
        else:
            raise NotImplementedError(f"Unsupported operating system: {self.system}")
    
    def _setup_windows(self):
        """Setup Windows-specific components"""
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
        """Initialize SQLite database with short breaks table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create short breaks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS short_breaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    break_start TIMESTAMP NOT NULL,
                    break_end TIMESTAMP,
                    duration_seconds REAL,
                    system_locked BOOLEAN DEFAULT FALSE,
                    lock_start TIMESTAMP,
                    lock_end TIMESTAMP,
                    lock_duration_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create system locks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_start TIMESTAMP NOT NULL,
                    lock_end TIMESTAMP,
                    duration_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_break_start 
                ON short_breaks(break_start)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_break_duration 
                ON short_breaks(duration_seconds)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_lock_start 
                ON system_locks(lock_start)
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
    
    def _check_system_lock_windows(self) -> bool:
        """Check if system is locked on Windows"""
        try:
            # Check if the workstation is locked
            # This is a simplified check - in production you might want more sophisticated detection
            return False  # Placeholder
        except Exception as e:
            self.logger.error(f"Error checking Windows system lock: {e}")
            return False
    
    def _check_system_lock_macos(self) -> bool:
        """Check if system is locked on macOS"""
        try:
            # Check if the screen is locked on macOS
            return False  # Placeholder
        except Exception as e:
            self.logger.error(f"Error checking macOS system lock: {e}")
            return False
    
    def _check_system_lock_linux(self) -> bool:
        """Check if system is locked on Linux"""
        try:
            # Check if the screen is locked on Linux
            return False  # Placeholder
        except Exception as e:
            self.logger.error(f"Error checking Linux system lock: {e}")
            return False
    
    def _check_system_lock(self) -> bool:
        """Check if system is locked based on platform"""
        if not self.enable_lock_detection:
            return False
            
        if self.system == "Windows":
            return self._check_system_lock_windows()
        elif self.system == "Darwin":
            return self._check_system_lock_macos()
        elif self.system == "Linux":
            return self._check_system_lock_linux()
        else:
            return False
    
    def _check_activity(self) -> bool:
        """Check if user is currently active"""
        try:
            # Get last input time
            last_input_time = self._get_last_input_time()
            
            if last_input_time is not None:
                # If we can get last input time from system
                return last_input_time < self.min_break_seconds
            else:
                # Fallback: use our own tracking
                time_since_last_activity = time.time() - self.last_activity_time
                return time_since_last_activity < self.min_break_seconds
                
        except Exception as e:
            self.logger.error(f"Error checking activity: {e}")
            return True  # Assume active on error
    
    def _log_short_break(self, break_start: datetime, break_end: datetime, 
                         duration: float, system_locked: bool = False,
                         lock_start: Optional[datetime] = None,
                         lock_end: Optional[datetime] = None,
                         lock_duration: Optional[float] = None):
        """Log short break to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO short_breaks 
                (break_start, break_end, duration_seconds, system_locked, 
                 lock_start, lock_end, lock_duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (break_start, break_end, duration, system_locked, 
                  lock_start, lock_end, lock_duration))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged short break: {duration:.1f}s ({break_start} to {break_end})")
            
        except Exception as e:
            self.logger.error(f"Failed to log short break: {e}")
    
    def _log_system_lock(self, lock_start: datetime, lock_end: Optional[datetime] = None,
                         duration: Optional[float] = None):
        """Log system lock event to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_locks 
                (lock_start, lock_end, duration_seconds)
                VALUES (?, ?, ?)
            ''', (lock_start, lock_end, duration))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged system lock: {lock_start}")
            
        except Exception as e:
            self.logger.error(f"Failed to log system lock: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Short break monitoring started")
        
        while self.is_running:
            try:
                current_time = time.time()
                is_active = self._check_activity()
                current_lock_state = self._check_system_lock()
                
                # Handle system lock/unlock events
                if self.enable_lock_detection and current_lock_state != self.last_lock_state:
                    if current_lock_state:
                        # System just locked
                        self.system_locked = True
                        lock_start = datetime.now()
                        self.logger.info("System locked")
                        self._log_system_lock(lock_start)
                    else:
                        # System just unlocked
                        self.system_locked = False
                        lock_end = datetime.now()
                        self.logger.info("System unlocked")
                        # Update the last lock record with end time
                        self._update_last_lock_end(lock_end)
                
                self.last_lock_state = current_lock_state
                
                if is_active:
                    # User is active
                    if self.is_in_break:
                        # User just became active after being in a break
                        break_end = datetime.now()
                        duration = (break_end - self.current_break_start).total_seconds()
                        
                        # Only log if it's within our short break range
                        if self.min_break_seconds <= duration <= self.max_break_seconds:
                            self._log_short_break(
                                self.current_break_start, break_end, duration,
                                self.system_locked
                            )
                        else:
                            self.logger.info(f"Break duration {duration:.1f}s outside range ({self.min_break_seconds}-{self.max_break_seconds}s)")
                        
                        self.is_in_break = False
                        self.current_break_start = None
                        self.logger.info(f"User became active after {duration:.1f}s break")
                    
                    # Update last activity time
                    self.last_activity_time = current_time
                    
                else:
                    # User is inactive
                    if not self.is_in_break:
                        # User just became inactive
                        self.is_in_break = True
                        self.current_break_start = datetime.now()
                        self.logger.info(f"User started break (min: {self.min_break_seconds}s)")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _update_last_lock_end(self, lock_end: datetime):
        """Update the last system lock record with end time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the most recent lock record without an end time
            cursor.execute('''
                UPDATE system_locks 
                SET lock_end = ?, duration_seconds = ?
                WHERE id = (
                    SELECT id FROM system_locks 
                    WHERE lock_end IS NULL 
                    ORDER BY lock_start DESC 
                    LIMIT 1
                )
            ''', (lock_end, (lock_end - datetime.now()).total_seconds()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to update lock end time: {e}")
    
    def start(self):
        """Start short break monitoring"""
        if self.is_running:
            self.logger.warning("Short break monitor is already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Short break monitor started")
    
    def stop(self):
        """Stop short break monitoring"""
        if not self.is_running:
            self.logger.warning("Short break monitor is not running")
            return
        
        self.is_running = False
        
        # Log final break if user is currently in a break
        if self.is_in_break and self.current_break_start:
            break_end = datetime.now()
            duration = (break_end - self.current_break_start).total_seconds()
            
            if self.min_break_seconds <= duration <= self.max_break_seconds:
                self._log_short_break(
                    self.current_break_start, break_end, duration,
                    self.system_locked
                )
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Short break monitor stopped")
    
    def get_recent_breaks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent short breaks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get breaks from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT break_start, break_end, duration_seconds, system_locked,
                       lock_start, lock_end, lock_duration_seconds
                FROM short_breaks
                WHERE break_start >= ?
                ORDER BY break_start DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            breaks = []
            for row in results:
                breaks.append({
                    'break_start': row[0],
                    'break_end': row[1],
                    'duration_seconds': row[2],
                    'system_locked': bool(row[3]),
                    'lock_start': row[4],
                    'lock_end': row[5],
                    'lock_duration_seconds': row[6]
                })
            
            return breaks
            
        except Exception as e:
            self.logger.error(f"Failed to get recent breaks: {e}")
            return []
    
    def get_break_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of short break activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_breaks,
                    SUM(duration_seconds) as total_break_time,
                    AVG(duration_seconds) as avg_break_duration,
                    MAX(duration_seconds) as max_break_duration,
                    MIN(duration_seconds) as min_break_duration,
                    SUM(CASE WHEN system_locked = 1 THEN 1 ELSE 0 END) as breaks_with_lock
                FROM short_breaks
                WHERE break_start >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                total_breaks, total_time, avg_duration, max_duration, min_duration, breaks_with_lock = result
                
                return {
                    'total_breaks': total_breaks,
                    'total_break_time': total_time or 0,
                    'avg_break_duration': avg_duration or 0,
                    'max_break_duration': max_duration or 0,
                    'min_break_duration': min_duration or 0,
                    'breaks_with_lock': breaks_with_lock or 0,
                    'hours_analyzed': hours
                }
            else:
                return {
                    'total_breaks': 0,
                    'total_break_time': 0,
                    'avg_break_duration': 0,
                    'max_break_duration': 0,
                    'min_break_duration': 0,
                    'breaks_with_lock': 0,
                    'hours_analyzed': hours
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get break summary: {e}")
            return {
                'total_breaks': 0,
                'total_break_time': 0,
                'avg_break_duration': 0,
                'max_break_duration': 0,
                'min_break_duration': 0,
                'breaks_with_lock': 0,
                'hours_analyzed': hours
            }
    
    def export_to_csv(self, csv_path: str, hours: int = 24):
        """Export short breaks to CSV file"""
        try:
            import csv
            
            breaks = self.get_recent_breaks(hours)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['break_start', 'break_end', 'duration_seconds', 
                             'system_locked', 'lock_start', 'lock_end', 'lock_duration_seconds']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for break_data in breaks:
                    writer.writerow(break_data)
            
            self.logger.info(f"Exported {len(breaks)} short breaks to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Short Break Monitor')
    parser.add_argument('--min-break', type=int, default=120, 
                       help='Minimum break duration in seconds (default: 120)')
    parser.add_argument('--max-break', type=int, default=900, 
                       help='Maximum break duration in seconds (default: 900)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Check interval in seconds (default: 1.0)')
    parser.add_argument('--db', type=str, default='short_breaks.db',
                       help='Database file path (default: short_breaks.db)')
    parser.add_argument('--duration', type=int, default=300,
                       help='Run duration in seconds (default: 300)')
    parser.add_argument('--no-lock-detection', action='store_true',
                       help='Disable system lock detection')
    parser.add_argument('--export-csv', type=str, default=None,
                       help='Export to CSV file after completion')
    
    args = parser.parse_args()
    
    monitor = ShortBreakMonitor(
        db_path=args.db,
        min_break_seconds=args.min_break,
        max_break_seconds=args.max_break,
        check_interval=args.interval,
        enable_lock_detection=not args.no_lock_detection
    )
    
    try:
        print(f"Starting short break monitor...")
        print(f"Break range: {args.min_break}-{args.max_break} seconds")
        print(f"Lock detection: {'Enabled' if not args.no_lock_detection else 'Disabled'}")
        monitor.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping short break monitor...")
        monitor.stop()
        
        # Show results
        print("\n" + "=" * 50)
        print("SHORT BREAKS:")
        breaks = monitor.get_recent_breaks(hours=1)
        
        if breaks:
            for break_data in breaks:
                print(f"• {break_data['break_start']} to {break_data['break_end']}: "
                      f"{break_data['duration_seconds']:.1f}s "
                      f"{'(locked)' if break_data['system_locked'] else ''}")
        else:
            print("No short breaks recorded.")
        
        print("\n" + "=" * 50)
        print("BREAK SUMMARY:")
        summary = monitor.get_break_summary(hours=1)
        
        print(f"Total breaks: {summary['total_breaks']}")
        print(f"Total break time: {summary['total_break_time']:.1f}s")
        print(f"Average duration: {summary['avg_break_duration']:.1f}s")
        print(f"Max duration: {summary['max_break_duration']:.1f}s")
        print(f"Min duration: {summary['min_break_duration']:.1f}s")
        print(f"Breaks with system lock: {summary['breaks_with_lock']}")
        
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