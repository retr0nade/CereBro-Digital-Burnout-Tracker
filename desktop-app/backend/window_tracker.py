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
from cerebro_db import CerebroDB
from config_manager import config

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
    
    def __init__(self, log_interval: float = 1.0, cerebro_db: CerebroDB = None):
        """
        Initialize the window tracker
        
        Args:
            log_interval: How often to check for window changes (seconds)
            cerebro_db: Unified CerebroDB instance for logging
        """
        # Validate configuration
        if log_interval is None or log_interval <= 0:
            raise ValueError("log_interval must be a positive number")
        self.log_interval = log_interval
        self.cerebro_db = cerebro_db or CerebroDB("cerebro.db")
        self.current_window = None
        self.current_start_time = None
        self.is_running = False
        self.tracker_thread = None
        
        # Setup logging
        log_config = config.get_log_config('window_tracker')
        handlers = [logging.StreamHandler()]
        
        if 'file' in log_config:
            handlers.append(logging.FileHandler(log_config['file']))
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
        

        
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
        """Get active window info based on platform.

        First tries the shared metrics.apps.get_foreground_app helper (so tests can patch it),
        falling back to platform-specific implementations.
        """
        # Preferred: shared helper (enables easy mocking in tests)
        try:
            from metrics.apps import get_foreground_app  # type: ignore
            result = get_foreground_app()
            if result is None:
                return None
            if isinstance(result, tuple):
                if len(result) == 3:
                    # app_name, window_title, pid
                    return result  # type: ignore[return-value]
                if len(result) == 2:
                    app_name, window_title = result
                    return app_name, window_title, 0
        except Exception:
            # Ignore and fall back
            pass

        # Fallback: platform-specific
        if self.system == "Windows":
            return self._get_active_window_windows()
        elif self.system == "Darwin":
            return self._get_active_window_macos()
        elif self.system == "Linux":
            return self._get_active_window_linux()
        else:
            return None
    
    def _log_window_activity(self, app_name: str, window_title: str, start_time, 
                           end_time, duration: float, pid: int):
        """Log window activity to database"""
        try:
            # Log to unified cerebro database
            try:
                # Normalize time inputs (accept datetime or epoch seconds)
                if hasattr(start_time, 'timestamp'):
                    norm_start = int(start_time.timestamp())
                else:
                    norm_start = int(start_time)
                if hasattr(end_time, 'timestamp'):
                    norm_end = int(end_time.timestamp())
                else:
                    norm_end = int(end_time)

                self.cerebro_db.insert_app_usage(
                    app_name,
                    norm_start,
                    norm_end,
                    int(duration)
                )
                
                self.logger.debug(f"Logged: {app_name} - {duration:.1f}s")
                
                # Emit WebSocket event for app usage update
                try:
                    from websocket_events import get_event_manager
                    event_manager = get_event_manager()
                    if event_manager:
                        event_manager.emit_app_usage_update({
                            "app_name": app_name,
                            "window_title": window_title,
                            "start_time": norm_start,
                            "end_time": norm_end,
                            "duration": int(duration),
                            "pid": pid
                        })
                except Exception as ws_error:
                    self.logger.debug(f"WebSocket event emission failed: {ws_error}")
                
            except Exception as db_error:
                error_msg = f"Database error in window tracker: {db_error}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - WINDOW_TRACKER - DATABASE ERROR: {error_msg}\n")
                except:
                    pass
                
                # Don't raise the exception - continue running
                
        except Exception as e:
            error_msg = f"Failed to log window activity: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - WINDOW_TRACKER - LOGGING ERROR: {error_msg}\n")
            except:
                pass
    
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
                            try:
                                duration = (current_time - self.current_start_time).total_seconds()
                                self._log_window_activity(
                                    self.current_window[0],  # app_name
                                    self.current_window[1],  # window_title
                                    self.current_start_time,
                                    current_time,
                                    duration,
                                    0  # pid for previous window
                                )
                            except Exception as log_error:
                                error_msg = f"Error logging previous window activity: {log_error}"
                                self.logger.error(error_msg, exc_info=True)
                                
                                # Log to cerebro.log for service manager monitoring
                                try:
                                    with open('cerebro.log', 'a') as f:
                                        f.write(f"{datetime.now().isoformat()} - WINDOW_TRACKER - LOGGING ERROR: {error_msg}\n")
                                except:
                                    pass
                        
                        # Update current window
                        self.current_window = (app_name, window_title)
                        self.current_start_time = current_time
                        self.logger.info(f"Active window: {app_name} - {window_title}")
                
                time.sleep(self.log_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Window tracker interrupted by user")
                break
            except Exception as e:
                error_msg = f"Critical error in window tracker main loop: {e}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - WINDOW_TRACKER - CRITICAL ERROR: {error_msg}\n")
                except:
                    pass
                
                # Brief pause before retrying
                time.sleep(5)

    def _tracking_loop_iteration(self):
        """Single iteration of tracking loop (test-friendly)."""
        try:
            window_info = self._get_active_window()
            if not window_info:
                return

            app_name, window_title, pid = window_info
            current_time = int(time.time())

            # Fast path: if unchanged, return immediately
            if self.current_window == (app_name, window_title):
                return

            # Log previous window if exists
            prev_start = self.current_start_time
            prev_window = self.current_window
            if prev_window is not None and prev_start is not None:
                duration = current_time - int(prev_start)
                if duration > 0:
                    # Keep this call minimal; errors are ignored for perf path
                    try:
                        self._log_window_activity(
                            app_name=prev_window[0],
                            window_title=prev_window[1],
                            start_time=int(prev_start),
                            end_time=current_time,
                            duration=duration,
                            pid=0
                        )
                    except Exception:
                        pass

            # Update current window
            self.current_window = (app_name, window_title)
            self.current_start_time = current_time
        except Exception:
            # Swallow errors in tight loops for tests
            pass
    
    def start(self):
        """Start window tracking"""
        if self.is_running:
            self.logger.warning("Window tracker is already running")
            return
        
        try:
            self.is_running = True
            self.tracker_thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self.tracker_thread.start()
            self.logger.info("Window tracker started")
            
        except Exception as e:
            error_msg = f"Failed to start window tracker: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - WINDOW_TRACKER - STARTUP ERROR: {error_msg}\n")
            except:
                pass
            
            raise
    
    def stop(self):
        """Stop window tracking"""
        if not self.is_running:
            self.logger.warning("Window tracker is not running")
            return
        
        try:
            self.is_running = False
            
            # Log final window if exists
            if self.current_window and self.current_start_time:
                try:
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
                except Exception as e:
                    self.logger.error(f"Error logging final window activity: {e}")
            
            if self.tracker_thread:
                try:
                    self.tracker_thread.join(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error joining tracker thread: {e}")
            
            self.logger.info("Window tracker stopped")
            
        except Exception as e:
            error_msg = f"Error stopping window tracker: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - WINDOW_TRACKER - STOP ERROR: {error_msg}\n")
            except:
                pass
    
    def get_recent_activity(self, hours: int = 24) -> list:
        """Get recent window activity from unified database"""
        try:
            cutoff_ts = int(time.time()) - (hours * 3600)
            rows = self.cerebro_db.get_app_usage(limit=1000)
            filtered = [r for r in rows if r.get('start_time', 0) >= cutoff_ts]
            # Map to a simple structure compatible with existing consumers
            return [
                {
                    'app_name': r.get('app_name'),
                    'window_title': None,
                    'start_time': r.get('start_time'),
                    'end_time': r.get('end_time'),
                    'duration': r.get('duration', 0)
                }
                for r in filtered
            ]
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_app_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of app usage from unified database"""
        try:
            cutoff_ts = int(time.time()) - (hours * 3600)
            rows = self.cerebro_db.get_app_usage(limit=5000)
            filtered = [r for r in rows if r.get('start_time', 0) >= cutoff_ts]
            summary: Dict[str, Any] = {
                'apps': [],
                'total_sessions': 0,
                'total_duration': 0
            }
            agg: Dict[str, Dict[str, Any]] = {}
            for r in filtered:
                name = r.get('app_name') or 'Unknown'
                duration = int(r.get('duration', 0) or 0)
                stats = agg.setdefault(name, {'sessions': 0, 'total_duration': 0})
                stats['sessions'] += 1
                stats['total_duration'] += duration
            for name, stats in sorted(agg.items(), key=lambda kv: kv[1]['total_duration'], reverse=True):
                total_duration = stats['total_duration']
                sessions = stats['sessions']
                avg_duration = (total_duration / sessions) if sessions else 0
                summary['apps'].append({
                    'name': name,
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