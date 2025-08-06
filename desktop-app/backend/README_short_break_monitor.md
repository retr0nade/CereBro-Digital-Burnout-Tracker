# Short Break Monitor

A Python script that monitors user inactivity over short durations (2-15 minutes) and logs them as breaks. Optionally detects system lock/unlock events.

## Features

- **Short Break Detection**: Monitors inactivity periods between 2-15 minutes (configurable)
- **System Lock Detection**: Optional detection of system lock/unlock events
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **SQLite Database**: Persistent storage of break data
- **Real-time Logging**: Comprehensive logging of all events
- **Data Export**: Export break data to CSV format
- **Configurable Parameters**: Customizable break duration ranges and check intervals

## Installation

### Prerequisites

The script uses existing dependencies from the project's `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Platform-Specific Dependencies

- **Windows**: Uses `pywin32` (already in requirements)
- **macOS**: Uses `pyobjc-framework-Quartz` (already in requirements)
- **Linux**: Uses `python-xlib` (already in requirements)

## Usage

### Basic Usage

```python
from short_break_monitor import ShortBreakMonitor

# Create monitor with default settings (2-15 minute breaks)
monitor = ShortBreakMonitor()

# Start monitoring
monitor.start()

# ... your application logic ...

# Stop monitoring
monitor.stop()
```

### Advanced Usage

```python
from short_break_monitor import ShortBreakMonitor

# Create monitor with custom settings
monitor = ShortBreakMonitor(
    db_path="my_breaks.db",
    min_break_seconds=180,    # 3 minutes minimum
    max_break_seconds=600,    # 10 minutes maximum
    check_interval=2.0,       # Check every 2 seconds
    enable_lock_detection=True # Enable system lock detection
)

# Start monitoring
monitor.start()

# Get recent breaks
breaks = monitor.get_recent_breaks(hours=24)

# Get summary statistics
summary = monitor.get_break_summary(hours=24)

# Export to CSV
monitor.export_to_csv("breaks_export.csv", hours=24)

# Stop monitoring
monitor.stop()
```

### Command Line Usage

```bash
# Basic usage with default settings
python short_break_monitor.py

# Custom break duration range (3-8 minutes)
python short_break_monitor.py --min-break 180 --max-break 480

# Disable system lock detection
python short_break_monitor.py --no-lock-detection

# Export data to CSV after completion
python short_break_monitor.py --export-csv breaks.csv

# Run for specific duration (10 minutes)
python short_break_monitor.py --duration 600
```

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_path` | str | "short_breaks.db" | SQLite database file path |
| `min_break_seconds` | int | 120 | Minimum seconds to consider a break |
| `max_break_seconds` | int | 900 | Maximum seconds before considering it long idle |
| `check_interval` | float | 1.0 | How often to check for activity (seconds) |
| `enable_lock_detection` | bool | True | Whether to detect system lock/unlock events |

## Database Schema

### Short Breaks Table

```sql
CREATE TABLE short_breaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    break_start TIMESTAMP NOT NULL,
    break_end TIMESTAMP,
    duration_seconds REAL,
    system_locked BOOLEAN DEFAULT FALSE,
    lock_start TIMESTAMP,
    lock_end TIMESTAMP,
    lock_duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### System Locks Table

