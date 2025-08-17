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
from data.unified_schema import BurnoutTrackerDB, InputActivity

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
    
    def __init__(self, db_path: str = "input_activity.db", log_interval: int = 60, 
                 enable_keyboard: bool = True, enable_mouse: bool = True, unified_db: BurnoutTrackerDB = None):
        """
        Initialize the input logger
        
        Args:
            db_path: Path to SQLite database file (legacy support)
            log_interval: How often to log data in seconds (default: 60)
            enable_keyboard: Whether to monitor keyboard input
            enable_mouse: Whether to monitor mouse input
            unified_db: Unified database instance for logging
        """
        self.db_path = db_path
        self.log_interval = log_interval
        self.enable_keyboard = enable_keyboard
        self.enable_mouse = enable_mouse
        self.unified_db = unified_db or BurnoutTrackerDB("data/burnout_tracker.db")
        self.is_running = False
        self.logger_thread = None
        
        # Input counters
        self.keypress_count = 0
        self.mouse_click_count = 0
        self.mouse_scroll_count = 0
        self.mouse_move_count = 0
        
        # Thread safety
        self.counter_lock = threading.Lock()
        
        # Input listeners
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('input_logger.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize legacy database (for backward compatibility)
        self._init_database()
        
        # Setup input monitoring
        if PYNPUT_AVAILABLE:
            self._setup_input_monitoring()
        else:
            self.logger.warning("pynput not available - input monitoring disabled")
    
    def _init_database(self):
        """Initialize SQLite database with input activity table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create input activity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS input_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    keypress_count INTEGER DEFAULT 0,
                    mouse_click_count INTEGER DEFAULT 0,
                    mouse_scroll_count INTEGER DEFAULT 0,
                    mouse_move_count INTEGER DEFAULT 0,
                    total_inputs INTEGER DEFAULT 0,
                    interval_seconds INTEGER DEFAULT 60,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON input_activity(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_total_inputs 
                ON input_activity(total_inputs)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
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
            self.logger.error(f"Error handling key press: {e}")
    
    def _on_key_release(self, key):
        """Handle keyboard key release"""
        try:
            # Only log on release to avoid double counting
            self.logger.debug(f"Key release: {key}")
        except Exception as e:
            self.logger.error(f"Error handling key release: {e}")
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click"""
        try:
            if pressed:  # Only count on press, not release
                with self.counter_lock:
                    self.mouse_click_count += 1
                    self.logger.debug(f"Mouse click: {button} at ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error handling mouse click: {e}")
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll"""
        try:
            with self.counter_lock:
                self.mouse_scroll_count += 1
                self.logger.debug(f"Mouse scroll: ({dx}, {dy}) at ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error handling mouse scroll: {e}")
    
    def _on_mouse_move(self, x, y):
        """Handle mouse movement"""
        try:
            with self.counter_lock:
                self.mouse_move_count += 1
                # Only log every 100th movement to avoid spam
                if self.mouse_move_count % 100 == 0:
                    self.logger.debug(f"Mouse move: ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error handling mouse move: {e}")
    
    def _log_input_activity(self):
        """Log current input activity to database"""
        try:
            with self.counter_lock:
                # Get current counts
                keypresses = self.keypress_count
                mouse_clicks = self.mouse_click_count
                mouse_scrolls = self.mouse_scroll_count
                mouse_moves = self.mouse_move_count
                total_inputs = keypresses + mouse_clicks + mouse_scrolls
                
                # Reset counters
                self.keypress_count = 0
                self.mouse_click_count = 0
                self.mouse_scroll_count = 0
                self.mouse_move_count = 0
            
            # Log to unified database
            input_activity = InputActivity(
                timestamp=int(time.time()),
                keypress_count=keypresses,
                mouse_click_count=mouse_clicks,
                scroll_events=mouse_scrolls,
                mouse_movement=mouse_moves
            )
            self.unified_db.insert_input_activity(input_activity)
            
            # Also log to legacy database for backward compatibility
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO input_activity 
                (timestamp, keypress_count, mouse_click_count, mouse_scroll_count, 
                 mouse_move_count, total_inputs, interval_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), keypresses, mouse_clicks, mouse_scrolls, 
                  mouse_moves, total_inputs, self.log_interval))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged input activity: {keypresses} keys, {mouse_clicks} clicks, "
                           f"{mouse_scrolls} scrolls, {mouse_moves} moves, {total_inputs} total")
            
        except Exception as e:
            self.logger.error(f"Failed to log input activity: {e}")
    
    def _logging_loop(self):
        """Main logging loop"""
        self.logger.info("Input logging started")
        
        while self.is_running:
            try:
                # Wait for the specified interval
                time.sleep(self.log_interval)
                
                if self.is_running:  # Check again in case we were stopped
                    self._log_input_activity()
                
            except Exception as e:
                self.logger.error(f"Error in logging loop: {e}")
                time.sleep(1)  # Brief pause before retrying
    
    def start(self):
        """Start input logging"""
        if self.is_running:
            self.logger.warning("Input logger is already running")
            return
        
        if not PYNPUT_AVAILABLE:
            self.logger.error("Cannot start - pynput not available")
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
            self.logger.error(f"Failed to start input logger: {e}")
            raise
    
    def stop(self):
        """Stop input logging"""
        if not self.is_running:
            self.logger.warning("Input logger is not running")
            return
        
        self.is_running = False
        
        # Log final activity
        self._log_input_activity()
        
        # Stop input listeners
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.logger.info("Keyboard listener stopped")
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.logger.info("Mouse listener stopped")
        
        if self.logger_thread:
            self.logger_thread.join(timeout=5)
        
        self.logger.info("Input logger stopped")
    
    def get_recent_activity(self, hours: int = 24) -> list:
        """Get recent input activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get activity from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT timestamp, keypress_count, mouse_click_count, mouse_scroll_count,
                       mouse_move_count, total_inputs, interval_seconds
                FROM input_activity
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_input_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of input activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_records,
                    SUM(keypress_count) as total_keypresses,
                    SUM(mouse_click_count) as total_clicks,
                    SUM(mouse_scroll_count) as total_scrolls,
                    SUM(mouse_move_count) as total_moves,
                    SUM(total_inputs) as total_inputs,
                    AVG(keypress_count) as avg_keypresses,
                    AVG(mouse_click_count) as avg_clicks,
                    AVG(total_inputs) as avg_total_inputs,
                    MAX(total_inputs) as max_inputs,
                    MIN(total_inputs) as min_inputs
                FROM input_activity
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                (total_records, total_keypresses, total_clicks, total_scrolls, 
                 total_moves, total_inputs, avg_keypresses, avg_clicks, 
                 avg_total_inputs, max_inputs, min_inputs) = result
                
                return {
                    'total_records': total_records,
                    'total_keypresses': total_keypresses or 0,
                    'total_clicks': total_clicks or 0,
                    'total_scrolls': total_scrolls or 0,
                    'total_moves': total_moves or 0,
                    'total_inputs': total_inputs or 0,
                    'avg_keypresses': avg_keypresses or 0,
                    'avg_clicks': avg_clicks or 0,
                    'avg_total_inputs': avg_total_inputs or 0,
                    'max_inputs': max_inputs or 0,
                    'min_inputs': min_inputs or 0,
                    'hours_analyzed': hours
                }
            else:
                return {
                    'total_records': 0,
                    'total_keypresses': 0,
                    'total_clicks': 0,
                    'total_scrolls': 0,
                    'total_moves': 0,
                    'total_inputs': 0,
                    'avg_keypresses': 0,
                    'avg_clicks': 0,
                    'avg_total_inputs': 0,
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
                'total_scrolls': 0,
                'total_moves': 0,
                'total_inputs': 0,
                'avg_keypresses': 0,
                'avg_clicks': 0,
                'avg_total_inputs': 0,
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
                fieldnames = ['timestamp', 'keypress_count', 'mouse_click_count', 
                            'mouse_scroll_count', 'mouse_move_count', 'total_inputs', 
                            'interval_seconds']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for (timestamp, keypresses, clicks, scrolls, moves, total, interval) in input_activity:
                    writer.writerow({
                        'timestamp': timestamp,
                        'keypress_count': keypresses,
                        'mouse_click_count': clicks,
                        'mouse_scroll_count': scrolls,
                        'mouse_move_count': moves,
                        'total_inputs': total,
                        'interval_seconds': interval
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
    
    logger = InputLogger(
        db_path=args.db,
        log_interval=args.interval,
        enable_keyboard=not args.no_keyboard,
        enable_mouse=not args.no_mouse
    )
    
    try:
        print(f"Starting input logger with {args.interval}s interval...")
        print(f"Keyboard monitoring: {'Enabled' if not args.no_keyboard else 'Disabled'}")
        print(f"Mouse monitoring: {'Enabled' if not args.no_mouse else 'Disabled'}")
        logger.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping input logger...")
        logger.stop()
        
        # Show results
        print("\n" + "=" * 50)
        print("INPUT ACTIVITY:")
        activity = logger.get_recent_activity(hours=1)
        
        if activity:
            for (timestamp, keypresses, clicks, scrolls, moves, total, interval) in activity:
                print(f"• {timestamp}: {keypresses} keys, {clicks} clicks, "
                      f"{scrolls} scrolls, {moves} moves, {total} total")
        else:
            print("No input activity recorded.")
        
        print("\n" + "=" * 50)
        print("INPUT SUMMARY:")
        summary = logger.get_input_summary(hours=1)
        
        print(f"Total records: {summary['total_records']}")
        print(f"Total keypresses: {summary['total_keypresses']}")
        print(f"Total clicks: {summary['total_clicks']}")
        print(f"Total scrolls: {summary['total_scrolls']}")
        print(f"Total moves: {summary['total_moves']}")
        print(f"Total inputs: {summary['total_inputs']}")
        print(f"Average keypresses per interval: {summary['avg_keypresses']:.1f}")
        print(f"Average clicks per interval: {summary['avg_clicks']:.1f}")
        print(f"Average total inputs per interval: {summary['avg_total_inputs']:.1f}")
        print(f"Max inputs in one interval: {summary['max_inputs']}")
        print(f"Min inputs in one interval: {summary['min_inputs']}")
        
        # Export to CSV if requested
        if args.export_csv:
            logger.export_to_csv(args.export_csv, hours=1)
            print(f"\nExported data to: {args.export_csv}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
        logger.stop()
        print("Test stopped by user.")
    
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.stop()

if __name__ == "__main__":
    main() 