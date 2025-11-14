#!/usr/bin/env python3
"""
Simple Break Monitor
A lightweight Python script that monitors user inactivity over short durations (2-15 minutes) 
and logs them as breaks. Optionally detects system lock/unlock events.

This is a simplified version focusing on the core functionality.
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import platform

# Platform-specific imports
# Windows-only MVP implementation
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
# elif platform.system() == "Darwin":  # macOS
#     try:
#         import Quartz
#     except ImportError:
#         Quartz = None
# elif platform.system() == "Linux":
#     try:
#         import Xlib
#         from Xlib import display, X
#     except ImportError:
#         Xlib = None

class SimpleBreakMonitor:
    """Simple monitor for short breaks (2-15 minutes of inactivity)"""
    
    def __init__(self, 
                 min_break_seconds: int = 120,  # 2 minutes
                 max_break_seconds: int = 900,  # 15 minutes
                 check_interval: float = 1.0,
                 enable_lock_detection: bool = True,
                 db_path: str = "simple_breaks.db"):
        """
        Initialize the simple break monitor
        
        Args:
            min_break_seconds: Minimum seconds of inactivity to consider a break
            max_break_seconds: Maximum seconds before considering it a long idle period
            check_interval: How often to check for activity (seconds)
            enable_lock_detection: Whether to detect system lock/unlock events
            db_path: Path to SQLite database file
        """
        self.min_break_seconds = min_break_seconds
        self.max_break_seconds = max_break_seconds
        self.check_interval = check_interval
        self.enable_lock_detection = enable_lock_detection
        self.db_path = db_path
        
        # State variables
        self.is_running = False
        self.monitor_thread = None
        self.last_activity_time = time.time()
        self.current_break_start = None
        self.is_in_break = False
        self.system_locked = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('simple_break_monitor.log'),
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
            self.logger.info("Initializing Windows break monitor")
            self._setup_windows()
        elif self.system == "Darwin":
            if Quartz is None:
                self.logger.warning("Quartz not available for macOS - lock detection disabled")
                self.enable_lock_detection = False
            else:
                self.logger.info("Initializing macOS break monitor")
        elif self.system == "Linux":
            if Xlib is None:
                self.logger.warning("Xlib not available for Linux - lock detection disabled")
                self.enable_lock_detection = False
            else:
                self.logger.info("Initializing Linux break monitor")
        else:
            self.logger.warning(f"Unsupported OS: {self.system}")
    
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
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create breaks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    system_locked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create system locks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_time TIMESTAMP NOT NULL,
                    unlock_time TIMESTAMP,
                    duration_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_idle_time(self) -> Optional[float]:
        """Get system idle time in seconds"""
        try:
            if self.system == "Windows":
                return self._get_idle_time_windows()
            elif self.system == "Darwin":
                return self._get_idle_time_macos()
            elif self.system == "Linux":
                return self._get_idle_time_linux()
            else:
                # Fallback to our own tracking
                return time.time() - self.last_activity_time
        except Exception as e:
            self.logger.error(f"Error getting idle time: {e}")
            return None
    
    def _get_idle_time_windows(self) -> Optional[float]:
        """Get idle time on Windows"""
        try:
            last_input_info = self.LASTINPUTINFO()
            if self.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
                tick_count = self.kernel32.GetTickCount()
                idle_time = (tick_count - last_input_info.dwTime) / 1000.0
                return idle_time
            return None
        except Exception as e:
            self.logger.error(f"Error getting Windows idle time: {e}")
            return None
    
    def _get_idle_time_macos(self) -> Optional[float]:
        """Get idle time on macOS"""
        # Simplified implementation - would need more complex Core Graphics code
        return None
    
    def _get_idle_time_linux(self) -> Optional[float]:
        """Get idle time on Linux"""
        # Simplified implementation - would need more complex X11 code
        return None
    
    def _check_system_lock(self) -> bool:
        """Check if system is locked"""
        if not self.enable_lock_detection:
            return False
        
        # Simplified implementation - would need platform-specific code
        return False
    
    def _log_break(self, start_time: datetime, end_time: datetime, 
                   duration: float, system_locked: bool = False):
        """Log break to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO breaks 
                (start_time, end_time, duration_seconds, system_locked)
                VALUES (?, ?, ?, ?)
            ''', (start_time, end_time, duration, system_locked))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged break: {duration:.1f}s ({start_time} to {end_time})")
            
        except Exception as e:
            self.logger.error(f"Failed to log break: {e}")
    
    def _log_system_lock(self, lock_time: datetime, unlock_time: Optional[datetime] = None):
        """Log system lock event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            duration = None
            if unlock_time:
                duration = (unlock_time - lock_time).total_seconds()
            
            cursor.execute('''
                INSERT INTO system_locks 
                (lock_time, unlock_time, duration_seconds)
                VALUES (?, ?, ?)
            ''', (lock_time, unlock_time, duration))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged system lock: {lock_time}")
            
        except Exception as e:
            self.logger.error(f"Failed to log system lock: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Break monitoring started")
        
        while self.is_running:
            try:
                # Check for activity
                idle_time = self._get_idle_time()
                is_active = idle_time is None or idle_time < self.min_break_seconds
                
                # Check system lock state
                current_lock_state = self._check_system_lock()
                
                if is_active:
                    # User is active
                    if self.is_in_break:
                        # User just became active after being in a break
                        break_end = datetime.now()
                        duration = (break_end - self.current_break_start).total_seconds()
                        
                        # Only log if it's within our break range
                        if self.min_break_seconds <= duration <= self.max_break_seconds:
                            self._log_break(
                                self.current_break_start, break_end, duration,
                                self.system_locked
                            )
                        else:
                            self.logger.info(f"Break duration {duration:.1f}s outside range "
                                           f"({self.min_break_seconds}-{self.max_break_seconds}s)")
                        
                        self.is_in_break = False
                        self.current_break_start = None
                        self.logger.info(f"User became active after {duration:.1f}s break")
                    
                    # Update last activity time
                    self.last_activity_time = time.time()
                    
                else:
                    # User is inactive
                    if not self.is_in_break:
                        # User just became inactive
                        self.is_in_break = True
                        self.current_break_start = datetime.now()
                        self.logger.info(f"User started break (min: {self.min_break_seconds}s)")
                
                # Handle system lock/unlock events
                if current_lock_state != self.system_locked:
                    if current_lock_state:
                        # System just locked
                        self.system_locked = True
                        lock_time = datetime.now()
                        self.logger.info("System locked")
                        self._log_system_lock(lock_time)
                    else:
                        # System just unlocked
                        self.system_locked = False
                        unlock_time = datetime.now()
                        self.logger.info("System unlocked")
                        # Update the last lock record
                        self._update_last_lock_end(unlock_time)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _update_last_lock_end(self, unlock_time: datetime):
        """Update the last system lock record with unlock time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE system_locks 
                SET unlock_time = ?, duration_seconds = ?
                WHERE id = (
                    SELECT id FROM system_locks 
                    WHERE unlock_time IS NULL 
                    ORDER BY lock_time DESC 
                    LIMIT 1
                )
            ''', (unlock_time, (unlock_time - datetime.now()).total_seconds()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to update lock end time: {e}")
    
    def start(self):
        """Start break monitoring"""
        if self.is_running:
            self.logger.warning("Break monitor is already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Break monitor started")
    
    def stop(self):
        """Stop break monitoring"""
        if not self.is_running:
            self.logger.warning("Break monitor is not running")
            return
        
        self.is_running = False
        
        # Log final break if user is currently in a break
        if self.is_in_break and self.current_break_start:
            break_end = datetime.now()
            duration = (break_end - self.current_break_start).total_seconds()
            
            if self.min_break_seconds <= duration <= self.max_break_seconds:
                self._log_break(
                    self.current_break_start, break_end, duration,
                    self.system_locked
                )
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Break monitor stopped")
    
    def get_recent_breaks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent breaks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT start_time, end_time, duration_seconds, system_locked
                FROM breaks
                WHERE start_time >= ?
                ORDER BY start_time DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            breaks = []
            for row in results:
                breaks.append({
                    'start_time': row[0],
                    'end_time': row[1],
                    'duration_seconds': row[2],
                    'system_locked': bool(row[3])
                })
            
            return breaks
            
        except Exception as e:
            self.logger.error(f"Failed to get recent breaks: {e}")
            return []
    
    def get_break_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of break activity"""
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
                    MIN(duration_seconds) as min_break_duration
                FROM breaks
                WHERE start_time >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                total_breaks, total_time, avg_duration, max_duration, min_duration = result
                
                return {
                    'total_breaks': total_breaks,
                    'total_break_time': total_time or 0,
                    'avg_break_duration': avg_duration or 0,
                    'max_break_duration': max_duration or 0,
                    'min_break_duration': min_duration or 0,
                    'hours_analyzed': hours
                }
            else:
                return {
                    'total_breaks': 0,
                    'total_break_time': 0,
                    'avg_break_duration': 0,
                    'max_break_duration': 0,
                    'min_break_duration': 0,
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
                'hours_analyzed': hours
            }

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Break Monitor')
    parser.add_argument('--min-break', type=int, default=120, 
                       help='Minimum break duration in seconds (default: 120)')
    parser.add_argument('--max-break', type=int, default=900, 
                       help='Maximum break duration in seconds (default: 900)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Check interval in seconds (default: 1.0)')
    parser.add_argument('--duration', type=int, default=300,
                       help='Run duration in seconds (default: 300)')
    parser.add_argument('--no-lock-detection', action='store_true',
                       help='Disable system lock detection')
    parser.add_argument('--db', type=str, default='simple_breaks.db',
                       help='Database file path (default: simple_breaks.db)')
    
    args = parser.parse_args()
    
    monitor = SimpleBreakMonitor(
        db_path=args.db,
        min_break_seconds=args.min_break,
        max_break_seconds=args.max_break,
        check_interval=args.interval,
        enable_lock_detection=not args.no_lock_detection
    )
    
    try:
        print(f"Starting simple break monitor...")
        print(f"Break range: {args.min_break}-{args.max_break} seconds")
        print(f"Lock detection: {'Enabled' if not args.no_lock_detection else 'Disabled'}")
        monitor.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping break monitor...")
        monitor.stop()
        
        # Show results
        print("\n" + "=" * 50)
        print("BREAK RESULTS:")
        breaks = monitor.get_recent_breaks(hours=1)
        
        if breaks:
            for i, break_data in enumerate(breaks, 1):
                print(f"{i}. {break_data['start_time']} to {break_data['end_time']}: "
                      f"{break_data['duration_seconds']:.1f}s "
                      f"{'(locked)' if break_data['system_locked'] else ''}")
        else:
            print("No breaks recorded.")
        
        print("\n" + "=" * 50)
        print("BREAK SUMMARY:")
        summary = monitor.get_break_summary(hours=1)
        
        print(f"Total breaks: {summary['total_breaks']}")
        print(f"Total break time: {summary['total_break_time']:.1f}s")
        print(f"Average duration: {summary['avg_break_duration']:.1f}s")
        print(f"Max duration: {summary['max_break_duration']:.1f}s")
        print(f"Min duration: {summary['min_break_duration']:.1f}s")
        
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