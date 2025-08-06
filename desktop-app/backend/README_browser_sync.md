# Browser Activity Sync

A Python script that reads browser activity data from Chrome extension storage and merges it with Cerebro's app data for unified analysis. Syncs every X minutes as configured.

## Features

- **Browser Data Reading**: Reads Chrome extension data from JSON files
- **App Data Integration**: Merges with Cerebro's app usage data
- **Unified Analysis**: Provides combined browser and app activity insights
- **Configurable Sync**: Adjustable sync intervals (default: 5 minutes)
- **SQLite Storage**: Persistent storage of unified activity data
- **Real-time Logging**: Comprehensive logging of sync operations
- **Domain Categorization**: Automatically categorizes websites as focus/distraction/other

## How It Works

### 1. Extension Data Structure
The script reads browser activity data from JSON files in the `extension_data/` directory:

- `site_visit_history.json`: Domain visit timestamps
- `site_category_stats.json`: Time spent in each category
- `tab_switches.json`: Number of tab switches

### 2. Data Processing
- Reads extension data from JSON files
- Categorizes domains (focus/distraction/other)
- Calculates visit durations and frequencies
- Stores processed data in SQLite database

### 3. App Data Integration
- Reads Cerebro's app usage data from `data/metrics.db`
- Merges browser and app activity into unified view
- Provides combined insights for analysis

### 4. Unified Analysis
- Single database with both browser and app data
- Time-based filtering and analysis
- Category-based statistics
- Cross-platform activity tracking

## Installation

### Prerequisites
The script uses existing dependencies from the project's `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Usage

```bash
# Basic usage with default settings (5-minute sync)
python browser_sync.py

# Custom sync interval (2 minutes)
python browser_sync.py --sync-interval 2

# Test run for 10 minutes
python browser_sync.py --duration 600

# Quick test (30 seconds, 1-minute sync)
python browser_sync.py --duration 30 --sync-interval 1
```

### Programmatic Usage

```python
from browser_sync import BrowserSync

# Create sync with custom settings
sync = BrowserSync(
    sync_interval_minutes=5,
    extension_data_path="extension_data",
    cerebro_db_path="data/metrics.db",
    browser_db_path="browser_activity.db"
)

# Start syncing
sync.start()

# ... your application logic ...

# Stop syncing
sync.stop()

# Get unified activity data
activity = sync.get_unified_activity(hours=24)
```

## Configuration

### BrowserSync Parameters
- `sync_interval_minutes`: How often to sync data (default: 5)
- `extension_data_path`: Path to extension data directory (default: "extension_data")
- `cerebro_db_path`: Path to Cerebro's main database (default: "data/metrics.db")
- `browser_db_path`: Path to browser activity database (default: "browser_activity.db")

### Domain Categorization
The script automatically categorizes domains:

**Focus Domains:**
- leetcode.com
- github.com
- stackoverflow.com

**Distraction Domains:**
- youtube.com
- twitter.com
- facebook.com

**Other Domains:**
- All other domains are categorized as "other"

## Database Schema

### Browser Activity Table
```sql
CREATE TABLE browser_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    category TEXT,
    duration_ms INTEGER,
    visit_count INTEGER DEFAULT 1,
    timestamp INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Unified Activity Table
```sql
CREATE TABLE unified_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,  -- 'browser' or 'app'
    domain_app TEXT,
    category TEXT,
    duration_seconds INTEGER,
    timestamp INTEGER,
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Extension Data Format

### site_visit_history.json
```json
{
  "github.com": [1640995200000, 1640995260000, 1640995320000],
  "leetcode.com": [1640995440000, 1640995500000],
  "youtube.com": [1640995620000, 1640995680000]
}
```

### site_category_stats.json
```json
{
  "focus": 1800000,
  "distraction": 600000,
  "other": 300000
}
```

### tab_switches.json
```json
42
```

## API Integration

The script can be integrated with Cerebro's API for real-time data sharing:

```python
# Enable HTTP sync
sync = BrowserSync(enable_http_sync=True, cerebro_api_url="http://localhost:5000/api")
```

## Output Examples

### Unified Activity Data
```python
{
    'unified_activity': [
        {
            'source': 'browser',
            'domain_app': 'github.com',
            'category': 'focus',
            'duration_seconds': 180,
            'timestamp': 1640995200000,
            'metadata': {'domain': 'github.com', 'visit_count': 4}
        },
        {
            'source': 'app',
            'domain_app': 'chrome.exe',
            'category': 'application',
            'duration_seconds': 0,
            'timestamp': 1640995200000,
            'metadata': {'app': 'chrome.exe', 'window_title': 'GitHub'}
        }
    ],
    'hours_analyzed': 24,
    'last_sync': '2024-01-15T10:30:00'
}
```

## Integration with Mental Burnout Tracker

The browser sync script integrates seamlessly with the Mental Burnout Tracker:

- **Data Source**: Reads from Chrome extension storage
- **App Integration**: Merges with existing app usage data
- **Unified Analysis**: Provides combined insights
- **Real-time Sync**: Configurable sync intervals
- **Persistent Storage**: SQLite database storage

## Testing

### Quick Test
```bash
# Test for 30 seconds with 1-minute sync interval
python browser_sync.py --duration 30 --sync-interval 1
```

### Sample Data
The `extension_data/` directory contains sample files for testing:
- `site_visit_history.json`: Sample visit timestamps
- `site_category_stats.json`: Sample category statistics
- `tab_switches.json`: Sample tab switch count

## Troubleshooting

### Common Issues

1. **Extension Data Not Found**: Ensure JSON files exist in `extension_data/` directory
2. **Database Errors**: Check file permissions and disk space
3. **Sync Failures**: Check log files for detailed error messages
4. **App Data Missing**: Ensure Cerebro's database exists and contains data

### Log Files
- `browser_sync.log`: Detailed sync operation logs

## Future Enhancements

- **Real-time Extension Communication**: Direct communication with Chrome extension
- **Advanced Analytics**: Machine learning-based activity analysis
- **Export Functionality**: CSV/JSON export of unified data
- **Web Dashboard**: Real-time activity visualization
- **Mobile Integration**: Sync with mobile app data

## Contributing

When modifying the browser sync script:

1. Maintain backward compatibility with existing data formats
2. Update documentation for new features
3. Test with sample extension data
4. Follow the existing code style
5. Add appropriate error handling

## License

Part of the Mental Burnout Tracker project. 