import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class BreakType(Enum):
    SHORT = "short"
    LONG = "long"
    MICRO = "micro"
    LUNCH = "lunch"
    COFFEE = "coffee"

@dataclass
class AppUsage:
    app_name: str
    start_time: int
    end_time: int
    duration: int
    window_title: Optional[str] = None
    category: Optional[str] = None

@dataclass
class IdlePeriod:
    start_time: int
    end_time: int
    duration: int
    reason: Optional[str] = None

@dataclass
class InputActivity:
    timestamp: int
    keypress_count: int
    mouse_click_count: int
    scroll_events: int = 0
    mouse_movement: int = 0

@dataclass
class FocusSession:
    session_id: str
    start_time: int
    end_time: int
    was_interrupted: bool
    focus_score: Optional[float] = None
    notes: Optional[str] = None

@dataclass
class BreakLog:
    start_time: int
    end_time: int
    break_type: BreakType
    duration: int
    was_productive: Optional[bool] = None
    notes: Optional[str] = None

class BurnoutTrackerDB:
    """
    Unified SQLite database for mental burnout tracking with comprehensive schema
    """
    
    def __init__(self, db_path: str = "data/burnout_tracker.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # 1. App Usage Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    window_title TEXT,
                    category TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(app_name, start_time)
                )
            """)
            
            # 2. Idle Periods Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS idle_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    reason TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(start_time)
                )
            """)
            
            # 3. Input Activity Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS input_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    keypress_count INTEGER DEFAULT 0,
                    mouse_click_count INTEGER DEFAULT 0,
                    scroll_events INTEGER DEFAULT 0,
                    mouse_movement INTEGER DEFAULT 0,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(timestamp)
                )
            """)
            
            # 4. Focus Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    was_interrupted BOOLEAN DEFAULT FALSE,
                    focus_score REAL,
                    notes TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 5. Break Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS break_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    break_type TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    was_productive BOOLEAN,
                    notes TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(start_time)
                )
            """)
            
            # 6. App Categories Table (for better organization)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    is_productive BOOLEAN DEFAULT FALSE,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 7. Burnout Signals Table (for tracking stress indicators)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS burnout_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_type TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    severity REAL DEFAULT 1.0,
                    description TEXT,
                    metadata TEXT,  -- JSON string for additional data
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_start_time ON app_usage(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_app_name ON app_usage(app_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_idle_periods_start_time ON idle_periods(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_input_activity_timestamp ON input_activity(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_focus_sessions_start_time ON focus_sessions(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_break_logs_start_time ON break_logs(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_burnout_signals_timestamp ON burnout_signals(timestamp)")
            
            conn.commit()
    
    def insert_app_usage(self, app_usage: AppUsage) -> int:
        """Insert app usage record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO app_usage 
                (app_name, start_time, end_time, duration, window_title, category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                app_usage.app_name,
                app_usage.start_time,
                app_usage.end_time,
                app_usage.duration,
                app_usage.window_title,
                app_usage.category,
                int(time.time())
            ))
            conn.commit()
            return cursor.lastrowid
    
    def insert_idle_period(self, idle_period: IdlePeriod) -> int:
        """Insert idle period record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO idle_periods 
                (start_time, end_time, duration, reason, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                idle_period.start_time,
                idle_period.end_time,
                idle_period.duration,
                idle_period.reason,
                int(time.time())
            ))
            conn.commit()
            return cursor.lastrowid
    
    def insert_input_activity(self, input_activity: InputActivity) -> int:
        """Insert input activity record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO input_activity 
                (timestamp, keypress_count, mouse_click_count, scroll_events, mouse_movement)
                VALUES (?, ?, ?, ?, ?)
            """, (
                input_activity.timestamp,
                input_activity.keypress_count,
                input_activity.mouse_click_count,
                input_activity.scroll_events,
                input_activity.mouse_movement
            ))
            conn.commit()
            return cursor.lastrowid
    
    def insert_focus_session(self, focus_session: FocusSession) -> int:
        """Insert focus session record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO focus_sessions 
                (session_id, start_time, end_time, was_interrupted, focus_score, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                focus_session.session_id,
                focus_session.start_time,
                focus_session.end_time,
                focus_session.was_interrupted,
                focus_session.focus_score,
                focus_session.notes,
                int(time.time())
            ))
            conn.commit()
            return cursor.lastrowid
    
    def insert_break_log(self, break_log: BreakLog) -> int:
        """Insert break log record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO break_logs 
                (start_time, end_time, break_type, duration, was_productive, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                break_log.start_time,
                break_log.end_time,
                break_log.break_type.value,
                break_log.duration,
                break_log.was_productive,
                break_log.notes,
                int(time.time())
            ))
            conn.commit()
            return cursor.lastrowid
    
    def insert_burnout_signal(self, signal_type: str, severity: float = 1.0, 
                            description: str = None, metadata: Dict = None) -> int:
        """Insert burnout signal record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO burnout_signals 
                (signal_type, timestamp, severity, description, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                signal_type,
                int(time.time()),
                severity,
                description,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_app_usage_by_date(self, date: str, limit: int = 100) -> List[Tuple]:
        """Get app usage records for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            start_timestamp = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
            end_timestamp = start_timestamp + 86400  # 24 hours
            
            cursor.execute("""
                SELECT app_name, start_time, end_time, duration, window_title, category
                FROM app_usage 
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (start_timestamp, end_timestamp, limit))
            return cursor.fetchall()
    
    def get_idle_periods_by_date(self, date: str, limit: int = 100) -> List[Tuple]:
        """Get idle periods for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            start_timestamp = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
            end_timestamp = start_timestamp + 86400
            
            cursor.execute("""
                SELECT start_time, end_time, duration, reason
                FROM idle_periods 
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (start_timestamp, end_timestamp, limit))
            return cursor.fetchall()
    
    def get_focus_sessions_by_date(self, date: str, limit: int = 50) -> List[Tuple]:
        """Get focus sessions for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            start_timestamp = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
            end_timestamp = start_timestamp + 86400
            
            cursor.execute("""
                SELECT session_id, start_time, end_time, was_interrupted, focus_score, notes
                FROM focus_sessions 
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (start_timestamp, end_timestamp, limit))
            return cursor.fetchall()
    
    def get_break_logs_by_date(self, date: str, limit: int = 50) -> List[Tuple]:
        """Get break logs for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            start_timestamp = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
            end_timestamp = start_timestamp + 86400
            
            cursor.execute("""
                SELECT start_time, end_time, break_type, duration, was_productive, notes
                FROM break_logs 
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (start_timestamp, end_timestamp, limit))
            return cursor.fetchall()
    
    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """Get comprehensive daily summary"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            start_timestamp = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
            end_timestamp = start_timestamp + 86400
            
            # Total app usage time
            cursor.execute("""
                SELECT SUM(duration) FROM app_usage 
                WHERE start_time >= ? AND start_time < ?
            """, (start_timestamp, end_timestamp))
            total_app_time = cursor.fetchone()[0] or 0
            
            # Total idle time
            cursor.execute("""
                SELECT SUM(duration) FROM idle_periods 
                WHERE start_time >= ? AND start_time < ?
            """, (start_timestamp, end_timestamp))
            total_idle_time = cursor.fetchone()[0] or 0
            
            # Focus sessions
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN was_interrupted = 0 THEN 1 ELSE 0 END)
                FROM focus_sessions 
                WHERE start_time >= ? AND start_time < ?
            """, (start_timestamp, end_timestamp))
            focus_data = cursor.fetchone()
            total_focus_sessions = focus_data[0] or 0
            completed_focus_sessions = focus_data[1] or 0
            
            # Break logs
            cursor.execute("""
                SELECT break_type, COUNT(*), SUM(duration)
                FROM break_logs 
                WHERE start_time >= ? AND start_time < ?
                GROUP BY break_type
            """, (start_timestamp, end_timestamp))
            break_summary = cursor.fetchall()
            
            # Burnout signals
            cursor.execute("""
                SELECT signal_type, COUNT(*), AVG(severity)
                FROM burnout_signals 
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY signal_type
            """, (start_timestamp, end_timestamp))
            burnout_signals = cursor.fetchall()
            
            return {
                "date": date,
                "total_app_time": total_app_time,
                "total_idle_time": total_idle_time,
                "focus_sessions": {
                    "total": total_focus_sessions,
                    "completed": completed_focus_sessions,
                    "interrupted": total_focus_sessions - completed_focus_sessions
                },
                "breaks": {break_type: {"count": count, "total_duration": duration} 
                          for break_type, count, duration in break_summary},
                "burnout_signals": {signal_type: {"count": count, "avg_severity": severity} 
                                  for signal_type, count, severity in burnout_signals}
            }
    
    def get_recent_activity(self, hours: int = 24, limit: int = 100) -> Dict[str, List]:
        """Get recent activity across all tables"""
        cutoff_time = int(time.time()) - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Recent app usage
            cursor.execute("""
                SELECT app_name, start_time, end_time, duration, category
                FROM app_usage 
                WHERE start_time >= ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (cutoff_time, limit))
            recent_app_usage = cursor.fetchall()
            
            # Recent idle periods
            cursor.execute("""
                SELECT start_time, end_time, duration, reason
                FROM idle_periods 
                WHERE start_time >= ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (cutoff_time, limit))
            recent_idle = cursor.fetchall()
            
            # Recent input activity
            cursor.execute("""
                SELECT timestamp, keypress_count, mouse_click_count, scroll_events
                FROM input_activity 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (cutoff_time, limit))
            recent_input = cursor.fetchall()
            
            return {
                "app_usage": recent_app_usage,
                "idle_periods": recent_idle,
                "input_activity": recent_input
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent database bloat"""
        cutoff_time = int(time.time()) - (days_to_keep * 86400)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM app_usage WHERE start_time < ?", (cutoff_time,))
            cursor.execute("DELETE FROM idle_periods WHERE start_time < ?", (cutoff_time,))
            cursor.execute("DELETE FROM input_activity WHERE timestamp < ?", (cutoff_time,))
            cursor.execute("DELETE FROM focus_sessions WHERE start_time < ?", (cutoff_time,))
            cursor.execute("DELETE FROM break_logs WHERE start_time < ?", (cutoff_time,))
            cursor.execute("DELETE FROM burnout_signals WHERE timestamp < ?", (cutoff_time,))
            
            conn.commit()

# Example usage and utility functions
def create_sample_data(db: BurnoutTrackerDB):
    """Create sample data for testing"""
    current_time = int(time.time())
    
    # Sample app usage
    app_usage = AppUsage(
        app_name="Chrome",
        start_time=current_time - 3600,
        end_time=current_time,
        duration=3600,
        window_title="GitHub - Mental Burnout Tracker",
        category="development"
    )
    db.insert_app_usage(app_usage)
    
    # Sample idle period
    idle_period = IdlePeriod(
        start_time=current_time - 1800,
        end_time=current_time - 1700,
        duration=100,
        reason="coffee_break"
    )
    db.insert_idle_period(idle_period)
    
    # Sample input activity
    input_activity = InputActivity(
        timestamp=current_time - 300,
        keypress_count=150,
        mouse_click_count=25,
        scroll_events=10,
        mouse_movement=500
    )
    db.insert_input_activity(input_activity)
    
    # Sample focus session
    focus_session = FocusSession(
        session_id=f"focus_{current_time}",
        start_time=current_time - 2700,
        end_time=current_time - 1800,
        was_interrupted=False,
        focus_score=0.85,
        notes="Productive coding session"
    )
    db.insert_focus_session(focus_session)
    
    # Sample break log
    break_log = BreakLog(
        start_time=current_time - 1800,
        end_time=current_time - 1700,
        break_type=BreakType.SHORT,
        duration=100,
        was_productive=True,
        notes="Quick stretch and coffee"
    )
    db.insert_break_log(break_log)
    
    # Sample burnout signal
    db.insert_burnout_signal(
        signal_type="rapid_tab_switching",
        severity=0.7,
        description="User switched tabs 15 times in 5 minutes",
        metadata={"tab_switches": 15, "time_window": 300}
    )

if __name__ == "__main__":
    # Initialize database
    db = BurnoutTrackerDB()
    
    # Create sample data
    create_sample_data(db)
    
    # Get today's summary
    today = datetime.now().strftime("%Y-%m-%d")
    summary = db.get_daily_summary(today)
    print(f"Daily Summary for {today}:")
    print(json.dumps(summary, indent=2))
    
    # Get recent activity
    recent = db.get_recent_activity(hours=1)
    print(f"\nRecent Activity (last hour):")
    print(f"App usage records: {len(recent['app_usage'])}")
    print(f"Idle periods: {len(recent['idle_periods'])}")
    print(f"Input activity records: {len(recent['input_activity'])}")
