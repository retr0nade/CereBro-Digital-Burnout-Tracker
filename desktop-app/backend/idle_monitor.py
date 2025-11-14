#!/usr/bin/env python3
"""
User Idle Monitor for CereBro Mental Burnout Tracker
Continuously monitors mouse and keyboard activity to detect user inactivity

Windows-only MVP implementation
TODO: Future cross-platform support for macOS and Linux
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import platform
import os
from cerebro_db import CerebroDB
from config_manager import config

# Platform-specific imports
# Windows-only MVP - macOS/Linux support disabled for now
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    import win32api
    import win32con
# else:
#     # Non-Windows platforms not supported in MVP
#     # TODO: Re-enable when implementing cross-platform support
#     pass
#     # elif platform.system() == "Darwin":  # macOS
#     #     try:
#     #         import Quartz  # type: ignore
#     #     except ImportError:
#     #         print("Quartz not available. Install with: pip install pyobjc-framework-Quartz")
#     #         Quartz = None
#     # elif platform.system() == "Linux":
#     #     try:
#     #         import Xlib
#     #         from Xlib import display, X
#     #         from Xlib.ext import randr
#     #     except ImportError:
#     #         print("Xlib not available. Install with: pip install python-xlib")
#     #         Xlib = None

class IdleMonitor:
    """Windows-only user idle monitoring (MVP implementation)"""
    
    def __init__(self, timeout_seconds: int = 300, 
                 check_interval: float = 1.0, cerebro_db: Optional[CerebroDB] = None):
        """
        Initialize the idle monitor (Windows only)
        
        Args:
            timeout_seconds: Seconds of inactivity before logging idle period
            check_interval: How often to check for activity (seconds)
            cerebro_db: Unified CerebroDB instance for logging
            
        Note:
            Windows-only MVP implementation
            TODO: Add macOS/Linux support in future releases
        """
        # Validate configuration
        if timeout_seconds is None or timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")
        if check_interval is None or check_interval <= 0:
            raise ValueError("check_interval must be > 0")

        self.timeout_seconds = timeout_seconds
        self.check_interval = check_interval
        self.cerebro_db = cerebro_db or CerebroDB("cerebro.db")
        self.is_running = False
        self.monitor_thread = None
        self.last_activity_time = time.time()
        self.current_idle_start: Optional[int] = None  # Unix timestamp
        self.is_idle = False
        
        # Setup logging
        log_config = config.get_log_config('idle_monitor')
        handlers: List[logging.Handler] = [logging.StreamHandler()]
        
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
        """Setup platform-specific components (Windows only for MVP)"""
        self.system = platform.system()
        
        if self.system == "Windows":
            self.logger.info("Initializing Windows idle monitor")
            self._setup_windows()
        else:
            # Non-Windows platforms not supported in MVP
            # TODO: Implement macOS support using Quartz/IOKit
            # TODO: Implement Linux support using X11/Wayland
            error_msg = f"Idle monitoring not supported on {self.system} in MVP release (Windows only)"
            self.logger.error(error_msg)
            raise NotImplementedError(error_msg)
    
    def _setup_windows(self):
        """Setup Windows-specific components for idle detection"""
        # Windows uses GetLastInputInfo for idle detection
        self.user32 = ctypes.windll.user32  # type: ignore
        self.kernel32 = ctypes.windll.kernel32  # type: ignore
        
        # Define structures for GetLastInputInfo
        class LASTINPUTINFO(ctypes.Structure):  # type: ignore
            _fields_ = [
                ("cbSize", ctypes.c_uint),  # type: ignore
                ("dwTime", ctypes.c_uint)  # type: ignore
            ]
        
        self.LASTINPUTINFO = LASTINPUTINFO
        self.LASTINPUTINFO.cbSize = ctypes.sizeof(LASTINPUTINFO)  # type: ignore
    
    # macOS/Linux setup methods disabled for MVP
    # TODO: Re-enable when implementing cross-platform support
    # def _setup_macos(self):
    #     """Setup macOS-specific components"""
    #     # macOS uses Core Graphics for idle detection
    #     pass
    # 
    # def _setup_linux(self):
    #     """Setup Linux-specific components"""
    #     try:
    #         self.display = display.Display()
    #         self.screen = self.display.screen()
    #         self.root = self.screen.root
    #         self.logger.info("X11 display initialized successfully")
    #     except Exception as e:
    #         self.logger.error(f"Failed to initialize X11 display: {e}")
    #         raise
    

    
    def _get_last_input_time_windows(self) -> Optional[float]:
        """Get last input time on Windows using GetLastInputInfo API"""
        try:
            last_input_info = self.LASTINPUTINFO()
            if self.user32.GetLastInputInfo(ctypes.byref(last_input_info)):  # type: ignore
                # Convert to seconds since boot
                tick_count = self.kernel32.GetTickCount()
                idle_time = (tick_count - last_input_info.dwTime) / 1000.0
                return idle_time
            return None
        except Exception as e:
            self.logger.error(f"Error getting Windows last input time: {e}")
            return None
    
    # macOS/Linux methods disabled for MVP
    # TODO: Re-enable when implementing cross-platform support
    # def _get_last_input_time_macos(self) -> Optional[float]:
    #     """Get last input time on macOS"""
    #     try:
    #         # Use Core Graphics to get last input time
    #         # This is a simplified implementation
    #         # For production, you might want to use IOKit for more accurate results
    #         return None  # Placeholder - would need more complex implementation
    #     except Exception as e:
    #         self.logger.error(f"Error getting macOS last input time: {e}")
    #         return None
    # 
    # def _get_last_input_time_linux(self) -> Optional[float]:
    #     """Get last input time on Linux"""
    #     try:
    #         # Check for mouse and keyboard activity using X11
    #         # This is a simplified implementation
    #         return None  # Placeholder - would need more complex implementation
    #     except Exception as e:
    #         self.logger.error(f"Error getting Linux last input time: {e}")
    #         return None
    
    def _get_last_input_time(self) -> Optional[float]:
        """Get last input time (Windows only for MVP)"""
        if self.system == "Windows":
            return self._get_last_input_time_windows()
        else:
            # Non-Windows platforms not supported in MVP
            self.logger.warning(f"Idle time detection not supported on {self.system}")
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
            # Log to unified cerebro database
            try:
                self.cerebro_db.insert_idle_period(
                    start_time=int(idle_start.timestamp()),
                    end_time=int(idle_end.timestamp()),
                    duration=int(duration)
                )
                
                self.logger.info(f"Logged idle period: {duration:.1f}s ({idle_start} to {idle_end})")
                
                # Emit WebSocket event for idle status update
                try:
                    from websocket_events import get_event_manager
                    event_manager = get_event_manager()
                    if event_manager:
                        event_manager.emit_idle_status({
                            "is_idle": False,  # User just became active
                            "idle_start": int(idle_start.timestamp()),
                            "idle_end": int(idle_end.timestamp()),
                            "duration": int(duration),
                            "reason": "user_activity_resumed"
                        })
                except Exception as ws_error:
                    self.logger.debug(f"WebSocket event emission failed: {ws_error}")
                
            except Exception as db_error:
                error_msg = f"Database error in idle monitor: {db_error}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - IDLE_MONITOR - DATABASE ERROR: {error_msg}\n")
                except:
                    pass
                
                # Don't raise the exception - continue running
                
        except Exception as e:
            error_msg = f"Failed to log idle period: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - IDLE_MONITOR - LOGGING ERROR: {error_msg}\n")
            except:
                pass

    # ---- Test-friendly helpers expected by unit tests ----
    def _check_idle_status(self) -> bool:
        """Check current idle status, update state, and log transitions."""
        try:
            from metrics.idle import get_idle_seconds  # type: ignore
            idle_sec = get_idle_seconds()
        except Exception:
            # On error, consider user active to avoid false positives
            return False

        is_idle_now = idle_sec >= self.timeout_seconds

        if is_idle_now and not self.is_idle:
            # Transition to idle
            # Set state before calling hook (so tests that mock the hook can still assert state)
            try:
                self.current_idle_start = int(time.time())
                self.last_activity_time = self.current_idle_start
            except Exception:
                self.current_idle_start = int(time.time())
            self._log_idle_start(idle_sec, "inactivity")
            self.is_idle = True
            return True

        if not is_idle_now and self.is_idle:
            # Transition to active
            # Clear state before calling hook (so tests that mock the hook can still assert state reset)
            self.current_idle_start = None
            self._log_idle_end()
            self.is_idle = False
            return False

        # No transition; return current status
        return is_idle_now

    def _log_idle_start(self, idle_seconds: int, reason: str):
        """Record the start of an idle period. DB write is deferred until end."""
        try:
            self.current_idle_start = int(time.time())
            self.last_activity_time = self.current_idle_start
            # Reason is not stored in DB but tests may patch/check behavior
        except Exception as e:
            self.logger.error(f"Failed to log idle start: {e}")

    def _log_idle_end(self):
        """Finalize and store the idle period in the database."""
        try:
            if self.current_idle_start is None:
                return
            idle_end = int(time.time())
            duration = int(idle_end - int(self.current_idle_start))
            # Persist to unified schema
            try:
                self.cerebro_db.insert_idle_period(
                    start_time=int(self.current_idle_start),
                    end_time=idle_end,
                    duration=duration
                )
            except Exception as db_error:
                # Keep service resilient during tests
                self.logger.error(f"DB error while writing idle period: {db_error}")
            finally:
                # Reset state regardless of DB outcome
                self.current_idle_start = None
        except Exception as e:
            self.logger.error(f"Failed to log idle end: {e}")

    def _calculate_idle_duration(self) -> int:
        if self.current_idle_start is None:
            return 0
        return int(time.time()) - int(self.current_idle_start)
    
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
                        try:
                            idle_end_ts = int(time.time())
                            duration = 0.0
                            if self.current_idle_start:
                                duration = float(idle_end_ts - self.current_idle_start)
                                idle_start_dt = datetime.fromtimestamp(self.current_idle_start)
                                idle_end_dt = datetime.fromtimestamp(idle_end_ts)
                                
                                self._log_idle_period(idle_start_dt, idle_end_dt, duration)
                            
                            self.is_idle = False
                            self.current_idle_start = None
                            self.logger.info(f"User became active after {duration:.1f}s of inactivity")
                        except Exception as log_error:
                            error_msg = f"Error logging idle period end: {log_error}"
                            self.logger.error(error_msg, exc_info=True)
                            
                            # Log to cerebro.log for service manager monitoring
                            try:
                                with open('cerebro.log', 'a') as f:
                                    f.write(f"{datetime.now().isoformat()} - IDLE_MONITOR - LOGGING ERROR: {error_msg}\n")
                            except:
                                pass
                    
                    # Update last activity time
                    self.last_activity_time = current_time
                    
                else:
                    # User is idle
                    if not self.is_idle:
                        # User just became idle
                        self.is_idle = True
                        self.current_idle_start = int(time.time())
                        self.logger.info(f"User became idle (timeout: {self.timeout_seconds}s)")
                        
                        # Emit WebSocket event for idle status update
                        try:
                            from websocket_events import get_event_manager
                            event_manager = get_event_manager()
                            if event_manager:
                                event_manager.emit_idle_status({
                                    "is_idle": True,
                                    "idle_start": self.current_idle_start,
                                    "reason": "user_inactivity"
                                })
                        except Exception as ws_error:
                            self.logger.debug(f"WebSocket event emission failed: {ws_error}")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Idle monitor interrupted by user")
                break
            except Exception as e:
                error_msg = f"Critical error in idle monitor main loop: {e}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - IDLE_MONITOR - CRITICAL ERROR: {error_msg}\n")
                except:
                    pass
                
                # Brief pause before retrying
                time.sleep(5)
    
    def start(self):
        """Start idle monitoring"""
        if self.is_running:
            self.logger.warning("Idle monitor is already running")
            return
        
        try:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Idle monitor started")
            
        except Exception as e:
            error_msg = f"Failed to start idle monitor: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - IDLE_MONITOR - STARTUP ERROR: {error_msg}\n")
            except:
                pass
            
            raise
    
    def stop(self):
        """Stop idle monitoring"""
        if not self.is_running:
            self.logger.warning("Idle monitor is not running")
            return
        
        try:
            self.is_running = False
            
            # Log final idle period if user is currently idle
            if self.is_idle and self.current_idle_start:
                try:
                    idle_end_ts = int(time.time())
                    duration = idle_end_ts - self.current_idle_start
                    idle_start_dt = datetime.fromtimestamp(self.current_idle_start)
                    idle_end_dt = datetime.fromtimestamp(idle_end_ts)
                    self._log_idle_period(idle_start_dt, idle_end_dt, float(duration))
                except Exception as e:
                    self.logger.error(f"Error logging final idle period: {e}")
            
            if self.monitor_thread:
                try:
                    self.monitor_thread.join(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error joining monitor thread: {e}")
            
            self.logger.info("Idle monitor stopped")
            
        except Exception as e:
            error_msg = f"Error stopping idle monitor: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - IDLE_MONITOR - STOP ERROR: {error_msg}\n")
            except:
                pass
    
    def get_recent_idle_periods(self, hours: int = 24) -> list:
        """Get recent idle periods from unified database"""
        try:
            cutoff_ts = int(time.time()) - (hours * 3600)
            rows = self.cerebro_db.get_idle_periods(limit=1000)
            filtered = [r for r in rows if r.get('start_time', 0) >= cutoff_ts]
            return [
                {
                    'start_time': r.get('start_time'),
                    'end_time': r.get('end_time'),
                    'duration': r.get('duration', 0)
                }
                for r in filtered
            ]
        except Exception as e:
            self.logger.error(f"Failed to get recent idle periods: {e}")
            return []
    
    def get_idle_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of idle activity from unified database"""
        try:
            cutoff_ts = int(time.time()) - (hours * 3600)
            rows = [r for r in self.cerebro_db.get_idle_periods(limit=5000) if r.get('start_time', 0) >= cutoff_ts]
            total_periods = len(rows)
            durations = [int(r.get('duration', 0) or 0) for r in rows]
            total_idle_time = sum(durations)
            avg_idle_duration = (total_idle_time / total_periods) if total_periods else 0
            max_idle_duration = max(durations) if durations else 0
            min_idle_duration = min(durations) if durations else 0
            return {
                'total_periods': total_periods,
                'total_idle_time': total_idle_time,
                'avg_idle_duration': avg_idle_duration,
                'max_idle_duration': max_idle_duration,
                'min_idle_duration': min_idle_duration,
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