```sql
CREATE TABLE system_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lock_start TIMESTAMP NOT NULL,
    lock_end TIMESTAMP,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Reference

### ShortBreakMonitor Class

#### Constructor

```python
ShortBreakMonitor(
    db_path: str = "short_breaks.db",
    min_break_seconds: int = 120,
    max_break_seconds: int = 900,
    check_interval: float = 1.0,
    enable_lock_detection: bool = True
)
```

#### Methods

##### `start()`
Start the short break monitoring.

##### `stop()`
Stop the short break monitoring and log any current break.

##### `get_recent_breaks(hours: int = 24) -> List[Dict[str, Any]]`
Get recent short breaks from the last N hours.

Returns a list of dictionaries with break data:
```python
{
    'break_start': datetime,
    'break_end': datetime,
    'duration_seconds': float,
    'system_locked': bool,
    'lock_start': datetime,
    'lock_end': datetime,
    'lock_duration_seconds': float
}
```

##### `get_break_summary(hours: int = 24) -> Dict[str, Any]`
Get summary statistics of short break activity.

Returns a dictionary with summary data:
```python
{
    'total_breaks': int,
    'total_break_time': float,
    'avg_break_duration': float,
    'max_break_duration': float,
    'min_break_duration': float,
    'breaks_with_lock': int,
    'hours_analyzed': int
}
```

##### `export_to_csv(csv_path: str, hours: int = 24)`
Export short breaks to a CSV file.

## Platform Support

### Windows
- Uses `GetLastInputInfo` API for accurate idle detection
- System lock detection via Windows API
- Requires `pywin32` package

### macOS
- Uses Core Graphics framework for idle detection
- System lock detection via macOS APIs
- Requires `pyobjc-framework-Quartz` package

### Linux
- Uses X11 for idle detection
- System lock detection via X11 events
- Requires `python-xlib` package

## Testing

Run the comprehensive test suite:

```bash
python test_short_break_monitor.py
```

The test suite includes:
- Basic functionality testing
- System lock detection testing
- Custom break range testing
- Data export functionality
- Concurrent usage scenarios
- Error handling validation

## Integration with Existing System

The short break monitor can be integrated with the existing mental burnout tracker system:

```python
# In your main application
from short_break_monitor import ShortBreakMonitor
from idle_monitor import IdleMonitor

# Run both monitors
short_break_monitor = ShortBreakMonitor(
    min_break_seconds=120,  # 2 minutes
    max_break_seconds=900   # 15 minutes
)

idle_monitor = IdleMonitor(
    timeout_seconds=1800     # 30 minutes
)

# Start both monitors
short_break_monitor.start()
idle_monitor.start()

# Your application logic here...

# Stop both monitors
short_break_monitor.stop()
idle_monitor.stop()
```

## Logging

The script creates a log file `short_break_monitor.log` with detailed information about:
- Monitor start/stop events
- Break detection and logging
- System lock/unlock events
- Error messages and debugging information

## Performance Considerations

- **Check Interval**: Lower intervals provide more responsive detection but use more CPU
- **Database Size**: Consider archiving old data for long-running deployments
- **Memory Usage**: Minimal memory footprint, primarily for logging and state tracking

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all platform-specific dependencies are installed
2. **Permission Errors**: Ensure write permissions for database and log files
3. **Platform Detection**: Verify the script correctly identifies your operating system

### Debug Mode

Enable debug logging by modifying the logging configuration:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

### Example 1: Basic Break Monitoring

```python
from short_break_monitor import ShortBreakMonitor
import time

monitor = ShortBreakMonitor()
monitor.start()

# Let it run for 10 minutes
time.sleep(600)

monitor.stop()

# Get results
breaks = monitor.get_recent_breaks(hours=1)
for break_data in breaks:
    print(f"Break: {break_data['duration_seconds']:.1f}s")
```

### Example 2: Custom Break Analysis

```python
from short_break_monitor import ShortBreakMonitor

monitor = ShortBreakMonitor(
    min_break_seconds=300,  # 5 minutes
    max_break_seconds=600   # 10 minutes
)

monitor.start()
# ... your application ...
monitor.stop()

# Analyze break patterns
summary = monitor.get_break_summary(hours=24)
print(f"Average break duration: {summary['avg_break_duration']:.1f} seconds")
print(f"Total break time: {summary['total_break_time'] / 3600:.1f} hours")
```

### Example 3: Integration with Web Dashboard

```python
from flask import Flask, jsonify
from short_break_monitor import ShortBreakMonitor

app = Flask(__name__)
monitor = ShortBreakMonitor()

@app.route('/api/breaks')
def get_breaks():
    breaks = monitor.get_recent_breaks(hours=24)
    return jsonify(breaks)

@app.route('/api/breaks/summary')
def get_break_summary():
    summary = monitor.get_break_summary(hours=24)
    return jsonify(summary)

if __name__ == '__main__':
    monitor.start()
    app.run(debug=True)
```

## License

This script is part of the Mental Burnout Tracker project and follows the same licensing terms. 