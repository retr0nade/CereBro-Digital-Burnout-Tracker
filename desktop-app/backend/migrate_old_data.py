#!/usr/bin/env python3
"""
Migration script to import data from old database files into the new unified cerebro.db
"""

import sqlite3
import os
import time
from datetime import datetime
from cerebro_db import CerebroDB

class DataMigrator:
    def __init__(self):
        self.new_db = CerebroDB()
        self.migration_log = []
    
    def log_migration(self, message: str):
        """Log migration activity"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def migrate_app_usage(self):
        """Migrate app usage data from old databases"""
        old_dbs = [
            ("window_activity.db", "window_activity"),
            ("screen_time.db", "screen_time"),
            ("data/metrics.db", "app_usage")
        ]
        
        for db_file, table_name in old_dbs:
            if not os.path.exists(db_file):
                continue
                
            try:
                with sqlite3.connect(db_file) as conn:
                    cursor = conn.cursor()
                    
                    # Check what tables exist in the old database
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if table_name in tables:
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        
                        migrated_count = 0
                        for row in rows:
                            try:
                                if table_name == "window_activity":
                                    # Assuming: id, app_name, window_title, timestamp
                                    if len(row) >= 4:
                                        app_name = row[1]
                                        timestamp = row[3]
                                        # Create a session with 60-second duration
                                        self.new_db.insert_app_usage(
                                            app_name=app_name,
                                            start_time=timestamp,
                                            end_time=timestamp + 60,
                                            duration=60
                                        )
                                        migrated_count += 1
                                
                                elif table_name == "screen_time":
                                    # Assuming: id, app_name, start_time, end_time, duration
                                    if len(row) >= 5:
                                        self.new_db.insert_app_usage(
                                            app_name=row[1],
                                            start_time=row[2],
                                            end_time=row[3],
                                            duration=row[4]
                                        )
                                        migrated_count += 1
                                
                                elif table_name == "app_usage":
                                    # Assuming: id, app, win_title, ts
                                    if len(row) >= 4:
                                        app_name = row[1]
                                        timestamp = row[3]
                                        # Create a session with 60-second duration
                                        self.new_db.insert_app_usage(
                                            app_name=app_name,
                                            start_time=timestamp,
                                            end_time=timestamp + 60,
                                            duration=60
                                        )
                                        migrated_count += 1
                                        
                            except Exception as e:
                                self.log_migration(f"Error migrating row from {table_name}: {e}")
                        
                        self.log_migration(f"Migrated {migrated_count} records from {db_file}")
                        
            except Exception as e:
                self.log_migration(f"Error accessing {db_file}: {e}")
    
    def migrate_idle_data(self):
        """Migrate idle data from old databases"""
        old_dbs = [
            ("idle_activity.db", "idle_events"),
            ("data/metrics.db", "idle_events")
        ]
        
        for db_file, table_name in old_dbs:
            if not os.path.exists(db_file):
                continue
                
            try:
                with sqlite3.connect(db_file) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if table_name in tables:
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        
                        migrated_count = 0
                        for row in rows:
                            try:
                                if len(row) >= 3:
                                    # Assuming: id, seconds, ts
                                    seconds = row[1]
                                    timestamp = row[2]
                                    
                                    self.new_db.insert_idle_period(
                                        start_time=timestamp,
                                        end_time=timestamp + seconds,
                                        duration=seconds
                                    )
                                    migrated_count += 1
                                    
                            except Exception as e:
                                self.log_migration(f"Error migrating idle row: {e}")
                        
                        self.log_migration(f"Migrated {migrated_count} idle records from {db_file}")
                        
            except Exception as e:
                self.log_migration(f"Error accessing {db_file}: {e}")
    
    def migrate_input_data(self):
        """Migrate input activity data"""
        if not os.path.exists("input_activity.db"):
            return
            
        try:
            with sqlite3.connect("input_activity.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    if "input" in table.lower() or "keypress" in table.lower() or "mouse" in table.lower():
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        
                        migrated_count = 0
                        for row in rows:
                            try:
                                if len(row) >= 3:
                                    # Try to extract timestamp and counts
                                    timestamp = row[1] if len(row) > 1 else int(time.time())
                                    keypress_count = row[2] if len(row) > 2 else 0
                                    mouse_click_count = row[3] if len(row) > 3 else 0
                                    
                                    self.new_db.insert_input_activity(
                                        timestamp=timestamp,
                                        keypress_count=keypress_count,
                                        mouse_click_count=mouse_click_count
                                    )
                                    migrated_count += 1
                                    
                            except Exception as e:
                                self.log_migration(f"Error migrating input row: {e}")
                        
                        self.log_migration(f"Migrated {migrated_count} input records from {table}")
                        
        except Exception as e:
            self.log_migration(f"Error accessing input_activity.db: {e}")
    
    def migrate_focus_data(self):
        """Migrate focus session data"""
        if not os.path.exists("focus_sessions.db"):
            return
            
        try:
            with sqlite3.connect("focus_sessions.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    if "focus" in table.lower() or "session" in table.lower():
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        
                        migrated_count = 0
                        for row in rows:
                            try:
                                if len(row) >= 4:
                                    # Assuming: id, start_time, end_time, was_interrupted
                                    start_time = row[1]
                                    end_time = row[2]
                                    was_interrupted = bool(row[3])
                                    duration = end_time - start_time
                                    
                                    self.new_db.insert_focus_session(
                                        start_time=start_time,
                                        end_time=end_time,
                                        was_interrupted=was_interrupted,
                                        duration=duration
                                    )
                                    migrated_count += 1
                                    
                            except Exception as e:
                                self.log_migration(f"Error migrating focus row: {e}")
                        
                        self.log_migration(f"Migrated {migrated_count} focus records from {table}")
                        
        except Exception as e:
            self.log_migration(f"Error accessing focus_sessions.db: {e}")
    
    def migrate_break_data(self):
        """Migrate break data"""
        old_dbs = [
            ("break_activity.db", "breaks"),
            ("data/burnout_tracker.db", "break_logs")
        ]
        
        for db_file, table_name in old_dbs:
            if not os.path.exists(db_file):
                continue
                
            try:
                with sqlite3.connect(db_file) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if table_name in tables:
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        
                        migrated_count = 0
                        for row in rows:
                            try:
                                if len(row) >= 4:
                                    # Assuming: id, start_time, end_time, break_type
                                    start_time = row[1]
                                    end_time = row[2]
                                    break_type = row[3]
                                    
                                    self.new_db.insert_break(
                                        start_time=start_time,
                                        end_time=end_time,
                                        break_type=str(break_type)
                                    )
                                    migrated_count += 1
                                    
                            except Exception as e:
                                self.log_migration(f"Error migrating break row: {e}")
                        
                        self.log_migration(f"Migrated {migrated_count} break records from {db_file}")
                        
            except Exception as e:
                self.log_migration(f"Error accessing {db_file}: {e}")
    
    def migrate_browser_data(self):
        """Migrate browser activity data"""
        if not os.path.exists("browser_activity.db"):
            return
            
        try:
            with sqlite3.connect("browser_activity.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    if "browser" in table.lower() or "url" in table.lower() or "domain" in table.lower():
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        
                        migrated_count = 0
                        for row in rows:
                            try:
                                if len(row) >= 6:
                                    # Assuming: id, domain, url, start_time, end_time, duration
                                    domain = row[1]
                                    url = row[2]
                                    start_time = row[3]
                                    end_time = row[4]
                                    duration = row[5]
                                    
                                    self.new_db.insert_browser_activity(
                                        domain=domain,
                                        url=url,
                                        start_time=start_time,
                                        end_time=end_time,
                                        duration=duration
                                    )
                                    migrated_count += 1
                                    
                            except Exception as e:
                                self.log_migration(f"Error migrating browser row: {e}")
                        
                        self.log_migration(f"Migrated {migrated_count} browser records from {table}")
                        
        except Exception as e:
            self.log_migration(f"Error accessing browser_activity.db: {e}")
    
    def run_migration(self):
        """Run the complete migration process"""
        self.log_migration("Starting migration to cerebro.db...")
        
        # Migrate each data type
        self.migrate_app_usage()
        self.migrate_idle_data()
        self.migrate_input_data()
        self.migrate_focus_data()
        self.migrate_break_data()
        self.migrate_browser_data()
        
        # Show final statistics
        stats = self.new_db.get_database_stats()
        self.log_migration("Migration completed!")
        self.log_migration("Final database statistics:")
        for table, count in stats.items():
            self.log_migration(f"  {table}: {count} records")
        
        # Save migration log
        with open("migration_log.txt", "w") as f:
            f.write("\n".join(self.migration_log))
        
        self.log_migration("Migration log saved to migration_log.txt")

def main():
    """Main migration function"""
    migrator = DataMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()
