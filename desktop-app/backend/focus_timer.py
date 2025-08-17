#!/usr/bin/env python3
"""
Focus Session Timer for CereBro Mental Burnout Tracker
A Python timer for managing focus sessions (Pomodoro-style)
Tracks session start, end, interruptions, and stores detailed logs
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
from cerebro_db import CerebroDB
from config_manager import config

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

class FocusTimer:
    """Focus session timer with interruption detection"""
    
    def __init__(self, idle_threshold: int = 60, cerebro_db: CerebroDB = None):  # 1 minute of inactivity
        self.idle_threshold = idle_threshold
        self.cerebro_db = cerebro_db or CerebroDB("cerebro.db")
        
        # Session state
        self.is_running = False
        self.session_id = None
        self.session_start = None
        self.session_end = None
        self.interrupted = False
        self.interruption_duration = 0.0
        
        # Timer state
        self.target_duration = 25 * 60  # 25 minutes default
        self.elapsed_time = 0.0
        self.timer_thread = None
        self.monitor_thread = None
        
        # Thread safety
        self.state_lock = threading.Lock()
        
        # Setup logging
        log_config = config.get_log_config('focus_timer')
        handlers = [logging.StreamHandler()]
        
        if 'file' in log_config:
            handlers.append(logging.FileHandler(log_config['file']))
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
        

        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        if self.is_running:
            self.stop_session()
        sys.exit(0)
    
    def _init_database(self):
        """Initialize SQLite database with focus sessions table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create focus sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    target_duration INTEGER DEFAULT 1500,
                    actual_duration REAL,
                    interrupted BOOLEAN DEFAULT 0,
                    interruption_duration REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
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
                return True
            
            idle_time = time.time() - last_input_time
            return idle_time < self.idle_threshold
            
        except Exception as e:
            self.logger.error(f"Error checking activity: {e}")
            return True
    
    def _monitor_activity(self):
        """Monitor user activity for interruptions"""
        while self.is_running:
            try:
                is_active = self._check_activity()
                
                with self.state_lock:
                    if not is_active and not self.interrupted:
                        # Starting interruption
                        self.interrupted = True
                        self.logger.info("Session interrupted - user inactive")
                        
                    elif is_active and self.interrupted:
                        # Ending interruption
                        self.interrupted = False
                        self.interruption_duration += 60  # Add 1 minute for each interruption
                        self.logger.info("Session resumed - user active")
                
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("Activity monitor interrupted by user")
                break
            except Exception as e:
                error_msg = f"Error in activity monitoring: {e}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - FOCUS_TIMER - ACTIVITY MONITOR ERROR: {error_msg}\n")
                except:
                    pass
                
                time.sleep(5)
    
    def _timer_loop(self):
        """Main timer loop"""
        start_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                
                with self.state_lock:
                    if not self.interrupted:
                        self.elapsed_time = current_time - start_time
                    
                    if self.elapsed_time >= self.target_duration:
                        self.logger.info("Focus session completed")
                        break
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Focus timer interrupted by user")
                break
            except Exception as e:
                error_msg = f"Critical error in focus timer main loop: {e}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - FOCUS_TIMER - CRITICAL ERROR: {error_msg}\n")
                except:
                    pass
                
                # Brief pause before retrying
                time.sleep(5)
    
    def start_session(self, duration_minutes: int = 25, notes: str = "") -> str:
        """Start a new focus session"""
        if self.is_running:
            raise RuntimeError("Session already running")
        
        try:
            # Generate session ID
            self.session_id = f"session_{int(time.time())}"
            self.session_start = datetime.now()
            self.target_duration = duration_minutes * 60
            self.elapsed_time = 0.0
            self.interrupted = False
            self.interruption_duration = 0.0
            
            # Start monitoring threads
            self.is_running = True
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.monitor_thread = threading.Thread(target=self._monitor_activity, daemon=True)
            
            self.timer_thread.start()
            self.monitor_thread.start()
            
            # Log session start
            try:
                self._log_session_start(notes)
            except Exception as e:
                self.logger.error(f"Error logging session start: {e}")
            
            self.logger.info(f"Started focus session: {self.session_id} ({duration_minutes} minutes)")
            return self.session_id
            
        except Exception as e:
            error_msg = f"Failed to start focus session: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - FOCUS_TIMER - STARTUP ERROR: {error_msg}\n")
            except:
                pass
            
            raise
    
    def stop_session(self, notes: str = "") -> Dict[str, Any]:
        """Stop the current focus session"""
        if not self.is_running:
            raise RuntimeError("No session running")
        
        try:
            # Stop monitoring
            self.is_running = False
            
            # Wait for threads to finish
            if self.timer_thread:
                try:
                    self.timer_thread.join(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error joining timer thread: {e}")
                    
            if self.monitor_thread:
                try:
                    self.monitor_thread.join(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error joining monitor thread: {e}")
            
            # Calculate final duration
            self.session_end = datetime.now()
            actual_duration = (self.session_end - self.session_start).total_seconds()
            
            # Log session end
            try:
                self._log_session_end(actual_duration, notes)
            except Exception as e:
                self.logger.error(f"Error logging session end: {e}")
            
            # Prepare result
            result = {
                'session_id': self.session_id,
                'start_time': self.session_start,
                'end_time': self.session_end,
                'target_duration': self.target_duration,
                'actual_duration': actual_duration,
                'interrupted': self.interrupted,
                'interruption_duration': self.interruption_duration,
                'completion_percentage': (actual_duration / self.target_duration) * 100
            }
            
            self.logger.info(f"Stopped focus session: {self.session_id}")
            return result
            
        except Exception as e:
            error_msg = f"Error stopping focus session: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - FOCUS_TIMER - STOP ERROR: {error_msg}\n")
            except:
                pass
            
            raise
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        if not self.is_running:
            return {'running': False}
        
        with self.state_lock:
            return {
                'running': True,
                'session_id': self.session_id,
                'elapsed_time': self.elapsed_time,
                'target_duration': self.target_duration,
                'remaining_time': max(0, self.target_duration - self.elapsed_time),
                'completion_percentage': (self.elapsed_time / self.target_duration) * 100,
                'interrupted': self.interrupted,
                'interruption_duration': self.interruption_duration
            }
    
    def _log_session_start(self, notes: str = ""):
        """Log session start to database"""
        try:
            # Session start is logged when session ends
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to log session start: {e}")
    
    def _log_session_end(self, actual_duration: float, notes: str = ""):
        """Log session end to database"""
        try:
            # Log to unified cerebro database
            try:
                self.cerebro_db.insert_focus_session(
                    start_time=int(self.session_start.timestamp()),
                    end_time=int(self.session_end.timestamp()),
                    was_interrupted=self.interrupted,
                    duration=int(actual_duration)
                )
                
            except Exception as db_error:
                error_msg = f"Database error in focus timer: {db_error}"
                self.logger.error(error_msg, exc_info=True)
                
                # Log to cerebro.log for service manager monitoring
                try:
                    with open('cerebro.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} - FOCUS_TIMER - DATABASE ERROR: {error_msg}\n")
                except:
                    pass
                
                # Don't raise the exception - continue running
                
        except Exception as e:
            error_msg = f"Failed to log session end: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - FOCUS_TIMER - LOGGING ERROR: {error_msg}\n")
            except:
                pass
    
    def get_session_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get session history from the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT session_id, start_time, end_time, target_duration, actual_duration,
                       interrupted, interruption_duration, notes
                FROM focus_sessions
                WHERE start_time >= ?
                ORDER BY start_time DESC
            ''', (cutoff_date,))
            
            results = cursor.fetchall()
            conn.close()
            
            sessions = []
            for (session_id, start_time, end_time, target_duration, actual_duration,
                 interrupted, interruption_duration, notes) in results:
                sessions.append({
                    'session_id': session_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'target_duration': target_duration,
                    'actual_duration': actual_duration,
                    'interrupted': bool(interrupted),
                    'interruption_duration': interruption_duration,
                    'notes': notes,
                    'completion_percentage': (actual_duration / target_duration) * 100 if target_duration > 0 else 0
                })
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get session history: {e}")
            return []
    
    def get_session_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get session statistics from the last N days"""
        try:
            sessions = self.get_session_history(days)
            
            if not sessions:
                return {
                    'total_sessions': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'completion_rate': 0,
                    'interruption_rate': 0
                }
            
            total_sessions = len(sessions)
            total_duration = sum(s['actual_duration'] for s in sessions)
            completed_sessions = sum(1 for s in sessions if s['completion_percentage'] >= 90)
            interrupted_sessions = sum(1 for s in sessions if s['interrupted'])
            
            return {
                'total_sessions': total_sessions,
                'total_duration': total_duration,
                'avg_duration': total_duration / total_sessions if total_sessions > 0 else 0,
                'completion_rate': (completed_sessions / total_sessions) * 100 if total_sessions > 0 else 0,
                'interruption_rate': (interrupted_sessions / total_sessions) * 100 if total_sessions > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session statistics: {e}")
            return {}
    
    def export_to_csv(self, csv_path: str, days: int = 7):
        """Export session data to CSV"""
        try:
            import csv
            
            sessions = self.get_session_history(days)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['session_id', 'start_time', 'end_time', 'target_duration', 
                            'actual_duration', 'interrupted', 'interruption_duration', 
                            'completion_percentage', 'notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for session in sessions:
                    writer.writerow(session)
            
            self.logger.info(f"Exported {len(sessions)} sessions to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Focus Session Timer')
    parser.add_argument('--duration', type=int, default=25, help='Session duration in minutes (default: 25)')
    parser.add_argument('--idle-threshold', type=int, default=60, help='Idle threshold in seconds (default: 60)')
    parser.add_argument('--db', type=str, default='focus_sessions.db', help='Database file path')
    parser.add_argument('--export-csv', type=str, default=None, help='Export to CSV file')
    parser.add_argument('--show-stats', action='store_true', help='Show session statistics')
    
    args = parser.parse_args()
    
    timer = FocusTimer(
        db_path=args.db,
        idle_threshold=args.idle_threshold
    )
    
    print("CereBro Focus Timer - CLI Mode")
    print("=" * 40)
    
    if args.show_stats:
        # Show statistics
        stats = timer.get_session_statistics(7)
        print("\nSession Statistics (Last 7 days):")
        print(f"Total sessions: {stats['total_sessions']}")
        print(f"Total duration: {stats['total_duration']/3600:.1f} hours")
        print(f"Average duration: {stats['avg_duration']/60:.1f} minutes")
        print(f"Completion rate: {stats['completion_rate']:.1f}%")
        print(f"Interruption rate: {stats['interruption_rate']:.1f}%")
        
        # Show recent sessions
        sessions = timer.get_session_history(7)
        if sessions:
            print("\nRecent Sessions:")
            for session in sessions[:5]:
                print(f"• {session['start_time']}: {session['actual_duration']/60:.1f}min "
                      f"({session['completion_percentage']:.1f}% complete)")
        
        if args.export_csv:
            timer.export_to_csv(args.export_csv, days=7)
            print(f"\nExported data to: {args.export_csv}")
        
    else:
        # Interactive CLI mode
        print(f"Starting {args.duration}-minute focus session...")
        print("Press Ctrl+C to stop early")
        
        try:
            session_id = timer.start_session(args.duration)
            print(f"Session started: {session_id}")
            
            # Monitor session
            while timer.is_running:
                status = timer.get_session_status()
                if status['running']:
                    remaining = status['remaining_time']
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    progress = status['completion_percentage']
                    
                    print(f"\rTime remaining: {minutes:02d}:{seconds:02d} "
                          f"({progress:.1f}% complete)", end='', flush=True)
                    
                    if status['interrupted']:
                        print(" [PAUSED]", end='')
                
                time.sleep(1)
            
            # Session completed
            result = timer.stop_session()
            print(f"\n\nSession completed!")
            print(f"Duration: {result['actual_duration']/60:.1f} minutes")
            print(f"Completion: {result['completion_percentage']:.1f}%")
            print(f"Interrupted: {'Yes' if result['interrupted'] else 'No'}")
            
        except KeyboardInterrupt:
            print("\n\nStopping session...")
            try:
                result = timer.stop_session()
                print(f"Session stopped early after {result['actual_duration']/60:.1f} minutes")
            except:
                pass

if __name__ == "__main__":
    main() 