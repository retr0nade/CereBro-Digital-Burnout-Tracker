#!/usr/bin/env python3
"""
Input Activity Logger for CereBro Mental Burnout Tracker
Logs keyboard keypresses and mouse clicks per minute without recording specific keys
Uses pynput library for cross-platform input monitoring
"""

import time
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import platform
import os
import json
from cerebro_db import CerebroDB
from config_manager import config

# Import pynput for input monitoring
try:
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, KeyCode
    from pynput.mouse import Button
    PYNPUT_AVAILABLE = True
except ImportError:
    print("pynput not available. Install with: pip install pynput")
    PYNPUT_AVAILABLE = False

class InputLogger:
    """Cross-platform input activity logger"""
    
    def __init__(self, log_interval: int = 60, emit_interval: float = 1.0,
                 enable_keyboard: bool = True, enable_mouse: bool = True, cerebro_db: CerebroDB = None):
        """
        Initialize the input logger
        
        Args:
            log_interval: How often to log data to DB in seconds (default: 60)
            emit_interval: How often to emit WebSocket events in seconds (default: 1.0)
            enable_keyboard: Whether to monitor keyboard input
            enable_mouse: Whether to monitor mouse input
            cerebro_db: Unified CerebroDB instance for logging
        """
        self.log_interval = log_interval
        self.emit_interval = emit_interval
        self.enable_keyboard = enable_keyboard
        self.enable_mouse = enable_mouse
        self.cerebro_db = cerebro_db or CerebroDB("cerebro.db")
        self.is_running = False
        self.logger_thread = None
        
        # Input counters (reset every emit_interval)
        self.keypress_count = 0
        self.mouse_click_count = 0
        self.mouse_scroll_count = 0
        self.mouse_move_count = 0
        
        # DB Accumulators (reset every log_interval)
        self.db_accumulator = {
            'keypress_count': 0,
            'mouse_click_count': 0,
            'mouse_scroll_count': 0,
            'mouse_move_count': 0
        }
        self.last_db_log_time = 0
        
        # Thread safety
        self.counter_lock = threading.Lock()
        
        # Input listeners
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # Setup logging
        log_config = config.get_log_config('input_logger')
        handlers = [logging.StreamHandler()]
        
        if 'file' in log_config:
            handlers.append(logging.FileHandler(log_config['file']))
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup input monitoring
        if PYNPUT_AVAILABLE:
            self._setup_input_monitoring()
        else:
            self.logger.warning("pynput not available - input monitoring disabled")
    
    def _setup_input_monitoring(self):
        """Setup keyboard and mouse listeners"""
        try:
            if self.enable_keyboard:
                self.keyboard_listener = keyboard.Listener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release
                )
                self.logger.info("Keyboard listener initialized")
            
            if self.enable_mouse:
                self.mouse_listener = mouse.Listener(
                    on_click=self._on_mouse_click,
                    on_scroll=self._on_mouse_scroll,
                    on_move=self._on_mouse_move
                )
                self.logger.info("Mouse listener initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to setup input monitoring: {e}")
            raise
    
    def _on_key_press(self, key):
        """Handle keyboard key press"""
        try:
            with self.counter_lock:
                self.keypress_count += 1
                self.logger.debug(f"Key press: {key}")
        except Exception as e:
            error_msg = f"Error handling key press: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - KEYPRESS ERROR: {error_msg}\n")
            except:
                pass
    
    def _on_key_release(self, key):
        """Handle keyboard key release"""
        try:
            # Only log on release to avoid double counting
            self.logger.debug(f"Key release: {key}")
        except Exception as e:
            error_msg = f"Error handling key release: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - KEYRELEASE ERROR: {error_msg}\n")
            except:
                pass
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click"""
        try:
            if pressed:  # Only count on press, not release
                with self.counter_lock:
                    self.mouse_click_count += 1
                    self.logger.debug(f"Mouse click: {button} at ({x}, {y})")
        except Exception as e:
            error_msg = f"Error handling mouse click: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - MOUSECLICK ERROR: {error_msg}\n")
            except:
                pass
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll"""
        try:
            with self.counter_lock:
                self.mouse_scroll_count += 1
                self.logger.debug(f"Mouse scroll: ({dx}, {dy}) at ({x}, {y})")
        except Exception as e:
            error_msg = f"Error handling mouse scroll: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - MOUSESCROLL ERROR: {error_msg}\n")
            except:
                pass
    
    def _on_mouse_move(self, x, y):
        """Handle mouse movement"""
        try:
            with self.counter_lock:
                self.mouse_move_count += 1
                # Only log every 100th movement to avoid spam
                if self.mouse_move_count % 100 == 0:
                    self.logger.debug(f"Mouse move: ({x}, {y})")
        except Exception as e:
            error_msg = f"Error handling mouse move: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - MOUSEMOVE ERROR: {error_msg}\n")
            except:
                pass

    def _process_interval(self):
        """Process current interval: emit events and optionally log to DB"""
        try:
            current_time = time.time()
            
            with self.counter_lock:
                # Get current counts since last emit
                keypresses = self.keypress_count
                mouse_clicks = self.mouse_click_count
                mouse_scrolls = self.mouse_scroll_count
                mouse_moves = self.mouse_move_count
                total_inputs = keypresses + mouse_clicks + mouse_scrolls
                
                # Reset short-term counters
                self.keypress_count = 0
                self.mouse_click_count = 0
                self.mouse_scroll_count = 0
                self.mouse_move_count = 0
                
                # Add to DB accumulators
                self.db_accumulator['keypress_count'] += keypresses
                self.db_accumulator['mouse_click_count'] += mouse_clicks
                self.db_accumulator['mouse_scroll_count'] += mouse_scrolls
                self.db_accumulator['mouse_move_count'] += mouse_moves
            
            # Emit WebSocket event (if there was activity or just heartbeat)
            # Always emit to keep chart moving
            try:
                from websocket_events import get_event_manager
                event_manager = get_event_manager()
                if event_manager:
                    event_manager.emit_input_activity({
                        "timestamp": int(current_time),
                        "keypress_count": keypresses,
                        "mouse_click_count": mouse_clicks,
                        "mouse_scroll_count": mouse_scrolls,
                        "mouse_move_count": mouse_moves,
                        "total_inputs": total_inputs
                    })
            except Exception as ws_error:
                self.logger.debug(f"WebSocket event emission failed: {ws_error}")

            # Check if it's time to log to DB
            if current_time - self.last_db_log_time >= self.log_interval:
                self._flush_to_db(current_time)
                
        except Exception as e:
            self.logger.error(f"Error in process interval: {e}", exc_info=True)

    def _flush_to_db(self, timestamp):
        """Flush accumulated data to database"""
        try:
            acc = self.db_accumulator
            total = acc['keypress_count'] + acc['mouse_click_count'] + acc['mouse_scroll_count']
            
            # Only log if there was activity (optional, but saves space)
            # But for consistency we might want to log 0s? 
            # Existing logic didn't check for 0. Let's log.
            
            self.cerebro_db.insert_input_activity(
                timestamp=int(timestamp),
                keypress_count=acc['keypress_count'],
                mouse_click_count=acc['mouse_click_count']
            )
            
            self.logger.info(f"Logged input activity to DB: {acc['keypress_count']} keys, {acc['mouse_click_count']} clicks")
            
            # Reset accumulators
            self.db_accumulator = {
                'keypress_count': 0,
                'mouse_click_count': 0,
                'mouse_scroll_count': 0,
                'mouse_move_count': 0
            }
            self.last_db_log_time = timestamp
            
        except Exception as e:
            self.logger.error(f"Database error in input logger: {e}", exc_info=True)

    def _logging_loop(self):
        """Main logging loop"""
        self.logger.info(f"Input logging started (Emit: {self.emit_interval}s, Log: {self.log_interval}s)")
        self.last_db_log_time = time.time()
        
        while self.is_running:
            try:
                time.sleep(self.emit_interval)
                
                if self.is_running:
                    self._process_interval()
                
            except KeyboardInterrupt:
                self.logger.info("Input logger interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Critical error in input logger main loop: {e}", exc_info=True)

    def start(self):
        """Start input logging"""
        if self.is_running:
            self.logger.warning("Input logger is already running")
            return
        
        if not PYNPUT_AVAILABLE:
            error_msg = "Cannot start - pynput not available"
            self.logger.error(error_msg)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - STARTUP ERROR: {error_msg}\n")
            except:
                pass
            return
        
        try:
            # Start input listeners
            if self.keyboard_listener:
                self.keyboard_listener.start()
                self.logger.info("Keyboard listener started")
            
            if self.mouse_listener:
                self.mouse_listener.start()
                self.logger.info("Mouse listener started")
            
            # Start logging thread
            self.is_running = True
            self.logger_thread = threading.Thread(target=self._logging_loop, daemon=True)
            self.logger_thread.start()
            
            self.logger.info("Input logger started")
            
        except Exception as e:
            error_msg = f"Failed to start input logger: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - STARTUP ERROR: {error_msg}\n")
            except:
                pass
            
            raise
    
    def stop(self):
        """Stop input logging"""
        if not self.is_running:
            self.logger.warning("Input logger is not running")
            return
        
        try:
            self.is_running = False
            
            # Log final activity
            try:
                # Flush any remaining data
                self._process_interval()
                self._flush_to_db(time.time())
            except Exception as e:
                self.logger.error(f"Error logging final activity: {e}")
            
            # Stop input listeners
            if self.keyboard_listener:
                try:
                    self.keyboard_listener.stop()
                    self.logger.info("Keyboard listener stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping keyboard listener: {e}")
            
            if self.mouse_listener:
                try:
                    self.mouse_listener.stop()
                    self.logger.info("Mouse listener stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping mouse listener: {e}")
            
            if self.logger_thread:
                try:
                    self.logger_thread.join(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error joining logger thread: {e}")
            
            self.logger.info("Input logger stopped")
            
        except Exception as e:
            error_msg = f"Error stopping input logger: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            # Log to cerebro.log for service manager monitoring
            try:
                with open('cerebro.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - INPUT_LOGGER - STOP ERROR: {error_msg}\n")
            except:
                pass
    
    def get_recent_activity(self, hours: int = 24) -> list:
        """Get recent input activity"""
        try:
            if self.cerebro_db:
                return self.cerebro_db.get_input_activity(limit=1000, start_time=int(time.time() - hours*3600))
            return []
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_input_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of input activity"""
        try:
            # Use self.cerebro_db.db_path if available
            db_path = self.cerebro_db.db_path if self.cerebro_db else "cerebro.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cutoff_time = int(time.time() - hours*3600)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_records,
                    SUM(keypress_count) as total_keypresses,
                    SUM(mouse_click_count) as total_clicks,
                    SUM(keypress_count + mouse_click_count) as total_inputs,
                    AVG(keypress_count) as avg_keypresses,
                    AVG(mouse_click_count) as avg_clicks,
                    MAX(keypress_count + mouse_click_count) as max_inputs,
                    MIN(keypress_count + mouse_click_count) as min_inputs
                FROM input_activity
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                (total_records, total_keypresses, total_clicks, total_inputs, 
                 avg_keypresses, avg_clicks, max_inputs, min_inputs) = result
                
                return {
                    'total_records': total_records,
                    'total_keypresses': total_keypresses or 0,
                    'total_clicks': total_clicks or 0,
                    'total_inputs': total_inputs or 0,
                    'avg_keypresses': avg_keypresses or 0,
                    'avg_clicks': avg_clicks or 0,
                    'max_inputs': max_inputs or 0,
                    'min_inputs': min_inputs or 0,
                    'hours_analyzed': hours
                }
            else:
                return {
                    'total_records': 0,
                    'total_keypresses': 0,
                    'total_clicks': 0,
                    'total_inputs': 0,
                    'avg_keypresses': 0,
                    'avg_clicks': 0,
                    'max_inputs': 0,
                    'min_inputs': 0,
                    'hours_analyzed': hours
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get input summary: {e}")
            return {
                'total_records': 0,
                'total_keypresses': 0,
                'total_clicks': 0,
                'total_inputs': 0,
                'avg_keypresses': 0,
                'avg_clicks': 0,
                'max_inputs': 0,
                'min_inputs': 0,
                'hours_analyzed': hours
            }
    
    def export_to_csv(self, csv_path: str, hours: int = 24):
        """Export input activity to CSV file"""
        try:
            import csv
            
            input_activity = self.get_recent_activity(hours)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'keypress_count', 'mouse_click_count']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in input_activity:
                    # row is a dict-like object (sqlite3.Row)
                    writer.writerow({
                        'timestamp': row['timestamp'],
                        'keypress_count': row['keypress_count'],
                        'mouse_click_count': row['mouse_click_count']
                    })
            
            self.logger.info(f"Exported {len(input_activity)} input records to {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Input Activity Logger')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Logging interval in seconds (default: 60)')
    parser.add_argument('--emit-interval', type=float, default=1.0,
                       help='Emit interval in seconds (default: 1.0)')
    parser.add_argument('--db', type=str, default='input_activity.db',
                       help='Database file path (default: input_activity.db)')
    parser.add_argument('--duration', type=int, default=300,
                       help='Run duration in seconds (default: 300)')
    parser.add_argument('--no-keyboard', action='store_true',
                       help='Disable keyboard monitoring')
    parser.add_argument('--no-mouse', action='store_true',
                       help='Disable mouse monitoring')
    parser.add_argument('--export-csv', type=str, default=None,
                       help='Export to CSV file after completion')
    
    args = parser.parse_args()
    
    # Create a dummy cerebro_db for testing if needed, or pass None and let it create default
    # But we want to use the db path from args
    db = CerebroDB(args.db)
    
    logger = InputLogger(
        log_interval=args.interval,
        emit_interval=args.emit_interval,
        enable_keyboard=not args.no_keyboard,
        enable_mouse=not args.no_mouse,
        cerebro_db=db
    )
    
    try:
        print(f"Starting input logger with {args.interval}s log interval, {args.emit_interval}s emit interval...")
        print(f"Keyboard monitoring: {'Enabled' if not args.no_keyboard else 'Disabled'}")
        print(f"Mouse monitoring: {'Enabled' if not args.no_mouse else 'Disabled'}")
        logger.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping input logger...")
        logger.stop()
        
        # Show results
        print("\\n" + "=" * 50)
        print("INPUT ACTIVITY:")
        activity = logger.get_recent_activity(hours=1)
        
        if activity:
            for row in activity:
                print(f"• {row['timestamp']}: {row['keypress_count']} keys, {row['mouse_click_count']} clicks")
        else:
            print("No input activity recorded.")
        
        print("\\n" + "=" * 50)
        print("INPUT SUMMARY:")
        summary = logger.get_input_summary(hours=1)
        
        print(f"Total records: {summary['total_records']}")
        print(f"Total keypresses: {summary['total_keypresses']}")
        print(f"Total clicks: {summary['total_clicks']}")
        print(f"Total inputs: {summary['total_inputs']}")
        
        # Export to CSV if requested
        if args.export_csv:
            logger.export_to_csv(args.export_csv, hours=1)
            print(f"\\nExported data to: {args.export_csv}")
        
        print("\\n" + "=" * 50)
        print("Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\\n\\nStopping...")
        logger.stop()
        print("Test stopped by user.")
    
    except Exception as e:
        print(f"\\nTest failed with error: {e}")
        logger.stop()

if __name__ == "__main__":
    main()