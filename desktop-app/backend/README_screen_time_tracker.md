# Screen Time Tracker

A comprehensive Python service that runs all day and logs total screen time by detecting active periods (excluding idle time). The service automatically resets daily totals at midnight and stores data in a local SQLite database with detailed session tracking.

## Features

- **24/7 Monitoring**: Runs continuously to track screen time throughout the day
- **Active Period Detection**: Detects when user is actively using the computer
- **Idle Time Exclusion**: Automatically excludes periods of inactivity
- **Daily Reset**: Automatically resets totals at midnight (configurable)
- **Session Tracking**: Detailed logging of active and idle sessions
- **Cross-platform Support**: Works on Windows, macOS, and Linux
- **SQLite Storage**: Efficient local database storage with indexed queries
- **CSV Export**: Export screen time data to CSV files
- **Thread-safe**: Safe for multi-threaded applications
- **Graceful Shutdown**: Proper cleanup on application exit

## Database Schema

The module creates a SQLite database with two main tables:

### Screen Time Table
```sql
CREATE TABLE screen_time (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_active_time REAL DEFAULT 0.0,
    total_idle_time REAL DEFAULT 0.0,
    break_count INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    avg_session_length REAL DEFAULT 0.0,
    longest_session REAL DEFAULT 0.0,
    shortest_session REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Screen Sessions Table
```sql
CREATE TABLE screen_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    duration_seconds REAL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Columns

#### Screen Time Table
- `id`: Unique identifier for each record
- `date`: The date for this screen time entry
- `total_active_time`: Total active screen time in seconds
- `total_idle_time`: Total idle time in seconds
- `break_count`: Number of breaks (transitions from active to idle)
- `session_count`: Number of active sessions
- `avg_session_length`: Average length of active sessions
- `longest_session`: Duration of the longest active session
- `shortest_session`: Duration of the shortest active session
- `created_at`: When the record was created
- `updated_at`: When the record was last updated

#### Screen Sessions Table
- `id`: Unique identifier for each session
- `date`: The date of the session
- `session_start`: When the session started
- `session_end`: When the session ended
- `duration_seconds`: Duration of the session in seconds
- `is_active`: Whether this was an active (1) or idle (0) session
- `created_at`: When the session record was created

## Installation

### Dependencies

The module uses platform-specific libraries for idle detection:

#### Windows
```bash
pip install pywin32
```

#### macOS
```bash
pip install pyobjc-framework-Quartz
```

#### Linux
```bash
pip install python-xlib
```

### All Platforms
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from screen_time_tracker import ScreenTimeTracker

# Create tracker instance
tracker = ScreenTimeTracker(
    db_path="screen_time.db",
    idle_threshold=60,  # 60 seconds of inactivity
    check_interval=1.0,  # Check every second
    daily_reset_hour=0  # Reset at midnight
)

# Start tracking
tracker.start()

# ... your application code ...

# Stop tracking
tracker.stop()
```

### Integration with CereBro

The screen time tracker is automatically integrated into the CereBro backend:

```python
# In app_service.py
from screen_time_tracker import ScreenTimeTracker

