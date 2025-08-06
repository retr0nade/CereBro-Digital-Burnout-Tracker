# User Idle Monitor

A comprehensive Python module for monitoring user inactivity using mouse and keyboard events. This module is integrated into the CereBro Mental Burnout Tracker to provide detailed idle period analytics.

## Features

- **Cross-platform Support**: Windows, macOS, and Linux
- **Real-time Monitoring**: Continuously tracks mouse and keyboard activity
- **Configurable Timeout**: Adjustable idle detection threshold
- **SQLite Storage**: Efficient database storage with indexed queries
- **CSV Export**: Export idle data to CSV files
- **Detailed Logging**: Comprehensive logging with configurable levels
- **Thread-safe**: Safe for multi-threaded applications
- **Integration Ready**: Easy integration with existing applications

## Database Schema

The module creates a SQLite database with the following structure:

```sql
CREATE TABLE idle_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idle_start TIMESTAMP NOT NULL,
    idle_end TIMESTAMP,
    duration_seconds REAL,
    timeout_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Columns

- `id`: Unique identifier for each record
- `idle_start`: When the idle period started
- `idle_end`: When the idle period ended
- `duration_seconds`: Duration of the idle period (in seconds)
- `timeout_seconds`: The timeout threshold that triggered this idle period
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
from idle_monitor import IdleMonitor

# Create monitor instance
monitor = IdleMonitor(
    db_path="idle_activity.db",
    timeout_seconds=300,  # 5 minutes
    check_interval=1.0    # Check every second
)

# Start monitoring
monitor.start()

# ... your application code ...

# Stop monitoring
monitor.stop()
```

### Integration with CereBro

The idle monitor is automatically integrated into the CereBro backend:

```python
# In app_service.py
from idle_monitor import IdleMonitor

# Initialize idle monitor
idle_timeout = settings.get("idle_threshold", 180)
idle_monitor = IdleMonitor(
    db_path="idle_activity.db", 
    timeout_seconds=idle_timeout, 
    check_interval=1.0
)
idle_monitor.start()
```

### API Endpoints

The CereBro backend provides REST API endpoints for accessing idle activity data:

#### Get Recent Idle Activity
```http
GET /api/idle_activity?hours=24
```

Response:
```json
{
    "idle_periods": [
        {
            "idle_start": "2024-01-01T10:00:00",
            "idle_end": "2024-01-01T10:05:30",
            "duration_seconds": 330.5,
            "timeout_seconds": 300
        }
    ],
    "total_entries": 15
}
```

#### Get Idle Summary
```http
GET /api/idle_summary?hours=24
```

Response:
```json
{
    "total_periods": 15,
    "total_idle_time": 7200.5,
    "avg_idle_duration": 480.0,
    "max_idle_duration": 1800.0,
    "min_idle_duration": 300.0,
    "hours_analyzed": 24
}
```

#### Export to CSV
```http
GET /api/export_idle_csv?hours=24
```

Response:
```json
{
    "success": true,
    "file_path": "idle_export_1704067200.csv",
    "message": "Exported 24 hours of idle data to idle_export_1704067200.csv"
}
```

## Configuration

### IdleMonitor Parameters

- `db_path`: Path to SQLite database file (default: "idle_activity.db")
- `timeout_seconds`: Seconds of inactivity before logging idle period (default: 300)
- `check_interval`: How often to check for activity in seconds (default: 1.0)

### Logging Configuration

The module uses Python's logging module with the following configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('idle_monitor.log'),
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
Start idle monitoring in a background thread.

#### `stop()`
Stop idle monitoring and log the final idle period if active.

#### `get_recent_idle_periods(hours=24)`
Get recent idle periods from the last N hours.

#### `get_idle_summary(hours=24)`
Get a summary of idle activity statistics.

#### `export_to_csv(csv_path, hours=24)`
Export idle periods to a CSV file.

### Internal Methods

#### `_get_last_input_time()`
Get the last input time from the system.

#### `_check_activity()`
Check if the user is currently active.

#### `_log_idle_period()`
Log an idle period to the database.

#### `_monitoring_loop()`
Main monitoring loop that runs in a background thread.

## Testing

### Quick Test
```bash
python test_idle_monitor.py
```

### Manual Testing
```python
from idle_monitor import IdleMonitor

monitor = IdleMonitor(timeout_seconds=10)  # 10 second timeout for testing
monitor.start()

# Stay inactive for 15 seconds to trigger idle detection
import time
time.sleep(15)

monitor.stop()

# View results
idle_periods = monitor.get_recent_idle_periods(hours=1)
for idle_start, idle_end, duration, timeout in idle_periods:
    print(f"{idle_start} to {idle_end}: {duration:.1f}s")
```

### Command Line Usage

```bash
# Basic usage with 5-minute timeout
python idle_monitor.py --timeout 300 --duration 60

# Export to CSV after completion
python idle_monitor.py --timeout 300 --duration 60 --export-csv idle_data.csv

# Custom database and interval
python idle_monitor.py --db custom_idle.db --interval 0.5 --timeout 180
```

## Performance Considerations

- **CPU Usage**: The monitoring loop runs every second by default. Adjust `check_interval` as needed.
- **Memory Usage**: Minimal memory footprint, primarily for the SQLite connection.
- **Database Size**: The database can grow large over time. Consider implementing a cleanup strategy.
- **Accuracy**: Windows provides the most accurate idle detection. macOS and Linux implementations may vary.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure platform-specific dependencies are installed
2. **Permission Errors**: Some systems require elevated permissions for input monitoring
3. **Database Errors**: Check file permissions for the database directory
4. **No Idle Detection**: Try adjusting the timeout value or check system settings

### Debug Mode

Enable debug logging by modifying the logging level:

```python
import logging
logging.getLogger('idle_monitor').setLevel(logging.DEBUG)
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
from idle_monitor import IdleMonitor

app = Flask(__name__)
monitor = IdleMonitor()

@app.before_first_request
def start_monitor():
    monitor.start()

@app.teardown_appcontext
def stop_monitor():
    monitor.stop()
```

### With Background Service
```python
import signal
from idle_monitor import IdleMonitor

monitor = IdleMonitor()

def signal_handler(signum, frame):
    monitor.stop()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

monitor.start()

# Keep the service running
while True:
    signal.pause()
```

### With Configuration Management
```python
import json
from idle_monitor import IdleMonitor

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

monitor = IdleMonitor(
    db_path=config.get('idle_db_path', 'idle_activity.db'),
    timeout_seconds=config.get('idle_timeout', 300),
    check_interval=config.get('idle_check_interval', 1.0)
)

monitor.start()
```

## Data Analysis

### Sample Queries

Get total idle time per day:
```sql
SELECT 
    DATE(idle_start) as date,
    SUM(duration_seconds) as total_idle_time
FROM idle_activity 
GROUP BY DATE(idle_start)
ORDER BY date;
```

Get average idle duration by hour:
```sql
SELECT 
    strftime('%H', idle_start) as hour,
    AVG(duration_seconds) as avg_duration
FROM idle_activity 
GROUP BY strftime('%H', idle_start)
ORDER BY hour;
```

Get longest idle periods:
```sql
SELECT 
    idle_start,
    idle_end,
    duration_seconds
FROM idle_activity 
ORDER BY duration_seconds DESC
LIMIT 10;
```

## License

This module is part of the CereBro Mental Burnout Tracker project and follows the same license terms.

## Contributing

When contributing to the idle monitor:

1. Test on multiple platforms
2. Follow the existing code style
3. Add appropriate error handling
4. Update documentation for new features
5. Add tests for new functionality
6. Consider performance implications 