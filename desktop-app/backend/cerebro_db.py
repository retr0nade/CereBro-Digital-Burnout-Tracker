import sqlite3
import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

class CerebroDB:
    """
    Unified SQLite database for CereBro mental burnout tracker
    """
    
    def __init__(self, db_path: str = "cerebro.db"):
        self.db_path = db_path
        self._init_database()
    
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
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 2. Idle Periods Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS idle_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 3. Input Activity Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS input_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    keypress_count INTEGER DEFAULT 0,
                    mouse_click_count INTEGER DEFAULT 0,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 4. Focus Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    was_interrupted BOOLEAN DEFAULT FALSE,
                    duration INTEGER NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 5. Breaks Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS breaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # 6. Browser Activity Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS browser_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    url TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_start_time ON app_usage(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_app_name ON app_usage(app_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_idle_periods_start_time ON idle_periods(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_input_activity_timestamp ON input_activity(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_focus_sessions_start_time ON focus_sessions(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_breaks_start_time ON breaks(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_browser_activity_start_time ON browser_activity(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_browser_activity_domain ON browser_activity(domain)")
            
            conn.commit()
    
    # App Usage Methods
    def insert_app_usage(self, app_name: str, start_time: int, end_time: int, duration: int) -> int:
        """Insert app usage record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_usage (app_name, start_time, end_time, duration)
                VALUES (?, ?, ?, ?)
            """, (app_name, start_time, end_time, duration))
            conn.commit()
            return cursor.lastrowid
    
    def get_app_usage(self, limit: int = 100) -> List[Dict]:
        """Get recent app usage records"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM app_usage 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Idle Periods Methods
    def insert_idle_period(self, start_time: int, end_time: int, duration: int) -> int:
        """Insert idle period record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO idle_periods (start_time, end_time, duration)
                VALUES (?, ?, ?)
            """, (start_time, end_time, duration))
            conn.commit()
            return cursor.lastrowid
    
    def get_idle_periods(self, limit: int = 100) -> List[Dict]:
        """Get recent idle periods"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM idle_periods 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Input Activity Methods
    def insert_input_activity(self, timestamp: int, keypress_count: int, mouse_click_count: int) -> int:
        """Insert input activity record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO input_activity (timestamp, keypress_count, mouse_click_count)
                VALUES (?, ?, ?)
            """, (timestamp, keypress_count, mouse_click_count))
            conn.commit()
            return cursor.lastrowid
    
    def get_input_activity(self, limit: int = 100) -> List[Dict]:
        """Get recent input activity"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM input_activity 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Focus Sessions Methods
    def insert_focus_session(self, start_time: int, end_time: int, was_interrupted: bool, duration: int) -> int:
        """Insert focus session record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO focus_sessions (start_time, end_time, was_interrupted, duration)
                VALUES (?, ?, ?, ?)
            """, (start_time, end_time, was_interrupted, duration))
            conn.commit()
            return cursor.lastrowid
    
    def get_focus_sessions(self, limit: int = 100) -> List[Dict]:
        """Get recent focus sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM focus_sessions 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Breaks Methods
    def insert_break(self, start_time: int, end_time: int, break_type: str) -> int:
        """Insert break record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO breaks (start_time, end_time, type)
                VALUES (?, ?, ?)
            """, (start_time, end_time, break_type))
            conn.commit()
            return cursor.lastrowid
    
    def get_breaks(self, limit: int = 100) -> List[Dict]:
        """Get recent breaks"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM breaks 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Browser Activity Methods
    def insert_browser_activity(self, domain: str, url: str, start_time: int, end_time: int, duration: int) -> int:
        """Insert browser activity record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO browser_activity (domain, url, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?)
            """, (domain, url, start_time, end_time, duration))
            conn.commit()
            return cursor.lastrowid
    
    def get_browser_activity(self, limit: int = 100) -> List[Dict]:
        """Get recent browser activity"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM browser_activity 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Utility Methods
    def get_database_stats(self) -> Dict[str, int]:
        """Get count of records in each table"""
        stats = {}
        tables = ['app_usage', 'idle_periods', 'input_activity', 'focus_sessions', 'breaks', 'browser_activity']
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
        
        return stats
    
    def clear_all_data(self):
        """Clear all data from all tables"""
        tables = ['app_usage', 'idle_periods', 'input_activity', 'focus_sessions', 'breaks', 'browser_activity']
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()

# Global database instance
db = CerebroDB()
