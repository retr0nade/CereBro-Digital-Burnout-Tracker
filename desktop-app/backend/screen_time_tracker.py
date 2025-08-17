#!/usr/bin/env python3
"""
Screen Time Tracker for CereBro Mental Burnout Tracker
Tracks daily active screen time by detecting active periods and excluding idle time
Resets daily totals at midnight and stores data in local SQLite database
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Tuple
import platform
import os
import signal
import sys
from config_manager import config

# Import existing modules for integration
try:
    from idle_monitor import IdleMonitor
    IDLE_MONITOR_AVAILABLE = True
except ImportError:
    print("idle_monitor not available - idle detection will be basic")
    IDLE_MONITOR_AVAILABLE = False

# Platform-specific imports for idle detection
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
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

class ScreenTimeTracker:
    """Daily screen time tracker with active period detection"""
    
    def __init__(self, db_path: str = "screen_time.db", 
                 idle_threshold: int = 60,  # 60 seconds of inactivity
                 check_interval: float = 1.0,  # Check every second
                 daily_reset_hour: int = 0,  # Reset at midnight
                 cerebro_db = None):  # Unified CerebroDB instance
        """
        Initialize the screen time tracker
        
        Args:
            db_path: Path to SQLite database file
            idle_threshold: Seconds of inactivity before considering idle
            check_interval: How often to check for activity in seconds
            daily_reset_hour: Hour of day to reset daily totals (0 = midnight)
            cerebro_db: Unified CerebroDB instance for logging
        """
        self.db_path = db_path
        self.idle_threshold = idle_threshold
        self.check_interval = check_interval
        self.daily_reset_hour = daily_reset_hour
        self.cerebro_db = cerebro_db
        
        # Tracking state
        self.is_running = False
        self.tracker_thread = None
        self.last_activity_time = time.time()
        self.current_session_start = None
        self.is_currently_active = False
        
        # Daily tracking
        self.current_date = date.today()
        self.daily_active_time = 0.0
        self.daily_idle_time = 0.0
        self.daily_break_count = 0
        self.last_session_end = None
        
        # Thread safety
        self.state_lock = threading.Lock()
        
        # Setup logging
        log_config = config.get_log_config('screen_time_tracker')
        handlers = [logging.StreamHandler()]
        
        if 'file' in log_config:
            handlers.append(logging.FileHandler(log_config['file']))
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        # Load today's data
        self._load_today_data()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _init_database(self):
        """Initialize SQLite database with screen time table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create screen time table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screen_time (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_active_time REAL DEFAULT 0.0,
                    total_idle_time REAL DEFAULT 0.0,
                    break_count INTEGER DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    avg_session_length REAL DEFAULT 0.0,
                    longest_session REAL DEFAULT 0.0,
                    shortest_session REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create session details table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screen_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    session_start TIMESTAMP NOT NULL,
                    session_end TIMESTAMP,
                    duration_seconds REAL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_screen_time_date 
                ON screen_time(date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_screen_sessions_date 
                ON screen_sessions(date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_screen_sessions_start 
                ON screen_sessions(session_start)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _load_today_data(self):
        """Load today's screen time data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_active_time, total_idle_time, break_count, session_count,
                       avg_session_length, longest_session, shortest_session
                FROM screen_time 
                WHERE date = ?
            ''', (self.current_date,))
            
            result = cursor.fetchone()
            
            if result:
                (self.daily_active_time, self.daily_idle_time, self.daily_break_count,
                 session_count, avg_session, longest_session, shortest_session) = result
                self.logger.info(f"Loaded today's data: {self.daily_active_time:.1f}s active, "
                               f"{self.daily_idle_time:.1f}s idle, {self.daily_break_count} breaks")
            else:
                # Create new entry for today
                cursor.execute('''
                    INSERT INTO screen_time (date, total_active_time, total_idle_time, 
                                          break_count, session_count, avg_session_length,
                                          longest_session, shortest_session)
                    VALUES (?, 0.0, 0.0, 0, 0, 0.0, 0.0, 0.0)
                ''', (self.current_date,))
                conn.commit()
                self.logger.info("Created new entry for today")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to load today's data: {e}")
    
    def _get_last_input_time(self) -> Optional[float]:
        """Get the last input time from the system"""
        try:
            if platform.system() == "Windows":
                # Windows implementation
                class LASTINPUTINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_uint),
                        ("dwTime", ctypes.c_uint)
                    ]
                
                last_input = LASTINPUTINFO()
                last_input.cbSize = ctypes.sizeof(last_input)
                
                if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input)):
                    return last_input.dwTime / 1000.0
                return None
                
            elif platform.system() == "Darwin" and Quartz:  # macOS
                # macOS implementation
                idle_time = Quartz.CGEventSourceSecondsSinceLastEventType(
                    Quartz.kCGEventSourceStateHIDSystemState,
                    Quartz.kCGEventSourceStateHIDSystemState
                )
                return time.time() - idle_time
                
            elif platform.system() == "Linux" and Xlib:  # Linux
                # Linux implementation
                display_obj = display.Display()
                root = display_obj.screen().root
                root.change_attributes(event_mask=X.MotionNotifyMask)
                return time.time()  # Simplified for now
                
            else:
                # Fallback - assume always active
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
            return idle_time < self.idle_threshold
            
        except Exception as e:
            self.logger.error(f"Error checking activity: {e}")
            return True  # Assume active on error
    
    def _check_daily_reset(self):
        """Check if we need to reset daily totals"""
        now = datetime.now()
        current_date = now.date()
        
        if current_date != self.current_date:
            self.logger.info(f"New day detected: {current_date}")
            
            # Save final data for previous day
            self._save_daily_data()
            
            # Reset for new day
            self.current_date = current_date
            self.daily_active_time = 0.0
            self.daily_idle_time = 0.0
            self.daily_break_count = 0
            self.current_session_start = None
            self.is_currently_active = False
            
            # Load new day's data
            self._load_today_data()
    
    def _save_daily_data(self):
        """Save current daily data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate session statistics
            cursor.execute('''
                SELECT COUNT(*), AVG(duration_seconds), MAX(duration_seconds), MIN(duration_seconds)
                FROM screen_sessions 
                WHERE date = ? AND is_active = 1
            ''', (self.current_date,))
            
            result = cursor.fetchone()
            session_count = result[0] if result[0] else 0
            avg_session = result[1] if result[1] else 0.0
            longest_session = result[2] if result[2] else 0.0
            shortest_session = result[3] if result[3] else 0.0
            
            # Update daily totals
            cursor.execute('''
                UPDATE screen_time 
                SET total_active_time = ?, total_idle_time = ?, break_count = ?,
                    session_count = ?, avg_session_length = ?, longest_session = ?,
                    shortest_session = ?, updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            ''', (self.daily_active_time, self.daily_idle_time, self.daily_break_count,
                  session_count, avg_session, longest_session, shortest_session, self.current_date))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved daily data: {self.daily_active_time:.1f}s active, "
                           f"{self.daily_idle_time:.1f}s idle, {self.daily_break_count} breaks")
            
        except Exception as e:
            self.logger.error(f"Failed to save daily data: {e}")
    
    def _log_session(self, session_start: datetime, session_end: datetime, 
                    duration: float, is_active: bool = True):
        """Log a screen session to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO screen_sessions (date, session_start, session_end, 
                                          duration_seconds, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.current_date, session_start, session_end, duration, is_active))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log session: {e}")
    
    def _tracking_loop(self):
        """Main tracking loop"""
        self.logger.info("Screen time tracking started")
        
        while self.is_running:
            try:
                # Check for daily reset
                try:
                    self._check_daily_reset()
                except Exception as e:
                    self.logger.error(f"Error in daily reset check: {e}")
                
                # Check current activity
                try:
                    is_active = self._check_activity()
                    current_time = time.time()
                except Exception as e:
                    self.logger.error(f"Error checking activity: {e}")
                    is_active = True  # Assume active on error
                    current_time = time.time()
                
                with self.state_lock:
                    if is_active:
                        # User is active
                        if not self.is_currently_active:
                            # Starting new active session
                            if self.current_session_start is not None:
                                try:
                                    # Log the previous idle session
                                    idle_duration = current_time - self.last_activity_time
                                    self.daily_idle_time += idle_duration
                                    self.daily_break_count += 1
                                    
                                    self._log_session(
                                        datetime.fromtimestamp(self.last_activity_time),
                                        datetime.fromtimestamp(current_time),
                                        idle_duration,
                                        is_active=False
                                    )
                                except Exception as e:
                                    self.logger.error(f"Error logging idle session: {e}")
                            
                            # Start new active session
                            self.current_session_start = current_time
                            self.is_currently_active = True
                            self.logger.debug("Started active session")
                        
                        # Update active time
                        if self.current_session_start:
                            active_duration = current_time - self.current_session_start
                            self.daily_active_time += self.check_interval
                    
                    else:
                        # User is idle
                        if self.is_currently_active:
                            # Ending active session
                            if self.current_session_start:
                                try:
                                    active_duration = current_time - self.current_session_start
                                    self._log_session(
                                        datetime.fromtimestamp(self.current_session_start),
                                        datetime.fromtimestamp(current_time),
                                        active_duration,
                                        is_active=True
                                    )
                                except Exception as e:
                                    self.logger.error(f"Error logging active session: {e}")
                            
                            self.current_session_start = None
                            self.is_currently_active = False
                            self.logger.debug("Ended active session")
                    
                    self.last_activity_time = current_time
                
                # Save data periodically (every 5 minutes)
                if int(current_time) % 300 == 0:
                    try:
                        self._save_daily_data()
                    except Exception as e:
                        self.logger.error(f"Error saving daily data: {e}")
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Screen time tracker interrupted by user")
                break
            except Exception as e:
                error_msg = f"Critical error in screen time tracker main loop: {e}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - SCREEN_TIME_TRACKER - CRITICAL ERROR: {error_msg}\n")
                except:
                    pass
                
                # Brief pause before retrying
                time.sleep(5)
    
    def start(self):
        """Start screen time tracking"""
        if self.is_running:
            self.logger.warning("Screen time tracker is already running")
            return
        
        try:
            self.is_running = True
            self.tracker_thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self.tracker_thread.start()
            
            self.logger.info("Screen time tracker started")
            
        except Exception as e:
            error_msg = f"Failed to start screen time tracker: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - SCREEN_TIME_TRACKER - STARTUP ERROR: {error_msg}\n")
            except:
                pass
            
            raise
    
    def stop(self):
        """Stop screen time tracking"""
        if not self.is_running:
            self.logger.warning("Screen time tracker is not running")
            return
        
        try:
            self.is_running = False
            
            # Log final session if active
            if self.is_currently_active and self.current_session_start:
                try:
                    current_time = time.time()
                    active_duration = current_time - self.current_session_start
                    self.daily_active_time += active_duration
                    
                    self._log_session(
                        datetime.fromtimestamp(self.current_session_start),
                        datetime.fromtimestamp(current_time),
                        active_duration,
                        is_active=True
                    )
                except Exception as e:
                    self.logger.error(f"Error logging final session: {e}")
            
            # Save final data
            try:
                self._save_daily_data()
            except Exception as e:
                self.logger.error(f"Error saving final data: {e}")
            
            if self.tracker_thread:
                try:
                    self.tracker_thread.join(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error joining tracker thread: {e}")
            
            self.logger.info("Screen time tracker stopped")
            
        except Exception as e:
            error_msg = f"Error stopping screen time tracker: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - SCREEN_TIME_TRACKER - STOP ERROR: {error_msg}\n")
            except:
                pass
    
    def get_today_summary(self) -> Dict[str, Any]:
        """Get today's screen time summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_active_time, total_idle_time, break_count, session_count,
                       avg_session_length, longest_session, shortest_session
                FROM screen_time 
                WHERE date = ?
            ''', (self.current_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                (total_active, total_idle, break_count, session_count,
                 avg_session, longest_session, shortest_session) = result
                
                return {
                    'date': self.current_date.isoformat(),
                    'total_active_time': total_active,
                    'total_idle_time': total_idle,
                    'break_count': break_count,
                    'session_count': session_count,
                    'avg_session_length': avg_session,
                    'longest_session': longest_session,
                    'shortest_session': shortest_session,
                    'total_time': total_active + total_idle,
                    'active_percentage': (total_active / (total_active + total_idle) * 100) if (total_active + total_idle) > 0 else 0
                }
            else:
                return {
                    'date': self.current_date.isoformat(),
                    'total_active_time': 0.0,
                    'total_idle_time': 0.0,
                    'break_count': 0,
                    'session_count': 0,
                    'avg_session_length': 0.0,
                    'longest_session': 0.0,
                    'shortest_session': 0.0,
                    'total_time': 0.0,
                    'active_percentage': 0.0
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get today's summary: {e}")
            return {
                'date': self.current_date.isoformat(),
                'total_active_time': 0.0,
                'total_idle_time': 0.0,
                'break_count': 0,
                'session_count': 0,
                'avg_session_length': 0.0,
                'longest_session': 0.0,
                'shortest_session': 0.0,
                'total_time': 0.0,
                'active_percentage': 0.0
            }
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get weekly screen time summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 7 days
            week_ago = date.today() - timedelta(days=7)
            
            cursor.execute('''
                SELECT date, total_active_time, total_idle_time, break_count, session_count
                FROM screen_time 
                WHERE date >= ?
                ORDER BY date DESC
            ''', (week_ago,))
            
            results = cursor.fetchall()
            conn.close()
            
            total_active = 0.0
            total_idle = 0.0
            total_breaks = 0
            total_sessions = 0
            daily_data = []
            
            for (date_str, active, idle, breaks, sessions) in results:
                total_active += active
                total_idle += idle
                total_breaks += breaks
                total_sessions += sessions
                
                daily_data.append({
                    'date': date_str,
                    'active_time': active,
                    'idle_time': idle,
                    'break_count': breaks,
                    'session_count': sessions
                })
            
            return {
                'period': 'week',
                'total_active_time': total_active,
                'total_idle_time': total_idle,
                'total_break_count': total_breaks,
                'total_session_count': total_sessions,
                'avg_daily_active': total_active / 7,
                'avg_daily_idle': total_idle / 7,
                'daily_data': daily_data
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get weekly summary: {e}")
            return {
                'period': 'week',
                'total_active_time': 0.0,
                'total_idle_time': 0.0,
                'total_break_count': 0,
                'total_session_count': 0,
                'avg_daily_active': 0.0,
                'avg_daily_idle': 0.0,
                'daily_data': []
            }
    
    def get_recent_sessions(self, hours: int = 24) -> list:
        """Get recent screen sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT session_start, session_end, duration_seconds, is_active
                FROM screen_sessions
                WHERE session_start >= ?
                ORDER BY session_start DESC
                LIMIT 100
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            sessions = []
            for (start, end, duration, is_active) in results:
                sessions.append({
                    'session_start': start,
                    'session_end': end,
                    'duration_seconds': duration,
                    'is_active': bool(is_active)
                })
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    def export_to_csv(self, csv_path: str, days: int = 7):
        """Export screen time data to CSV"""
        try:
            import csv
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = date.today() - timedelta(days=days)
            
            cursor.execute('''
                SELECT date, total_active_time, total_idle_time, break_count, session_count,
                       avg_session_length, longest_session, shortest_session
                FROM screen_time
                WHERE date >= ?
                ORDER BY date DESC
            ''', (cutoff_date,))
            
            results = cursor.fetchall()
            conn.close()
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['date', 'total_active_time', 'total_idle_time', 'break_count',
                            'session_count', 'avg_session_length', 'longest_session', 'shortest_session']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for (date_str, active, idle, breaks, sessions, avg_session, longest, shortest) in results:
                    writer.writerow({
                        'date': date_str,
                        'total_active_time': active,
                        'total_idle_time': idle,
                        'break_count': breaks,
                        'session_count': sessions,
                        'avg_session_length': avg_session,
                        'longest_session': longest,
                        'shortest_session': shortest
                    })
            
            self.logger.info(f"Exported {len(results)} days of screen time data to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Screen Time Tracker')
    parser.add_argument('--db', type=str, default='screen_time.db',
                       help='Database file path (default: screen_time.db)')
    parser.add_argument('--idle-threshold', type=int, default=60,
                       help='Idle threshold in seconds (default: 60)')
    parser.add_argument('--check-interval', type=float, default=1.0,
                       help='Check interval in seconds (default: 1.0)')
    parser.add_argument('--reset-hour', type=int, default=0,
                       help='Daily reset hour (0-23, default: 0)')
    parser.add_argument('--duration', type=int, default=3600,
                       help='Run duration in seconds (default: 3600)')
    parser.add_argument('--export-csv', type=str, default=None,
                       help='Export to CSV file after completion')
    
    args = parser.parse_args()
    
    tracker = ScreenTimeTracker(
        db_path=args.db,
        idle_threshold=args.idle_threshold,
        check_interval=args.check_interval,
        daily_reset_hour=args.reset_hour
    )
    
    try:
        print(f"Starting screen time tracker...")
        print(f"Idle threshold: {args.idle_threshold}s")
        print(f"Check interval: {args.check_interval}s")
        print(f"Daily reset hour: {args.reset_hour}:00")
        tracker.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping screen time tracker...")
        tracker.stop()
        
        # Show results
        print("\n" + "=" * 50)
        print("TODAY'S SUMMARY:")
        summary = tracker.get_today_summary()
        
        print(f"Date: {summary['date']}")
        print(f"Total active time: {summary['total_active_time']:.1f}s ({summary['active_percentage']:.1f}%)")
        print(f"Total idle time: {summary['total_idle_time']:.1f}s")
        print(f"Break count: {summary['break_count']}")
        print(f"Session count: {summary['session_count']}")
        print(f"Average session length: {summary['avg_session_length']:.1f}s")
        print(f"Longest session: {summary['longest_session']:.1f}s")
        print(f"Shortest session: {summary['shortest_session']:.1f}s")
        
        # Export to CSV if requested
        if args.export_csv:
            tracker.export_to_csv(args.export_csv, days=7)
            print(f"\nExported data to: {args.export_csv}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
        tracker.stop()
        print("Test stopped by user.")
    
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        tracker.stop()

if __name__ == "__main__":
    main() 