#!/usr/bin/env python3
"""
Window Activity Tracker for CereBro Mental Burnout Tracker
Tracks active window changes and logs them to unified database
Supports Windows, macOS, and Linux
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import platform
import os
from data.unified_schema import BurnoutTrackerDB, AppUsage

# Platform-specific imports
if platform.system() == "Windows":
    import win32gui
    import win32process
    import psutil
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

class WindowTracker:
    """Cross-platform window activity tracker"""
    
    def __init__(self, db_path: str = "window_activity.db", log_interval: float = 1.0, unified_db: BurnoutTrackerDB = None):
        """
        Initialize the window tracker
        
        Args:
            db_path: Path to SQLite database file (legacy support)
            log_interval: How often to check for window changes (seconds)
            unified_db: Unified database instance for logging
        """
        self.db_path = db_path
        self.log_interval = log_interval
        self.unified_db = unified_db or BurnoutTrackerDB("data/burnout_tracker.db")
        self.current_window = None
        self.current_start_time = None
        self.is_running = False
        self.tracker_thread = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('window_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize legacy database (for backward compatibility)
        self._init_database()
        
        # Platform-specific setup
        self._setup_platform()
    
    def _setup_platform(self):
        """Setup platform-specific components"""
        self.system = platform.system()
        
        if self.system == "Windows":
            self.logger.info("Initializing Windows window tracker")
        elif self.system == "Darwin":
            if Quartz is None:
                raise ImportError("Quartz module not available for macOS")
            self.logger.info("Initializing macOS window tracker")
        elif self.system == "Linux":
            if Xlib is None:
                raise ImportError("Xlib module not available for Linux")
            self.logger.info("Initializing Linux window tracker")
            self._setup_x11()
        else:
            raise NotImplementedError(f"Unsupported operating system: {self.system}")
    
    def _setup_x11(self):
        """Setup X11 display for Linux"""
        try:
            self.display = display.Display()
            self.screen = self.display.screen()
            self.root = self.screen.root
            self.logger.info("X11 display initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize X11 display: {e}")
            raise
    
    def _init_database(self):
        """Initialize SQLite database with window activity table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create window activity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS window_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    window_title TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    process_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_start_time 
                ON window_activity(start_time)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_app_name 
                ON window_activity(app_name)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_active_window_windows(self) -> Optional[Tuple[str, str, int]]:
        """Get active window info on Windows"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Validate process ID
            if pid is None or pid <= 0:
                self.logger.warning(f"Invalid process ID: {pid}")
                return "unknown", window_title, 0
            
            # Get process name
            try:
                process = psutil.Process(pid)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.logger.warning(f"Error accessing process {pid}: {e}")
                app_name = f"Unknown_{pid}"
            except ValueError as e:
                self.logger.warning(f"Invalid process ID {pid}: {e}")
                app_name = f"Unknown_{pid}"
            
            return app_name, window_title, pid
            
        except Exception as e:
            self.logger.error(f"Error getting Windows active window: {e}")
            return None
    
    def _get_active_window_macos(self) -> Optional[Tuple[str, str, int]]:
        """Get active window info on macOS"""
        try:
            # Get active application
            active_app = Quartz.CGSCopyActiveApplicationList(Quartz.CGSMainConnectionID(), None, None)
            if not active_app:
                return None
            
            # Get frontmost application
            app_list = Quartz.CGSApplicationListCopyApplicationArray(Quartz.CGSMainConnectionID(), active_app)
            if not app_list:
                return None
            
            # Get the first (frontmost) application
            app_info = app_list[0]
            app_name = Quartz.CGSApplicationListCopyApplicationName(Quartz.CGSMainConnectionID(), app_info)
            
            # Get window title (this is more complex on macOS)
            window_title = "Unknown"  # Placeholder - would need more complex implementation
            
            # Get process ID
            pid = Quartz.CGSApplicationListCopyApplicationPID(Quartz.CGSMainConnectionID(), app_info)
            
            return app_name, window_title, pid
            
        except Exception as e:
            self.logger.error(f"Error getting macOS active window: {e}")
            return None
    
    def _get_active_window_linux(self) -> Optional[Tuple[str, str, int]]:
        """Get active window info on Linux"""
        try:
            # Get active window
            active_window = self.root.get_full_property(
                self.display.intern_atom('_NET_ACTIVE_WINDOW'),
                X.AnyPropertyType
            )
            
            if not active_window:
                return None
            
            window_id = active_window.value[0]
            window = self.display.create_resource_object('window', window_id)
            
            # Get window title
            window_title_prop = window.get_full_property(
                self.display.intern_atom('_NET_WM_NAME'),
                X.AnyPropertyType
            )
            
            window_title = window_title_prop.value.decode('utf-8') if window_title_prop else "Unknown"
            
            # Get process ID
            pid_prop = window.get_full_property(
                self.display.intern_atom('_NET_WM_PID'),
                X.AnyPropertyType
            )
            
            pid = pid_prop.value[0] if pid_prop else 0
            
            # Validate process ID
            if pid <= 0:
                self.logger.warning(f"Invalid process ID: {pid}")
                return "unknown", window_title, 0
            
            # Get process name
            try:
                process = psutil.Process(pid)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.logger.warning(f"Error accessing process {pid}: {e}")
                app_name = f"Unknown_{pid}"
            except ValueError as e:
                self.logger.warning(f"Invalid process ID {pid}: {e}")
                app_name = f"Unknown_{pid}"
            
            return app_name, window_title, pid
            
        except Exception as e:
            self.logger.error(f"Error getting Linux active window: {e}")
            return None
    
    def _get_active_window(self) -> Optional[Tuple[str, str, int]]:
        """Get active window info based on platform"""
        if self.system == "Windows":
            return self._get_active_window_windows()
        elif self.system == "Darwin":
            return self._get_active_window_macos()
        elif self.system == "Linux":
            return self._get_active_window_linux()
        else:
            return None
    
    def _log_window_activity(self, app_name: str, window_title: str, start_time: datetime, 
                           end_time: datetime, duration: float, pid: int):
        """Log window activity to database"""
        try:
            # Log to unified database
            app_usage = AppUsage(
                app_name=app_name,
                start_time=int(start_time.timestamp()),
                end_time=int(end_time.timestamp()),
                duration=int(duration),
                window_title=window_title,
                category=self._categorize_app(app_name)
            )
            self.unified_db.insert_app_usage(app_usage)
            
            # Also log to legacy database for backward compatibility
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO window_activity 
                (app_name, window_title, start_time, end_time, duration_seconds, process_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (app_name, window_title, start_time, end_time, duration, pid))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Logged: {app_name} - {duration:.1f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to log window activity: {e}")
    
    def _categorize_app(self, app_name: str) -> str:
        """Categorize application based on name"""
        app_name_lower = app_name.lower()
        
        # Development tools
        if any(dev in app_name_lower for dev in ['code', 'studio', 'pycharm', 'intellij', 'eclipse', 'vim', 'emacs', 'sublime']):
            return 'development'
        
        # Communication tools
        if any(comm in app_name_lower for comm in ['slack', 'teams', 'discord', 'zoom', 'skype', 'whatsapp', 'telegram']):
            return 'communication'
        
        # Productivity tools
        if any(prod in app_name_lower for prod in ['excel', 'word', 'powerpoint', 'outlook', 'onenote', 'notion', 'trello']):
            return 'productivity'
        
        # Browsers
        if any(browser in app_name_lower for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera']):
            return 'browsing'
        
        # Entertainment
        if any(ent in app_name_lower for ent in ['youtube', 'netflix', 'spotify', 'steam', 'game']):
            return 'entertainment'
        
        # System tools
        if any(sys in app_name_lower for sys in ['explorer', 'finder', 'terminal', 'cmd', 'powershell']):
            return 'system'
        
        return 'other'
    
    def _tracking_loop(self):
        """Main tracking loop"""
        self.logger.info("Window tracking started")
        
        while self.is_running:
            try:
                # Get current active window
                window_info = self._get_active_window()
                
                if window_info:
                    app_name, window_title, pid = window_info
                    current_time = datetime.now()
                    
                    # Check if window changed
                    if (self.current_window is None or 
                        self.current_window != (app_name, window_title)):
                        
                        # Log previous window if exists
                        if self.current_window and self.current_start_time:
                            duration = (current_time - self.current_start_time).total_seconds()
                            self._log_window_activity(
                                self.current_window[0],  # app_name
                                self.current_window[1],  # window_title
                                self.current_start_time,
                                current_time,
                                duration,
                                0  # pid for previous window
                            )
                        
                        # Update current window
                        self.current_window = (app_name, window_title)
                        self.current_start_time = current_time
                        self.logger.info(f"Active window: {app_name} - {window_title}")
                
                time.sleep(self.log_interval)
                
            except Exception as e:
                self.logger.error(f"Error in tracking loop: {e}")
                time.sleep(self.log_interval)
    
    def start(self):
        """Start window tracking"""
        if self.is_running:
            self.logger.warning("Window tracker is already running")
            return
        
        self.is_running = True
        self.tracker_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.tracker_thread.start()
        self.logger.info("Window tracker started")
    
    def stop(self):
        """Stop window tracking"""
        if not self.is_running:
            self.logger.warning("Window tracker is not running")
            return
        
        self.is_running = False
        
        # Log final window if exists
        if self.current_window and self.current_start_time:
            current_time = datetime.now()
            duration = (current_time - self.current_start_time).total_seconds()
            self._log_window_activity(
                self.current_window[0],
                self.current_window[1],
                self.current_start_time,
                current_time,
                duration,
                0
            )
        
        if self.tracker_thread:
            self.tracker_thread.join(timeout=5)
        
        self.logger.info("Window tracker stopped")
    
    def get_recent_activity(self, hours: int = 24) -> list:
        """Get recent window activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get activity from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT app_name, window_title, start_time, end_time, duration_seconds
                FROM window_activity
                WHERE start_time >= ?
                ORDER BY start_time DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_app_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of app usage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT 
                    app_name,
                    COUNT(*) as sessions,
                    SUM(duration_seconds) as total_duration,
                    AVG(duration_seconds) as avg_duration
                FROM window_activity
                WHERE start_time >= ?
                GROUP BY app_name
                ORDER BY total_duration DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            summary = {
                'apps': [],
                'total_sessions': 0,
                'total_duration': 0
            }
            
            for app_name, sessions, total_duration, avg_duration in results:
                summary['apps'].append({
                    'name': app_name,
                    'sessions': sessions,
                    'total_duration': total_duration,
                    'avg_duration': avg_duration
                })
                summary['total_sessions'] += sessions
                summary['total_duration'] += total_duration
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get app summary: {e}")
            return {'apps': [], 'total_sessions': 0, 'total_duration': 0}

def main():
    """Main function for standalone testing"""
    tracker = WindowTracker()
    
    try:
        print("Starting window tracker...")
        tracker.start()
        
        # Run for 60 seconds
        time.sleep(60)
        
        print("Stopping window tracker...")
        tracker.stop()
        
        # Show recent activity
        print("\nRecent activity:")
        activity = tracker.get_recent_activity(hours=1)
        for app_name, window_title, start_time, end_time, duration in activity:
            print(f"{app_name}: {duration:.1f}s - {window_title}")
        
        # Show app summary
        print("\nApp summary:")
        summary = tracker.get_app_summary(hours=1)
        for app in summary['apps'][:5]:  # Top 5 apps
            print(f"{app['name']}: {app['total_duration']:.1f}s ({app['sessions']} sessions)")
        
    except KeyboardInterrupt:
        print("\nStopping...")
        tracker.stop()

if __name__ == "__main__":
    main() 