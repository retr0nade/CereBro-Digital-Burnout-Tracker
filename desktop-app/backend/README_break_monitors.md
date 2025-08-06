# Break Monitor Scripts

This directory contains Python scripts that monitor user inactivity over short durations (2-15 minutes) and log them as breaks. The scripts also optionally detect system lock/unlock events.

## Available Scripts

### 1. `short_break_monitor.py` (Full-Featured)
A comprehensive break monitoring script with advanced features:
- Cross-platform support (Windows, macOS, Linux)
- System lock/unlock detection
- SQLite database storage
- CSV export functionality
- Configurable break duration ranges
- Real-time logging
- Thread-safe operation

### 2. `simple_break_monitor.py` (Lightweight)
A simplified version focusing on core functionality:
- Basic break detection
- SQLite database storage
- Configurable parameters
- Easy to understand and modify

### 3. `example_short_break_usage.py` (Examples)
Demonstrates various usage patterns and configurations.

## Features

### Core Functionality
- **Short Break Detection**: Monitors inactivity periods between 2-15 minutes (configurable)
- **System Lock Detection**: Optional detection of system lock/unlock events
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **SQLite Database**: Persistent storage of break data
- **Real-time Logging**: Comprehensive logging of all events
- **Data Export**: Export break data to CSV format
- **Configurable Parameters**: Customizable break duration ranges and check intervals

### Break Detection Logic
- Monitors user activity using system APIs
- Considers periods of inactivity as "breaks" when they fall within the configured range
- Logs break start time, end time, and duration
- Tracks whether the system was locked during the break
- Ignores periods shorter than minimum or longer than maximum duration

## Installation

### Prerequisites
The scripts use dependencies from the project's `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Platform-Specific Dependencies
- **Windows**: Uses `pywin32` (already in requirements)
- **macOS**: Uses `pyobjc-framework-Quartz` (already in requirements)
- **Linux**: Uses `python-xlib` (already in requirements)

## Usage

### Command Line Usage

#### Basic Usage (Simple Version)
```bash
# Run with default settings (2-15 minute breaks)
python simple_break_monitor.py

# Run for 10 minutes with custom break range (3-8 minutes)
python simple_break_monitor.py --duration 600 --min-break 180 --max-break 480

# Disable system lock detection
python simple_break_monitor.py --no-lock-detection

# Use custom database file
python simple_break_monitor.py --db my_breaks.db
```

#### Advanced Usage (Full-Featured Version)
```bash
# Run with default settings
python short_break_monitor.py

# Custom break duration range (3-8 minutes)
python short_break_monitor.py --min-break 180 --max-break 480

# Export data to CSV after completion
python short_break_monitor.py --export-csv breaks.csv

# Run for specific duration (10 minutes)
python short_break_monitor.py --duration 600

# Disable system lock detection
python short_break_monitor.py --no-lock-detection
```

### Programmatic Usage

#### Basic Integration
```python
from simple_break_monitor import SimpleBreakMonitor

# Create monitor with default settings
monitor = SimpleBreakMonitor()

# Start monitoring
monitor.start()

# ... your application logic ...

# Stop monitoring
monitor.stop()

# Get results
breaks = monitor.get_recent_breaks(hours=24)
summary = monitor.get_break_summary(hours=24)
```

#### Advanced Integration
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

## Configuration Parameters

### SimpleBreakMonitor Parameters
- `min_break_seconds`: Minimum seconds of inactivity to consider a break (default: 120)
- `max_break_seconds`: Maximum seconds before considering it a long idle period (default: 900)
- `check_interval`: How often to check for activity in seconds (default: 1.0)
- `enable_lock_detection`: Whether to detect system lock/unlock events (default: True)
- `db_path`: Path to SQLite database file (default: "simple_breaks.db")

### ShortBreakMonitor Parameters
- `db_path`: Path to SQLite database file (default: "short_breaks.db")
- `min_break_seconds`: Minimum seconds of inactivity to consider a break (default: 120)
- `max_break_seconds`: Maximum seconds before considering it a long idle period (default: 900)
- `check_interval`: How often to check for activity in seconds (default: 1.0)
- `enable_lock_detection`: Whether to detect system lock/unlock events (default: True)

## Database Schema

### Breaks Table
```sql
CREATE TABLE breaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds REAL,
    system_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### System Locks Table
```sql
CREATE TABLE system_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lock_time TIMESTAMP NOT NULL,
    unlock_time TIMESTAMP,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Output Examples

### Break Data
```python
{
    'start_time': '2024-01-15 10:30:00',
    'end_time': '2024-01-15 10:32:30',
    'duration_seconds': 150.0,
    'system_locked': False
}
```

### Summary Data
```python
{
    'total_breaks': 5,
    'total_break_time': 750.0,
    'avg_break_duration': 150.0,
    'max_break_duration': 300.0,
    'min_break_duration': 120.0,
    'hours_analyzed': 24
}
```

## Testing

### Run Examples
```bash
# Run usage examples
python example_short_break_usage.py

# Run tests
python test_short_break_monitor.py
```

### Quick Test
```bash
# Test for 30 seconds with 5-60 second break range
python simple_break_monitor.py --duration 30 --min-break 5 --max-break 60
```

## Platform Support

### Windows
- Uses `GetLastInputInfo` API for idle detection
- System lock detection available
- Full feature support

### macOS
- Uses Core Graphics for idle detection
- System lock detection available (requires Quartz)
- Full feature support

### Linux
- Uses X11 for idle detection
- System lock detection available (requires Xlib)
- Full feature support

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission Errors**: Run with appropriate permissions for system access

3. **Database Errors**: Check file permissions and disk space

4. **Platform-Specific Issues**: 
   - Windows: Ensure `pywin32` is installed
   - macOS: Install `pyobjc-framework-Quartz`
   - Linux: Install `python-xlib`

### Log Files
- `simple_break_monitor.log`: Log file for simple version
- `short_break_monitor.log`: Log file for full-featured version

## Integration with Mental Burnout Tracker

These scripts are designed to integrate with the Mental Burnout Tracker application:

- Data can be accessed via the API routes
- Database files are compatible with the main application
- Logging follows the same format as other components
- Configuration can be managed through the settings system

## Contributing

When modifying these scripts:

1. Maintain backward compatibility
2. Update tests accordingly
3. Document new features
4. Follow the existing code style
5. Test on multiple platforms

## License

Part of the Mental Burnout Tracker project. 