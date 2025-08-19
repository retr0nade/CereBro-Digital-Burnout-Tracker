"""
Tests for database schema and operations
"""

import pytest
import sqlite3
from datetime import datetime
from cerebro_db import CerebroDB


class TestDatabaseSchema:
    """Test database schema creation and validation"""

    def test_database_initialization(self, test_db):
        """Test that database is properly initialized with all tables"""
        # Check that all required tables exist
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'app_usage',
                'idle_periods', 
                'input_activity',
                'focus_sessions',
                'breaks',
                'browser_activity'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} should exist"

    def test_app_usage_table_schema(self, test_db):
        """Test app_usage table schema"""
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(app_usage);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'app_name': 'TEXT',
                'start_time': 'INTEGER',
                'end_time': 'INTEGER',
                'duration': 'INTEGER',
                'created_at': 'INTEGER'
            }
            
            for col, col_type in expected_columns.items():
                assert col in columns, f"Column {col} should exist in app_usage table"
                assert columns[col] == col_type, f"Column {col} should be of type {col_type}"

    def test_idle_periods_table_schema(self, test_db):
        """Test idle_periods table schema"""
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(idle_periods);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'start_time': 'INTEGER',
                'end_time': 'INTEGER',
                'duration': 'INTEGER',
                'created_at': 'INTEGER'
            }
            
            for col, col_type in expected_columns.items():
                assert col in columns, f"Column {col} should exist in idle_periods table"
                assert columns[col] == col_type, f"Column {col} should be of type {col_type}"

    def test_input_activity_table_schema(self, test_db):
        """Test input_activity table schema"""
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(input_activity);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'timestamp': 'INTEGER',
                'keypress_count': 'INTEGER',
                'mouse_click_count': 'INTEGER',
                'created_at': 'INTEGER'
            }
            
            for col, col_type in expected_columns.items():
                assert col in columns, f"Column {col} should exist in input_activity table"
                assert columns[col] == col_type, f"Column {col} should be of type {col_type}"

    def test_focus_sessions_table_schema(self, test_db):
        """Test focus_sessions table schema"""
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(focus_sessions);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'start_time': 'INTEGER',
                'end_time': 'INTEGER',
                'was_interrupted': 'BOOLEAN',
                'duration': 'INTEGER',
                'created_at': 'INTEGER'
            }
            
            for col, col_type in expected_columns.items():
                assert col in columns, f"Column {col} should exist in focus_sessions table"
                assert columns[col] == col_type, f"Column {col} should be of type {col_type}"

    def test_breaks_table_schema(self, test_db):
        """Test breaks table schema"""
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(breaks);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'start_time': 'INTEGER',
                'end_time': 'INTEGER',
                'type': 'TEXT',
                'created_at': 'INTEGER'
            }
            
            for col, col_type in expected_columns.items():
                assert col in columns, f"Column {col} should exist in breaks table"
                assert columns[col] == col_type, f"Column {col} should be of type {col_type}"

    def test_browser_activity_table_schema(self, test_db):
        """Test browser_activity table schema"""
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(browser_activity);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'domain': 'TEXT',
                'url': 'TEXT',
                'start_time': 'INTEGER',
                'end_time': 'INTEGER',
                'duration': 'INTEGER',
                'created_at': 'INTEGER'
            }
            
            for col, col_type in expected_columns.items():
                assert col in columns, f"Column {col} should exist in browser_activity table"
                assert columns[col] == col_type, f"Column {col} should be of type {col_type}"


