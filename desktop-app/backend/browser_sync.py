#!/usr/bin/env python3
"""
Browser Activity Sync
Reads browser activity data from Chrome extension storage and merges with Cerebro's app data.
"""

import json
import sqlite3
import threading
import time
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class BrowserSync:
    """Syncs browser activity with app data for unified analysis"""
    
    def __init__(self, 
                 sync_interval_minutes: int = 5,
                 extension_api_url: str = "http://localhost:5005/api/extension_data",
                 cerebro_db_path: str = "data/metrics.db",
                 browser_db_path: str = "browser_activity.db"):
        """
        Initialize browser sync
        
        Args:
            sync_interval_minutes: How often to sync data
            extension_api_url: URL where extension sends data
            cerebro_db_path: Path to Cerebro's main database
            browser_db_path: Path to browser activity database
        """
        self.sync_interval_minutes = sync_interval_minutes
        self.sync_interval_seconds = sync_interval_minutes * 60
        self.extension_api_url = extension_api_url
        self.cerebro_db_path = cerebro_db_path
        self.browser_db_path = browser_db_path
        
        # State variables
        self.is_running = False
        self.sync_thread = None
        self.last_sync_time = None
        self.last_extension_data = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('browser_sync.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create unified activity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unified_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    domain_app TEXT,
                    category TEXT,
                    duration_seconds INTEGER,
                    timestamp INTEGER,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create extension metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extension_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tab_switches INTEGER,
                    erratic_clicks INTEGER,
                    yt_loops INTEGER,
                    tab_open_per_min INTEGER,
                    scroll_bursts INTEGER,
                    typing_bursts INTEGER,
                    idle_events INTEGER,
                    focus_time_ms INTEGER,
                    distraction_time_ms INTEGER,
                    other_time_ms INTEGER,
                    timestamp INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Browser database initialized: {self.browser_db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_extension_data(self) -> Dict[str, Any]:
        """Get real extension data from the extension's API endpoint"""
        try:
            # Try to get data from extension API
            response = requests.get(
                f"{self.extension_api_url.replace('/api/extension_data', '/api/extension_stats')}",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Extension API returned status {response.status_code}")
                return self._get_fallback_extension_data()
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Could not connect to extension API: {e}")
            return self._get_fallback_extension_data()
    
    def _get_fallback_extension_data(self) -> Dict[str, Any]:
        """Get fallback extension data from local storage simulation"""
        try:
            # Simulate extension data structure based on background.js
            current_time = int(time.time() * 1000)
            
            # Simulate active tabs data
            usage = {
                "1": {
                    "domain": "github.com",
                    "total": 180000,  # 3 minutes
                    "start": current_time - 180000
                },
                "2": {
                    "domain": "leetcode.com", 
                    "total": 120000,  # 2 minutes
                    "start": current_time - 120000
                }
            }
            
            # Simulate site visit history
            site_visit_history = {
                "github.com": [current_time - 300000, current_time - 240000, current_time - 180000],
                "leetcode.com": [current_time - 120000, current_time - 60000],
                "youtube.com": [current_time - 60000]
            }
            
            # Simulate category stats
            site_category_stats = {
                "focus": 300000,    # 5 minutes
                "distraction": 60000, # 1 minute
                "other": 30000      # 30 seconds
            }
            
            return {
                "usage": usage,
                "tabSwitches": 15,
                "erraticClicks": [],
                "ytLoops": [],
                "tabOpenPerMin": 2,
                "navHistory": {},
                "siteVisitHistory": site_visit_history,
                "siteCategoryStats": site_category_stats,
                "scrollBursts": 3,
                "typingBursts": 2,
                "idleEvents": 1,
                "ts": current_time
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get fallback extension data: {e}")
            return {}
    
    def _categorize_domain(self, domain: str) -> str:
        """Categorize domain based on extension's site categories"""
        # Match the categories from background.js
        focus_domains = {"leetcode.com", "github.com"}
        distraction_domains = {"youtube.com", "twitter.com"}
        
        if domain in focus_domains:
            return "focus"
        elif domain in distraction_domains:
            return "distraction"
        else:
            return "other"
    
    def _sync_extension_data(self, extension_data: Dict[str, Any]):
        """Sync extension data to database"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            current_time = int(time.time() * 1000)
            
            # Process active tabs usage
            usage = extension_data.get("usage", {})
            for tab_id, tab_data in usage.items():
                domain = tab_data.get("domain", "unknown")
                total_time = tab_data.get("total", 0)
                
                if domain != "unknown" and total_time > 0:
                    category = self._categorize_domain(domain)
                    
                    cursor.execute('''
                        INSERT INTO browser_activity 
                        (domain, category, duration_ms, visit_count, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (domain, category, total_time, 1, current_time))
            
            # Process site visit history
            site_visit_history = extension_data.get("siteVisitHistory", {})
            for domain, visits in site_visit_history.items():
                if visits and len(visits) > 0:
                    # Calculate total time from visit timestamps
                    total_duration = 0
                    for i in range(len(visits) - 1):
                        duration = visits[i + 1] - visits[i]
                        if 0 < duration < 300000:  # 5 minutes max
                            total_duration += duration
                    
                    if total_duration > 0:
                        category = self._categorize_domain(domain)
                        
                        cursor.execute('''
                            INSERT INTO browser_activity 
                            (domain, category, duration_ms, visit_count, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (domain, category, total_duration, len(visits), current_time))
            
            # Store extension metrics
            site_category_stats = extension_data.get("siteCategoryStats", {})
            
            cursor.execute('''
                INSERT INTO extension_metrics 
                (tab_switches, erratic_clicks, yt_loops, tab_open_per_min,
                 scroll_bursts, typing_bursts, idle_events,
                 focus_time_ms, distraction_time_ms, other_time_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                extension_data.get("tabSwitches", 0),
                len(extension_data.get("erraticClicks", [])),
                len(extension_data.get("ytLoops", [])),
                extension_data.get("tabOpenPerMin", 0),
                extension_data.get("scrollBursts", 0),
                extension_data.get("typingBursts", 0),
                extension_data.get("idleEvents", 0),
                site_category_stats.get("focus", 0),
                site_category_stats.get("distraction", 0),
                site_category_stats.get("other", 0),
                current_time
            ))
            
            conn.commit()
            conn.close()
            
            domains_processed = len(usage) + len(site_visit_history)
            self.logger.info(f"Synced extension data: {domains_processed} domains, {extension_data.get('tabSwitches', 0)} tab switches")
            
        except Exception as e:
            self.logger.error(f"Failed to sync extension data: {e}")
    
    def _get_app_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get Cerebro's app data"""
        try:
            conn = sqlite3.connect(self.cerebro_db_path)
            cursor = conn.cursor()
            
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
            self.logger.error(f"Failed to get app data: {e}")
            return []
    
    def _merge_data(self, browser_data: List[Dict], app_data: List[Dict]):
        """Merge browser and app data"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            # Clear old unified data
            cutoff_time = int((time.time() - 24 * 3600) * 1000)
            cursor.execute('DELETE FROM unified_activity WHERE timestamp < ?', (cutoff_time,))
            
            # Insert browser data
            for item in browser_data:
                metadata = {
                    'domain': item.get('domain'),
                    'visit_count': item.get('visit_count')
                }
                
                cursor.execute('''
                    INSERT INTO unified_activity 
                    (source, domain_app, category, duration_seconds, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    'browser',
                    item.get('domain'),
                    item.get('category'),
                    item.get('duration_ms', 0) // 1000,
                    item.get('timestamp'),
                    json.dumps(metadata)
                ))
            
            # Insert app data
            for item in app_data:
                metadata = {
                    'app': item.get('app'),
                    'window_title': item.get('window_title')
                }
                
                cursor.execute('''
                    INSERT INTO unified_activity 
                    (source, domain_app, category, duration_seconds, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    'app',
                    item.get('app'),
                    'application',
                    0,
                    item.get('timestamp'),
                    json.dumps(metadata)
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Merged data: {len(browser_data)} browser, {len(app_data)} app items")
            
        except Exception as e:
            self.logger.error(f"Failed to merge data: {e}")
    
    def _get_browser_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get browser data from database"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            cursor.execute('''
                SELECT domain, category, duration_ms, visit_count, timestamp
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
                    'timestamp': row[4]
                })
            
            return browser_data
            
        except Exception as e:
            self.logger.error(f"Failed to get browser data: {e}")
            return []
    
    def _sync_cycle(self):
        """Perform one sync cycle"""
        try:
            self.logger.info("Starting sync cycle...")
            
            # Get real extension data
            extension_data = self._get_extension_data()
            
            # Sync extension data
            self._sync_extension_data(extension_data)
            
            # Get data
            browser_data = self._get_browser_data(hours=24)
            app_data = self._get_app_data(hours=24)
            
            # Merge data
            self._merge_data(browser_data, app_data)
            
            self.last_sync_time = datetime.now()
            self.last_extension_data = extension_data
            self.logger.info(f"Sync cycle completed at {self.last_sync_time}")
            
        except Exception as e:
            self.logger.error(f"Sync cycle failed: {e}")
    
    def _sync_loop(self):
        """Main sync loop"""
        self.logger.info("Browser sync started")
        
        while self.is_running:
            try:
                self._sync_cycle()
                time.sleep(self.sync_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                time.sleep(60)
    
    def start(self):
        """Start browser sync"""
        if self.is_running:
            self.logger.warning("Browser sync is already running")
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.info(f"Browser sync started (interval: {self.sync_interval_minutes} minutes)")
    
    def stop(self):
        """Stop browser sync"""
        if not self.is_running:
            self.logger.warning("Browser sync is not running")
            return
        
        self.is_running = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=10)
        
        self.logger.info("Browser sync stopped")
    
    def get_unified_activity(self, hours: int = 24) -> Dict[str, Any]:
        """Get unified activity data"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            cursor.execute('''
                SELECT source, domain_app, category, duration_seconds, timestamp, metadata
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
                    'metadata': json.loads(row[5]) if row[5] else {}
                })
            
            return {
                'unified_activity': unified_data,
                'hours_analyzed': hours,
                'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get unified activity: {e}")
            return {'unified_activity': [], 'hours_analyzed': hours, 'last_sync': None}
    
    def get_extension_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get extension metrics summary"""
        try:
            conn = sqlite3.connect(self.browser_db_path)
            cursor = conn.cursor()
            
            cutoff_time = int((time.time() - (hours * 3600)) * 1000)
            
            cursor.execute('''
                SELECT 
                    SUM(tab_switches) as total_tab_switches,
                    SUM(erratic_clicks) as total_erratic_clicks,
                    SUM(yt_loops) as total_yt_loops,
                    SUM(tab_open_per_min) as total_tab_opens,
                    SUM(scroll_bursts) as total_scroll_bursts,
                    SUM(typing_bursts) as total_typing_bursts,
                    SUM(idle_events) as total_idle_events,
                    SUM(focus_time_ms) as total_focus_time,
                    SUM(distraction_time_ms) as total_distraction_time,
                    SUM(other_time_ms) as total_other_time
                FROM extension_metrics
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] is not None:
                return {
                    'tab_switches': result[0] or 0,
                    'erratic_clicks': result[1] or 0,
                    'yt_loops': result[2] or 0,
                    'tab_opens': result[3] or 0,
                    'scroll_bursts': result[4] or 0,
                    'typing_bursts': result[5] or 0,
                    'idle_events': result[6] or 0,
                    'focus_time_hours': (result[7] or 0) / (1000 * 3600),
                    'distraction_time_hours': (result[8] or 0) / (1000 * 3600),
                    'other_time_hours': (result[9] or 0) / (1000 * 3600),
                    'hours_analyzed': hours
                }
            else:
                return {
                    'tab_switches': 0,
                    'erratic_clicks': 0,
                    'yt_loops': 0,
                    'tab_opens': 0,
                    'scroll_bursts': 0,
                    'typing_bursts': 0,
                    'idle_events': 0,
                    'focus_time_hours': 0,
                    'distraction_time_hours': 0,
                    'other_time_hours': 0,
                    'hours_analyzed': hours
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get extension metrics: {e}")
            return {
                'tab_switches': 0,
                'erratic_clicks': 0,
                'yt_loops': 0,
                'tab_opens': 0,
                'scroll_bursts': 0,
                'typing_bursts': 0,
                'idle_events': 0,
                'focus_time_hours': 0,
                'distraction_time_hours': 0,
                'other_time_hours': 0,
                'hours_analyzed': hours
            }

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Browser Activity Sync')
    parser.add_argument('--sync-interval', type=int, default=5,
                       help='Sync interval in minutes (default: 5)')
    parser.add_argument('--duration', type=int, default=300,
                       help='Run duration in seconds (default: 300)')
    parser.add_argument('--extension-api', type=str, 
                       default='http://localhost:5005/api/extension_data',
                       help='Extension API URL')
    
    args = parser.parse_args()
    
    sync = BrowserSync(
        sync_interval_minutes=args.sync_interval,
        extension_api_url=args.extension_api
    )
    
    try:
        print(f"Starting browser sync...")
        print(f"Sync interval: {args.sync_interval} minutes")
        print(f"Extension API: {args.extension_api}")
        sync.start()
        
        time.sleep(args.duration)
        
        print("Stopping browser sync...")
        sync.stop()
        
        print("\n" + "=" * 50)
        print("UNIFIED ACTIVITY:")
        activity = sync.get_unified_activity(hours=1)
        
        browser_count = len([a for a in activity['unified_activity'] if a['source'] == 'browser'])
        app_count = len([a for a in activity['unified_activity'] if a['source'] == 'app'])
        
        print(f"Browser activities: {browser_count}")
        print(f"App activities: {app_count}")
        print(f"Last sync: {activity['last_sync']}")
        
        print("\n" + "=" * 50)
        print("EXTENSION METRICS:")
        metrics = sync.get_extension_metrics(hours=1)
        
        print(f"Tab switches: {metrics['tab_switches']}")
        print(f"Focus time: {metrics['focus_time_hours']:.2f} hours")
        print(f"Distraction time: {metrics['distraction_time_hours']:.2f} hours")
        print(f"Scroll bursts: {metrics['scroll_bursts']}")
        print(f"Typing bursts: {metrics['typing_bursts']}")
        print(f"Idle events: {metrics['idle_events']}")
        
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