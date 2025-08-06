#!/usr/bin/env python3
"""
Browser Activity Sync
Reads browser activity data from Chrome extension storage and merges it with Cerebro's app data
for unified analysis. Syncs every X minutes as configured.
"""

import json
import sqlite3
import threading
import time
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path

class BrowserActivitySync:
    """Syncs browser activity data with Cerebro's app data for unified analysis"""
    
    def __init__(self, 
                 sync_interval_minutes: int = 5,
                 extension_data_path: str = "extension_data",
                 cerebro_db_path: str = "data/metrics.db",
                 browser_db_path: str = "browser_activity.db",
                 enable_http_sync: bool = True,
                 cerebro_api_url: str = "http://localhost:5000/api"):
        """
        Initialize browser activity sync
        
        Args:
            sync_interval_minutes: How often to sync data (default: 5 minutes)
            extension_data_path: Path to extension data directory
            cerebro_db_path: Path to Cerebro's main database
            browser_db_path: Path to browser activity database
            enable_http_sync: Whether to sync via HTTP API
            cerebro_api_url: URL of Cerebro's API
        """
        self.sync_interval_minutes = sync_interval_minutes
        self.sync_interval_seconds = sync_interval_minutes * 60
        self.extension_data_path = Path(extension_data_path)
        self.cerebro_db_path = cerebro_db_path
        self.browser_db_path = browser_db_path
        self.enable_http_sync = enable_http_sync
        self.cerebro_api_url = cerebro_api_url
        
        # State variables
        self.is_running = False
        self.sync_thread = None
        self.last_sync_time = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('browser_activity_sync.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize databases
        self._init_databases()
        
        # Create extension data directory if it doesn't exist
        self.extension_data_path.mkdir(exist_ok=True)
    
    def _init_databases(self):
        """Initialize browser activity database"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            # Create browser activity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS browser_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    category TEXT,
                    duration_ms INTEGER,
                    visit_count INTEGER DEFAULT 1,
                    timestamp INTEGER,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create tab switches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tab_switches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tab_id INTEGER,
                    domain TEXT,
                    switch_time INTEGER,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create site categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create unified activity table (merged data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unified_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,  -- 'browser' or 'app'
                    domain_app TEXT,
                    category TEXT,
                    duration_seconds INTEGER,
                    timestamp INTEGER,
                    session_id TEXT,
                    metadata TEXT,  -- JSON metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_browser_domain 
                ON browser_activity(domain)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_browser_timestamp 
                ON browser_activity(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_unified_source 
                ON unified_activity(source)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_unified_timestamp 
                ON unified_activity(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Browser activity database initialized: {self.browser_db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser database: {e}")
            raise
    
    def _read_extension_data(self) -> Dict[str, Any]:
        """Read browser extension data from local storage"""
        try:
            extension_data = {}
            
            # Read from extension data directory
            extension_files = [
                "tab_switches.json",
                "site_visit_history.json", 
                "site_category_stats.json",
                "active_tabs.json",
                "erratic_clicks.json",
                "yt_loops.json"
            ]
            
            for filename in extension_files:
                file_path = self.extension_data_path / filename
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        extension_data[filename.replace('.json', '')] = json.load(f)
                else:
                    # Create empty structure if file doesn't exist
                    if filename == "tab_switches.json":
                        extension_data["tab_switches"] = 0
                    elif filename == "site_visit_history.json":
                        extension_data["site_visit_history"] = {}
                    elif filename == "site_category_stats.json":
                        extension_data["site_category_stats"] = {"focus": 0, "distraction": 0, "other": 0}
                    elif filename == "active_tabs.json":
                        extension_data["active_tabs"] = {}
                    elif filename == "erratic_clicks.json":
                        extension_data["erratic_clicks"] = []
                    elif filename == "yt_loops.json":
                        extension_data["yt_loops"] = []
            
            return extension_data
            
        except Exception as e:
            self.logger.error(f"Failed to read extension data: {e}")
            return {}
    
    def _sync_browser_activity(self, extension_data: Dict[str, Any]):
        """Sync browser activity data to database"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            current_time = int(time.time() * 1000)  # Milliseconds
            
            # Process site visit history
            site_visit_history = extension_data.get("site_visit_history", {})
            for domain, visits in site_visit_history.items():
                if visits and len(visits) > 0:
                    # Calculate total time spent on domain
                    total_duration = 0
                    for i in range(len(visits) - 1):
                        duration = visits[i + 1] - visits[i]
                        if 0 < duration < 300000:  # Between 0 and 5 minutes
                            total_duration += duration
                    
                    # Determine category
                    category = self._categorize_domain(domain)
                    
                    # Store browser activity
                    cursor.execute('''
                        INSERT INTO browser_activity 
                        (domain, category, duration_ms, visit_count, timestamp, session_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (domain, category, total_duration, len(visits), current_time, f"session_{current_time}"))
            
            # Process site category stats
            site_category_stats = extension_data.get("site_category_stats", {})
            for category, duration_ms in site_category_stats.items():
                if duration_ms > 0:
                    # Store category summary
                    cursor.execute('''
                        INSERT INTO browser_activity 
                        (domain, category, duration_ms, visit_count, timestamp, session_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (f"category_{category}", category, duration_ms, 1, current_time, f"session_{current_time}"))
            
            # Process tab switches
            tab_switches = extension_data.get("tab_switches", 0)
            if tab_switches > 0:
                cursor.execute('''
                    INSERT INTO tab_switches 
                    (tab_id, domain, switch_time, session_id)
                    VALUES (?, ?, ?, ?)
                ''', (0, "tab_switch_count", current_time, f"session_{current_time}"))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Synced browser activity: {len(site_visit_history)} domains, {tab_switches} tab switches")
            
        except Exception as e:
            self.logger.error(f"Failed to sync browser activity: {e}")
    
    def _categorize_domain(self, domain: str) -> str:
        """Categorize domain based on predefined rules"""
        focus_domains = {
            "leetcode.com", "github.com", "stackoverflow.com", "docs.python.org",
            "developer.mozilla.org", "w3schools.com", "geeksforgeeks.org",
            "hackerrank.com", "codewars.com", "exercism.io", "freecodecamp.org"
        }
        
        distraction_domains = {
            "youtube.com", "twitter.com", "facebook.com", "instagram.com",
            "tiktok.com", "reddit.com", "netflix.com", "spotify.com",
            "twitch.tv", "discord.com", "slack.com"
        }
        
        if domain in focus_domains:
            return "focus"
        elif domain in distraction_domains:
            return "distraction"
        else:
            return "other"
    
    def _get_cerebro_app_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get Cerebro's app usage data"""
        try:
            conn = sqlite3.connect(self.cerebro_db_path)
            cursor = conn.cursor()
            
            # Get app usage data from last N hours
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            cursor.execute('''
                SELECT app, win_title, ts 
                FROM app_usage 
                WHERE ts >= ?
                ORDER BY ts DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            app_data = []
            for row in results:
                app_data.append({
                    'app': row[0],
                    'window_title': row[1],
                    'timestamp': row[2]
                })
            
            return app_data
            
        except Exception as e:
            self.logger.error(f"Failed to get Cerebro app data: {e}")
            return []
    
    def _merge_activity_data(self, browser_data: List[Dict], app_data: List[Dict]):
        """Merge browser and app activity data for unified analysis"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            # Clear previous unified data (keep only last 24 hours)
            cutoff_time = int((time.time() - 24 * 3600) * 1000)
            cursor.execute('DELETE FROM unified_activity WHERE timestamp < ?', (cutoff_time,))
            
            # Insert browser activity
            for browser_item in browser_data:
                metadata = {
                    'domain': browser_item.get('domain'),
                    'visit_count': browser_item.get('visit_count'),
                    'category': browser_item.get('category')
                }
                
                cursor.execute('''
                    INSERT INTO unified_activity 
                    (source, domain_app, category, duration_seconds, timestamp, session_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'browser',
                    browser_item.get('domain'),
                    browser_item.get('category'),
                    browser_item.get('duration_ms', 0) // 1000,  # Convert to seconds
                    browser_item.get('timestamp'),
                    browser_item.get('session_id'),
                    json.dumps(metadata)
                ))
            
            # Insert app activity
            for app_item in app_data:
                metadata = {
                    'app': app_item.get('app'),
                    'window_title': app_item.get('window_title')
                }
                
                cursor.execute('''
                    INSERT INTO unified_activity 
                    (source, domain_app, category, duration_seconds, timestamp, session_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'app',
                    app_item.get('app'),
                    'application',
                    0,  # Duration not available in app data
                    app_item.get('timestamp'),
                    f"session_{app_item.get('timestamp')}",
                    json.dumps(metadata)
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Merged activity data: {len(browser_data)} browser items, {len(app_data)} app items")
            
        except Exception as e:
            self.logger.error(f"Failed to merge activity data: {e}")
    
    def _get_browser_activity_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get browser activity data from database"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            cursor.execute('''
                SELECT domain, category, duration_ms, visit_count, timestamp, session_id
                FROM browser_activity
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            browser_data = []
            for row in results:
                browser_data.append({
                    'domain': row[0],
                    'category': row[1],
                    'duration_ms': row[2],
                    'visit_count': row[3],
                    'timestamp': row[4],
                    'session_id': row[5]
                })
            
            return browser_data
            
        except Exception as e:
            self.logger.error(f"Failed to get browser activity data: {e}")
            return []
    
    def _sync_via_http(self, unified_data: Dict[str, Any]):
        """Sync unified data via HTTP API"""
        if not self.enable_http_sync:
            return
        
        try:
            # Send unified activity data to Cerebro API
            api_url = f"{self.cerebro_api_url}/unified_activity"
            
            response = requests.post(
                api_url,
                json=unified_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Successfully synced unified data via HTTP API")
            else:
                self.logger.warning(f"HTTP sync failed with status {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"HTTP sync failed: {e}")
    
    def _sync_cycle(self):
        """Perform one sync cycle"""
        try:
            self.logger.info("Starting sync cycle...")
            
            # Read extension data
            extension_data = self._read_extension_data()
            
            # Sync browser activity to database
            self._sync_browser_activity(extension_data)
            
            # Get browser and app data
            browser_data = self._get_browser_activity_data(hours=24)
            app_data = self._get_cerebro_app_data(hours=24)
            
            # Merge data for unified analysis
            self._merge_activity_data(browser_data, app_data)
            
            # Prepare unified data for HTTP sync
            unified_data = {
                'browser_activity': browser_data,
                'app_activity': app_data,
                'sync_timestamp': int(time.time() * 1000),
                'sync_interval_minutes': self.sync_interval_minutes
            }
            
            # Sync via HTTP if enabled
            self._sync_via_http(unified_data)
            
            self.last_sync_time = datetime.now()
            self.logger.info(f"Sync cycle completed at {self.last_sync_time}")
            
        except Exception as e:
            self.logger.error(f"Sync cycle failed: {e}")
    
    def _sync_loop(self):
        """Main sync loop"""
        self.logger.info("Browser activity sync started")
        
        while self.is_running:
            try:
                self._sync_cycle()
                time.sleep(self.sync_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def start(self):
        """Start browser activity sync"""
        if self.is_running:
            self.logger.warning("Browser activity sync is already running")
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.info(f"Browser activity sync started (interval: {self.sync_interval_minutes} minutes)")
    
    def stop(self):
        """Stop browser activity sync"""
        if not self.is_running:
            self.logger.warning("Browser activity sync is not running")
            return
        
        self.is_running = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=10)
        
        self.logger.info("Browser activity sync stopped")
    
    def get_unified_activity(self, hours: int = 24) -> Dict[str, Any]:
        """Get unified activity data"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            cursor.execute('''
                SELECT source, domain_app, category, duration_seconds, timestamp, session_id, metadata
                FROM unified_activity
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            unified_data = []
            for row in results:
                unified_data.append({
                    'source': row[0],
                    'domain_app': row[1],
                    'category': row[2],
                    'duration_seconds': row[3],
                    'timestamp': row[4],
                    'session_id': row[5],
                    'metadata': json.loads(row[6]) if row[6] else {}
                })
            
            return {
                'unified_activity': unified_data,
                'hours_analyzed': hours,
                'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get unified activity: {e}")
            return {'unified_activity': [], 'hours_analyzed': hours, 'last_sync': None}
    
    def get_activity_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary statistics"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            # Browser activity summary
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_visits,
                    SUM(duration_ms) as total_duration_ms,
                    COUNT(DISTINCT domain) as unique_domains,
                    SUM(CASE WHEN category = 'focus' THEN duration_ms ELSE 0 END) as focus_time_ms,
                    SUM(CASE WHEN category = 'distraction' THEN duration_ms ELSE 0 END) as distraction_time_ms
                FROM browser_activity
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            browser_summary = cursor.fetchone()
            
            # App activity summary
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_app_switches,
                    COUNT(DISTINCT domain_app) as unique_apps
                FROM unified_activity
                WHERE source = 'app' AND timestamp >= ?
            ''', (cutoff_time,))
            
            app_summary = cursor.fetchone()
            
            conn.close()
            
            if browser_summary and app_summary:
                total_visits, total_duration_ms, unique_domains, focus_time_ms, distraction_time_ms = browser_summary
                total_app_switches, unique_apps = app_summary
                
                return {
                    'browser_activity': {
                        'total_visits': total_visits or 0,
                        'total_duration_hours': (total_duration_ms or 0) / (1000 * 3600),
                        'unique_domains': unique_domains or 0,
                        'focus_time_hours': (focus_time_ms or 0) / (1000 * 3600),
                        'distraction_time_hours': (distraction_time_ms or 0) / (1000 * 3600)
                    },
                    'app_activity': {
                        'total_app_switches': total_app_switches or 0,
                        'unique_apps': unique_apps or 0
                    },
                    'hours_analyzed': hours,
                    'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None
                }
            else:
                return {
                    'browser_activity': {
                        'total_visits': 0,
                        'total_duration_hours': 0,
                        'unique_domains': 0,
                        'focus_time_hours': 0,
                        'distraction_time_hours': 0
                    },
                    'app_activity': {
                        'total_app_switches': 0,
                        'unique_apps': 0
                    },
                    'hours_analyzed': hours,
                    'last_sync': None
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get activity summary: {e}")
            return {
                'browser_activity': {},
                'app_activity': {},
                'hours_analyzed': hours,
                'last_sync': None
            }

def main():
    """Main function for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Browser Activity Sync')
    parser.add_argument('--sync-interval', type=int, default=5,
                       help='Sync interval in minutes (default: 5)')
    parser.add_argument('--extension-data', type=str, default='extension_data',
                       help='Path to extension data directory')
    parser.add_argument('--duration', type=int, default=300,
                       help='Run duration in seconds (default: 300)')
    parser.add_argument('--no-http-sync', action='store_true',
                       help='Disable HTTP API sync')
    parser.add_argument('--api-url', type=str, default='http://localhost:5000/api',
                       help='Cerebro API URL')
    
    args = parser.parse_args()
    
    sync = BrowserActivitySync(
        sync_interval_minutes=args.sync_interval,
        extension_data_path=args.extension_data,
        enable_http_sync=not args.no_http_sync,
        cerebro_api_url=args.api_url
    )
    
    try:
        print(f"Starting browser activity sync...")
        print(f"Sync interval: {args.sync_interval} minutes")
        print(f"Extension data path: {args.extension_data}")
        print(f"HTTP sync: {'Enabled' if not args.no_http_sync else 'Disabled'}")
        sync.start()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        print("Stopping browser activity sync...")
        sync.stop()
        
        # Show results
        print("\n" + "=" * 50)
        print("ACTIVITY SUMMARY:")
        summary = sync.get_activity_summary(hours=1)
        
        browser = summary['browser_activity']
        app = summary['app_activity']
        
        print(f"Browser Activity:")
        print(f"• Total visits: {browser['total_visits']}")
        print(f"• Total duration: {browser['total_duration_hours']:.2f} hours")
        print(f"• Unique domains: {browser['unique_domains']}")
        print(f"• Focus time: {browser['focus_time_hours']:.2f} hours")
        print(f"• Distraction time: {browser['distraction_time_hours']:.2f} hours")
        
        print(f"\nApp Activity:")
        print(f"• Total app switches: {app['total_app_switches']}")
        print(f"• Unique apps: {app['unique_apps']}")
        
        print(f"\nLast sync: {summary['last_sync']}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
        sync.stop()
        print("Test stopped by user.")
    
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sync.stop()

if __name__ == "__main__":
    main() 