# Initialize screen time tracker
screen_time_tracker = ScreenTimeTracker(
    db_path="screen_time.db",
    idle_threshold=60,  # 60 seconds of inactivity
    check_interval=1.0,  # Check every second
    daily_reset_hour=0  # Reset at midnight
)
screen_time_tracker.start()
```

### API Endpoints

The CereBro backend provides REST API endpoints for accessing screen time data:

#### Get Today's Screen Time Summary
```http
GET /api/screen_time_summary
```

Response:
```json
{
    "date": "2024-01-01",
    "total_active_time": 28800.0,
    "total_idle_time": 7200.0,
    "break_count": 15,
    "session_count": 25,
    "avg_session_length": 1152.0,
    "longest_session": 3600.0,
    "shortest_session": 60.0,
    "total_time": 36000.0,
    "active_percentage": 80.0
}
```

#### Get Weekly Screen Time Summary
```http
GET /api/screen_time_weekly
```

Response:
```json
{
    "period": "week",
    "total_active_time": 201600.0,
    "total_idle_time": 50400.0,
    "total_break_count": 105,
    "total_session_count": 175,
    "avg_daily_active": 28800.0,
    "avg_daily_idle": 7200.0,
    "daily_data": [
        {
            "date": "2024-01-01",
            "active_time": 28800.0,
            "idle_time": 7200.0,
            "break_count": 15,
            "session_count": 25
        }
    ]
}
```

#### Get Recent Sessions
```http
GET /api/screen_time_sessions?hours=24
```

Response:
```json
{
    "sessions": [
        {
            "session_start": "2024-01-01T09:00:00",
            "session_end": "2024-01-01T09:30:00",
            "duration_seconds": 1800.0,
            "is_active": true
        }
    ],
    "total_entries": 48
}
```

#### Export to CSV
```http
GET /api/export_screen_time_csv?days=7
```

Response:
```json
{
    "success": true,
    "file_path": "screen_time_export_1704067200.csv",
    "message": "Exported 7 days of screen time data to screen_time_export_1704067200.csv"
}
```

## Configuration

### ScreenTimeTracker Parameters

- `db_path`: Path to SQLite database file (default: "screen_time.db")
- `idle_threshold`: Seconds of inactivity before considering idle (default: 60)
- `check_interval`: How often to check for activity in seconds (default: 1.0)
- `daily_reset_hour`: Hour of day to reset daily totals (0-23, default: 0)

### Logging Configuration

The module uses Python's logging module with the following configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screen_time_tracker.log'),
        logging.StreamHandler()
    ]
)
```

## Platform-Specific Implementation

### Windows
- Uses `GetLastInputInfo` API for accurate idle detection
- Uses `ctypes` to interface with Windows API
- Provides most accurate results on Windows

### macOS
- Uses Core Graphics framework for idle detection
- Requires `pyobjc-framework-Quartz` dependency
- Provides good accuracy on macOS

### Linux
- Uses X11 for idle detection
- Requires `python-xlib` dependency
- Works well on X11-based Linux systems

## Methods

### Core Methods

#### `start()`
Start screen time tracking in a background thread.

#### `stop()`
Stop screen time tracking and save final data.

#### `get_today_summary()`
Get today's screen time summary.

#### `get_weekly_summary()`
Get weekly screen time summary.

#### `get_recent_sessions(hours=24)`
Get recent screen sessions from the last N hours.

#### `export_to_csv(csv_path, days=7)`
Export screen time data to a CSV file.

### Internal Methods

#### `_get_last_input_time()`
Get the last input time from the system.

#### `_check_activity()`
Check if the user is currently active.

#### `_check_daily_reset()`
Check if we need to reset daily totals.

#### `_save_daily_data()`
Save current daily data to database.

#### `_log_session()`
Log a screen session to the database.

#### `_tracking_loop()`
Main tracking loop that runs in a background thread.

## Testing

### Quick Test
```bash
python test_screen_time_tracker.py
```

### Manual Testing
```python
from screen_time_tracker import ScreenTimeTracker

tracker = ScreenTimeTracker(idle_threshold=10)  # 10 second idle threshold for testing
tracker.start()

# Stay active and idle for periods to test
import time
time.sleep(60)

tracker.stop()

# View results
summary = tracker.get_today_summary()
print(f"Active time: {summary['total_active_time']:.1f}s")
print(f"Idle time: {summary['total_idle_time']:.1f}s")
print(f"Break count: {summary['break_count']}")
```

### Command Line Usage

```bash
# Basic usage with 60-second idle threshold
python screen_time_tracker.py --idle-threshold 60 --duration 3600

# Export to CSV after completion
python screen_time_tracker.py --idle-threshold 60 --duration 3600 --export-csv screen_time.csv

# Custom database and reset hour
python screen_time_tracker.py --db custom_screen_time.db --reset-hour 6 --duration 7200

# Short intervals for testing
python screen_time_tracker.py --idle-threshold 10 --check-interval 0.5 --duration 300
```

## Performance Considerations

