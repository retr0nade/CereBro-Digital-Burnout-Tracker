#!/usr/bin/env python3
"""
Break Monitor for CereBro Mental Burnout Tracker
Monitors for user inactivity over short durations (2-15 minutes) and considers them breaks
Optionally detects system lock/unlock events and logs them
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import platform
import os
import signal
import sys

# Platform-specific imports for idle detection
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
        Quartz = None
elif platform.system() == "Linux":
    try:
        import Xlib
        from Xlib import display, X
    except ImportError:
        Xlib = None

class BreakMonitor:
    """Monitor for short user inactivity periods (breaks) and system lock events"""
    
    def __init__(self, db_path: str = "break_activity.db", 
                 min_break_duration: int = 120,  # 2 minutes minimum
                 max_break_duration: int = 900,  # 15 minutes maximum
                 check_interval: float = 1.0,  # Check every second
                 detect_lock_events: bool = True):  # Detect system lock/unlock
        """
        Initialize the break monitor
        
        Args:
            db_path: Path to SQLite database file
            min_break_duration: Minimum break duration in seconds (default: 120)
            max_break_duration: Maximum break duration in seconds (default: 900)
            check_interval: How often to check for activity in seconds
            detect_lock_events: Whether to detect system lock/unlock events
        """
        self.db_path = db_path
        self.min_break_duration = min_break_duration
        self.max_break_duration = max_break_duration
        self.check_interval = check_interval
        self.detect_lock_events = detect_lock_events
        
        # Monitoring state
        self.is_running = False
        self.monitor_thread = None
        self.lock_thread = None
        
        # Break tracking
        self.break_start = None
        self.break_duration = 0.0
        self.is_on_break = False
        
        # Lock tracking
        self.last_lock_state = None
        self.lock_events = []
        
        # Thread safety
        self.state_lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('break_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _init_database(self):
        """Initialize SQLite database with break activity tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create breaks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    break_start TIMESTAMP NOT NULL,
                    break_end TIMESTAMP,
                    duration_seconds REAL,
                    break_type TEXT DEFAULT 'inactivity',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create lock events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lock_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time TIMESTAMP NOT NULL,
                    event_type TEXT NOT NULL,
                    session_duration REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_breaks_start 
                ON breaks(break_start)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_breaks_duration 
                ON breaks(duration_seconds)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_lock_events_time 
                ON lock_events(event_time)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_last_input_time(self) -> Optional[float]:
        """Get the last input time from the system"""
        try:
            if platform.system() == "Windows":
                class LASTINPUTINFO(ctypes.Structure):
                    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
                
                last_input = LASTINPUTINFO()
                last_input.cbSize = ctypes.sizeof(last_input)
                
                if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input)):
                    return last_input.dwTime / 1000.0
                return None
                
            elif platform.system() == "Darwin" and Quartz:
                idle_time = Quartz.CGEventSourceSecondsSinceLastEventType(
                    Quartz.kCGEventSourceStateHIDSystemState,
                    Quartz.kCGEventSourceStateHIDSystemState
                )
                return time.time() - idle_time
                
            elif platform.system() == "Linux" and Xlib:
                # Linux implementation
                display_obj = display.Display()
                root = display_obj.screen().root
                root.change_attributes(event_mask=X.MotionNotifyMask)
                return time.time()  # Simplified for now
                
            else:
                return time.time()
                
        except Exception as e:
            self.logger.error(f"Error getting last input time: {e}")
            return time.time()
    
    def _check_activity(self) -> bool:
        """Check if the user is currently active"""
        try:
            last_input_time = self._get_last_input_time()
            if last_input_time is None:
                return True  # Assume active if we can't determine
            
            idle_time = time.time() - last_input_time
            return idle_time < 60  # Consider active if idle less than 1 minute
            
        except Exception as e:
            self.logger.error(f"Error checking activity: {e}")
            return True  # Assume active on error
    
    def _check_system_lock_state(self) -> Optional[str]:
        """Check if the system is currently locked"""
        try:
            if platform.system() == "Windows":
                # Windows: Check if workstation is locked
                try:
                    # Get the current session
                    session_id = ctypes.windll.kernel32.WTSGetActiveConsoleSessionId()
                    if session_id == 0xFFFFFFFF:
                        return "locked"
                    else:
                        return "unlocked"
                except:
                    # Fallback: Check if screensaver is active
                    try:
                        result = ctypes.windll.user32.SystemParametersInfoW(
                            win32con.SPI_GETSCREENSAVERRUNNING, 0, None, 0
                        )
                        if result:
                            return "locked"
                        else:
                            return "unlocked"
                    except:
                        return None
                        
            elif platform.system() == "Darwin" and Quartz:
                # macOS: Check if screen is locked
                try:
                    # This is a simplified check - in practice you'd need more complex logic
                    return "unlocked"  # Placeholder
                except:
                    return None
                    
            elif platform.system() == "Linux":
                # Linux: Check if screen is locked
                try:
                    # This would require checking X11 session state
                    return "unlocked"  # Placeholder
                except:
                    return None
                    
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking system lock state: {e}")
            return None
    
    def _log_break(self, break_start: datetime, break_end: datetime, 
                   duration: float, break_type: str = "inactivity", notes: str = ""):
        """Log a break to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO breaks (break_start, break_end, duration_seconds, break_type, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (break_start, break_end, duration, break_type, notes))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged break: {duration:.1f}s ({break_type})")
            
        except Exception as e:
            self.logger.error(f"Failed to log break: {e}")
    
    def _log_lock_event(self, event_time: datetime, event_type: str, 
                       session_duration: float = 0.0, notes: str = ""):
        """Log a lock event to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO lock_events (event_time, event_type, session_duration, notes)
                VALUES (?, ?, ?, ?)
            ''', (event_time, event_type, session_duration, notes))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged lock event: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to log lock event: {e}")
    
    def _monitor_breaks(self):
        """Monitor for user inactivity breaks"""
        while self.is_running:
            try:
                is_active = self._check_activity()
                current_time = datetime.now()
                
                with self.state_lock:
                    if not is_active and not self.is_on_break:
                        # Starting a potential break
                        self.break_start = current_time
                        self.is_on_break = True
                        self.break_duration = 0.0
                        self.logger.info("Break started - user inactive")
                        
                    elif is_active and self.is_on_break:
                        # Ending break
                        if self.break_start:
                            break_duration = (current_time - self.break_start).total_seconds()
                            
                            # Only log if break meets minimum duration criteria
                            if break_duration >= self.min_break_duration:
                                self._log_break(
                                    self.break_start, 
                                    current_time, 
                                    break_duration,
                                    "inactivity",
                                    f"Break ended by user activity"
                                )
                            else:
                                self.logger.info(f"Short inactivity period ignored: {break_duration:.1f}s")
                        
                        self.is_on_break = False
                        self.break_start = None
                        self.break_duration = 0.0
                        self.logger.info("Break ended - user active")
                        
                    elif self.is_on_break and self.break_start:
                        # Update break duration
                        self.break_duration = (current_time - self.break_start).total_seconds()
                        
                        # Check if break exceeds maximum duration
                        if self.break_duration >= self.max_break_duration:
                            self._log_break(
                                self.break_start,
                                current_time,
                                self.break_duration,
                                "inactivity",
                                f"Break exceeded maximum duration ({self.max_break_duration}s)"
                            )
                            self.is_on_break = False
                            self.break_start = None
                            self.break_duration = 0.0
                            self.logger.info(f"Break logged (max duration): {self.break_duration:.1f}s")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in break monitoring: {e}")
                time.sleep(1)
    
    def _monitor_lock_events(self):
        """Monitor for system lock/unlock events"""
        if not self.detect_lock_events:
            return
            
        while self.is_running:
            try:
                current_lock_state = self._check_system_lock_state()
                current_time = datetime.now()
                
                if current_lock_state is not None:
                    with self.state_lock:
                        if self.last_lock_state is None:
                            # First check
                            self.last_lock_state = current_lock_state
                        elif current_lock_state != self.last_lock_state:
                            # Lock state changed
                            event_type = f"system_{current_lock_state}"
                            
                            self._log_lock_event(
                                current_time,
                                event_type,
                                0.0,
                                f"System {current_lock_state}"
                            )
                            
                            self.last_lock_state = current_lock_state
                            self.logger.info(f"System {current_lock_state}")
                
                time.sleep(5)  # Check lock state every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in lock monitoring: {e}")
                time.sleep(5)
    
    def start(self):
        """Start break monitoring"""
        if self.is_running:
            raise RuntimeError("Break monitor already running")
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_breaks, daemon=True)
        self.monitor_thread.start()
        
        if self.detect_lock_events:
            self.lock_thread = threading.Thread(target=self._monitor_lock_events, daemon=True)
            self.lock_thread.start()
        
        self.logger.info("Break monitor started")
    
    def stop(self):
        """Stop break monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Log any ongoing break
        if self.is_on_break and self.break_start:
            current_time = datetime.now()
            break_duration = (current_time - self.break_start).total_seconds()
            
            if break_duration >= self.min_break_duration:
                self._log_break(
                    self.break_start,
                    current_time,
                    break_duration,
                    "inactivity",
                    "Break ended by monitor shutdown"
                )
        
        # Wait for threads to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.lock_thread:
            self.lock_thread.join(timeout=5)
        
        self.logger.info("Break monitor stopped")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        with self.state_lock:
            return {
                'running': self.is_running,
                'is_on_break': self.is_on_break,
                'break_start': self.break_start.isoformat() if self.break_start else None,
                'break_duration': self.break_duration,
                'last_lock_state': self.last_lock_state
            }
    
    def get_recent_breaks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent breaks from the last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT break_start, break_end, duration_seconds, break_type, notes
                FROM breaks
                WHERE break_start >= ?
                ORDER BY break_start DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            breaks = []
            for (break_start, break_end, duration_seconds, break_type, notes) in results:
                breaks.append({
                    'break_start': break_start,
                    'break_end': break_end,
                    'duration_seconds': duration_seconds,
                    'break_type': break_type,
                    'notes': notes,
                    'duration_minutes': duration_seconds / 60.0
                })
            
            return breaks
            
        except Exception as e:
            self.logger.error(f"Failed to get recent breaks: {e}")
            return []
    
    def get_recent_lock_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent lock events from the last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT event_time, event_type, session_duration, notes
                FROM lock_events
                WHERE event_time >= ?
                ORDER BY event_time DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            events = []
            for (event_time, event_type, session_duration, notes) in results:
                events.append({
                    'event_time': event_time,
                    'event_type': event_type,
                    'session_duration': session_duration,
                    'notes': notes
                })
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get recent lock events: {e}")
            return []
    
    def get_break_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get break statistics from the last N hours"""
        try:
            breaks = self.get_recent_breaks(hours)
            
            if not breaks:
                return {
                    'total_breaks': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'shortest_break': 0,
                    'longest_break': 0,
                    'break_types': {}
                }
            
            total_breaks = len(breaks)
            total_duration = sum(b['duration_seconds'] for b in breaks)
            durations = [b['duration_seconds'] for b in breaks]
            break_types = {}
            
            for break_item in breaks:
                break_type = break_item['break_type']
                if break_type not in break_types:
                    break_types[break_type] = 0
                break_types[break_type] += 1
            
            return {
                'total_breaks': total_breaks,
                'total_duration': total_duration,
                'avg_duration': total_duration / total_breaks if total_breaks > 0 else 0,
                'shortest_break': min(durations) if durations else 0,
                'longest_break': max(durations) if durations else 0,
                'break_types': break_types
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get break statistics: {e}")
            return {}
    
    def export_to_csv(self, csv_path: str, hours: int = 24):
        """Export break data to CSV"""
        try:
            import csv
            
            breaks = self.get_recent_breaks(hours)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['break_start', 'break_end', 'duration_seconds', 
                            'duration_minutes', 'break_type', 'notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for break_item in breaks:
                    writer.writerow(break_item)
            
            self.logger.info(f"Exported {len(breaks)} breaks to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Break Monitor')
    parser.add_argument('--min-duration', type=int, default=120, 
                       help='Minimum break duration in seconds (default: 120)')
    parser.add_argument('--max-duration', type=int, default=900, 
                       help='Maximum break duration in seconds (default: 900)')
    parser.add_argument('--check-interval', type=float, default=1.0, 
                       help='Check interval in seconds (default: 1.0)')
    parser.add_argument('--db', type=str, default='break_activity.db', 
                       help='Database file path')
    parser.add_argument('--no-lock-events', action='store_true', 
                       help='Disable lock event detection')
    parser.add_argument('--show-stats', action='store_true', 
                       help='Show break statistics')
    parser.add_argument('--export-csv', type=str, default=None, 
                       help='Export to CSV file')
    parser.add_argument('--duration', type=int, default=0, 
                       help='Run for specified duration in seconds (0 = run indefinitely)')
    
    args = parser.parse_args()
    
    monitor = BreakMonitor(
        db_path=args.db,
        min_break_duration=args.min_duration,
        max_break_duration=args.max_duration,
        check_interval=args.check_interval,
        detect_lock_events=not args.no_lock_events
    )
    
    print("CereBro Break Monitor")
    print("=" * 40)
    print(f"Min break duration: {args.min_duration}s ({args.min_duration/60:.1f} minutes)")
    print(f"Max break duration: {args.max_duration}s ({args.max_duration/60:.1f} minutes)")
    print(f"Check interval: {args.check_interval}s")
    print(f"Lock event detection: {'Enabled' if not args.no_lock_events else 'Disabled'}")
    print("=" * 40)
    
    if args.show_stats:
        # Show statistics
        stats = monitor.get_break_statistics(24)
        print("\nBreak Statistics (Last 24 hours):")
        print(f"Total breaks: {stats['total_breaks']}")
        print(f"Total duration: {stats['total_duration']/60:.1f} minutes")
        print(f"Average duration: {stats['avg_duration']/60:.1f} minutes")
        print(f"Shortest break: {stats['shortest_break']/60:.1f} minutes")
        print(f"Longest break: {stats['longest_break']/60:.1f} minutes")
        
        if stats['break_types']:
            print("\nBreak types:")
            for break_type, count in stats['break_types'].items():
                print(f"  {break_type}: {count}")
        
        # Show recent breaks
        breaks = monitor.get_recent_breaks(24)
        if breaks:
            print("\nRecent Breaks:")
            for break_item in breaks[:5]:
                print(f"• {break_item['break_start']}: {break_item['duration_minutes']:.1f}min "
                      f"({break_item['break_type']})")
        
        # Show recent lock events
        if not args.no_lock_events:
            events = monitor.get_recent_lock_events(24)
            if events:
                print("\nRecent Lock Events:")
                for event in events[:5]:
                    print(f"• {event['event_time']}: {event['event_type']}")
        
        if args.export_csv:
            monitor.export_to_csv(args.export_csv, hours=24)
            print(f"\nExported data to: {args.export_csv}")
        
    else:
        # Interactive monitoring mode
        print("Starting break monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            monitor.start()
            
            # Monitor for specified duration or indefinitely
            if args.duration > 0:
                print(f"Running for {args.duration} seconds...")
                time.sleep(args.duration)
                monitor.stop()
                print("Monitoring completed.")
            else:
                # Run indefinitely
                while True:
                    status = monitor.get_current_status()
                    if status['is_on_break']:
                        print(f"\rBreak in progress: {status['break_duration']:.1f}s", end='', flush=True)
                    else:
                        print(f"\rMonitoring... (Last lock state: {status['last_lock_state']})", end='', flush=True)
                    time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\nStopping break monitor...")
            monitor.stop()
            print("Break monitor stopped.")
        
        # Show final statistics
        stats = monitor.get_break_statistics(1)
        print(f"\nSession Summary:")
        print(f"Breaks detected: {stats['total_breaks']}")
        print(f"Total break time: {stats['total_duration']/60:.1f} minutes")

if __name__ == "__main__":
    main() 