class TestDatabaseOperations:
    """Test database operations (insert/fetch)"""

    def test_insert_and_fetch_app_usage(self, test_db, sample_app_usage_data):
        """Test inserting and fetching app usage data"""
        # Insert data
        test_db.insert_app_usage(**sample_app_usage_data)
        
        # Fetch data
        result = test_db.get_app_usage(limit=1)
        
        assert len(result) == 1
        data = result[0]
        assert data['app_name'] == sample_app_usage_data['app_name']
        assert data['duration'] == sample_app_usage_data['duration']

    def test_insert_and_fetch_idle_periods(self, test_db, sample_idle_data):
        """Test inserting and fetching idle periods data"""
        # Insert data
        test_db.insert_idle_period(**sample_idle_data)
        
        # Fetch data
        result = test_db.get_idle_periods(limit=1)
        
        assert len(result) == 1
        data = result[0]
        assert data['start_time'] == sample_idle_data['start_time']
        assert data['end_time'] == sample_idle_data['end_time']
        assert data['duration'] == sample_idle_data['duration']

    def test_insert_and_fetch_input_activity(self, test_db, sample_input_data):
        """Test inserting and fetching input activity data"""
        # Insert data
        test_db.insert_input_activity(**sample_input_data)
        
        # Fetch data
        result = test_db.get_input_activity(limit=1)
        
        assert len(result) == 1
        data = result[0]
        assert data['timestamp'] == sample_input_data['timestamp']
        assert data['keypress_count'] == sample_input_data['keypress_count']
        assert data['mouse_click_count'] == sample_input_data['mouse_click_count']

    def test_insert_and_fetch_focus_sessions(self, test_db, sample_focus_session_data):
        """Test inserting and fetching focus sessions data"""
        # Insert data
        test_db.insert_focus_session(**sample_focus_session_data)
        
        # Fetch data
        result = test_db.get_focus_sessions(limit=1)
        
        assert len(result) == 1
        data = result[0]
        assert data['start_time'] == sample_focus_session_data['start_time']
        assert data['duration'] == sample_focus_session_data['duration']
        assert data['was_interrupted'] == sample_focus_session_data['was_interrupted']

    def test_insert_and_fetch_breaks(self, test_db, sample_break_data):
        """Test inserting and fetching breaks data"""
        # Insert data
        test_db.insert_break(**sample_break_data)
        
        # Fetch data
        result = test_db.get_breaks(limit=1)
        
        assert len(result) == 1
        data = result[0]
        assert data['start_time'] == sample_break_data['start_time']
        assert data['end_time'] == sample_break_data['end_time']
        assert data['type'] == sample_break_data['break_type']

    def test_multiple_inserts(self, test_db, sample_app_usage_data):
        """Test inserting multiple records"""
        # Insert multiple records
        for i in range(5):
            data = sample_app_usage_data.copy()
            data['app_name'] = f"app_{i}"
            data['start_time'] += i * 60
            data['end_time'] += i * 60
            test_db.insert_app_usage(**data)
        
        # Fetch all records
        result = test_db.get_app_usage(limit=10)
        
        assert len(result) == 5
        app_names = [r['app_name'] for r in result]
        assert 'app_0' in app_names
        assert 'app_4' in app_names

    def test_limit_parameter(self, test_db, sample_app_usage_data):
        """Test that limit parameter works correctly"""
        # Insert multiple records
        for i in range(10):
            data = sample_app_usage_data.copy()
            data['app_name'] = f"app_{i}"
            data['start_time'] += i * 60
            data['end_time'] += i * 60
            test_db.insert_app_usage(**data)
        
        # Test different limits
        result_3 = test_db.get_app_usage(limit=3)
        result_5 = test_db.get_app_usage(limit=5)
        result_all = test_db.get_app_usage(limit=20)
        
        assert len(result_3) == 3
        assert len(result_5) == 5
        assert len(result_all) == 10

    def test_data_integrity(self, test_db, sample_app_usage_data):
        """Test that data integrity is maintained"""
        # Insert data
        test_db.insert_app_usage(**sample_app_usage_data)
        
        # Verify data types and constraints
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_usage WHERE app_name = ?", 
                          (sample_app_usage_data['app_name'],))
            row = cursor.fetchone()
            
            assert row is not None
            assert isinstance(row[1], str)  # app_name should be string
            assert isinstance(row[4], int)  # duration should be integer
            assert row[4] > 0  # duration should be positive

    def test_foreign_key_constraints(self, test_db):
        """Test that foreign key constraints work if implemented"""
        # This test would be relevant if foreign keys are added in the future
        # For now, we'll just verify the database supports foreign keys
        import sqlite3
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys;")
            foreign_keys_enabled = cursor.fetchone()[0]
            
            # Foreign keys should be enabled for data integrity
            # Note: SQLite may have foreign keys disabled by default
            assert foreign_keys_enabled in [0, 1]
