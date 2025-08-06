# Window Activity Tracker

A comprehensive Python module for tracking active window changes across different operating systems. This module is integrated into the CereBro Mental Burnout Tracker to provide detailed application usage analytics.

## Features

- **Cross-platform Support**: Windows, macOS, and Linux
- **Real-time Tracking**: Monitors active window changes in the background
- **SQLite Storage**: Efficient database storage with indexed queries
- **Detailed Logging**: Comprehensive logging with configurable levels
- **Thread-safe**: Safe for multi-threaded applications
- **Integration Ready**: Easy integration with existing applications

## Database Schema

The module creates a SQLite database with the following structure:

```sql
CREATE TABLE window_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    window_title TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds REAL,
    process_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Columns

- `id`: Unique identifier for each record
- `app_name`: Name of the active application (e.g., "chrome.exe", "notepad.exe")
- `window_title`: Title of the active window
- `start_time`: When the window became active
- `end_time`: When the window became inactive
- `duration_seconds`: Duration the window was active (in seconds)
- `process_id`: Process ID of the application
- `created_at`: When the record was created

## Installation

### Dependencies

The module requires different dependencies based on your operating system:

#### Windows
```bash
pip install pywin32 psutil
```

#### macOS
```bash
pip install pyobjc-framework-Quartz psutil
```

#### Linux
```bash
pip install python-xlib psutil
```

### All Platforms
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from window_tracker import WindowTracker

# Create tracker instance
tracker = WindowTracker(db_path="window_activity.db", log_interval=1.0)

# Start tracking
tracker.start()

# ... your application code ...

# Stop tracking
tracker.stop()
```

### Integration with CereBro

The window tracker is automatically integrated into the CereBro backend:

```python
# In app_service.py
from window_tracker import WindowTracker

# Initialize window tracker
window_tracker = WindowTracker(db_path="window_activity.db", log_interval=1.0)
window_tracker.start()
```

### API Endpoints

The CereBro backend provides REST API endpoints for accessing window activity data:

#### Get Recent Activity
```http
GET /api/window_activity?hours=24
```

Response:
```json
{
    "activity": [
        {
            "app_name": "chrome.exe",
            "window_title": "Google - Chrome",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T10:05:30",
            "duration_seconds": 330.5
        }
    ],
    "total_entries": 150
}
```

#### Get App Summary
```http
GET /api/window_summary?hours=24
```

Response:
```json
{
    "apps": [
        {
            "name": "chrome.exe",
            "sessions": 25,
            "total_duration": 7200.5,
            "avg_duration": 288.0
        }
    ],
    "total_sessions": 150,
    "total_duration": 28800.0
}
```

## Configuration

### WindowTracker Parameters

- `db_path`: Path to SQLite database file (default: "window_activity.db")
- `log_interval`: How often to check for window changes in seconds (default: 1.0)

### Logging Configuration

The module uses Python's logging module with the following configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('window_tracker.log'),
        logging.StreamHandler()
    ]
)
```

## Platform-Specific Implementation

### Windows
- Uses `win32gui` for window management
- Uses `win32process` for process information
- Uses `psutil` for process details

### macOS
- Uses `Quartz` framework for window management
- Uses `psutil` for process information

### Linux
- Uses `Xlib` for X11 window management
- Uses `psutil` for process information

## Methods

### Core Methods

#### `start()`
Start window tracking in a background thread.

#### `stop()`
Stop window tracking and log the final window activity.

#### `get_recent_activity(hours=24)`
Get recent window activity from the last N hours.

#### `get_app_summary(hours=24)`
Get a summary of app usage statistics.

### Internal Methods

#### `_get_active_window()`
Get information about the currently active window.

#### `_log_window_activity()`
Log window activity to the database.

#### `_tracking_loop()`
Main tracking loop that runs in a background thread.

## Testing

### Quick Test
```bash
python quick_test.py
```

### Full Test
```bash
python test_window_tracker.py
```

### Manual Testing
```python
from window_tracker import WindowTracker

tracker = WindowTracker()
tracker.start()

# Switch between applications for 30 seconds
import time
time.sleep(30)

tracker.stop()

# View results
activity = tracker.get_recent_activity(hours=1)
for app_name, window_title, start_time, end_time, duration in activity:
    print(f"{app_name}: {duration:.1f}s - {window_title}")
```

## Performance Considerations

- **Database Size**: The database can grow large over time. Consider implementing a cleanup strategy.
- **CPU Usage**: The tracking loop runs every second by default. Adjust `log_interval` as needed.
- **Memory Usage**: Minimal memory footprint, primarily for the SQLite connection.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure platform-specific dependencies are installed
2. **Permission Errors**: Some systems require elevated permissions for window tracking
3. **Database Errors**: Check file permissions for the database directory

### Debug Mode

Enable debug logging by modifying the logging level:

```python
import logging
logging.getLogger('window_tracker').setLevel(logging.DEBUG)
```

## Integration Examples

### With Flask Application
```python
from flask import Flask
from window_tracker import WindowTracker

app = Flask(__name__)
tracker = WindowTracker()

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
from window_tracker import WindowTracker

tracker = WindowTracker()

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

## License

This module is part of the CereBro Mental Burnout Tracker project and follows the same license terms.

## Contributing

When contributing to the window tracker:

1. Test on multiple platforms
2. Follow the existing code style
3. Add appropriate error handling
4. Update documentation for new features
5. Add tests for new functionality 