- **CPU Usage**: Minimal CPU usage, primarily for activity checking
- **Memory Usage**: Minimal memory footprint, primarily for session tracking
- **Database Size**: The database can grow large over time. Consider implementing a cleanup strategy
- **Accuracy**: Windows provides the most accurate idle detection. macOS and Linux implementations may vary

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure platform-specific dependencies are installed
2. **Permission Errors**: Some systems require elevated permissions for input monitoring
3. **Database Errors**: Check file permissions for the database directory
4. **No Activity Detection**: Try adjusting the idle threshold or check system settings

### Debug Mode

Enable debug logging by modifying the logging level:

```python
import logging
logging.getLogger('screen_time_tracker').setLevel(logging.DEBUG)
```

### Platform-Specific Issues

#### Windows
- Ensure `pywin32` is properly installed
- Check Windows security settings
- Verify user has appropriate permissions

#### macOS
- Install `pyobjc-framework-Quartz`
- Check accessibility permissions in System Preferences
- May require running with elevated permissions

#### Linux
- Install `python-xlib`
- Ensure X11 is running
- Check display permissions

## Integration Examples

### With Flask Application
```python
from flask import Flask
from screen_time_tracker import ScreenTimeTracker

app = Flask(__name__)
tracker = ScreenTimeTracker()

@app.before_first_request
def start_tracker():
    tracker.start()

@app.teardown_appcontext
def stop_tracker():
    tracker.stop()
```

### With Background Service
```python
import signal
from screen_time_tracker import ScreenTimeTracker

tracker = ScreenTimeTracker()

def signal_handler(signum, frame):
    tracker.stop()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

tracker.start()

# Keep the service running
while True:
    signal.pause()
```

### With Configuration Management
```python
import json
from screen_time_tracker import ScreenTimeTracker

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

tracker = ScreenTimeTracker(
    db_path=config.get('screen_time_db_path', 'screen_time.db'),
    idle_threshold=config.get('screen_time_idle_threshold', 60),
    check_interval=config.get('screen_time_check_interval', 1.0),
    daily_reset_hour=config.get('screen_time_reset_hour', 0)
)

tracker.start()
```

## Data Analysis

### Sample Queries

Get daily screen time trends:
```sql
SELECT 
    date,
    total_active_time / 3600.0 as active_hours,
    total_idle_time / 3600.0 as idle_hours,
    break_count,
    session_count
FROM screen_time 
ORDER BY date DESC
LIMIT 30;
```

Get average session length by day:
```sql
SELECT 
    date,
    AVG(duration_seconds) as avg_session_length,
    COUNT(*) as session_count
FROM screen_sessions 
WHERE is_active = 1
GROUP BY date
ORDER BY date DESC;
```

Get longest sessions:
```sql
SELECT 
    session_start,
    session_end,
    duration_seconds / 60.0 as duration_minutes
FROM screen_sessions 
WHERE is_active = 1
ORDER BY duration_seconds DESC
LIMIT 10;
```

Get break patterns:
```sql
SELECT 
    strftime('%H', session_start) as hour,
    COUNT(*) as break_count,
    AVG(duration_seconds) as avg_break_length
FROM screen_sessions 
WHERE is_active = 0
GROUP BY strftime('%H', session_start)
ORDER BY hour;
```

## Privacy and Security

### Privacy Features

- **Local Storage**: All data stored in local SQLite database
- **No Content Recording**: Only tracks activity timing, never records content
- **No Network Transmission**: No automatic data transmission
- **User Control**: Users can enable/disable tracking through preferences

### Security Considerations

- **Local Storage**: All data stored in local SQLite database
- **No Remote Access**: No automatic data transmission
- **User Control**: Users can enable/disable tracking through preferences
- **Transparent Operation**: Clear logging of all activities

## License

This module is part of the CereBro Mental Burnout Tracker project and follows the same license terms.

## Contributing

When contributing to the screen time tracker:

1. Test on multiple platforms
2. Follow the existing code style
3. Add appropriate error handling
4. Update documentation for new features
5. Add tests for new functionality
6. Consider performance implications
7. Ensure proper cleanup on shutdown 